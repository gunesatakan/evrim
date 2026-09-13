"""Katman fizigi: cizilen lif fizigin lifidir, molekulun dairesi life gomulmez,
hucrenin geometrisi degisince katmanlar molekulun ustunden atlamaz, doz bagli
molekullerin sayisidir."""

import math
import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import lab
from organs.peripheral.membrane.logic_membrane import MembraneLogic

V = pygame.math.Vector2
PI = {p[0]: i for i, p in enumerate(lab.PAYLOADS)}
DT = 1.0 / 30.0


def _zar(*katmanlar):
    zar = MembraneLogic()
    for alan in ('mucus', 'capsule', 'slayer', 'wall'):
        setattr(zar, 'var_' + alan, alan in katmanlar)
    return zar


class _Hucre:
    """lab.Molecule'un bekledigi arayuz, GERCEK bir lab.Zarf uzerinde."""

    def __init__(self, zar, cekirdek=20.0):
        self.zar = zar
        self.center = V(600, 400)
        self.prev_center = V(self.center)
        self.generation = 0
        self.bagli = []
        self.tier_of = {}
        self.z = None
        self.cekirdek(cekirdek)

    def cekirdek(self, r):
        self.z = lab.zarf_geometrisi(self.zar, r)

    def active(self):
        return self.z.active()

    def boundaries(self):
        return self.z.boundaries()

    def flat_sheets(self):
        return self.z.flat_sheets()

    @property
    def core_r(self):
        return self.z.core_r

    @property
    def outer_r(self):
        return self.z.outer_r

    @property
    def pore_px(self):
        return self.z.pore_px

    @property
    def hiz_olcegi(self):
        return self.z.core_r / 110.0

    @property
    def arrived(self):
        return lab._bagli_say(self)

    def receive(self, mol):
        if all(m is not mol for m in self.bagli):
            self.bagli.append(mol)

    def agza_girdi(self, pos):
        return None


def _gomulme(hucre, m):
    """Serbest molekulun dairesi bir tabakanin katı parcasina ne kadar giriyor?

    Derinlik, dairenin katı bolgeden cikmak icin gitmesi gereken en kisa yol:
    radyal (tabakanin yuzeyine) ya da tegetsel (en yakin deligin kenarina).
    """
    d = m.pos - hucre.center
    r = d.length()
    a = math.atan2(d.y, d.x) % (2 * math.pi)
    rho = m.yaricap_px()
    en_kotu = 0.0
    for rr, _bi, sh in hucre.flat_sheets():
        if sh.tam_acik:
            continue
        derinlik = sh.h + rho - abs(r - rr)
        if derinlik <= 0.0 or sh.pencere(a, 2.0 * rho) is not None:
            continue
        m_aci = rho / rr
        teget = math.inf
        for a0, a1 in sh.acik:
            w0, w1 = a0 + m_aci, a1 - m_aci
            if w0 > w1:
                continue
            for x in (a, a + 2 * math.pi, a - 2 * math.pi):
                teget = min(teget, max(w0 - x, x - w1, 0.0) * rr)
        en_kotu = max(en_kotu, min(derinlik, teget))
    return en_kotu


def _firlat(hucre, ad, n, tohum):
    random.seed(tohum)
    mols = []
    v0 = lab.CARRIER_REACH[2] * lab._DRAG_K * hucre.hiz_olcegi * 0.5 * 2.0
    for k in range(n):
        a0 = 2 * math.pi * k / n
        yon = V(-math.cos(a0), -math.sin(a0)).rotate(random.uniform(-10, 10))
        p = hucre.center + V(math.cos(a0), math.sin(a0)) * (hucre.outer_r + 3.0)
        mols.append(lab.Molecule(hucre, p, yon * v0 * random.uniform(0.8, 1.2), PI[ad]))
    return mols


def _dondur(m):
    m.vel = V()
    m.jig = V()
    m.tumble = 1e9


def _katman_adi(hucre, m):
    b = m.band()
    if b < 0:
        return 'disarida'
    if b >= len(hucre.boundaries()):
        return 'sitoplazma'
    return hucre.active()[b].name


class KatmanFizigiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 240))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_cizilen_lif_fizigin_lifidir(self):
        """Her tabaka kendi yaricapinda, cizimle aci aci ayni yerde katı/acik."""
        olcek, N = 20.0, 1800
        for katmanlar in (('capsule', 'wall'), ('mucus', 'slayer')):
            zar = _zar(*katmanlar)
            yuz = pygame.Surface((N, N))
            yuz.fill((0, 0, 0))
            lab.zarf_ciz(yuz, zar, (0.0, 0.0), 20.0, olcek=olcek, kaydir=(N / 2, N / 2))
            z = lab.zarf_geometrisi(zar, 20.0)
            aktif = z.active()
            for rr, bi, sh in z.flat_sheets():
                if sh.solid or sh.tam_acik:
                    continue
                renk = tuple(aktif[bi].color)
                uyum = 0
                M = 720
                for k in range(M):
                    a = 2 * math.pi * (k + 0.5) / M
                    x = N / 2 + math.cos(a) * rr * olcek
                    y = N / 2 + math.sin(a) * rr * olcek
                    kati_cizim = tuple(yuz.get_at((int(x), int(y))))[:3] == renk
                    kati_fizik = sh.pencere(a, 0.0) is None
                    uyum += kati_cizim == kati_fizik
                self.assertGreaterEqual(
                    uyum / M, 0.96, "%s tabaka r=%.2f cizimle uyusmuyor: %%%.0f"
                    % (aktif[bi].name, rr, 100.0 * uyum / M))

    def test_serbest_molekulun_dairesi_life_gomulmez(self):
        for katmanlar in (('capsule', 'wall'), ('mucus', 'slayer', 'wall')):
            hucre = _Hucre(_zar(*katmanlar))
            for ad in ('Antimikrobiyal peptit', 'Lizozim', 'alfa-hemolizin'):
                mols = _firlat(hucre, ad, 16, 7)
                en_kotu = 0.0
                for _ in range(150):
                    for m in mols:
                        m.update(DT)
                        if m.state == 'free':
                            en_kotu = max(en_kotu, _gomulme(hucre, m))
                self.assertLess(en_kotu, 1e-3 * hucre.pore_px,
                                "%s %s life %.4f px gomuldu" % (katmanlar, ad, en_kotu))

    def test_kucuk_molekul_gecer_buyuk_molekul_duvarda_kalir(self):
        hucre = _Hucre(_zar('capsule', 'wall'))
        peptit = _firlat(hucre, 'Antimikrobiyal peptit', 12, 3)
        hemolizin = _firlat(hucre, 'alfa-hemolizin', 12, 3)
        for _ in range(180):
            for m in peptit + hemolizin:
                m.update(DT)
        self.assertGreaterEqual(sum(m.state == 'arrived' for m in peptit), 8)
        self.assertEqual(sum(m.state == 'arrived' for m in hemolizin), 0)

    def test_sisme_katmanlari_molekulun_ustunden_atlatmaz(self):
        hucre = _Hucre(_zar('capsule', 'wall'))
        b = hucre.boundaries()
        tab = sorted(rr for rr, _bi, sh in hucre.flat_sheets() if not sh.solid)
        # Peptit, lifler arasindaki her boslugun ORTASINA; hemolizin disarida.
        yerler = [('alfa-hemolizin', b[0] + 4.0, False), ('Antimikrobiyal peptit', b[0] + 1.2, False)]
        for alt, ust in zip(tab, tab[1:]):
            yerler.append(('Antimikrobiyal peptit', (alt + ust) * 0.5, False))
        # Igneyle sitoplazmaya birakilmis yuzey toksini: iceriden baglanmaz.
        yerler.append(('Norotoksin', hucre.core_r * 0.5, True))
        mols = []
        for i, (ad, r, ignede) in enumerate(yerler):
            for k in range(6):
                a = 2 * math.pi * (k + 0.2 * i) / 6
                m = lab.Molecule(hucre, hucre.center + V(math.cos(a), math.sin(a)) * r, V(), PI[ad])
                m.injected = ignede
                _dondur(m)
                mols.append(m)
        for m in mols:
            m.update(DT)
            _dondur(m)
        self.assertTrue(all(m.state == 'free' for m in mols))
        self.assertTrue(all(_gomulme(hucre, m) < 1e-3 * hucre.pore_px for m in mols))
        once = [_katman_adi(hucre, m) for m in mols]
        for carpan in (1.18, 1.0 / 1.18):
            hucre.cekirdek(hucre.core_r * carpan)
            for _ in range(3):
                for m in mols:
                    _dondur(m)
                    m.update(DT)
            sonra = [_katman_adi(hucre, m) for m in mols]
            self.assertEqual(once, sonra, "carpan %.3f" % carpan)
            self.assertTrue(all(_gomulme(hucre, m) < 1e-3 * hucre.pore_px for m in mols))

    def test_sismede_bagli_molekul_bagli_kalir_ve_dozu_suresinde_duser(self):
        hucre = _Hucre(_zar())
        mols = _firlat(hucre, 'Antimikrobiyal peptit', 16, 5)
        for _ in range(240):
            for m in mols:
                m.update(DT)
        bagli = [m for m in mols if m.state == 'arrived']
        self.assertGreaterEqual(len(bagli), 12)
        self.assertEqual(hucre.arrived.get(PI['Antimikrobiyal peptit'], 0), len(bagli))
        koruma = lab.KORUMA_TETIK
        hucre.cekirdek(hucre.core_r * 1.18)
        for _ in range(30):
            for m in mols:
                m.update(DT)
        self.assertEqual(lab.KORUMA_TETIK, koruma)
        self.assertTrue(all(m.state == 'arrived' for m in bagli))
        zari = hucre.boundaries()[-1]
        for m in bagli:
            d = m.pos.distance_to(hucre.center)
            self.assertGreaterEqual(d - m.yaricap_px(), hucre.core_r - 1e-6)
            self.assertLessEqual(d, zari + 1e-6)
        for _ in range(int((lab.CLEARANCE + 0.5) / DT)):
            for m in mols:
                m.update(DT)
        self.assertEqual(hucre.arrived, {})

    def test_bagli_molekul_capasi_koruma_tetiklemez(self):
        hucre = _Hucre(_zar())
        m = lab.Molecule(hucre, hucre.center + V(hucre.outer_r + 2.0, 0), V(), PI['Norotoksin'])
        self.assertTrue(m._bind(0, m.pos))
        self.assertEqual(m.state, 'arrived')
        koruma = lab.KORUMA_TETIK
        m.pos = V(hucre.center)             # eski bir konum: cekirdegin ortasi
        m.update(DT)
        self.assertEqual(m.state, 'arrived')
        self.assertEqual(lab.KORUMA_TETIK, koruma)
        self.assertGreater(m.pos.distance_to(hucre.center), hucre.core_r)

    def test_keseden_kacan_gozenek_acici_gorunur_ve_temizlenir(self):
        hucre = lab.LabCell((400, 400))
        pi = PI['alfa-hemolizin']
        kese = lab.Kese(hucre, 0.3, hucre.core_r * 0.2, pi)
        kese.update(DT)
        self.assertTrue(kese.teslim)
        cikan = hucre.cikanlari_al()
        self.assertEqual(len(cikan), 1)
        self.assertEqual(cikan[0].state, 'arrived')
        self.assertEqual(hucre.count_of(pi), 1)
        for _ in range(int((lab.CLEARANCE + 0.5) / DT)):
            cikan[0].update(DT)
        self.assertEqual(hucre.count_of(pi), 0)


if __name__ == "__main__":
    unittest.main()

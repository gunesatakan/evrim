"""Kemoreseptor: tek karelik algi ayni kalir; uzamsal yon ortalamasi tabani
sifir olan ayri bir gendir (hucre onu gen kopyalariyla dogar, bkz.
test_gen_dozu), gen buyudukce alici olcumu daha uzun ortalanir."""

import math
import os
import random
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import game_settings
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor
from organs.receptors.Chemoreceptor.logic_chemoreceptor import ChemoreceptorLogic

V = pygame.math.Vector2
DT = 1.0 / 30.0


class _Alan:
    """Kaynagi (0, 0) olan ustel koku alani."""

    def __init__(self, tepe, boy):
        self.tepe, self.boy = tepe, boy

    def get_concentration(self, x, y):
        return self.tepe * math.exp(-math.hypot(x, y) / self.boy)


def _yon(alicilar, ebeveyn):
    """Oyundaki uzamsal gradyan hesabi (Organism.update) ile ayni."""
    okumalar = [(a._taban_ve_boy(ebeveyn)[1], a.logic.yon_algisi(a._son)) for a in alicilar]
    if max(p for _y, p in okumalar) <= 0.0:
        return None
    ort = sum(p for _y, p in okumalar) / len(okumalar)
    v = V()
    for yon, p in okumalar:
        v += yon * (p - ort)
    if v.length() > max(0.02, ort * game_settings.SPATIAL_CHEMO_MIN):
        return v.normalize()
    return None


class KemoreseptorOrtalamaTests(unittest.TestCase):
    def setUp(self):
        self._gurultu = game_settings.CHEMO_GURULTU

    def tearDown(self):
        game_settings.CHEMO_GURULTU = self._gurultu

    def test_tek_karelik_algi_degismedi(self):
        game_settings.CHEMO_GURULTU = 0.0
        lg = ChemoreceptorLogic(length=6.0)
        esik = lg.scent_sensitivity
        self.assertEqual(lg.perceive(esik * 0.05, DT), 0.0)
        self.assertAlmostEqual(lg.perceive(esik * 4.0, DT), math.log(5.0))

    def test_gen_sifirken_yon_bu_karenin_algisidir(self):
        lg = ChemoreceptorLogic(length=6.0)
        self.assertEqual(lg.uzamsal_ortalama, game_settings.CHEMO_ORTALAMA_TABAN)
        self.assertEqual(lg.uzamsal_ortalama, 0.0)
        for olculen in (1.0, 5.0, 0.3):
            lg.ortalamaya_ekle(olculen, DT)
            self.assertEqual(lg.ort_ham, olculen)
        self.assertEqual(lg.yon_algisi(0.77), 0.77)

    def test_gen_buyur_ve_tavanda_durur(self):
        lg = ChemoreceptorLogic(length=6.0)
        lg.grow_ortalama()
        self.assertAlmostEqual(lg.uzamsal_ortalama, game_settings.GROW_CHEMO_ORTALAMA)
        for _ in range(100):
            lg.grow_ortalama()
        self.assertAlmostEqual(lg.uzamsal_ortalama, game_settings.CHEMO_ORTALAMA_MAX)

    def test_gen_ortalamanin_suresini_belirler(self):
        game_settings.CHEMO_GURULTU = 0.0
        for sure in (0.5, 2.0):
            lg = ChemoreceptorLogic(length=6.0)
            lg.uzamsal_ortalama = sure
            lg.ortalamaya_ekle(1.0, DT)
            for _ in range(int(round(sure / DT))):
                lg.ortalamaya_ekle(3.0, DT)
            # Gen suresi kadar sonra adimin ~%63'u (1 - 1/e) alinir.
            self.assertAlmostEqual((lg.ort_ham - 1.0) / 2.0, 1.0 - math.exp(-1.0), delta=0.02)
        kisa, uzun = ChemoreceptorLogic(6.0), ChemoreceptorLogic(6.0)
        kisa.uzamsal_ortalama, uzun.uzamsal_ortalama = 0.5, 2.0
        for lg in (kisa, uzun):
            lg.ortalamaya_ekle(1.0, DT)
            for _ in range(15):
                lg.ortalamaya_ekle(3.0, DT)
        self.assertGreater(kisa.ort_ham, uzun.ort_ham)

    def test_zayif_kokuda_ortalama_yonu_duzeltir(self):
        """Esigin uc kati kokuda: ortalama dogru yonu artirir, ters yonu azaltir."""
        esik = game_settings.SCENT_SENSITIVITY_BASE / 6.0
        boy, mesafe = 100.0, 320.0
        alan = _Alan(tepe=3.0 * esik * math.exp(mesafe / boy), boy=boy)
        sayac = {}
        for sure in (0.5, 0.0):
            random.seed(3)
            dogru = ters = kare_say = 0
            for deneme in range(36):
                aci = 2 * math.pi * deneme / 36
                ebeveyn = SimpleNamespace(
                    pos=V(math.cos(aci), math.sin(aci)) * mesafe,
                    direction=V(1, 0).rotate(deneme * 37.0), radius=22.45,
                    body=SimpleNamespace(logic=SimpleNamespace(radius=20.0)))
                dogru_yon = -ebeveyn.pos.normalize()
                alicilar = [Chemoreceptor(attachment_angle=a, length=6.0)
                            for a in (0.0, 2 * math.pi / 3, 4 * math.pi / 3)]
                for a in alicilar:
                    a.logic.uzamsal_ortalama = sure
                for kare in range(90):
                    for a in alicilar:
                        a._son = a.sample_environment(ebeveyn, alan, DT)
                    if kare < 30:
                        continue                     # ortalama otursun
                    kare_say += 1
                    v = _yon(alicilar, ebeveyn)
                    if v is None:
                        continue
                    derece = math.degrees(math.acos(max(-1.0, min(1.0, v.dot(dogru_yon)))))
                    if derece < 45.0:
                        dogru += 1
                    elif derece > 90.0:
                        ters += 1
            sayac[sure] = (dogru / kare_say, ters / kare_say)
        self.assertGreater(sayac[0.5][0], sayac[0.0][0] + 0.2, sayac)
        self.assertLess(sayac[0.5][1], sayac[0.0][1] * 0.5, sayac)


if __name__ == "__main__":
    unittest.main()

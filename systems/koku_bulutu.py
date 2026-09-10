# -*- coding: utf-8 -*-
"""Hucre koku bulutunun cizimi + populasyonun en hassas burnu.

Kemoreseptor bir hucrenin kokusunu alicisinin UCUNDAKI derisimden okur:

    C(d) = KOKU_YAYIM * koku * exp(-d / KOKU_BULUT)     d: kaynak yuzeyinden

Bu bulut ekranda hic cizilmiyordu: hucreler birbirine tepki verirken
ortada gorunen bir koku yoktu ve algi "temassiz" gibi duruyordu. Oysa
besin kokusu (isi haritasi) ve izler (diskler) ciziliyordu.

CIZILEN = DUYULABILEN. Bulutun kenari, populasyondaki EN HASSAS burnun
duyabilecegi son noktadir (C = esik_min); orayi kimse duyamaz, cizilmez.
Icerisi Weber-Fechner ile: algilanan siddet log(C/esik), mesafeyle
DOGRUSAL duser - alfa da oyle. Ayni kural isi haritasinin tabanina ve
izlere de uygulanir (bkz. en_hassas_esikler).
"""
import math

import pygame

import game_settings
from systems.signaling.scent_profile import koku_derisimi, koku_erimi

try:
    import numpy as _np
except ImportError:      # numpy yoksa damgali (daha kaba) yol kullanilir
    _np = None


def en_hassas_esikler(hucreler):
    """(koku esigi, iz esigi): populasyondaki en hassas burun.

    Cizimin kenari bununla belirlenir: bir koku kimsenin duyamayacagi
    kadar seyrekse ekranda da yoktur. Burnu olan hucre yoksa baslangic
    burnunun (boy 5) esikleri kullanilir - bulut fiziksel olarak orada.
    """
    koku = None
    iz = None
    for o in hucreler:
        if getattr(o, 'dead', False):
            continue
        for c in getattr(o, '_koku_alicilari', ()):
            e = c.logic.scent_sensitivity
            t = c.logic.smell_threshold
            if e > 0.0 and (koku is None or e < koku):
                koku = e
            if iz is None or t < iz:
                iz = t
    if koku is None:
        koku = game_settings.SCENT_SENSITIVITY_BASE / 5.0
    if iz is None:
        iz = 500.0 / 5.0
    return koku, iz


class KokuBulutu:
    """Butun hucrelerin koku bulutlarini tek bir dunya-boyu yuzeye cizer.

    BESIN ISI HARITASIYLA AYNI KALITE. Once her hucre icin hazir bir
    damga (ic ice daireler) basiliyordu; gradyan basamakliydi ve alfa
    yalnizca kabaca mesafeyle iniyordu. Artik izgara uzerinde GERCEK
    DERISIM ALANI hesaplanir - besin kokusunun yaptigi is - ve her
    izgara hucresinin alfasi tam olarak o noktada ALGILANAN SIDDETTIR:

        p = log(C / esik) / log(KOKU_DOYUM),   0..1

    Yani ekrandaki parlaklik, oraya giren bir burnun okuyacagi degerdir.
    Ust uste binen bulutlarda en guclusu gorunur; algi da her kaynagi
    ayri ayri esikle karsilastirir, toplamaz.

    Alan izgara cozunurlugunde uretilip smoothscale ile dunya boyuna
    buyutulur (isi haritasinin yolu): maliyet nufusla degil alanla
    orantili kalir.
    """

    #: Kac karede bir yeniden uretilir; bulut yavas degisir.
    ARALIK = 3

    def __init__(self, genislik, yukseklik, hucre_boyu=None):
        gs = int(hucre_boyu or game_settings.SCENT_CELL_SIZE)
        self.gs = max(1, gs)
        self.cols = max(1, int(genislik) // self.gs)
        self.rows = max(1, int(yukseklik) // self.gs)
        self.kucuk = pygame.Surface((self.cols, self.rows), pygame.SRCALPHA)
        self.boy = (self.cols * self.gs, self.rows * self.gs)
        self.onbellek = None
        self.yas = 10 ** 9
        self._damgalar = {}
        self._p = None            # algi alani (numpy), kare basina yeniden
        self._agirlik = None      # katki toplami (renk paydasi)
        self._renk = None         # katki x renk toplami
        self._rgba = None         # cizime hazir tampon

    @staticmethod
    def kenar(hucre, esik_min):
        """Bulutun kenari: kaynak MERKEZINDEN px. Kimse duyamiyorsa 0.

        Algiyla AYNI denklem - ikisi de scent_profile.koku_erimi'ni
        cagirir, cizim ile duyma birbirinden ayrilamaz.
        """
        return koku_erimi(hucre.scent_value, max(1.0, hucre.radius), esik_min)

    def _damga(self, renk, r0g, Rg, tepe):
        """Izgara biriminde radyal damga: kenarda 0, govdede `tepe` alfa.

        Buyukten kucuge daireler ust uste YAZILIR (cizim fonksiyonlari
        karistirmaz) - basamakli bir gradyan cikar. Her (renk, boy)
        icin bir kez uretilir, onbellekte kalir.
        """
        key = (renk, r0g, Rg, tepe)
        d = self._damgalar.get(key)
        if d is None:
            if len(self._damgalar) > 512:
                self._damgalar.clear()
            n = Rg * 2 + 1
            d = pygame.Surface((n, n), pygame.SRCALPHA)
            pay = max(1, Rg - r0g)
            for r in range(Rg, 0, -1):
                t = 1.0 if r <= r0g else (Rg - r) / pay
                a = int(round(tepe * min(1.0, t)))
                if a <= 0:
                    continue
                pygame.draw.circle(d, (renk[0], renk[1], renk[2], a), (Rg, Rg), r)
            self._damgalar[key] = d
        return d

    def ciz(self, hedef, hucreler, esik_min):
        tepe = int(getattr(game_settings, 'KOKU_BULUT_ALFA', 90))
        if tepe <= 0:
            return
        self.yas += 1
        if self.onbellek is None or self.yas >= self.ARALIK:
            self._uret(hucreler, esik_min, tepe)
            self.yas = 0
        hedef.blit(self.onbellek, (0, 0))

    def _uret(self, hucreler, esik_min, tepe):
        if _np is not None:
            self._uret_alan(hucreler, esik_min, tepe)
        else:
            self._uret_damga(hucreler, esik_min, tepe)

    def _uret_alan(self, hucreler, esik_min, tepe):
        """GERCEK DERISIM ALANI (numpy). Alfa = o noktada algilanan siddet.

        LOGARITMADA DOGRUSAL. Algi zaten logaritma aliyor; usluyu
        hesaplayip logunu almak iki islemin birbirini goturmesi demek.
        Acilmis hali izgara hucresi basina bir karekok + bir logaritma
        birakir, us alma tamamen duser:

            p = [ ln(yuzey*r0/esik) + r0/B - ln(d) - d/B ] / ln(DOYUM)

RENK KARISIR, ALFA EN GUCLUYU IZLER. Once her noktaya yalnizca
        en guclu kokan hucrenin rengi yaziliyordu; bulutlar arasinda
        Voronoi gibi keskin arklar cikiyordu. Oysa iki bulutun ortusrugu
        yerde alicilar IKI kaynagin da molekulunu yakalar. Renk artik
        katkilariyla agirlikli ortalama - gecisler yumusak. Alfa yine
        EN GUCLU kaynagin algisi: kenar tam olarak duyma sinirinda kalir.
        """
        np = _np
        gs = self.gs
        rows, cols = self.rows, self.cols
        if self._p is None:
            self._p = np.zeros((rows, cols), dtype=np.float32)
            self._agirlik = np.zeros((rows, cols), dtype=np.float32)
            self._renk = np.zeros((rows, cols, 3), dtype=np.float32)
            self._rgba = np.zeros((rows, cols, 4), dtype=np.uint8)
        p_alan = self._p          # en guclu algi -> alfa
        agirlik = self._agirlik   # katkilarin toplami -> renk paydasi
        renk_top = self._renk     # katki x renk toplami
        p_alan.fill(0.0)
        agirlik.fill(0.0)
        renk_top.fill(0.0)
        bulut = max(1.0, game_settings.KOKU_BULUT)
        ref = max(1e-6, getattr(game_settings, 'KOKU_REF_YARICAP', 22.45))
        yayim = game_settings.KOKU_YAYIM
        doyum = math.log(max(1.0001, game_settings.KOKU_DOYUM))
        ters_b = 1.0 / bulut
        ters_doyum = 1.0 / doyum
        for o in hucreler:
            if getattr(o, 'dead', False):
                continue
            R = self.kenar(o, esik_min)
            r0 = max(1.0, o.radius)
            if R <= r0:
                continue                      # kimse duyamaz: bulut yok
            kaynak = o.koku_kaynagi()          # hareketle geride kalan kaynak
            kx, ky = float(kaynak.x), float(kaynak.y)
            c0 = max(0, int((kx - R) // gs))
            c1 = min(cols, int((kx + R) // gs) + 1)
            s0 = max(0, int((ky - R) // gs))
            s1 = min(rows, int((ky + R) // gs) + 1)
            if c1 <= c0 or s1 <= s0:
                continue
            xs = (np.arange(c0, c1, dtype=np.float32) + 0.5) * gs - kx
            ys = (np.arange(s0, s1, dtype=np.float32) + 0.5) * gs - ky
            d2 = ys[:, None] * ys[:, None] + xs[None, :] * xs[None, :]
            np.maximum(d2, r0 * r0, out=d2)    # govde ici: yuzey degeri
            d = np.sqrt(d2)
            yuzey = yayim * o.scent_value * (r0 / ref)
            sabit = math.log(yuzey * r0 / esik_min) + r0 * ters_b
            p = np.log(d)
            p += d * ters_b
            np.subtract(sabit, p, out=p)
            p *= ters_doyum
            np.clip(p, 0.0, 1.0, out=p)
            # ALFA: en guclu kaynak (kenar = duyma siniri)
            dilim = p_alan[s0:s1, c0:c1]
            np.maximum(dilim, p, out=dilim)
            # RENK: katkisiyla agirlikli - ortusen bulutlar karisir
            agirlik[s0:s1, c0:c1] += p
            renk_top[s0:s1, c0:c1] += p[:, :, None] * np.asarray(
                o.color[:3], dtype=np.float32)
        rgba = self._rgba
        np.maximum(agirlik, 1e-6, out=agirlik)
        renk_top /= agirlik[:, :, None]
        np.clip(renk_top, 0.0, 255.0, out=renk_top)
        rgba[..., :3] = renk_top
        np.multiply(p_alan, float(tepe), out=p_alan)
        rgba[..., 3] = p_alan
        yuz = self._yuzeye(rgba.tobytes(), cols, rows)
        self.onbellek = pygame.transform.smoothscale(yuz, self.boy)

    @staticmethod
    def _yuzeye(ham, cols, rows):
        """RGBA tamponu -> EKRAN BICIMINDE yuzey.

        frombuffer'in verdigi yuzeyde bayt sirasi ekraninkinin TERSI
        (RGBA / BGRA). Donusturulmeden blit edilirse pygame her pikseli
        tek tek cevirir: 2400x1600'de kare basina 30 ms - alan
        hesabinin kendisinin dort kati. convert_alpha bunu 3.5 ms'ye
        indirir.
        """
        yuz = pygame.image.frombuffer(ham, (cols, rows), 'RGBA')
        try:
            return yuz.convert_alpha()
        except pygame.error:      # ekran kipi yoksa (basli basina test)
            return yuz

    def _uret_damga(self, hucreler, esik_min, tepe):
        """numpy yoksa: hazir damgalar. Daha kaba ama calisir."""
        k = self.kucuk
        k.fill((0, 0, 0, 0))
        gs = self.gs
        for o in hucreler:
            if getattr(o, 'dead', False):
                continue
            R = self.kenar(o, esik_min)
            r0 = max(1.0, o.radius)
            if R <= r0:
                continue
            Rg = max(1, int(round(R / gs)))
            r0g = int(round(r0 / gs))
            renk = tuple(int(c) // 8 * 8 for c in o.color[:3])
            kaynak = o.koku_kaynagi()
            cx = int(math.floor(kaynak.x / gs))
            cy = int(math.floor(kaynak.y / gs))
            k.blit(self._damga(renk, r0g, Rg, tepe), (cx - Rg, cy - Rg),
                   special_flags=pygame.BLEND_RGBA_MAX)
        self.onbellek = pygame.transform.smoothscale(k, self.boy)

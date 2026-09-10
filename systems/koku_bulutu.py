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

    Isi haritasiyla ayni yol: izgara cozunurlugunde kucuk bir yuzeye
    damgalar basilir, sonra smoothscale ile dunya boyuna buyutulur.
    Ust uste binen bulutlarda EN GUCLUSU gorunur (BLEND_RGBA_MAX):
    algi da her kaynagi ayri ayri esikle karsilastirir, toplamaz -
    toplama olsaydi yuz hucrenin bulutu ekrani tek renge boyardi.
    Hucre basina ekran boyunda gradyan cizmek 100 hucrede kare basina
    on milyonlarca piksel demekti; bu yol nufustan bagimsiz.
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

    @staticmethod
    def kenar(hucre, esik_min):
        """Bulutun kenari: kaynak MERKEZINDEN px. Kimse duyamiyorsa 0.

        Algi ile ayni denklem (perceive_and_decide): alici ucundaki
        derisim C = YAYIM * koku * exp(-(d - r0) / BULUT) esigi asarsa
        koku alinir. Kenar, C = esik_min cozumudur.
        """
        sv = game_settings.KOKU_YAYIM * hucre.scent_value
        if sv <= 0.0 or esik_min <= 0.0:
            return 0.0
        oran = sv / esik_min
        if oran <= 1.0:
            return 0.0
        r0 = max(1.0, hucre.radius)
        return max(1.0, game_settings.KOKU_BULUT) * math.log(oran) + r0

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
        k = self.kucuk
        k.fill((0, 0, 0, 0))
        gs = self.gs
        for o in hucreler:
            if getattr(o, 'dead', False):
                continue
            R = self.kenar(o, esik_min)
            if R <= 0.0:
                continue                      # kimse duyamaz: bulut yok
            r0 = max(1.0, o.radius)
            Rg = max(1, int(round(R / gs)))
            r0g = int(round(r0 / gs))
            renk = tuple(int(c) // 8 * 8 for c in o.color[:3])
            kaynak = o.koku_kaynagi()          # hareketle geride kalan kaynak
            cx = int(math.floor(kaynak.x / gs))
            cy = int(math.floor(kaynak.y / gs))
            k.blit(self._damga(renk, r0g, Rg, tepe), (cx - Rg, cy - Rg),
                   special_flags=pygame.BLEND_RGBA_MAX)
        self.onbellek = pygame.transform.smoothscale(k, self.boy)

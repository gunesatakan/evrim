# -*- coding: utf-8 -*-
"""ISIK ALANI: haritaya konulan aydinlik bolgeler.

FIZIK - NEDEN USSEL, NEDEN 1/d^2 DEGIL.

Suda isik iki sekilde zayiflar: kaynaktan uzaklastikca ayni foton sayisi
buyuyen bir kureye dagilir (1/d^2, GEOMETRIK) ve su ile cozunmus madde
fotonu yutar (Beer-Lambert, USSEL). Hangisinin baskin oldugu KAYNAGIN
BICIMINE baglidir:

  - Noktasal bir lamba icin 1/d^2 baskindir ve isik birkac gövde boyunda
    biter. Yaricapi 40 px olan bir lamba 800 px oteye yalnizca 1/400'unu
    gonderir - daha yutulma hesabina bile girmeden soner.
  - GENIS bir aydinlik yuzey (su yuzeyinden giren gun isigi, isildayan
    bir yosun tabakasi) icin geometrik seyrelme yoktur; alanin her
    noktasindan gelen isik toplandiginda 1/d^2 birbirini goturur.
    Geriye YALNIZCA yutulma kalir:

        I(d) = guc * exp(-d / lambda)

Buradaki kaynak ikincisidir: bir nokta degil, konulan bir BOLGE. Bu ayni
zamanda denizin fotik bolgesinin gercek profilidir - yuzeyde %100, oksijen
uretiminin durdugu derinlikte %1.

ERIM ve lambda: kullanici "erim"i verir (isigin bittigi uzaklik). lambda
oradan cikar - erimde siddet ISIK_KESIM'e (varsayilan %2) duser ve altinda
KARANLIK sayilir. Yani "haritanin en ustune konulan isik ortada biter"
demek, erim = harita yuksekliginin yarisi demektir.

TOPLANMA: iki isik ust uste geldiginde siddetleri TOPLANIR. Koku
imzalarindan farki bu - fotonun imzasi yoktur, hepsi ayni seydir ve ayni
alicida toplanir.
"""
import math

import game_settings

try:
    import numpy as _np
except ImportError:      # numpy yoksa cizim kabalasır, fizik degismez
    _np = None


def _kesim():
    k = float(getattr(game_settings, 'ISIK_KESIM', 0.02))
    return min(0.5, max(1e-4, k))


def lambda_px(erim):
    """Erimden yutulma boyu: I(erim) = ISIK_KESIM."""
    erim = max(1.0, float(erim))
    return erim / math.log(1.0 / _kesim())


def kaynaklar():
    """[(x, y, guc, erim)] - duzenleyicide konulan isiklar."""
    ham = getattr(game_settings, 'HARITA_ISIKLARI', None) or ()
    out = []
    for k in ham:
        if len(k) < 2:
            continue
        x = float(k[0]); y = float(k[1])
        guc = float(k[2]) if len(k) > 2 else 1.0
        erim = float(k[3]) if len(k) > 3 else varsayilan_erim()
        if guc > 0.0 and erim > 0.0:
            out.append((x, y, guc, erim))
    return out


def varsayilan_erim():
    """Haritanin en ustune konulan isik ORTASINDA bitsin: yukseklik / 2."""
    e = getattr(game_settings, 'ISIK_ERIM', 0.0)
    if e and float(e) > 0.0:
        return float(e)
    from entities.entity import HEIGHT
    return HEIGHT * 0.5


def siddet(x, y, kaynak_listesi=None):
    """(x, y) noktasindaki toplam isik siddeti. 0 = karanlik.

    Kaynaklar toplanir; tek bir kaynagin erimi disinda katkisi SIFIRDIR
    (kesim altinda karanlik sayilir), bu yuzden uzaktaki isiklar haritayi
    zeminden aydinlatmaz.
    """
    top = 0.0
    kes = _kesim()
    for kx, ky, guc, erim in (kaynaklar() if kaynak_listesi is None
                              else kaynak_listesi):
        dx = x - kx; dy = y - ky
        d = math.sqrt(dx * dx + dy * dy)
        if d >= erim:
            continue
        s = guc * math.exp(-d / lambda_px(erim))
        if s > guc * kes:
            top += s
    return top


def siddet_ve_yon(x, y, kaynak_listesi=None):
    """(siddet, yon) - yon, siddetle agirlikli kaynak merkezine dogru.

    Fototaksi ISIGIN GELDIGI yonu izler. Alici tek noktadan okuma yapar,
    ayri ayri kaynak goremez; okudugu sey tek bir aydinliktir. Bu yuzden
    yon de kaynaklarin siddetle agirlikli ortalamasidir - tam olarak
    ust uste binen koku bulutlarinda yapilan sey.
    """
    import pygame
    top = 0.0
    vx = vy = 0.0
    kes = _kesim()
    for kx, ky, guc, erim in (kaynaklar() if kaynak_listesi is None
                              else kaynak_listesi):
        dx = kx - x; dy = ky - y
        d = math.sqrt(dx * dx + dy * dy)
        if d >= erim:
            continue
        s = guc * math.exp(-d / lambda_px(erim))
        if s <= guc * kes:
            continue
        top += s
        vx += dx * s
        vy += dy * s
    if top <= 0.0:
        return 0.0, pygame.math.Vector2(0.0, 0.0)
    return top, pygame.math.Vector2(vx / top, vy / top)


def eksen(s):
    """Siddeti 0-100 DAVRANIS EKSENINE cevir.

    Eksen dogrusal degil logaritmik: alicilar isigi de kokuyu de
    Weber-Fechner ile okur, yani onemli olan siddetin kendisi degil kac
    KAT oldugudur. Kesim (%2) ekseni 0'dan, tam guc 100'den baslatir.
    """
    if s <= 0.0:
        return 0.0
    kes = _kesim()
    if s <= kes:
        return 0.0
    x = 100.0 * math.log(s / kes) / math.log(1.0 / kes)
    return 0.0 if x < 0.0 else (100.0 if x > 100.0 else x)


def besin_carpani(x, y):
    """Bu noktada besin kac kat olusur.

    Isik fotosentezi surer: aydinlik suda uretim yuksektir. Carpan
    siddetle DOGRUSAL artar - tam isikta ISIK_BESIN_CARPANI, karanlikta 1.
    """
    kat = float(getattr(game_settings, 'ISIK_BESIN_CARPANI', 2.0))
    s = min(1.0, siddet(x, y))
    return 1.0 + (kat - 1.0) * s


class IsikAlani:
    """Isik alanini ekrana cizer.

    Koku bulutuyla ayni yol: izgara uzerinde alan hesaplanir, smoothscale
    ile dunya boyuna buyutulur. Fark, kaynaklarin nasil birlestigi -
    isikta TOPLANIR (fotonun imzasi yoktur, hepsi ayni seydir), kokuda
    en guclusu gorunur (farkli molekuller ayri baglanma bolgelerine
    oturur). Toplama alanda yapilir; ekrana normal harmanla cizilir.
    """

    ARALIK = 6          # isik HIC degismez; nadiren yeniden uretilir

    def __init__(self, genislik, yukseklik, hucre_boyu=None):
        gs = int(hucre_boyu or getattr(game_settings, 'SCENT_CELL_SIZE', 10))
        self.gs = max(1, gs)
        self.cols = max(1, int(genislik) // self.gs)
        self.rows = max(1, int(yukseklik) // self.gs)
        self.boy = (self.cols * self.gs, self.rows * self.gs)
        self.onbellek = None
        self.yas = 10 ** 9
        self._imza = None

    def ciz(self, hedef):
        """Isigi zemine ciz.

        TOPLAMA ALANDA YAPILIR, HARMANDA DEGIL. Once toplamali harman
        (BLEND_RGBA_ADD) kullaniliyordu ve o kip alfayi bir maske olarak
        DEGIL bir kanal olarak toplar: siddeti sifir olan piksellerin
        rengi de eklenip butun haritayi sariya boyuyordu. Ust uste binen
        isiklarin toplanmasi zaten `_uret` icinde, siddet duzeyinde
        oluyor; harmanin normal olmasi hem dogru hem yeterli.
        """
        alfa = int(getattr(game_settings, 'ISIK_ALFA', 70))
        ks = kaynaklar()
        if alfa <= 0 or not ks:
            return
        imza = (tuple(map(tuple, ks)), alfa, _kesim())
        self.yas += 1
        if self.onbellek is None or self._imza != imza or self.yas >= self.ARALIK:
            self._uret(ks, alfa)
            self._imza = imza
            self.yas = 0
        hedef.blit(self.onbellek, (0, 0))

    def _uret(self, ks, alfa):
        import pygame
        gs = self.gs
        rows, cols = self.rows, self.cols
        renk = getattr(game_settings, 'ISIK_RENK', (255, 232, 150))
        if _np is None:
            self._uret_yavas(ks, alfa, renk)
            return
        np = _np
        alan = np.zeros((rows, cols), dtype=np.float32)
        kes = _kesim()
        for kx, ky, guc, erim in ks:
            lam = lambda_px(erim)
            c0 = max(0, int((kx - erim) // gs)); c1 = min(cols, int((kx + erim) // gs) + 1)
            s0 = max(0, int((ky - erim) // gs)); s1 = min(rows, int((ky + erim) // gs) + 1)
            if c1 <= c0 or s1 <= s0:
                continue
            xs = (np.arange(c0, c1, dtype=np.float32) + 0.5) * gs - kx
            ys = (np.arange(s0, s1, dtype=np.float32) + 0.5) * gs - ky
            d = np.sqrt(ys[:, None] * ys[:, None] + xs[None, :] * xs[None, :])
            s = guc * np.exp(-d / lam)
            s[d >= erim] = 0.0
            s[s <= guc * kes] = 0.0
            alan[s0:s1, c0:c1] += s
        np.clip(alan, 0.0, 1.0, out=alan)
        rgba = np.empty((rows, cols, 4), dtype=np.uint8)
        rgba[..., 0] = renk[0]; rgba[..., 1] = renk[1]; rgba[..., 2] = renk[2]
        rgba[..., 3] = (alan * float(alfa)).astype(np.uint8)
        yuz = pygame.image.frombuffer(rgba.tobytes(), (cols, rows), 'RGBA')
        try:
            yuz = yuz.convert_alpha()   # bayt sirasi ekranınkiyle ayni olsun
        except pygame.error:
            pass
        self.onbellek = pygame.transform.smoothscale(yuz, self.boy)

    def _uret_yavas(self, ks, alfa, renk):
        """numpy yoksa: izgarayi elle dolas."""
        import pygame
        gs = self.gs
        kucuk = pygame.Surface((self.cols, self.rows), pygame.SRCALPHA)
        for r in range(self.rows):
            wy = (r + 0.5) * gs
            for c in range(self.cols):
                s = min(1.0, siddet((c + 0.5) * gs, wy, ks))
                if s <= 0.0:
                    continue
                kucuk.set_at((c, r), (renk[0], renk[1], renk[2],
                                      int(s * alfa)))
        self.onbellek = pygame.transform.smoothscale(kucuk, self.boy)

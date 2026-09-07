# -*- coding: utf-8 -*-
"""Evrim olcutleri: uc basari kriterini SAYIYA cevirir.

Kriterler goz kararasi degerlendirilemez. "Avlanma basladi" demek icin
avin gercekten silahla oldurulup yenmis olmasi, "ogrendi" demek icin
davranis tablosunun rastgeleden ISTATISTIKSEL olarak ayrilmasi gerekir.
Bu dosya her olcutu tek bir sayiya indirger; boylece bir degisiklik
sonrasi ileri mi gittik geri mi, tartisilmadan gorulur.
"""
import math

from organs.peripheral.weapons.weapons import BaseWeapon
from systems.signaling.behavior_genome import BehaviorGenome

SILAH_ADLARI = ("Stylet", "Harpoon", "Nematocyst", "Toxin", "Lysin",
                "Phagocytosis")
KATMANLAR = ("wall", "capsule", "mucus", "slayer")


def _zar(o):
    return getattr(getattr(o, 'membrane', None), 'logic', None)


def silah_sayisi(o):
    return sum(1 for x in o.organs if isinstance(x, BaseWeapon))


def savunma_puani(o):
    """Katman yatirimlarinin toplami - yalnizca VAR OLAN katmanlar."""
    z = _zar(o)
    if z is None:
        return 0.0
    puan = getattr(z, 'katman_puani', None)
    if callable(puan):
        return sum(float(puan(a)) for a in KATMANLAR)
    return sum(float(getattr(z, a, 0.0)) for a in KATMANLAR)


def katman_sayisi(o):
    z = _zar(o)
    if z is None:
        return 0
    var = getattr(z, 'katman_var', None)
    if callable(var):
        return sum(1 for a in KATMANLAR if var(a))
    return 0


# ---------------------------------------------------------------- OLCUT 2
def spektrum_egilimi(o):
    """Bu hucre "zayifa saldir, gucluden kac" der mi?

    Koku ekseni 0-100: 50 = benimle esit, altinda benden zayif, ustunde
    benden guclu. Ekseni 0.5 adimlarla tarayip her konumda tepkiyi okuruz.

    Doner: (saldiri_egilimi, kacis_egilimi)
      saldiri_egilimi : zayif tarafta saldiri orani - guclu tarafta saldiri orani
      kacis_egilimi   : guclu tarafta kacis orani  - zayif tarafta kacis orani

    Ikisi de rastgele bir tabloda 0 civarinda olur. Pozitife kayarsa
    populasyon "kimden kacilir kime saldirilir" ayrimini ogrenmis demektir;
    negatife kayarsa TERS ogrenmis demektir - ki bu da gecerli bir sonuctur,
    yeter ki sifirdan uzaklassin.
    """
    b = getattr(o, 'behavior', None)
    if b is None:
        return 0.0, 0.0
    zayif_s = zayif_k = guclu_s = guclu_k = 0
    n = 0
    x = 0.0
    while x < 50.0:
        r1 = b.spectrum_response(x)
        r2 = b.spectrum_response(100.0 - x)
        zayif_s += (r1 == 'attack')
        zayif_k += (r1 == 'flee')
        guclu_s += (r2 == 'attack')
        guclu_k += (r2 == 'flee')
        n += 1
        x += 0.5
    if not n:
        return 0.0, 0.0
    return (zayif_s - guclu_s) / n, (guclu_k - zayif_k) / n


def kairomon_kacisi(o):
    """"Yakinda avlanmis birinden kac" ogrenildi mi?

    Kairomon, avcinin AV YEDIGINI ele veren sizintidir; kutu 0 temiz,
    5 taze ve cok yemis. Yuksek kutularda kacis orani ile dusuk
    kutulardaki kacis orani arasindaki fark olculur.
    """
    b = getattr(o, 'behavior', None)
    if b is None:
        return 0.0
    dusuk = yuksek = 0
    nd = ny = 0
    for c in range(BehaviorGenome.KAIROMONE_BINS):
        for lvl in range(BehaviorGenome.LEVEL_BINS):
            r = b.respond('kairomone', c, lvl)
            if c <= 1:
                dusuk += (r == 'flee'); nd += 1
            elif c >= 4:
                yuksek += (r == 'flee'); ny += 1
    if not nd or not ny:
        return 0.0
    return yuksek / ny - dusuk / nd


# ---------------------------------------------------------------- OZET
def _ort(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs):
    xs = list(xs)
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def olc(d):
    """Dunyanin o anki durumundan olcut sozlugu uret."""
    h = d.hucreler
    n = len(h)
    if not n:
        return {"t": round(d.gecen_sure, 1), "n": 0}

    silahli = [o for o in h if silah_sayisi(o) > 0]
    savunmali = [o for o in h if savunma_puani(o) > 0.5]
    # SAVUNMACI TIP: zirhi var, silahi yok. Ikisini de tasiyan bir hucre
    # "savunma tipi" degildir; ayirt edici olan seyi TASIMAMASI.
    savunmaci = [o for o in savunmali if silah_sayisi(o) == 0]

    sal, kac = zip(*(spektrum_egilimi(o) for o in h)) if h else ((0,), (0,))
    silah_dagilim = {}
    for o in h:
        for x in o.organs:
            if isinstance(x, BaseWeapon):
                ad = x.__class__.__name__
                silah_dagilim[ad] = silah_dagilim.get(ad, 0) + 1

    return {
        "t": round(d.gecen_sure, 1),
        "n": n,
        "dogum": d.dogum,
        "besin": len(d.foods),
        # --- olcut 1: silahli avlanma ---
        "silahli_oran": round(len(silahli) / n, 3),
        "silah": silah_dagilim,
        "silah_olum": dict(d.silah_olumu),
        "av_yeme": d.av_yeme,
        # --- olcut 2: ogrenilmis kac/saldir ---
        "saldiri_egilimi": round(_ort(sal), 4),
        "kacis_egilimi": round(_ort(kac), 4),
        "kairomon_kacisi": round(_ort(kairomon_kacisi(o) for o in h), 4),
        # --- olcut 3: savunma tipleri ---
        "savunma_ort": round(_ort(savunma_puani(o) for o in h), 3),
        "savunma_std": round(_std([savunma_puani(o) for o in h]), 3),
        "savunmaci_oran": round(len(savunmaci) / n, 3),
        "katman_ort": round(_ort(katman_sayisi(o) for o in h), 3),
        # --- genel ---
        "organ_ort": round(_ort(len(o.organs) for o in h), 2),
        "olum": dict(d.olum_nedeni),
    }

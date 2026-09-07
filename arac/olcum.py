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
from systems.signaling.behavior_genome import BehaviorGenome, etiket

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
#
# DIKKAT: burasi "populasyon BENIM kuralimi ogrendi mi" diye sormaz.
#
# Kural dayatilmamali. Sans eseri silah kazanmis bir hucrenin etrafinda,
# ona saldiranlar olur ve kacanlar yasar; kural kodda degil OLULERDE
# birikir. Bu yuzden asagidakiler bir HEDEF degil, birer GOZLEM: davranis
# ekseninin nereye yerlestigini tarif ederler.
#
# "Ogrenildi mi" sorusunun kanitlayici cevabi arac/rekabet.py'dedir:
# evrimlesmis tabloyu AYNI BEDENDE rastgele tabloya karsi yaristirmak.

def spektrum_ozeti(o):
    """Koku ekseni boyunca tepkinin sekli.

    Doner: (ortalama, kararlilik, zayif_taraf, guclu_taraf)
      ortalama    : eksenin tamamindaki ortalama tepki (-1..1)
      kararlilik  : |tepki| ortalamasi - 0'a yakinsa hucre umursamiyor,
                    1'e yakinsa her karsilasmada tam gucle tepki veriyor
      zayif_taraf : kendinden ZAYIF kokanlara ortalama tepki
      guclu_taraf : kendinden GUCLU kokanlara ortalama tepki
    """
    b = getattr(o, 'behavior', None)
    if b is None:
        return 0.0, 0.0, 0.0, 0.0
    top = kar = zayif = guclu = 0.0
    n = 0
    x = 0.0
    while x < 50.0:
        r1 = b.spectrum_response(x)
        r2 = b.spectrum_response(100.0 - x)
        zayif += r1
        guclu += r2
        top += r1 + r2
        kar += abs(r1) + abs(r2)
        n += 1
        x += 0.5
    if not n:
        return 0.0, 0.0, 0.0, 0.0
    return top / (2 * n), kar / (2 * n), zayif / n, guclu / n


def ses_ozeti(o):
    """SES ekseninin sekli: (ortalama, kararlilik, kucuge, iriye)."""
    b = getattr(o, 'behavior', None)
    if b is None:
        return 0.0, 0.0, 0.0, 0.0
    top = kar = kucuk = iri = 0.0
    n = 0
    x = 0.0
    while x < 50.0:
        r1 = b.ses_tepkisi(x)
        r2 = b.ses_tepkisi(100.0 - x)
        kucuk += r1
        iri += r2
        top += r1 + r2
        kar += abs(r1) + abs(r2)
        n += 1
        x += 0.5
    if not n:
        return 0.0, 0.0, 0.0, 0.0
    return top / (2 * n), kar / (2 * n), kucuk / n, iri / n


def renk_ozeti(o):
    """RENK cemberinin sekli: (ortalama, kararlilik)."""
    b = getattr(o, 'behavior', None)
    if b is None:
        return 0.0, 0.0
    top = kar = 0.0
    n = 0
    x = 0.0
    while x < 100.0:
        r = b.renk_tepkisi(x)
        top += r
        kar += abs(r)
        n += 1
        x += 1.0
    if not n:
        return 0.0, 0.0
    return top / n, kar / n


def kairomon_tepkisi(o):
    """Yakinda avlanmis birine verilen tepki eksi temiz birine verilen.

    Negatif = "yemek yemis olandan uzak dur" yonunde bir ayrim var.
    """
    b = getattr(o, 'behavior', None)
    if b is None:
        return 0.0
    dusuk = yuksek = 0.0
    nd = ny = 0
    for c in range(BehaviorGenome.KAIROMONE_BINS):
        for lvl in range(BehaviorGenome.LEVEL_BINS):
            r = b.respond('kairomone', c, lvl)
            if c <= 1:
                dusuk += r; nd += 1
            elif c >= 4:
                yuksek += r; ny += 1
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


def silah_gucu(o):
    """Tasinan silahlarin toplam gucu."""
    return sum(float(x.logic.power) for x in o.organs
               if isinstance(x, BaseWeapon))


def uzmanlasma(h):
    """Populasyon SILAH ve ZIRH ekseninde ayrisiyor mu?

    "Savunma tipi ortaya cikti" demek icin yalnizca zirhin yayilmasi
    yetmez - herkes hem zirhli hem silahli olabilir, o zaman ortada bir
    TIP yoktur. Ayrisma, iki yatirimin birbiriyle TERS gitmesidir: kimi
    hucre zirha yatirir ve silahtan vazgecer, kimi tersini yapar.

    Pearson korelasyonu doner. Negatif = uzmanlasma (savunmaci ve avci
    ayri tipler), 0 = ilgisiz, pozitif = "cok tasiyan cok tasiyor".
    """
    if len(h) < 3:
        return 0.0
    xs = [savunma_puani(o) for o in h]
    ys = [silah_gucu(o) for o in h]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs)
    sy = sum((y - my) ** 2 for y in ys)
    if sx <= 1e-12 or sy <= 1e-12:
        return 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sx * sy)


# ---------------------------------------------------------------- OZET
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

    ozet = [spektrum_ozeti(o) for o in h]
    tepki_ort = _ort(x[0] for x in ozet)
    kararlilik = _ort(x[1] for x in ozet)
    zayif = _ort(x[2] for x in ozet)
    guclu = _ort(x[3] for x in ozet)
    sozet = [ses_ozeti(o) for o in h]
    ses_kararlilik = _ort(x[1] for x in sozet)
    ses_ayrim = _ort(x[2] - x[3] for x in sozet)   # kucuge - iriye
    rozet = [renk_ozeti(o) for o in h]
    renk_kararlilik = _ort(x[1] for x in rozet)
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
        "atis": sum(getattr(o, 'atis_sayisi', 0) for o in h),
        "silah_guc": round(_ort(
            [max((x.logic.power for x in o.organs
                  if isinstance(x, BaseWeapon)), default=0.0) for o in h]), 3),
        # --- olcut 2: davranis ekseninin sekli (GOZLEM, hedef degil) ---
        "tepki_ort": round(tepki_ort, 4),
        "kararlilik": round(kararlilik, 4),
        "zayifa_tepki": round(zayif, 4),
        "gucluye_tepki": round(guclu, 4),
        "ayrim": round(zayif - guclu, 4),
        "kairomon_tepkisi": round(_ort(kairomon_tepkisi(o) for o in h), 4),
        # uc spektrumun kendi kararliliklari (rastgele genomda ~0.50)
        "ses_kararlilik": round(ses_kararlilik, 4),
        "ses_ayrim": round(ses_ayrim, 4),
        "renk_kararlilik": round(renk_kararlilik, 4),
        # anlik surus: uc kanalin BILESKESI
        "surus_ort": round(_ort(abs(getattr(o, 'current_response', 0.0))
                                for o in h), 4),
        "motor_efor": round(_ort(getattr(o, 'motor_efor', 0.0) for o in h), 4),
        "sosyal_ort": round(_ort(
            getattr(getattr(o, 'behavior', None), 'sosyal_oncelik', 0.0)
            for o in h), 3),
        # --- olcut 3: savunma tipleri ---
        "savunma_ort": round(_ort(savunma_puani(o) for o in h), 3),
        "savunma_std": round(_std([savunma_puani(o) for o in h]), 3),
        "savunmaci_oran": round(len(savunmaci) / n, 3),
        "silahli_savunmali": round(
            sum(1 for o in h if silah_sayisi(o) > 0 and savunma_puani(o) > 0.5)
            / n, 3),
        "katman_ort": round(_ort(katman_sayisi(o) for o in h), 3),
        "uzmanlasma": round(uzmanlasma(h), 3),
        "zirhli_oran": round(
            sum(1 for o in h if savunma_puani(o) > 0.5) / n, 3),
        # --- genel ---
        "organ_ort": round(_ort(len(o.organs) for o in h), 2),
        "hiz_ort": round(_ort(getattr(o, 'speed', 0.0) for o in h), 2),
        "burun_ort": round(_ort(
            sum(1 for x in o.organs
                if x.__class__.__name__ == 'Chemoreceptor') for o in h), 3),
        "govde_ort": round(_ort(
            getattr(getattr(o, 'body', None), 'logic', None).size
            if getattr(o, 'body', None) is not None else 0.0 for o in h), 3),
        "sindirim_ort": round(_ort(
            getattr(getattr(getattr(o, 'body', None), 'logic', None),
                    'enzyme', None).base_digestion_time
            if getattr(o, 'body', None) is not None else 0.0 for o in h), 2),
        "hafiza_ort": round(_ort(
            getattr(getattr(o, 'direction_memory', None), 'capacity', 0)
            for o in h), 1),
        "kamci_ort": round(_ort(
            sum(1 for x in o.organs
                if x.__class__.__name__ == 'Flagella') for o in h), 3),
        "goz_ort": round(_ort(
            sum(1 for x in o.organs
                if x.__class__.__name__ == 'Photoreceptor') for o in h), 3),
        "kulak_ort": round(_ort(
            sum(1 for x in o.organs
                if x.__class__.__name__ == 'Mechanoreceptor') for o in h), 3),
        "renk_cesit": len({o.color for o in h}),
        "bant": {k: round(v, 3) for k, v in _bant_ortalama(h).items()},
        "olum": dict(d.olum_nedeni),
    }


def _bant_ortalama(h):
    """Koku ekseninin ne kadari hangi tepki bolgesinde.

    Surekli deger okunabilir olsun diye bes bolgeye ayrilir:
    kac / uzaklas / yoksay / yaklas / saldir. Rastgele bir genomda
    dagilim yaklasik esittir; uclara yigilma bir sey secildigini gosterir.
    """
    top = {r: 0.0 for r in BehaviorGenome.ETIKETLER}
    for o in h:
        b = getattr(o, 'behavior', None)
        if b is None:
            continue
        n = 0
        x = 0.0
        while x <= 100.0:
            top[etiket(b.spectrum_response(x))] += 1.0
            n += 1
            x += 2.0
        for k in top:
            pass
    toplam = sum(top.values()) or 1.0
    return {k: v / toplam for k, v in top.items()}

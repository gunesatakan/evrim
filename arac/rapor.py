# -*- coding: utf-8 -*-
"""Kosu ciktisini uc BASARI OLCUTUNE gore degerlendirir.

Tek bir kosunun sonucu kanit degildir: evrim sansa cok duyarlidir ve bir
tohumda gorulen egilim otekinde tersine donebilir. Bu yuzden her olcut
TOHUMLAR ARASINDA degerlendirilir - kac tohumda gerceklesti, ortalama ne,
sifirdan ne kadar uzak (standart hataya gore).
"""
import argparse
import json
import math


def _ort(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def _sh(xs):
    """Ortalamanin standart hatasi."""
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(var / len(xs))


def _son(kayit):
    return kayit[-1] if kayit else {}


def _ilk(kayit):
    return kayit[0] if kayit else {}


def _t(deger, sifir=0.0):
    """Kaba bir t degeri: ortalamanin sifirdan kac standart hata uzakta."""
    o, h = _ort(deger), _sh(deger)
    return 0.0 if h <= 0 else (o - sifir) / h


def rapor(veri):
    ham = veri["ham"]
    n_tohum = len(ham)
    son = [_son(k) for k in ham]
    ilk = [_ilk(k) for k in ham]

    print("=" * 68)
    print("EVRIM RAPORU  |  %d tohum x %.0f sim-saniye" % (n_tohum, veri["sure"]))
    print("=" * 68)

    yasayan = [s for s in son if s.get("n", 0) > 0]
    print("\nPOPULASYON")
    print("  yasayan tohum      : %d/%d" % (len(yasayan), n_tohum))
    print("  son nufus          : %.0f  (baslangic %.0f)"
          % (_ort([s.get("n") for s in son]), _ort([s.get("n") for s in ilk])))
    print("  toplam dogum       : %.0f" % _ort([s.get("dogum") for s in son]))
    print("  kusak (kabaca)     : %.1f"
          % (_ort([s.get("dogum") for s in son])
             / max(1.0, _ort([s.get("n") for s in son]))))
    print("  ortalama hiz       : %.1f px/sn" % _ort([s.get("hiz_ort") for s in son]))

    # ---------------------------------------------------------- OLCUT 1
    print("\n" + "-" * 68)
    print("OLCUT 1  |  SILAHLI AVLANMA")
    print("-" * 68)
    silahli = [s.get("silahli_oran", 0) for s in son]
    olduren = []
    av = [s.get("av_yeme", 0) for s in son]
    for s in son:
        olduren.append(sum((s.get("silah_olum") or {}).values()))
    print("  silahli hucre orani : %.3f  (+-%.3f)  [baslangic 0.000]"
          % (_ort(silahli), _sh(silahli)))
    print("  silahla olum        : %.1f  (+-%.1f)" % (_ort(olduren), _sh(olduren)))
    print("  hucre yeme olayi    : %.1f  (+-%.1f)" % (_ort(av), _sh(av)))
    silah_top = {}
    for s in son:
        for k, v in (s.get("silah") or {}).items():
            silah_top[k] = silah_top.get(k, 0) + v
    olum_top = {}
    for s in son:
        for k, v in (s.get("silah_olum") or {}).items():
            olum_top[k] = olum_top.get(k, 0) + v
    print("  tasinan silahlar    : %s" % (silah_top or "yok"))
    print("  oldurme dagilimi    : %s" % (olum_top or "yok"))
    k1 = (_ort(silahli) > 0.05 and _ort(olduren) >= 1.0
          and sum(1 for x in olduren if x > 0) >= n_tohum * 0.5)
    print("  >> %s" % ("GERCEKLESTI" if k1 else "HENUZ DEGIL"))

    # ---------------------------------------------------------- OLCUT 2
    print("\n" + "-" * 68)
    print("OLCUT 2  |  OGRENILMIS KAC / SALDIR")
    print("-" * 68)
    sal = [s.get("saldiri_egilimi", 0) for s in son]
    kac = [s.get("kacis_egilimi", 0) for s in son]
    kai = [s.get("kairomon_kacisi", 0) for s in son]
    for ad, dizi in (("zayifa saldiri egilimi", sal),
                     ("gucluden kacis egilimi", kac),
                     ("kairomondan kacis    ", kai)):
        print("  %-22s: %+.4f (+-%.4f)  t=%+.2f"
              % (ad, _ort(dizi), _sh(dizi), _t(dizi)))
    bant = {}
    for s in son:
        for k, v in (s.get("bant") or {}).items():
            bant[k] = bant.get(k, 0.0) + v
    if bant:
        top = sum(bant.values()) or 1.0
        print("  tepki dagilimi      : %s"
              % {k: round(v / top, 3) for k, v in sorted(bant.items())})
        print("     (rastgele tabloda hepsi 0.250 olur)")
    k2 = max(abs(_t(sal)), abs(_t(kac)), abs(_t(kai))) >= 2.0
    print("  >> %s" % ("GERCEKLESTI (rastgeleden ayrildi)" if k2
                       else "HENUZ DEGIL (rastgeleden ayirt edilemiyor)"))

    # ---------------------------------------------------------- OLCUT 3
    print("\n" + "-" * 68)
    print("OLCUT 3  |  SAVUNMA TIPLERI")
    print("-" * 68)
    kat = [s.get("katman_ort", 0) for s in son]
    sav = [s.get("savunma_ort", 0) for s in son]
    std = [s.get("savunma_std", 0) for s in son]
    tip = [s.get("savunmaci_oran", 0) for s in son]
    ss = [s.get("silahli_savunmali", 0) for s in son]
    print("  hucre basina katman : %.3f (+-%.3f)  [baslangic 0.000]"
          % (_ort(kat), _sh(kat)))
    print("  savunma yatirimi    : %.3f (+-%.3f)" % (_ort(sav), _sh(sav)))
    print("  yatirim dagilimi    : %.3f  (populasyon ici cesitlilik)" % _ort(std))
    print("  SAVUNMACI tip orani : %.3f (+-%.3f)  (zirhli ve SILAHSIZ)"
          % (_ort(tip), _sh(tip)))
    print("  zirhli avci orani   : %.3f" % _ort(ss))
    k3 = _ort(kat) > 0.15 and _ort(tip) > 0.05
    print("  >> %s" % ("GERCEKLESTI" if k3 else "HENUZ DEGIL"))

    # ---------------------------------------------------------- zaman serisi
    print("\n" + "-" * 68)
    print("ZAMAN SERISI (tohum ortalamasi)")
    print("-" * 68)
    basliklar = ("t", "n", "silahli_oran", "katman_ort", "savunmaci_oran",
                 "saldiri_egilimi", "kacis_egilimi", "organ_ort", "burun_ort")
    print("  " + "".join("%>14s" % b if False else "%14s" % b for b in basliklar))
    for satir in veri["ozet"]:
        print("  " + "".join("%14s" % (
            round(satir.get(b), 3) if isinstance(satir.get(b), float)
            else satir.get(b, "-")) for b in basliklar))

    print("\n" + "=" * 68)
    print("SONUC: %d/3 olcut" % sum((k1, k2, k3)))
    print("=" * 68)
    return k1, k2, k3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dosya")
    a = ap.parse_args()
    with open(a.dosya, encoding="utf-8") as f:
        rapor(json.load(f))


if __name__ == "__main__":
    main()

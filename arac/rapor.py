# -*- coding: utf-8 -*-
"""Kosu ciktisini uc BASARI OLCUTUNE gore degerlendirir.

Tek bir kosunun sonucu kanit degildir: evrim sansa cok duyarlidir ve bir
tohumda gorulen egilim otekinde tersine donebilir. Bu yuzden her olcut
TOHUMLAR ARASINDA degerlendirilir - kac tohumda gerceklesti, ortalama ne,
sifirdan ne kadar uzak.

OLCUT 2 ICIN NOT: burada "populasyon BENIM kuralimi ogrendi mi" diye
sorulmaz. Kural dayatilmamali - sans eseri silah kazanmis bir hucrenin
etrafinda ona saldiranlar olur, kacanlar yasar; kural kodda degil
OLULERDE birikir. Sorulan sey davranis ekseninin RASTGELEDEN AYRILIP
AYRILMADIGI. Yonu ne olursa olsun ayrilmissa bir sey secilmis demektir.
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


def _t(deger, sifir=0.0):
    """Kaba bir t degeri: ortalamanin sifirdan kac standart hata uzakta."""
    o, h = _ort(deger), _sh(deger)
    return 0.0 if h <= 0 else (o - sifir) / h


def _al(kayitlar, anahtar, ilk=False):
    out = []
    for k in kayitlar:
        if not k:
            continue
        s = k[0] if ilk else k[-1]
        v = s.get(anahtar)
        if isinstance(v, (int, float)):
            out.append(v)
    return out


def rapor(veri):
    ham = veri["ham"]
    n_tohum = len(ham)
    son = [k[-1] for k in ham if k]
    ilk = [k[0] for k in ham if k]

    print("=" * 72)
    print("EVRIM RAPORU  |  %d tohum x %.0f sim-saniye" % (n_tohum, veri["sure"]))
    print("=" * 72)

    print("\nPOPULASYON")
    print("  yasayan tohum      : %d/%d"
          % (sum(1 for s in son if s.get("n", 0) > 0), n_tohum))
    print("  son nufus          : %.0f  (baslangic %.0f)"
          % (_ort(_al(ham, "n")), _ort(_al(ham, "n", ilk=True))))
    print("  toplam dogum       : %.0f" % _ort(_al(ham, "dogum")))
    print("  kusak (kabaca)     : %.0f"
          % (_ort(_al(ham, "dogum")) / max(1.0, _ort(_al(ham, "n")))))
    print("  ortalama hiz       : %.1f px/sn" % _ort(_al(ham, "hiz_ort")))

    # ---------------------------------------------------------- OLCUT 1
    print("\n" + "-" * 72)
    print("OLCUT 1  |  SILAHLI AVLANMA")
    print("-" * 72)
    silahli = _al(ham, "silahli_oran")
    guc = _al(ham, "silah_guc")
    atis = _al(ham, "atis")
    olduren = [sum((s.get("silah_olum") or {}).values()) for s in son]
    print("  silahli hucre orani : %.3f (+-%.3f)   [baslangic 0.000]"
          % (_ort(silahli), _sh(silahli)))
    print("  en guclu silah gucu : %.3f (+-%.3f)   [baslangic 0.000]"
          % (_ort(guc), _sh(guc)))
    print("  silah KULLANIMI     : %.0f atis (+-%.0f)" % (_ort(atis), _sh(atis)))
    print("  silahla olum        : %.1f (+-%.1f)" % (_ort(olduren), _sh(olduren)))
    silah_top, olum_top = {}, {}
    for s in son:
        for k, v in (s.get("silah") or {}).items():
            silah_top[k] = silah_top.get(k, 0) + v
        for k, v in (s.get("silah_olum") or {}).items():
            olum_top[k] = olum_top.get(k, 0) + v
    print("  tasinan silahlar    : %s" % (silah_top or "yok"))
    print("  oldurme dagilimi    : %s" % (olum_top or "yok"))
    k1 = (_ort(silahli) > 0.10 and _ort(atis) > 100
          and sum(1 for x in olduren if x > 0) >= n_tohum * 0.5)
    print("  >> %s" % ("GERCEKLESTI" if k1 else "HENUZ DEGIL"))

    # ---------------------------------------------------------- OLCUT 2
    print("\n" + "-" * 72)
    print("OLCUT 2  |  DAVRANISIN RASTGELEDEN AYRILMASI")
    print("-" * 72)
    for ad, an in (("kararlilik (|tepki|)", "kararlilik"),
                   ("ortalama tepki      ", "tepki_ort"),
                   ("zayifa tepki        ", "zayifa_tepki"),
                   ("gucluye tepki       ", "gucluye_tepki"),
                   ("ayrim (zayif-guclu) ", "ayrim"),
                   ("kairomon tepkisi    ", "kairomon_tepkisi"),
                   ("sosyal oncelik geni ", "sosyal_ort")):
        s0 = _ort(_al(ham, an, ilk=True))
        s1 = _al(ham, an)
        print("  %s: %+.4f -> %+.4f (+-%.4f)  degisim t=%+.2f"
              % (ad, s0, _ort(s1), _sh(s1), _t([x - s0 for x in s1])))

    b0, b1 = {}, {}
    for s in ilk:
        for k, v in (s.get("bant") or {}).items():
            b0[k] = b0.get(k, 0.0) + v / max(1, len(ilk))
    for s in son:
        for k, v in (s.get("bant") or {}).items():
            b1[k] = b1.get(k, 0.0) + v / max(1, len(son))
    if b1:
        print("\n  KOKU EKSENININ TEPKI DAGILIMI (eksenin ne kadari hangi bolgede)")
        print("    %-10s %8s %8s %8s" % ("bolge", "basta", "sonda", "fark"))
        for k in ("kac", "uzaklas", "yoksay", "yaklas", "saldir"):
            print("    %-10s %8.3f %8.3f %+8.3f"
                  % (k, b0.get(k, 0), b1.get(k, 0), b1.get(k, 0) - b0.get(k, 0)))
        sapma = sum(abs(b1.get(k, 0) - b0.get(k, 0))
                    for k in ("kac", "uzaklas", "yoksay", "yaklas", "saldir"))
        print("    toplam kayma: %.3f  (0 = hic degismedi)" % sapma)
    else:
        sapma = 0.0

    k2 = (sapma > 0.15
          or abs(_t([x - _ort(_al(ham, "kararlilik", ilk=True))
                     for x in _al(ham, "kararlilik")])) >= 2.0)
    print("  >> %s" % ("DAVRANIS DEGISTI (rastgeleden ayrildi)" if k2
                       else "HENUZ AYIRT EDILEMIYOR"))
    print("  NOT: yonun ne oldugu bir basari olcutu DEGIL. Kanitlayici")
    print("       sinama arac/rekabet.py - evrimlesmis tabloyu ayni bedende")
    print("       rastgele tabloya karsi yaristirir.")

    # ---------------------------------------------------------- OLCUT 3
    print("\n" + "-" * 72)
    print("OLCUT 3  |  SAVUNMA TIPLERI")
    print("-" * 72)
    kat = _al(ham, "katman_ort")
    tip = _al(ham, "savunmaci_oran")
    uzm = _al(ham, "uzmanlasma")
    zir = _al(ham, "zirhli_oran")
    print("  hucre basina katman : %.3f (+-%.3f)   [baslangic 0.000]"
          % (_ort(kat), _sh(kat)))
    print("  zirhli hucre orani  : %.3f (+-%.3f)" % (_ort(zir), _sh(zir)))
    print("  SAVUNMACI tip orani : %.3f (+-%.3f)   (zirhli VE silahsiz)"
          % (_ort(tip), _sh(tip)))
    print("  uzmanlasma (zirh~silah korelasyonu): %+.3f (+-%.3f)  t=%+.2f"
          % (_ort(uzm), _sh(uzm), _t(uzm)))
    print("     negatif = zirha yatiran silahtan vazgeciyor: AYRI TIPLER")
    k3 = _ort(kat) > 0.15 and (_ort(tip) > 0.05 or _ort(uzm) < -0.10)
    print("  >> %s" % ("GERCEKLESTI" if k3 else "HENUZ DEGIL"))

    # ---------------------------------------------------------- seri
    print("\n" + "-" * 72)
    print("ZAMAN SERISI (tohum ortalamasi)")
    print("-" * 72)
    basliklar = ("t", "n", "organ_ort", "burun_ort", "silahli_oran",
                 "silah_guc", "katman_ort", "savunmaci_oran", "uzmanlasma",
                 "kararlilik")
    print("  " + "".join("%14s" % b for b in basliklar))
    for satir in veri["ozet"]:
        print("  " + "".join("%14s" % (
            round(satir.get(b), 3) if isinstance(satir.get(b), float)
            else satir.get(b, "-")) for b in basliklar))

    print("\n" + "=" * 72)
    print("SONUC: %d/3 olcut" % sum((k1, k2, k3)))
    print("=" * 72)
    return k1, k2, k3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dosya")
    a = ap.parse_args()
    with open(a.dosya, encoding="utf-8") as f:
        rapor(json.load(f))


if __name__ == "__main__":
    main()

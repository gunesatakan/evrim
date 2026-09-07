# -*- coding: utf-8 -*-
"""Suren bir kosunun ilerleme dosyalarini ozetler.

arac/kos.py her tohumun olcumunu aninda `<cikti>.tN.jsonl` dosyasina
yaziyor. Bu arac onlari okuyup o ana kadarki tohum ortalamasini basar -
kosunun bitmesini beklemeden ne oldugunu gormek icin.
"""
import argparse
import glob
import json
import os


ALANLAR = (("n", "%5.0f"), ("dogum", "%6.0f"), ("organ_ort", "%6.2f"),
           ("burun_ort", "%6.2f"), ("goz_ort", "%6.2f"),
           ("kulak_ort", "%6.2f"), ("kamci_ort", "%6.2f"),
           ("silahli_oran", "%7.3f"), ("silah_guc", "%7.3f"),
           ("atis", "%7.0f"), ("katman_ort", "%7.3f"),
           ("savunmaci_oran", "%8.3f"), ("uzmanlasma", "%8.3f"),
           ("tepki_ort", "%8.3f"), ("kararlilik", "%8.3f"),
           ("ayrim", "%8.3f"), ("govde_ort", "%6.2f"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("onek", help="orn. arac/sonuc/kosu5")
    a = ap.parse_args()
    dosyalar = sorted(glob.glob(a.onek + ".t*.jsonl"))
    if not dosyalar:
        print("ilerleme dosyasi yok:", a.onek + ".t*.jsonl")
        return
    kova = {}
    for d in dosyalar:
        with open(d, encoding="utf-8") as f:
            for satir in f:
                satir = satir.strip()
                if not satir:
                    continue
                try:
                    s = json.loads(satir)
                except ValueError:
                    continue       # yarim yazilmis son satir
                kova.setdefault(s["t"], []).append(s)

    print("%d tohum  |  %s" % (len(dosyalar), os.path.basename(a.onek)))
    print("%7s %3s " % ("t", "k") +
          " ".join(("%%%ds" % max(6, len(ad)) % ad) for ad, _f in ALANLAR))
    for t in sorted(kova):
        satirlar = kova[t]
        parca = []
        for ad, bic in ALANLAR:
            dd = [s.get(ad) for s in satirlar
                  if isinstance(s.get(ad), (int, float))]
            parca.append((bic % (sum(dd) / len(dd))) if dd else "     -")
        print("%7.0f %3d " % (t, len(satirlar)) + " ".join(parca))


if __name__ == "__main__":
    main()

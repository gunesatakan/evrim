# -*- coding: utf-8 -*-
"""Bassiz kosucu. Birden cok tohumu PARALEL kosturur ve olcut doker.

Tek tohum yanilticidir: evrim sansa cok duyarlidir ve tek kosuda gorulen
bir egilim, baska bir tohumda tersine donebilir. Bu yuzden varsayilan
davranis birkac tohumu ayni anda kosturup ortalamalarini bildirmektir.
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _hazirla():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    if KOK not in sys.path:
        sys.path.insert(0, KOK)
    import pygame
    pygame.init()
    import game_settings
    # Olcum kosusu kullanicinin settings.json'ini KIRLETMEZ.
    game_settings.save_all = lambda *a, **k: None


def _bir_tohum(arg):
    tohum, sure, dt, her, ayar, izlek = arg
    _hazirla()
    import game_settings
    for k, v in (ayar or {}).items():
        setattr(game_settings, k, v)
    from systems.world import Dunya
    from arac.olcum import olc

    # ILERLEME DOSYASI: uzun kosularda her sey bitene kadar hicbir sey
    # gorunmuyordu; tek yavas tohum butun sonucu bekletiyor. Her tohum
    # kendi satirini olctugu anda yaziyor.
    def _yaz(satir):
        if not izlek:
            return
        with open("%s.t%d.jsonl" % (izlek, tohum), "a", encoding="utf-8") as f:
            f.write(json.dumps(satir, ensure_ascii=False) + "\n")

    d = Dunya(tohum=tohum)
    kayit = [dict(olc(d), tohum=tohum)]
    _yaz(kayit[0])
    sonraki = her
    n = int(round(sure / dt))
    for _ in range(n):
        d.adim(dt)
        if d.gecen_sure >= sonraki:
            sonraki += her
            kayit.append(dict(olc(d), tohum=tohum))
            _yaz(kayit[-1])
        if not d.hucreler:
            break
    if kayit[-1]["t"] != round(d.gecen_sure, 1):
        kayit.append(dict(olc(d), tohum=tohum))
    return kayit


def _birlestir(kayitlar, anahtar):
    """Ayni t degerindeki olcumlerin tohumlar arasi ortalamasi."""
    from collections import defaultdict
    kova = defaultdict(list)
    for k in kayitlar:
        for satir in k:
            kova[satir["t"]].append(satir)
    out = []
    for t in sorted(kova):
        satirlar = kova[t]
        birlesik = {"t": t, "tohum_sayisi": len(satirlar)}
        for a in anahtar:
            dd = [s.get(a) for s in satirlar if isinstance(s.get(a), (int, float))]
            if dd:
                birlesik[a] = round(sum(dd) / len(dd), 4)
        # sozluk alanlari toplanir
        for a in ("silah", "silah_olum", "olum", "bant"):
            top = {}
            for s in satirlar:
                for kk, vv in (s.get(a) or {}).items():
                    top[kk] = top.get(kk, 0) + vv
            if top:
                birlesik[a] = top
        out.append(birlesik)
    return out


SAYISAL = ("n", "dogum", "besin", "silahli_oran", "av_yeme",
           "saldiri_egilimi", "kacis_egilimi", "kairomon_kacisi",
           "savunma_ort", "savunma_std", "savunmaci_oran",
           "silahli_savunmali", "katman_ort",
           "organ_ort", "hiz_ort", "burun_ort", "govde_ort",
           "sindirim_ort", "hafiza_ort", "sosyal_ort", "kamci_ort",
           "atis", "silah_guc", "uzmanlasma", "zirhli_oran")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sure", type=float, default=600.0)
    ap.add_argument("--dt", type=float, default=1.0 / 30.0)
    ap.add_argument("--tohum", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--her", type=float, default=60.0)
    ap.add_argument("--ayar", type=str, default=None,
                    help='JSON: {"FOOD_COUNT": 500}')
    ap.add_argument("--cikti", type=str, default=None)
    a = ap.parse_args()

    ayar = json.loads(a.ayar) if a.ayar else {}
    izlek = a.cikti.replace(".json", "") if a.cikti else None
    isler = [(t, a.sure, a.dt, a.her, ayar, izlek) for t in a.tohum]
    t0 = time.time()
    if len(isler) == 1:
        sonuc = [_bir_tohum(isler[0])]
    else:
        with mp.Pool(min(len(isler), os.cpu_count() or 1)) as p:
            sonuc = p.map(_bir_tohum, isler)
    gecen = time.time() - t0

    ozet = _birlestir(sonuc, SAYISAL)
    for satir in ozet:
        print(json.dumps(satir, ensure_ascii=False), flush=True)
    print("# %d tohum x %.0fs  ->  %.0f sn gercek (%.1fx)"
          % (len(a.tohum), a.sure, gecen, a.sure * len(a.tohum) / max(1e-9, gecen)))
    if a.cikti:
        with open(a.cikti, "w", encoding="utf-8") as f:
            json.dump({"ayar": ayar, "tohum": a.tohum, "sure": a.sure,
                       "ozet": ozet, "ham": sonuc}, f, ensure_ascii=False, indent=1)
        print("# yazildi:", a.cikti)


if __name__ == "__main__":
    mp.freeze_support()
    main()

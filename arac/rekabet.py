# -*- coding: utf-8 -*-
"""ATAYLA REKABET: evrimlesmis davranis gercekten ise yariyor mu?

"Hucreler nerede kacacagini nerede saldiracagini ogrendi" iddiasi, tablonun
rastgeleden farklilasmasiyla kanitlanmaz - surukleme de farklilastirir. Tek
bir soy supurdugunde butun populasyon onun tablosunu tasir ve o tablo
rastgele bir tablodan istatistiksel olarak ayrilir, ama bu ONUN DAHA IYI
OLDUGUNU gostermez.

Deneysel evrimde bunun cevabi bellidir: evrimlesmis olani ATASIYLA ayni
kaba koy ve hangisinin cogaldigina bak.

Yontem:
  1. Dunya T saniye evrimlesir.
  2. Son populasyon ikiye kopyalanir. A grubu tablosunu KORUR;
     B grubuna RASTGELE bir tablo verilir. Bedenler birebir aynidir -
     organlar, katmanlar, genom, soy imzasi, enerji. Tek fark davranis.
  3. Ikisi ayni dunyaya birlikte birakilir ve T2 saniye sonra hangi grubun
     kac hucresi kaldigina bakilir.

Grup etiketi bolunmede deepcopy ile yavrulara gecer, yani sayilan sey
soyun cogalmasidir.
"""
import argparse
import copy
import json
import multiprocessing as mp
import os
import random
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _hazirla():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    if KOK not in sys.path:
        sys.path.insert(0, KOK)
    import pygame
    pygame.init()
    import game_settings
    game_settings.save_all = lambda *a, **k: None


def _bir_tohum(arg):
    tohum, evrim_sure, yaris_sure, dt, kontrol = arg
    _hazirla()
    import game_settings
    from entities.entity import WIDTH, HEIGHT
    from systems.world import Dunya
    from entities.organism import Organism
    from systems.signaling.behavior_genome import BehaviorGenome

    # --- 1) EVRIM ---
    d = Dunya(tohum=tohum)
    for _ in range(int(round(evrim_sure / dt))):
        d.adim(dt)
        if not d.hucreler:
            return {"tohum": tohum, "hata": "populasyon soncu"}
    evrimlesmis = d.hucreler
    if len(evrimlesmis) < 20:
        return {"tohum": tohum, "hata": "yetersiz populasyon"}

    # --- 2) IKI GRUP ---
    # Tavan iki grubu birden alsin diye gecici olarak iki katina cikarilir;
    # aksi halde yaris baslar baslamaz yarisi yikanip gider.
    eski_cap = game_settings.DIVISION_MAX_POPULATION
    game_settings.DIVISION_MAX_POPULATION = int(eski_cap * 2) or 0

    d2 = Dunya(tohum=tohum + 10007)
    yeni = []
    for o in evrimlesmis:
        a = copy.deepcopy(o)
        a.grup = "evrim"
        a.pending_children = []
        a.bound_target = None
        a.bound_by = None
        b = copy.deepcopy(o)
        b.grup = "rastgele"
        b.pending_children = []
        b.bound_target = None
        b.bound_by = None
        # TEK FARK BU SATIR.
        #
        # KONTROL modunda bu satir atlanir: iki grup da evrimlesmis
        # tabloyu tasir. Sonuc 0.5'ten sapiyorsa testin KENDISINDE bir
        # yanlilik var demektir (siralama, konum, yikanma) ve asil sonuc
        # o yanliliga gore okunmali. Boyle bir bos kontrol olmadan
        # "evrimlesmis kaybetti" cumlesi kurulamaz.
        if not kontrol:
            b.behavior = BehaviorGenome.random()
        for x in (a, b):
            Organism._next_index += 1
            x.index = Organism._next_index
            # ARENA BOYUTU SABIT YAZILMAMALI. Once 1200x800 yaziliydi;
            # arena 2400x1600'e cikinca butun yaris hucreleri haritanin
            # SOL UST CEYREGINE yiginiyor, yogunluk dort katina cikiyordu.
            # Olculen sey davranis degil, tikisiklik olurdu.
            x.pos = x.pos.__class__(random.uniform(60, WIDTH - 60),
                                    random.uniform(60, HEIGHT - 60))
        yeni.extend((a, b))
    d2.optropis = yeni
    d2.kaotropis = []

    # --- 3) YARIS ---
    for _ in range(int(round(yaris_sure / dt))):
        d2.adim(dt)
        if not d2.hucreler:
            break
    game_settings.DIVISION_MAX_POPULATION = eski_cap

    say = {"evrim": 0, "rastgele": 0, "?": 0}
    for o in d2.hucreler:
        say[getattr(o, "grup", "?")] = say.get(getattr(o, "grup", "?"), 0) + 1
    return {"tohum": tohum, "baslangic": len(evrimlesmis),
            "evrim": say["evrim"], "rastgele": say["rastgele"],
            "toplam": len(d2.hucreler)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evrim", type=float, default=900.0,
                    help="kac saniye evrimlessin")
    ap.add_argument("--yaris", type=float, default=400.0,
                    help="yaris kac saniye sursun")
    ap.add_argument("--dt", type=float, default=1.0 / 30.0)
    ap.add_argument("--tohum", type=int, nargs="+",
                    default=[1, 2, 3, 4, 5, 6, 7, 8])
    ap.add_argument("--kontrol", action="store_true",
                    help="bos kontrol: iki grup da evrimlesmis tabloyu tasir")
    ap.add_argument("--cikti", type=str, default=None)
    a = ap.parse_args()

    isler = [(t, a.evrim, a.yaris, a.dt, a.kontrol) for t in a.tohum]
    with mp.Pool(min(len(isler), os.cpu_count() or 1)) as p:
        sonuc = p.map(_bir_tohum, isler)

    print("%s" % ("BOS KONTROL (iki grup da evrimlesmis)" if a.kontrol
                  else "EVRIMLESMIS vs RASTGELE"))
    print("tohum   A grubu  B grubu   A payi")
    paylar = []
    for r in sonuc:
        if "hata" in r:
            print("%5d   %s" % (r["tohum"], r["hata"]))
            continue
        top = r["evrim"] + r["rastgele"]
        pay = r["evrim"] / top if top else 0.0
        paylar.append(pay)
        print("%5d %7d %9d %11.3f" % (r["tohum"], r["evrim"],
                                      r["rastgele"], pay))
    if paylar:
        ort = sum(paylar) / len(paylar)
        import math
        if len(paylar) > 1:
            var = sum((x - ort) ** 2 for x in paylar) / (len(paylar) - 1)
            sh = math.sqrt(var / len(paylar))
        else:
            sh = 0.0
        print("-" * 44)
        print("ortalama evrim payi: %.3f (+-%.3f)   [0.5 = fark yok]"
              % (ort, sh))
        if sh > 0:
            print("t = %+.2f" % ((ort - 0.5) / sh))
        print("%d/%d tohumda evrimlesmis grup one gecti"
              % (sum(1 for x in paylar if x > 0.5), len(paylar)))
    if a.cikti:
        with open(a.cikti, "w", encoding="utf-8") as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    mp.freeze_support()
    main()

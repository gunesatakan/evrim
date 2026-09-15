# -*- coding: utf-8 -*-
"""FOTOTAKSI TESTI: hucre bir isik kaynaginin merkezine ilerleyebiliyor mu?

Koku yaklasma testinin isik karsiligi. Dunyada besin ve baska hucre yok;
haritanin ortasinda tek bir isik kaynagi var. Hucre kaynaktan belli bir
uzaklikta, rastgele bir yone bakarak birakilir ve merkeze ulasmasi beklenir.

DAVRANIS SABITLENIR: isik bantlarinin hepsi +1 (her siddette isiga yaklas),
oteki butun tepkiler 0. Rastgele bir tablo isiktan kacan ya da onu
umursamayan bir hucre de uretebilirdi; sorulan soru davranisin degil
ORGANIN yeterliligi.

Varyantlar (hepsinde arkada bir kamci):
  gozsuz  : fotoreseptor yok - sans duzeyi
  tek_goz : bir fotoreseptor, one bakar
  iki_goz : iki fotoreseptor, +-60 derece
  uc_goz  : uc fotoreseptor, 120 derece arayla

Olculenler: merkeze (--yaricap px) ulasan oran ve sure; hareket eden
karelerin kacinda hucrenin gercekten isiga dogru (<45 der) ya da ters
(>90 der) ilerledigi; yol verimi (baslangic uzakligi / katedilen yol).

Kullanim: python arac/isik_yonelim.py [--tohum 20] [--mesafe 300 600] [--tek]
"""
import argparse
import json
import math
import multiprocessing as mp
import os
import random
import sys
import time

from gradyan import KOK, _hazirla

DT = 1.0 / 30.0

#: ad -> fotoreseptor takilma acilari (derece, 0 = hucrenin onu)
VARYANTLAR = {
    "gozsuz": (),
    "tek_goz": (0.0,),
    "iki_goz": (60.0, -60.0),
    "uc_goz": (0.0, 120.0, 240.0),
}


def _hucre_kur(hucre, goz_acilari):
    """Ciplak govde + arkada kamci + istenen acilarda fotoreseptorler."""
    from entities.organism import Morphology
    from organs.peripheral.membrane.membrane import Membrane
    from organs.central.cytoplasm.cytoplasm import Cytoplasm
    from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
    from organs.central.vacuole.vacuole import Vacuole
    from organs.central.ribosome.ribosome import Ribosome

    hucre.organs = []
    for a in ("body", "membrane", "cytoskeleton", "vacuole", "ribosome"):
        if hasattr(hucre, a):
            delattr(hucre, a)
    zar = Membrane()
    for alan in list(zar.logic.KATMANLAR):
        zar.logic.katman_cikar(alan)
    hucre.add_organ(zar)
    hucre.add_organ(Cytoplasm(size=2.0))
    hucre.add_organ(Cytoskeleton())
    hucre.add_organ(Vacuole(size=1.0))
    hucre.add_organ(Ribosome())
    hucre.add_organ(Morphology.build_organ("Flagella", math.pi, {"length": 10.0}))
    for aci in goz_acilari:
        hucre.add_organ(Morphology.build_organ("Photoreceptor", math.radians(aci)))
    hucre.morphology = Morphology.from_organism(hucre)
    hucre.genomu_kur()
    hucre.recalculate_physics()


def _isiga_yaklassin(hucre):
    """Her siddette isiga yaklas; koku, ses, renk ve akraba tepkisi yok."""
    b = hucre.behavior
    for k in list(b.table):
        b.table[k] = 0.0
    b.scent_bands = [0.0] * len(b.scent_bands)
    b.ses_bands = [0.0] * len(b.ses_bands)
    b.renk_bands = [0.0] * len(b.renk_bands)
    b.kin_response = 0.0
    b.isik_bands = [1.0] * len(b.isik_bands)


def deneme(arg):
    tohum, varyant, mesafe, sure, yaricap, erim = arg
    _hazirla()
    os.chdir(KOK)
    import pygame
    import game_settings as g
    from entities.entity import WIDTH, HEIGHT
    from entities.optropi import Optropi
    from systems import isik
    from systems.world import Dunya
    V = pygame.math.Vector2

    g.DIVISION_MODE = False
    g.DIVISION_MAX_POPULATION = 0
    g.BEHAVIOR_ENABLED = True
    g.FOOD_COUNT = g.FOOD_MAX = 0
    g.FOOD_SPAWN_RATE = 0.0
    g.HARITA_YAMALARI = []
    merkez = V(WIDTH * 0.5, HEIGHT * 0.5)
    g.HARITA_ISIKLARI = [(merkez.x, merkez.y, 1.0, erim)]

    d = Dunya(kaotropi_count=0, optropi_count=0, notropi_count=0,
              food_count=0, tohum=tohum)
    d.optropis = []
    d.foods = []

    # Ayni tohum ayni baslangic: varyantlar ayni yerden, ayni yone bakarak.
    rng = random.Random(tohum * 7919 + int(mesafe))
    aci = rng.uniform(0.0, 2.0 * math.pi)
    bakis = rng.uniform(0.0, 360.0)
    p = merkez + V(math.cos(aci), math.sin(aci)) * mesafe
    o = Optropi(0, int(p.x), int(p.y), (200, 200, 200))
    _hucre_kur(o, VARYANTLAR[varyant])
    _isiga_yaklassin(o)
    o.pos = V(p)
    o.direction = V(1, 0).rotate(bakis)
    o.energy = o.max_energy
    d.optropis = [o]
    random.seed(tohum * 104729 + int(mesafe))

    t = 0.0
    kare = hareketli = dogru = ters = isikli = 0
    yol = 0.0
    onceki = V(o.pos)
    ulasti = None
    while t < sure:
        d.adim(DT)
        t += DT
        if o.dead:
            break
        kare += 1
        adim = o.pos - onceki
        yol += adim.length()
        if getattr(o, 'isik_siddeti', 0.0) > 0.0:
            isikli += 1
        hedef = merkez - onceki
        # Neredeyse duran karede yon anlamsiz: yalnizca ilerleyen kareler.
        if adim.length() > 0.2 and hedef.length() > 1.0:
            hareketli += 1
            c = max(-1.0, min(1.0, adim.normalize().dot(hedef.normalize())))
            derece = math.degrees(math.acos(c))
            if derece < 45.0:
                dogru += 1
            elif derece > 90.0:
                ters += 1
        onceki = V(o.pos)
        if o.pos.distance_to(merkez) <= yaricap:
            ulasti = t
            break
    return {"tohum": tohum, "varyant": varyant, "mesafe": mesafe,
            "ulasti": ulasti, "son_mesafe": o.pos.distance_to(merkez),
            "kare": kare, "hareketli": hareketli, "dogru": dogru,
            "ters": ters, "isikli": isikli, "yol": yol,
            "baslangic_isik": isik.siddet(p.x, p.y)}


def ozet(sonuc, mesafeler, varyantlar, sure):
    for m in mesafeler:
        print("mesafe %.0f px" % m)
        for v in varyantlar:
            rs = [r for r in sonuc if r["varyant"] == v and r["mesafe"] == m]
            if not rs:
                continue
            ulasan = [r for r in rs if r["ulasti"] is not None]
            cezali = sorted(r["ulasti"] if r["ulasti"] is not None else sure
                            for r in rs)
            medyan = cezali[len(cezali) // 2]
            ort = (sum(r["ulasti"] for r in ulasan) / len(ulasan)
                   if ulasan else float('nan'))
            verim = (sum(m / max(1.0, r["yol"]) for r in ulasan) / len(ulasan)
                     if ulasan else float('nan'))
            hareketli = sum(r["hareketli"] for r in rs)
            kare = sum(r["kare"] for r in rs)
            print("  %-8s ulasan %2d/%d  medyan %5.1f sn  ulasanlarin ort %5.1f sn"
                  "  isik okunan kare %%%3.0f  dogru %%%3.0f  ters %%%3.0f  yol verimi %.2f"
                  % (v, len(ulasan), len(rs), medyan, ort,
                     100.0 * sum(r["isikli"] for r in rs) / max(1, kare),
                     100.0 * sum(r["dogru"] for r in rs) / max(1, hareketli),
                     100.0 * sum(r["ters"] for r in rs) / max(1, hareketli),
                     verim))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tohum", type=int, default=20)
    ap.add_argument("--mesafe", type=float, nargs="+", default=[300.0, 600.0])
    ap.add_argument("--sure", type=float, default=90.0)
    ap.add_argument("--yaricap", type=float, default=40.0,
                    help="merkeze bu kadar yaklasan ulasmis sayilir (px)")
    ap.add_argument("--erim", type=float, default=800.0,
                    help="isigin bittigi uzaklik (px)")
    ap.add_argument("--varyant", type=str, nargs="+", default=list(VARYANTLAR))
    ap.add_argument("--tek", action="store_true", help="her varyanttan tek deneme")
    ap.add_argument("--cikti", type=str, default=None)
    a = ap.parse_args()

    if a.tek:
        t0 = time.perf_counter()
        for v in a.varyant:
            print(deneme((1, v, a.mesafe[0], a.sure, a.yaricap, a.erim)))
        print("sure: %.1f sn" % (time.perf_counter() - t0))
        return
    isler = [(s, v, m, a.sure, a.yaricap, a.erim)
             for s in range(1, a.tohum + 1) for m in a.mesafe for v in a.varyant]
    with mp.Pool(2) as havuz:
        sonuc = havuz.map(deneme, isler, chunksize=1)
    if a.cikti:
        json.dump(sonuc, open(a.cikti, "w", encoding="utf-8"), ensure_ascii=False)
    ozet(sonuc, a.mesafe, a.varyant, a.sure)


if __name__ == "__main__":
    mp.freeze_support()
    main()

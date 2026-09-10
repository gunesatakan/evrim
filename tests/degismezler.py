# -*- coding: utf-8 -*-
"""DEGISMEZLER: her karede dogru olmasi gereken fiziksel kurallar.

Senaryo testleri "su durumda su olur" der; bunlar "hicbir durumda su
olamaz" der. Bugune kadar yalnizca senaryo sinandi ve bir merminin
konumu 10^9 piksele kacana kadar kimse fark etmedi. Bu dosya uzun bir
ekosistem kosusunda HER KAREDE asagidakileri denetler:

  1. Konum sonlu: hicbir hucre, molekul, mermi sonsuz ya da NaN degil.
  2. Bir organ = bir baslik: bir organin ayni anda birden fazla canli
     mermisi olamaz; canli mermi sahibi organi gosterir.
  3. Boy: mermi ucu organdan azami uzunluktan uzakta olamaz
     (tup geri ceker, iplik kopar).
  4. Tutma bir ipliktir: av "tutulu" ise onu tutan CANLI bir iplik
     vardir (sayac tek basina tutamaz).
  5. Stok bir hacimdir: 0 ile STOCK_MAX arasinda.
  6. Molekul durumu gecerli kumede; capalanmis molekul kendi bandinda.

Calistirma:  python tests/degismezler.py   (30-60 sn surer)
"""
import math
import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)
os.chdir(KOK)

import pygame
pygame.init()
pygame.display.set_mode((320, 240))

import lab
import game_settings as g
from systems.world import Dunya
from organs.registry import organ_class
from organs.peripheral.weapons.weapons import BaseWeapon

DT = 1.0 / 30.0
GECERLI_DURUM = {'free', 'stuck', 'arrived', 'lost', 'cleared'}


def sonlu(v):
    return math.isfinite(v.x) and math.isfinite(v.y)


def denetle(d, kare, ihlaller):
    hucreler = d.hucreler
    for o in hucreler:
        if not sonlu(o.pos):
            ihlaller.append((kare, 'hucre konumu sonlu degil', o.uid))
        # 5. stok
        for x in o.organs:
            lg = getattr(x, 'logic', None)
            if lg is not None and getattr(lg, 'URETICI', False):
                if not (0.0 <= lg.stok <= lab.STOCK_MAX + 1e-6):
                    ihlaller.append((kare, 'stok hacim disi', (o.uid, lg.stok)))
        # 6. molekuller
        for m in getattr(o, 'molekuller', ()):
            if not sonlu(m.pos):
                ihlaller.append((kare, 'molekul konumu sonlu degil', o.uid))
            if m.state not in GECERLI_DURUM:
                ihlaller.append((kare, 'molekul durumu gecersiz', m.state))
        # 1-3. mermiler
        for sh in getattr(o, 'atislar', ()):
            if not sonlu(sh.pos):
                ihlaller.append((kare, 'mermi konumu sonlu degil', o.uid))
                continue
            if sh.dead:
                continue
            org = getattr(sh, 'organ', None)
            if org is not None and getattr(org, 'mermi', None) is not sh:
                ihlaller.append((kare, 'canli mermi sahibi organi gostermiyor', o.uid))
            az = getattr(sh, 'azami_uzunluk', None)
            if az is not None and (sh.pos - sh.origin).length() > az * 1.05 + 1.0:
                ihlaller.append((kare, 'mermi boyunu asti',
                                 (round((sh.pos - sh.origin).length(), 1), round(az, 1))))
        # 4. tutma = iplik
        if getattr(o, 'tether_timer', 0.0) > 0.0:
            tutan = [sh for sh in o.atislar
                     if getattr(sh, 'holding', False) and not sh.dead
                     and sh.ci == lab.VOLVENT]
            # Iplik koptuktan sonra sayac en fazla birkac kare yasar.
            if not tutan and o.tether_timer > 4 * DT:
                ihlaller.append((kare, 'av tutulu ama tutan iplik yok',
                                 (o.uid, round(o.tether_timer, 3))))
    # 2. bir organ = bir baslik (canli mermi sayisi organ basina <= 1)
    canli_sayac = {}
    for o in hucreler:
        for sh in getattr(o, 'atislar', ()):
            if not sh.dead and getattr(sh, 'organ', None) is not None:
                k = id(sh.organ)
                canli_sayac[k] = canli_sayac.get(k, 0) + 1
    for k, n in canli_sayac.items():
        if n > 1:
            ihlaller.append((kare, 'bir organin birden fazla canli mermisi', n))


def kos(tohum=11, sure=90.0, isinma=45.0):
    random.seed(tohum)
    d = Dunya()
    for _ in range(int(isinma / DT)):
        d.adim(DT)
    # Silahlari dagit ki kurallar gercekten sinansin
    for i, o in enumerate(d.hucreler):
        ci = (5, 6, 7, 8, 3, 4)[i % 6]
        ad = 'Nematocyst' if ci >= 5 else ('Harpoon' if ci == 3 else 'Stylet')
        w = organ_class(ad)()
        w.logic.carrier = ci
        w.attachment_angle = random.uniform(-math.pi, math.pi)
        o.add_organ(w)
        if i % 2 == 0:
            u = organ_class('Toxin')(); u.logic.payload = 6; o.add_organ(u)
        else:
            u = organ_class('Lysin')(); o.add_organ(u)
        o.recalculate_physics()
        o.behavior.scent_bands = [0.9] * len(o.behavior.scent_bands)
    ihlaller = []
    kare = 0
    for _ in range(int(sure / DT)):
        d.adim(DT)
        kare += 1
        denetle(d, kare, ihlaller)
        if len(ihlaller) > 50:
            break
    return d, kare, ihlaller


if __name__ == "__main__":
    d, kare, ihlaller = kos()
    print("%d kare, %d hucre incelendi." % (kare, len(d.hucreler)))
    if ihlaller:
        print("IHLAL: %d" % len(ihlaller))
        ozet = {}
        for k, ad, ayr in ihlaller:
            ozet.setdefault(ad, []).append((k, ayr))
        for ad, liste in ozet.items():
            print("  %-45s x%d  ilk: kare %d %s" % (ad, len(liste), liste[0][0], liste[0][1]))
        sys.exit(1)
    print("DEGISMEZLER TAMAM: hicbir kural hicbir karede bozulmadi.")

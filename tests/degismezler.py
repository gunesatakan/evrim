# -*- coding: utf-8 -*-
"""DEGISMEZLER: her karede dogru olmasi gereken fiziksel kurallar.

Senaryo testleri "su durumda su olur" der; bunlar "hicbir durumda su
olamaz" der. Bugune kadar yalnizca senaryo sinandi ve bir merminin
konumu 10^9 piksele kacana kadar kimse fark etmedi. Bu dosya uzun bir
ekosistem kosusunda HER KAREDE asagidakileri denetler:

  1. Konum sonlu: hicbir hucre, molekul, mermi sonsuz ya da NaN degil.
  2. Mermi organindir: canli mermiyi sahibi organ tasir, hedefin
     listesinde mermi yasamaz.
  3. Boy: ucan merminin ucu organdan azami uzunluktan uzakta olamaz;
     bir ipin yolu (govdeye sarilma dahil) kendi boyunu asamaz.
  4. Tutma bir ipliktir: av "tutulu" ise onu tutan CANLI bir iplik
     vardir (sayac tek basina tutamaz).
  7. Ipin capasi hedef olmayan bir hucrenin icinde olamaz.
  8. Ip ya da stilet tupuyle bagli iki hucre derin ic ice olamaz (temas
     payi + birkac piksel). (Bolunmede yavrunun komsusunun ustune dogmasi
     silahlardan bagimsiz, ayri bir konudur; burada sinanmaz.)
  5. Stok bir hacimdir: 0 ile STOCK_MAX arasinda; igneli silahin kapsul
     yuku 0 ile tasiyicinin kapasitesi arasinda.
  6. Molekul durumu gecerli kumede; capalanmis molekul kendi bandinda.
  9. Serbest molekulun DAIRESI hicbir lifin ya da zarin katı parcasina
     gomulmez (cizilen lif fizigin lifidir).
 10. Doz gorunen bagli moleküllerdir: zarfin saydigi doz, hucrenin
     listesindeki bagli molekul sayisina esittir.
 11. Sitoplazma korumasi (yedek emniyet) hic tetiklenmez.

Calistirma:  python tests/degismezler.py   (30-60 sn surer)
             python tests/degismezler.py --katmanli
               (hucrelerin bir kismina duvar/kapsul/S-layer ve farkli boyda
                yukler verilir; molekul kurallari katmanlarla sinanir)
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


def gomulme(merkez, flat, m):
    """Serbest molekulun dairesi katı bir tabakaya ne kadar giriyor (px)."""
    d = m.pos - merkez
    r = d.length()
    a = math.atan2(d.y, d.x) % (2 * math.pi)
    rho = m.yaricap_px()
    en_kotu = 0.0
    for rr, _bi, sh in flat:
        if sh.tam_acik:
            continue
        derinlik = sh.h + rho - abs(r - rr)
        if derinlik <= 0.0 or sh.pencere(a, 2.0 * rho) is not None:
            continue
        m_aci = rho / rr
        teget = math.inf
        for a0, a1 in sh.acik:
            if a0 + m_aci > a1 - m_aci:
                continue
            for x in (a, a + 2 * math.pi, a - 2 * math.pi):
                teget = min(teget, max(a0 + m_aci - x, x - a1 + m_aci, 0.0) * rr)
        en_kotu = max(en_kotu, min(derinlik, teget))
    return en_kotu


_ONCEKI_UIDLER = None


def denetle(d, kare, ihlaller):
    global _ONCEKI_UIDLER
    hucreler = d.hucreler
    # Bu karede bolunmeyle dogan hucreler (yeni kimlikler).
    uidler = {c.uid for c in hucreler}
    yeniler = ([c for c in hucreler if c.uid not in _ONCEKI_UIDLER]
               if _ONCEKI_UIDLER is not None else [])
    _ONCEKI_UIDLER = uidler
    for o in hucreler:
        if not sonlu(o.pos):
            ihlaller.append((kare, 'hucre konumu sonlu degil', o.uid))
        # 5. stok
        for x in o.organs:
            lg = getattr(x, 'logic', None)
            if lg is not None and getattr(lg, 'URETICI', False):
                if not (0.0 <= lg.stok <= lab.STOCK_MAX + 1e-6):
                    ihlaller.append((kare, 'stok hacim disi', (o.uid, lg.stok)))
            ky = int(getattr(lg, 'kapsul_yuk', 0) or 0) if lg is not None else 0
            ci = getattr(lg, 'carrier', None) if lg is not None else None
            if ky and not (isinstance(ci, int) and 0 <= ci < len(lab.CARRIER_EMIT)
                           and 0 <= ky <= lab.CARRIER_EMIT[ci]):
                ihlaller.append((kare, 'kapsul yuku kapasite disi', (o.uid, ky, ci)))
        # 6. molekuller
        for m in getattr(o, 'molekuller', ()):
            if not sonlu(m.pos):
                ihlaller.append((kare, 'molekul konumu sonlu degil', o.uid))
            if m.state not in GECERLI_DURUM:
                ihlaller.append((kare, 'molekul durumu gecersiz', m.state))
        # 9-10. molekul dairesi ve doz. Molekuller hucrenin guncellemesinde
        # `onceki_pos` merkezine gore hareket etti; sonradan gelen itmeler
        # (ortusme cozumu, ipler) bir sonraki karede hesaba katilir.
        z = getattr(o, '_zarf_arayuz', None)
        mols = getattr(o, 'molekuller', ())
        if z is not None and not o.dead:
            flat = z.flat_sheets()
            merkez = getattr(o, 'onceki_pos', o.pos)
            for m in mols:
                # Henuz fizikten gecmemis molekul sayilmaz: bu karede dogan
                # (yas 0) ya da son adimindan sonra zarfi degisen (bolunme,
                # sisme) molekul bir sonraki adimda yerlesir.
                if (m.state == 'free' and m.gen == z.generation and m.age > 0.0
                        and m.geo[0] == tuple(z.boundaries())):
                    g_px = gomulme(merkez, flat, m)
                    if g_px > 1e-3 * z.pore_px:
                        ihlaller.append((kare, 'serbest molekul life gomuldu',
                                         (o.uid, lab.PAYLOADS[m.pi][0], round(g_px, 4))))
            doz = z.arrived
            gorunen = {}
            for m in mols:
                if m.state == 'arrived' and m.gen == z.generation:
                    gorunen[m.pi] = gorunen.get(m.pi, 0) + 1
            if doz != gorunen:
                ihlaller.append((kare, 'doz gorunen bagli moleküllerden farkli',
                                 (o.uid, doz, gorunen)))
        # 2. hedefin listesinde mermi yasamaz
        if getattr(o, 'atislar', None):
            ihlaller.append((kare, 'hedef listesinde mermi var', o.uid))
        # 1-3, 7. organlarimin mermileri ve ipleri
        for x in o.organs:
            sh = getattr(x, 'mermi', None)
            if sh is None:
                continue
            if not sonlu(sh.pos):
                ihlaller.append((kare, 'mermi konumu sonlu degil', o.uid))
                continue
            if sh.dead:
                continue
            if getattr(sh, 'organ', None) is not x:
                ihlaller.append((kare, 'canli mermi sahibi organi gostermiyor', o.uid))
            az = getattr(sh, 'azami_uzunluk', None)
            if getattr(sh, 'ip', False):
                uz = o._ip_geometrisi(sh)[0]
                # Ciftler en son birbirinden ayrilir (resolve_overlaps); o
                # itme ipi birkac piksel gerebilir, bir sonraki karede ip
                # yeniden cozulur.
                if uz > sh.ip_boy + 4.0:
                    ihlaller.append((kare, 'ip boyunu asti',
                                     (round(uz, 1), round(sh.ip_boy, 1))))
                if az is not None and sh.ip_boy > az + 1.0:
                    ihlaller.append((kare, 'ip boyu organin ipinden uzun',
                                     (round(sh.ip_boy, 1), round(az, 1))))
                for c in hucreler:
                    if c is o or c is sh.hedef or c.dead:
                        continue
                    if c.pos.distance_to(sh.pos) < float(c.radius) * 0.7:
                        ihlaller.append((kare, 'ip capasi baska hucrenin icinde', o.uid))
                        break
            elif az is not None and (sh.pos - sh.origin).length() > az * 1.05 + 1.0:
                ihlaller.append((kare, 'mermi boyunu asti',
                                 (round((sh.pos - sh.origin).length(), 1), round(az, 1))))
    # 8. temas: iple/tupla bagli cift derin ic ice degil
    for o in hucreler:
        if o.dead:
            continue
        for x in o.organs:
            sh = getattr(x, 'mermi', None)
            b = getattr(sh, 'hedef', None) if sh is not None else None
            if b is None or sh.dead or b.dead or not getattr(sh, 'ip', False):
                continue
            # Bu karede bu hucrelerden birinin USTUNE bir yavru dogduysa ortusme
            # cozumu onu ip ortagina iter (olculdu: yedi bolunmenin ayni karede
            # oldugu bir anda 12 px'lik itme). Yavrunun ustune dogmasi silahlardan
            # bagimsiz, ayri bir konudur (bkz. kural 8); bir sonraki karede ayrisir.
            if any(n.pos.distance_to(c.pos) < float(n.radius) + float(c.radius)
                   for n in yeniler for c in (o, b) if n is not c):
                continue
            ic = float(o.radius) + float(b.radius) - o.pos.distance_to(b.pos)
            # Kalabalikta ayrisma birkac turda tamamlanir; olculen en derin
            # kalinti ~4,3 px. Ic ice gomulme (izoriza/harpun eskiden 5-13 px)
            # bunun belirgin ustundedir.
            pay = (float(o.radius) + float(b.radius)) * g.OVERLAP_TOLERANCE + 5.0
            if ic > pay:
                ihlaller.append((kare, 'bagli cift derin ic ice', (round(ic, 1), round(pay, 1))))
    # 4. tutma = iplik
    tutanlar = {}
    for o in hucreler:
        for x in o.organs:
            sh = getattr(x, 'mermi', None)
            if (sh is not None and not sh.dead and getattr(sh, 'holding', False)
                    and sh.ci == lab.VOLVENT and sh.hedef is not None):
                tutanlar[id(sh.hedef)] = True
    for o in hucreler:
        # Iplik koptuktan sonra sayac en fazla birkac kare yasar.
        if getattr(o, 'tether_timer', 0.0) > 4 * DT and id(o) not in tutanlar:
            ihlaller.append((kare, 'av tutulu ama tutan iplik yok',
                             (o.uid, round(o.tether_timer, 3))))

def kos(tohum=11, sure=90.0, isinma=45.0, katmanli=False):
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
            u = organ_class('Toxin')()
            # Katmanli kosuda farkli boyutlar: T3SS efektoru, peptit,
            # alfa-hemolizin, norotoksin.
            u.logic.payload = (6, 2, 5, 1)[(i // 2) % 4] if katmanli else 6
            o.add_organ(u)
        else:
            u = organ_class('Lysin')(); o.add_organ(u)
        if katmanli:
            # Zarf cesitliligi: molekuller duvara, kapsule, S-layer'a da carpsin
            zar = o.membrane.logic
            zar.var_wall = (i % 3 == 0)
            zar.var_capsule = (i % 4 == 1)
            zar.var_slayer = (i % 5 == 2)
        o.recalculate_physics()
        o.behavior.scent_bands = [0.9] * len(o.behavior.scent_bands)
    ihlaller = []
    kare = 0
    koruma0 = lab.KORUMA_TETIK
    for _ in range(int(sure / DT)):
        d.adim(DT)
        kare += 1
        denetle(d, kare, ihlaller)
        # 11. yedek koruma
        if lab.KORUMA_TETIK != koruma0:
            ihlaller.append((kare, 'sitoplazma korumasi tetiklendi',
                             lab.KORUMA_TETIK - koruma0))
            koruma0 = lab.KORUMA_TETIK
        if len(ihlaller) > 50:
            break
    return d, kare, ihlaller


if __name__ == "__main__":
    d, kare, ihlaller = kos(katmanli='--katmanli' in sys.argv)
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

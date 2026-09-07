# -*- coding: utf-8 -*-
"""SECILIM GRADYANI TESTI: bir organ tasimak gercekten ise yariyor mu?

Evrim, kalitilabilir cesitlilik + FARKLI BASARI demektir. Ikincisi yoksa
mutasyon birikir ama hicbir yone gitmez; ortaya cikan sey evrim degil
suruklenmedir. Bu yuzden populasyonu kosturmadan once tek tek sormak
gerekir: kemoreseptor tasiyan hucre, tasimayandan gercekten daha cok mu
besin buluyor? Flagella ise yariyor mu? Duvar sagkalimi artiriyor mu?

Yontem: ayni dunyaya iki fenotipten esit sayida hucre birakilir, bolunme
KAPALI tutulur (yoksa sayilar birbirine karisir) ve belli bir sure sonunda
her grubun aldigi besin ve kalan enerjisi karsilastirilir.
"""
import argparse
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


TAKIMLAR = {
    # ad -> (organ listesi, katman sozlugu)
    "ciplak":   ([], {}),
    "burun":    ([("Chemoreceptor", 6.0)], {}),
    "kamci":    ([("Flagella", 10.0)], {}),
    "burun+kamci": ([("Chemoreceptor", 6.0), ("Flagella", 10.0)], {}),
    "iki_burun": ([("Chemoreceptor", 6.0), ("Chemoreceptor", 6.0),
                   ("Flagella", 10.0)], {}),
    "uzun_burun": ([("Chemoreceptor", 12.0), ("Flagella", 10.0)], {}),
    "goz":      ([("Photoreceptor", 25.0), ("Flagella", 10.0)], {}),
    "duvarli":  ([("Chemoreceptor", 6.0), ("Flagella", 10.0)], {"wall": 3.0}),
    "stilet":   ([("Chemoreceptor", 6.0), ("Flagella", 10.0),
                  ("Stylet", 1.0)], {}),
    "toksin":   ([("Chemoreceptor", 6.0), ("Flagella", 10.0),
                  ("Toxin", 1.0)], {}),
    "zipkin":   ([("Chemoreceptor", 6.0), ("Flagella", 10.0),
                  ("Nematocyst", 1.0)], {}),
    "fagosit":  ([("Chemoreceptor", 6.0), ("Flagella", 10.0),
                  ("Phagocytosis", 1.0)], {}),
    "av":       ([("Chemoreceptor", 6.0), ("Flagella", 10.0)], {}),
    "lizin":    ([("Chemoreceptor", 6.0), ("Flagella", 10.0),
                  ("Lysin", 1.0)], {}),
    "harpun":   ([("Chemoreceptor", 6.0), ("Flagella", 10.0),
                  ("Harpoon", 1.0)], {}),
    "av_duvar": ([("Chemoreceptor", 6.0), ("Flagella", 10.0)], {"wall": 4.0}),
    "av_kapsul": ([("Chemoreceptor", 6.0), ("Flagella", 10.0)], {"capsule": 4.0}),
    "av_mukus": ([("Chemoreceptor", 6.0), ("Flagella", 10.0)], {"mucus": 4.0}),
    "av_slayer": ([("Chemoreceptor", 6.0), ("Flagella", 10.0)], {"slayer": 4.0}),
}

#: Testte davranis tablosu SABITLENIR.
#
# Silahin ise yarayip yaramadigini olcerken rastgele bir davranis
# tablosu her seyi bulaniklastirir: hucrenin dortte uc ihtimalle
# saldirmadigi bir denemede "silah ise yaramiyor" sonucu cikar, oysa
# olculen sey silah degil zar atisi olur. Avcilara "saldir", avlara
# "kac" verilir; sorulan soru yalnizca MEKANIZMANIN calisip
# calismadigidir.
AVCI_TAKIMLARI = ("stilet", "toksin", "zipkin", "fagosit",
                  "lizin", "harpun")


def _davranis_sabitle(hucre, saldirgan):
    """Tepki artik SUREKLI: +1 tam saldiri, -1 tam kacis, 0 ilgisizlik."""
    b = hucre.behavior
    tepki = 1.0 if saldirgan else -1.0
    for k in list(b.table):
        b.table[k] = tepki
    b.scent_bands = [tepki] * len(b.scent_bands)
    b.kin_response = 0.0           # kendi turunu yeme
    b.sosyal_oncelik = 1.0         # testte komsu her zaman oncelikli



def _kur(hucre, takim):
    """Hucreyi baslangictan kurup istenen organlari tak."""
    import math
    from entities.organism import Morphology
    from organs.peripheral.membrane.membrane import Membrane
    from organs.central.cytoplasm.cytoplasm import Cytoplasm
    from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
    from organs.central.vacuole.vacuole import Vacuole
    from organs.central.ribosome.ribosome import Ribosome

    organlar, katmanlar = TAKIMLAR[takim]
    hucre.organs = []
    for a in ("body", "membrane", "cytoskeleton", "vacuole", "ribosome"):
        if hasattr(hucre, a):
            delattr(hucre, a)
    zar = Membrane()
    for alan in list(zar.logic.KATMANLAR):
        zar.logic.katman_cikar(alan)
    for alan, deger in katmanlar.items():
        zar.logic.katman_ekle(alan)
        setattr(zar.logic, alan, deger)
    hucre.add_organ(zar)
    hucre.add_organ(Cytoplasm(size=2.0))
    hucre.add_organ(Cytoskeleton())
    hucre.add_organ(Vacuole(size=1.0))
    hucre.add_organ(Ribosome())
    for i, (tip, deger) in enumerate(organlar):
        aci = i * 2.0 * math.pi / max(1, len(organlar))
        anahtar = {"Chemoreceptor": "length", "Flagella": "length",
                   "Photoreceptor": "range"}.get(tip, "power")
        hucre.add_organ(Morphology.build_organ(tip, aci, {anahtar: deger}))
    hucre.morphology = Morphology.from_organism(hucre)
    hucre.recalculate_physics()
    hucre.takim = takim
    return hucre


def _bir_tohum(arg):
    tohum, takimlar, sure, dt, sayi, besin, sabit = arg
    _hazirla()
    import game_settings
    from entities.entity import WIDTH, HEIGHT
    from entities.optropi import Optropi
    from systems.world import Dunya

    random.seed(tohum)
    # Bolunme KAPALI: yoksa basarili grup cogalir ve "kac besin aldi"
    # sorusu "kac hucre vardi" sorusuna donusur.
    game_settings.DIVISION_MODE = False
    game_settings.DIVISION_MAX_POPULATION = 0
    if besin:
        game_settings.FOOD_MAX = besin

    d = Dunya(kaotropi_count=0, optropi_count=0, notropi_count=0,
              food_count=besin, tohum=tohum)
    hepsi = []
    for takim in takimlar:
        for i in range(sayi):
            o = Optropi(len(hepsi), random.randint(80, WIDTH - 80),
                        random.randint(80, HEIGHT - 80), (200, 200, 200))
            _kur(o, takim)
            if sabit:
                _davranis_sabitle(o, takim in AVCI_TAKIMLARI)
            o.energy = o.max_energy
            hepsi.append(o)
    d.optropis = hepsi

    n = int(round(sure / dt))
    for _ in range(n):
        d.adim(dt)

    out = {}
    for takim in takimlar:
        grup = [o for o in d.optropis if getattr(o, 'takim', None) == takim]
        yenen = sum(getattr(o, 'toplam_besin', 0) for o in grup)
        out[takim] = {
            "sag": len(grup),
            "besin": yenen,
            "av": sum(getattr(o, 'prey_eaten', 0) for o in grup),
            "enerji": round(sum(o.energy for o in grup) / max(1, len(grup)), 1),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sure", type=float, default=120.0)
    ap.add_argument("--dt", type=float, default=1.0 / 30.0)
    ap.add_argument("--tohum", type=int, nargs="+", default=[1, 2, 3, 4, 5, 6])
    ap.add_argument("--sayi", type=int, default=12)
    ap.add_argument("--besin", type=int, default=None)
    ap.add_argument("--sabit", action="store_true",
                    help="davranis tablosunu sabitle (avci=saldir, av=kac)")
    ap.add_argument("--bolun", action="store_true")
    ap.add_argument("--takim", type=str, nargs="+",
                    default=["ciplak", "burun", "kamci", "burun+kamci"])
    a = ap.parse_args()

    isler = [(t, a.takim, a.sure, a.dt, a.sayi, a.besin, a.sabit)
             for t in a.tohum]
    with mp.Pool(min(len(isler), os.cpu_count() or 1)) as p:
        sonuc = p.map(_bir_tohum, isler)

    print("takim           sagkalan   besin/hucre   av   enerji")
    for takim in a.takim:
        sag = sum(r[takim]["sag"] for r in sonuc)
        besin = sum(r[takim]["besin"] for r in sonuc)
        av = sum(r[takim]["av"] for r in sonuc)
        enerji = sum(r[takim]["enerji"] for r in sonuc) / len(sonuc)
        toplam = a.sayi * len(a.tohum)
        print("%-15s %3d/%-3d   %9.2f %5d   %7.1f"
              % (takim, sag, toplam, besin / max(1, toplam), av, enerji))
    print(json.dumps(sonuc[:1], ensure_ascii=False))


if __name__ == "__main__":
    mp.freeze_support()
    main()

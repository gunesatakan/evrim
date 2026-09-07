"""Organ kayit defteri - ADI verilen organi kuran TEK yer.

launcher.py'de ORGAN_TYPES sozlugu vardi ama sinifa nasil ulasilacagi
bilgisi orada DEGILDI: launcher her organ turu icin ayri bir import ve
ayri bir dal tutuyordu. lab.py'nin de ayni organlari kurabilmesi icin bu
eslemenin tek bir yerde olmasi gerekiyor - aksi halde yeni bir organ
eklemek iki dosyayi birden duzenlemeyi gerektirirdi.

Buradaki ORGAN_PATHS, launcher'daki ORGAN_TYPES ile AYNI anahtarlari
kullanir; ikisinin ortusmesi `check_registry()` ile dogrulanabilir.
"""

import importlib

# ad -> (modul yolu, sinif adi). Silahlar WEAPON_CLASSES'tan gelir.
ORGAN_PATHS = {
    'Photoreceptor':   'organs.receptors.Photoreceptor.photoreceptor',
    'Mechanoreceptor': 'organs.receptors.Mechanoreceptor.mechanoreceptor',
    'Chemoreceptor':   'organs.receptors.Chemoreceptor.chemoreceptor',
    'Flagella':        'organs.peripheral.flagella.flagella',
    'Cilia':           'organs.peripheral.cilia.cilia',
    'Membrane':        'organs.peripheral.membrane.membrane',
    'Cytoplasm':       'organs.central.cytoplasm.cytoplasm',
    'Vacuole':         'organs.central.vacuole.vacuole',
    'Cytoskeleton':    'organs.central.cytoskeleton.cytoskeleton',
    'Ribosome':        'organs.central.ribosome.ribosome',
}

# IC organlar: konumu olmayan, hucrenin ICINDE duran yapilar. Zarf
# cizilirken bunlar cekirdek yaricapinda, otekiler zarfin DIS yuzeyinde
# cizilir. Bu bilgi launcher.ORGAN_TYPES'ta duruyordu; entities tarafi
# onu okuyabilmek icin launcher'i import etmek zorunda kalirdi ve
# launcher zaten entities'i import ediyor - dongusel bagimlilik.
IC_ORGANLAR = frozenset({
    'Membrane', 'Cytoplasm', 'Vacuole', 'Cytoskeleton', 'Ribosome',
})


def ic_organ(ad):
    """Bu organ hucrenin ICINDE mi durur?"""
    return ad in IC_ORGANLAR


_cache = {}


def organ_class(name):
    """Ada karsilik gelen organ sinifini dondur (tembel import)."""
    if name in _cache:
        return _cache[name]
    from organs.peripheral.weapons.weapons import WEAPON_CLASSES
    if name in WEAPON_CLASSES:
        cls = WEAPON_CLASSES[name]
    elif name in ORGAN_PATHS:
        cls = getattr(importlib.import_module(ORGAN_PATHS[name]), name)
    else:
        raise KeyError(f'bilinmeyen organ: {name}')
    _cache[name] = cls
    return cls


def all_organ_names():
    """Kurulabilir butun organlarin adlari."""
    from organs.peripheral.weapons.weapons import WEAPON_CLASSES
    return list(ORGAN_PATHS) + list(WEAPON_CLASSES)


def make_organ(name, **kw):
    """Organi varsayilan degerleriyle kur. Hepsi varsayilanli kuruculara sahip."""
    return organ_class(name)(**kw)


def check_registry(organ_types):
    """Kayit defteri ile launcher'in ORGAN_TYPES'i ortusuyor mu?

    Ayrisirlarsa lab ile launcher farkli organ kumelerini gosterir; bu
    sessizce olursa fark edilmesi zordur.
    """
    ours, theirs = set(all_organ_names()), set(organ_types)
    return sorted(theirs - ours), sorted(ours - theirs)


# Uzunluk turu organ parametreleri. Bunlar settings.json'dan mutlak piksel
# olarak geliyor; kuresel olcek buyuyunce olceklenmezlerse oranlar bozulur -
# olculdu: olcek 30'da hucre kendi gorus menzilinin 12 KATI oluyordu.
UZUNLUK_ALANLARI = ('length', 'range')
BOYUT_ALANLARI = ('size',)      # sensitivity = size * 30 gibi turevler


def olcekle(organ, k):
    """Organin uzunluk parametrelerini kuresel olcekle carp.

    Iki kez uygulanmasin diye organ isaretlenir; add_organ birden fazla
    yoldan cagrilabiliyor.
    """
    if k == 1.0 or organ is None or getattr(organ, '_olcekli', False):
        return organ
    lg = getattr(organ, 'logic', None)
    if lg is not None:
        for alan in UZUNLUK_ALANLARI + BOYUT_ALANLARI:
            if hasattr(lg, alan):
                try:
                    setattr(lg, alan, getattr(lg, alan) * k)
                except Exception:
                    pass
        if hasattr(lg, 'recalculate_boosts'):
            try:
                lg.recalculate_boosts()
            except Exception:
                pass
    organ._olcekli = True
    return organ

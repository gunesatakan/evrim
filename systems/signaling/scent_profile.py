"""Koku puanı: hücrenin genetik/fenotipik ağırlığının tek bir sayıya inmesi.

Eski tasarımda koku AYRIK bir sınıftı (0-5) ve eşik aşılınca bir anda
başka bir sınıfa atlıyordu. Sonuç saçmaydı: sekiz bölünme sonra hiç
tanımadık biri beliriyordu. Oysa gerçekte akrabalık kademelidir.

Burada koku SÜREKLİ bir büyüklük: hücrenin taşıdığı organların ağırlıklı
toplamı. Küçük bir genetik değişim puanı biraz oynatır, davranış çoğunlukla
aynı kalır; ancak bir sınıra yakınsa değişir. Ani yabancı yoktur.

Ağırlıklar organa göre farklıdır ve GELİŞİMLE ölçeklenir: taban güçteki
bir stilet 2.0 verir, geliştirilmiş bir stilet bunun üstüne çıkar. Bir
vakuol ise 0.2 - yer kaplar ama tehdit anlatmaz.
"""

import game_settings

# organ adı -> (taban ağırlık, gelişim niteliği, o niteliğin taban değeri)
# Katkı = taban_ağırlık * (nitelik / taban_değer)
ORGAN_WEIGHTS = {
    # --- silahlar: en ağır basanlar ---
    'Phagocytosis':    (3.0, 'power', 2.0),
    'Harpoon':         (2.5, 'power', 2.0),
    'Nematocyst':      (2.5, 'power', 2.0),
    'Stylet':          (2.0, 'power', 2.0),
    'Toxin':           (2.0, 'power', 2.0),
    'Lysin':           (2.0, 'power', 2.0),
    # --- gövde ve hareket ---
    'Cytoplasm':       (1.0, 'size', 3.0),
    'Flagella':        (0.8, 'length', 15.0),
    'Cilia':           (0.4, 'length', 2.0),
    # --- duyular ---
    'Chemoreceptor':   (0.3, 'length', 5.0),
    'Photoreceptor':   (0.3, 'range', 15.0),
    'Mechanoreceptor': (0.3, 'sensitivity', 40.0),
    # --- iç makine: yer kaplar, tehdit anlatmaz ---
    'Ribosome':        (0.3, 'area', 25.0),
    'Cytoskeleton':    (0.3, 'area', 10.0),
    'Vacuole':         (0.2, 'size', 1.0),
}

_DEFAULT = (0.2, None, 1.0)


def organ_score(organ):
    """Tek bir organın koku puanına katkısı."""
    weight, attr, ref = ORGAN_WEIGHTS.get(type(organ).__name__, _DEFAULT)
    if attr is None or ref <= 0:
        return weight
    value = getattr(organ.logic, attr, None)
    if not isinstance(value, (int, float)):
        return weight
    return weight * (float(value) / ref)


def membrane_score(membrane_logic):
    """Zar ayrı ele alınır: ölçek niteliği yok, yatırımları var."""
    if membrane_logic is None:
        return 0.0
    # Katman YOKSA kokusu da yok: duvarini kaybeden hucre duvarli gibi
    # kokmamali - fenotipi degistiren en buyuk adim bu. Ayrica mukus ve
    # S-layer sonradan eklenmisti ve bu toplama hic girmiyordu.
    _puan = getattr(membrane_logic, 'katman_puani', None)
    if callable(_puan):
        katmanlar = sum(_puan(a) for a in ('wall', 'capsule', 'mucus', 'slayer'))
    else:
        katmanlar = membrane_logic.wall + membrane_logic.capsule
    defenses = (katmanlar + membrane_logic.outer
                + membrane_logic.efflux + membrane_logic.slip)
    integrity = membrane_logic.max_integrity / max(1.0, game_settings.MEMBRANE_INTEGRITY_BASE)
    return game_settings.SCENT_WEIGHT_MEMBRANE * (defenses + integrity)


def scent_value(organism):
    """Hücrenin toplam koku puanı. Geliştikçe büyür - bu normaldir.

    Enflasyon sorun DEĞİLDİR çünkü puan mutlak okunmaz: algılayan hücre
    kendi puanına ORANLA okur (bkz. relative_position). Herkes birlikte
    büyüdüğünde oranlar sabit kalır, evrimleşmiş sınırlar eskimez.
    """
    total = 0.0
    for organ in organism.organs:
        if type(organ).__name__ == 'Membrane':
            total += membrane_score(organ.logic)
        else:
            total += organ_score(organ)
    return total

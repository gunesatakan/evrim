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


# ---------------------------------------------------------------------------
# KOKU ALANI: puanin cevredeki derisime donusmesi
#
# TEK KAYNAK. Ayni denklem dort yerde kullaniliyor - algi (alici ucundaki
# derisim), kaba uzamsal eleme, menzil ust siniri ve ekran cizimi. Dordu
# ayri ayri yazilinca biri degisip digerleri geride kaliyordu; hepsi
# buradan gecer.
#
# FIZIK. Hucre kokusunu YUZEYINDEN salgilar. Kuresel bir kaynaktan
# difuzyon + birinci derece bozunma (buharlasma, hidroliz) kararli halde
# su profili verir:
#
#     C(d) = (Q / 4piD d) * exp(-(d - r0) / lambda)
#
# Iki carpan var ve ikisi de gercek:
#
#   1/d  : GEOMETRIK SEYRELME. Ayni molekul sayisi giderek buyuyen bir
#          kurenin yuzeyine dagilir. Eskiden bu carpan YOKTU - koku
#          yalnizca ussel olarak seyreliyordu ve bulut olmasi gerekenden
#          cok genis kaliyordu (dunyanin %46'si, hucre basina 10 komsu).
#
#   Q ~ r0^2 : SALGI YUZEY ALANIYLA ORANTILI. Iri hucrenin zari daha
#          genis, daha cok molekul birakir. Yuzeydeki derisim boylece
#          r0 ile buyur (Q/4piD r0 ~ r0). Yani BOYUT KOKUYU ARTIRIR:
#          ayni organ yukunu tasiyan iri bir hucre daha uzaktan duyulur.
#          Organ yukunun getirdigi `koku` puani bunun uzerine biner.
#
# lambda = KOKU_BULUT = sqrt(D/k), bulutun karakteristik boyu.
# KOKU_REF_YARICAP olcegi sabitler: o yaricaptaki bir hucrede yuzey
# derisimi tam KOKU_YAYIM * koku olur, yani eski kalibrasyon korunur.


def koku_derisimi(koku, r0, d):
    """Kaynak MERKEZINDEN d px uzaktaki derisim. Govde icinde yuzey degeri."""
    if koku <= 0.0:
        return 0.0
    r0 = r0 if r0 > 1.0 else 1.0
    bulut = game_settings.KOKU_BULUT
    if bulut < 1.0:
        bulut = 1.0
    ref = getattr(game_settings, 'KOKU_REF_YARICAP', 22.45)
    if ref <= 0.0:
        ref = 22.45
    yuzey = game_settings.KOKU_YAYIM * koku * (r0 / ref)
    if d <= r0:
        return yuzey
    import math as _m
    return yuzey * (r0 / d) * _m.exp(-(d - r0) / bulut)


def koku_erimi(koku, r0, esik):
    """C(R) = esik cozumu: bu kokunun duyulabildigi en uzak nokta (merkezden).

    Cozulecek denklem  A/R * exp(-R/BULUT) = 1  kapali bicimde Lambert W
    ister; Newton ile uc dort adimda yakinsar (f = lnA - lnR - R/BULUT).
    Duyulamiyorsa 0 doner - o zaman bulut da cizilmez.
    """
    import math as _m
    r0 = r0 if r0 > 1.0 else 1.0
    if koku <= 0.0 or esik <= 0.0:
        return 0.0
    if koku_derisimi(koku, r0, r0) < esik:
        return 0.0                       # yuzeyde bile esigin altinda
    bulut = game_settings.KOKU_BULUT
    if bulut < 1.0:
        bulut = 1.0
    ref = getattr(game_settings, 'KOKU_REF_YARICAP', 22.45)
    if ref <= 0.0:
        ref = 22.45
    # A = yuzey_derisimi * r0 * exp(r0/BULUT) / esik
    lnA = (_m.log(game_settings.KOKU_YAYIM * koku * (r0 / ref) / esik)
           + _m.log(r0) + r0 / bulut)
    R = bulut * (lnA - _m.log(bulut)) if lnA > _m.log(bulut) + 1.0 else r0
    if R < r0:
        R = r0
    for _ in range(24):
        f = lnA - _m.log(R) - R / bulut
        if -1e-4 < f < 1e-4:
            break
        R += f / (1.0 / R + 1.0 / bulut)
        if R < r0:
            R = r0
            break
    return R if R > r0 else r0

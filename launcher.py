import pygame
import sys
import math
import game_settings
from simulation import main as run_simulation
from entities.entity import BLACK, WHITE
from entities.optropi import Optropi
from entities.notropi import Notropi
from entities.kaotropi import Kaotropi
from organs.receptors.Photoreceptor.photoreceptor import Photoreceptor
from organs.receptors.Mechanoreceptor.mechanoreceptor import Mechanoreceptor
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.cilia.cilia import Cilia
from organs.peripheral.membrane.membrane import Membrane
from organs.central.cytoplasm.cytoplasm import Cytoplasm
from organs.central.vacuole.vacuole import Vacuole
from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
from organs.central.ribosome.ribosome import Ribosome
from organs.peripheral.weapons.weapons import WEAPON_CLASSES

# --- MODERN COLOR PALETTE ---
BG_COLOR = (15, 20, 28)
SIDEBAR_COLOR = (22, 28, 38)
CARD_COLOR = (30, 38, 50)
ACCENT_COLOR = (0, 230, 255)
TEXT_COLOR = (220, 230, 240)
GRAY = (120, 130, 140)
LIGHT_GRAY = (180, 190, 200)
HIGHLIGHT = (45, 55, 75)
SUCCESS = (50, 255, 150)
WARNING = (255, 180, 50)
DANGER = (255, 80, 80)

# Organ türleri ve özellikleri
ORGAN_TYPES = {
    "Photoreceptor": {"color": (255, 255, 0), "internal": False, "base_width": 15},
    "Mechanoreceptor": {"color": (255, 100, 100), "internal": False, "base_width": 20},
    "Chemoreceptor": {"color": (100, 255, 100), "internal": False, "base_width": 10},
    "Flagella": {"color": (100, 200, 255), "internal": False, "base_width": 12},
    "Cilia": {"color": (200, 150, 255), "internal": False, "base_width": 8},
    "Membrane": {"color": (150, 150, 150), "internal": True, "base_width": 0},
    "Cytoplasm": {"color": (200, 200, 200), "internal": True, "base_width": 0},
    "Vacuole": {"color": (100, 150, 200), "internal": True, "base_width": 0},
    "Cytoskeleton": {"color": (180, 180, 180), "internal": True, "base_width": 0},
    "Ribosome": {"color": (255, 200, 100), "internal": True, "base_width": 0},
    # --- Saldiri organlari (oyun oncesi yerlestirilebilir) ---
    "Stylet": {"color": (255, 210, 120), "internal": False, "base_width": 10},
    "Harpoon": {"color": (150, 220, 255), "internal": False, "base_width": 9},
    "Nematocyst": {"color": (255, 120, 220), "internal": False, "base_width": 8},
    "Toxin": {"color": (170, 255, 120), "internal": False, "base_width": 12},
    "Lysin": {"color": (255, 150, 90), "internal": False, "base_width": 7},
    "Phagocytosis": {"color": (200, 200, 255), "internal": False, "base_width": 10},
}

# Palet ORGAN_TYPES'tan turetilir. Eskiden iki ayri yerde SABIT liste vardi
# ve ORGAN_TYPES'a organ eklemek editorde gorunmesini saglamiyordu.
# Palet ARTIK ic organlari da icerir. Onceden yalnizca konumu olanlar
# eklenebiliyordu; varliklar bos baslayinca sitoplazma eklemek imkansiz
# hale geldi.
# Zar ve sitoplazma ORGAN DEGIL, hucrenin kendisidir: zarsiz hucre
# saldiri almiyor (take_damage "zar yok" deyip 0 donuyordu), sitoplazmasiz
# hucrenin govdesi yok. Ikisi de her varlikta dogustan bulunur
# (Organism.temel_yapiyi_tamamla) ve palette YER ALMAZ.
TEMEL_YAPILAR = ("Membrane", "Cytoplasm")

# Palet ve organ listesi SINIFLARA ayrilir; onceki tek yigin duzende
# hangi dugmenin ne oldugu okunmuyordu.
ORGAN_SINIFLARI = [
    ("TEMEL YAPI", ["Membrane", "Cytoplasm"]),   # Membrane = zarin AYARLARI
    ("DUYU",       ["Photoreceptor", "Mechanoreceptor", "Chemoreceptor"]),
    ("HAREKET",    ["Flagella", "Cilia"]),
    ("IC YAPI",    ["Vacuole", "Cytoskeleton", "Ribosome"]),
    ("SILAH",      ["Stylet", "Harpoon", "Nematocyst", "Toxin", "Lysin",
                    "Phagocytosis"]),
]

# Palet: temel yapilar disindaki her sey, sinifiyla birlikte
PALET_SINIFLARI = [(ad, [o for o in liste if o not in TEMEL_YAPILAR])
                   for ad, liste in ORGAN_SINIFLARI]
PALET_SINIFLARI = [(ad, liste) for ad, liste in PALET_SINIFLARI if liste]
# --- KATMANLAR ---
#
# Katmanlar entity.organs'a GIRMEZ. Girseydi: Morphology.from_organism
# onlari kalitsal govde planina yazar ama build_organ bilmedigi turu None
# dondurur (mitozda dusrlerdi), extract_organ_config {"type":"Duvar"}
# yazar ama varliklarin yukleyicisinde eslesen dal yoktur (sessizce
# atilirdi), LabCell.from_organism ORGAN_CAPA'ya bakip elerdi ve
# "Total Organs" bese kadar sismis gorunurdu. Bunun yerine katman
# varligi ZARIN bir maskesidir; editor ikinci bir secim kanali kazanir.
KATMAN_ALANLARI = [       # (yatirim alani, gorunen ad, kisa ad)
    ("mucus",   "Mukus",   "Mukus"),
    ("capsule", "Kapsul",  "Kapsul"),
    ("slayer",  "S-layer", "S-layer"),
    ("wall",    "Duvar",   "Duvar"),
]
KATMAN_ADI = {a: ad for a, ad, _k in KATMAN_ALANLARI}
KATMAN_ALANI_ADI = {ad: a for a, ad, _k in KATMAN_ALANLARI}


def _katman_renkleri():
    """Katman renkleri lab'daki kesitle AYNI olsun."""
    try:
        import lab as _lab
        return {l.name: l.color for l in _lab.default_layers()}
    except Exception:
        return {}


KATMAN_RENK = _katman_renkleri()

# Kaldirilamayan yapilar TEK yerde. Uc ayri kopyasi vardi ve birbirini
# tutmuyordu: remove_selected_organ Cytoskeleton'u da engelliyordu ama
# KALDIR dugmesi onun icin ciziliyor ve sessizce hicbir sey yapmiyordu.
KALDIRILAMAZ = ("Membrane", "Cytoplasm", "Cytoskeleton")


def kaldirilabilir(organ_adi):
    return organ_adi not in KALDIRILAMAZ

# Listede gorunecek okunur adlar
ORGAN_ADLARI = {
    "Photoreceptor": "Isik alicisi", "Mechanoreceptor": "Basinc alicisi",
    "Chemoreceptor": "Koku alicisi", "Flagella": "Kamci", "Cilia": "Sil",
    "Membrane": "Zar (katmanlar)", "Cytoplasm": "Sitoplazma",
    "Vacuole": "Koful", "Cytoskeleton": "Hucre iskeleti",
    "Ribosome": "Ribozom", "Stylet": "Stilet", "Harpoon": "Zipkin",
    "Nematocyst": "Nematosist", "Toxin": "Toksin", "Lysin": "Lizin",
    "Phagocytosis": "Fagositoz",
}

# Parametreler de sinif sinif: zarin dokuz ayari tek liste halinde
# okunmuyordu.
PARAM_GRUPLARI = {
    "Membrane": [
        ("PLAZMA ZARI", ["outer"]),
        ("MEKANIZMALAR", ["efflux", "slip", "repair"]),
        ("BUTUNLUK", ["integrity"]),
    ],
    "_silah": [
        ("GELISIM", ["power"]),
        ("YUKLEME", ["carrier", "payload", "marker"]),
    ],
}

# Buton etiketleri - iki ayri palet ayni sozlugu kullansin
ORGAN_SHORT_NAMES = {
    "Photoreceptor": "Eye", "Mechanoreceptor": "Ear", "Chemoreceptor": "Nose",
    "Flagella": "Flag", "Cilia": "Cilia",
    "Vacuole": "Koful", "Cytoskeleton": "Iskelet", "Ribosome": "Ribozom",
    "Stylet": "Stilet", "Harpoon": "Zipkin", "Nematocyst": "Nemato",
    "Toxin": "Toksin", "Lysin": "Lizin", "Phagocytosis": "Fagosit",
}


class InputBox:
    def __init__(self, x, y, w, h, attr, font, ent_id=None, on_change=None):
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.attr = attr
        self.ent_id = ent_id
        self.font = font
        self.active = False
        self.on_change = on_change  # Callback fonksiyonu
        self.update_text()

    def handle_event(self, event, scroll_y=0):
        adjusted_rect = self.rect.move(0, int(scroll_y))
        if event.type == pygame.MOUSEBUTTONDOWN:
            was_active = self.active
            self.active = adjusted_rect.collidepoint(event.pos)
            if was_active and not self.active:
                self.submit()
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                self.submit()
            elif event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            else:
                if event.unicode in "0123456789.-": self.text += event.unicode

    def submit(self):
        try:
            if self.text == "": return
            if self.ent_id:
                old_val = game_settings.ENTITY_CONFIGS[self.ent_id][self.attr]
                new_val = int(float(self.text)) if isinstance(old_val, int) else float(self.text)
                # Sadece değer değiştiyse kaydet ve callback çağır
                if new_val != old_val:
                    game_settings.set_entity_value(self.ent_id, self.attr, new_val)
                    self.text = str(new_val)
                    if self.on_change:
                        self.on_change()
            else:
                old_val = getattr(game_settings, self.attr)
                new_val = int(float(self.text)) if isinstance(old_val, int) else float(self.text)
                # Ekranda yuvarlanmis gosterilen degeri dokunmadan Enter'lamak
                # tam degeri bozmasin
                if self.fmt(new_val) != self.fmt(old_val):
                    game_settings.set_value(self.attr, new_val)
                    self.text = str(new_val)
                    if self.on_change:
                        self.on_change()
        except: self.update_text()

    @staticmethod
    def fmt(v):
        """Kutuya sigacak sekilde kisalt (16.666666666666668 -> 16.6667)."""
        if isinstance(v, bool) or isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            return f"{v:.6g}"
        return str(v)

    def update_text(self):
        if not self.active:
            if self.ent_id:
                self.text = self.fmt(game_settings.ENTITY_CONFIGS[self.ent_id][self.attr])
            else:
                self.text = self.fmt(getattr(game_settings, self.attr))

    def draw(self, screen, scroll_y=0, screen_height=1080):
        draw_rect = self.rect.move(0, int(scroll_y))
        if draw_rect.bottom < 80 or draw_rect.top > screen_height: return
        color = ACCENT_COLOR if self.active else HIGHLIGHT
        pygame.draw.rect(screen, color, draw_rect, 1)
        if self.active:
            overlay = pygame.Surface((draw_rect.width-2, draw_rect.height-2), pygame.SRCALPHA)
            overlay.fill((0, 230, 255, 30))
            screen.blit(overlay, (draw_rect.x+1, draw_rect.y+1))
        txt = self.font.render(self.text, True, TEXT_COLOR)
        screen.blit(txt, (int(draw_rect.x + 8), int(draw_rect.y + 6)))

    # (anahtar, aciklama) - TUM ayarlar burada; eskiden 20'si gorunuyordu,
# geri kalani yalnizca settings.json elle acilarak degistirilebiliyordu.
SETTINGS_SCHEMA = {
        "DÜNYA": [
        ("FOOD_COUNT",        "Başlangıçta haritadaki besin sayısı"),
        ("FOOD_AREA",         "Bir besinin alanı (yarıçapını belirler)"),
        ("FOOD_SPAWN_RATE",   "Saniyede beliren yeni besin (0 = kapalı)"),
        ("FOOD_MAX",          "Haritada aynı anda durabilecek en fazla besin"),
        ("KAOTROPI_COUNT",    "Düşman (kaotropi) sayısı"),
    ],
        "HAREKET (FİZİK)": [
        ("THRUST_SCALE",     "İtki ölçeği: organ kuvvetini px/sn'ye çevirir (hızı topluca ölçekler)"),
        ("DRAG_REF_RADIUS",  "Bu yarıçapta sürüklenme cezası yok (büyük hücre yavaşlar)"),
        ("DRAG_EXPONENT",    "Boyut-hız ters orantısının üssü (1 = Stokes)"),
        ("OVERLAP_TOLERANCE","Hücrelerin iç içe girebileceği pay (yarıçap toplamının oranı)"),
        ("SEPARATION_STRENGTH","Girişmenin bir karede düzeltilen oranı"),
    ],
        "ENERJİ EKONOMİSİ": [
        ("FOOD_ENERGY",          "Sindirilen bir besinin verdiği enerji (ETC verimiyle çarpılır)"),
        ("DIVISION_ENERGY_COST", "Bölünerek yeni hücre üretmenin bedeli"),
        ("BASLANGIC_ENERJI_ORANI", "Kurucu hücreler deposunun bu oranıyla doğar (1 = tam)"),
        ("VACUOLE_ENERGY_MULTI", "Depo = vakuol alanı x bu çarpan"),
        ("ENERGY_REGEN_BASE",    "ETC başlangıç verimi (şu an zar bunu okumuyor)"),
    ],
        "BÖLÜNME (MİTOZ)": [
        ("DIVISION_MODE",           "Açıksa besin sindirilince hücre ikiye bölünür"),
        ("DIVISION_MAX_POPULATION", "Nüfus tavanı (0 = sınırsız)"),
    ],
        "KOKU İLE TANIMA": [
        ("KOKU_YAYIM",              "Koku alaninin gucu: C = bu x koku x exp(-d/KOKU_BULUT) (menzil buradan DOGAR)"),
        ("KOKU_BULUT",              "Bulutun karakteristik boyu (px): her bu kadar mesafede derisim x0.37"),
        ("KOKU_REF_YARICAP",        "Salgi yuzey alaniyla orantili: bu yaricapta yuzey derisimi tam KOKU_YAYIM x koku"),
        ("KOKU_TOPLAM_TAVANI",      "Ayni molekulu salgilayanlar toplanir: esigin bu katindan zayif katkilar dislanir"),
        ("ISIK_BESIN_CARPANI",      "Tam isikta besin kac kat olusur (fotosentez)"),
        ("ISIK_KESIM",              "Isigin bittigi kabul edilen siddet orani: erimde bu degere duser"),
        ("ISIK_ERIM",               "Yeni isigin varsayilan erimi (px); 0 = harita yuksekliginin yarisi"),
        ("ISIK_ALFA",               "Isigin ekrandaki parlakligi (0 = cizme)"),
        ("KOKU_BULUT_ALFA",         "Hucre koku bulutunun ekran yogunlugu (0 = cizme); kenari en hassas burnun duyma siniri"),
        ("KOKU_DOYUM",              "Tepkinin doydugu derisim/esik orani"),
        ("SIGNATURE_ALLELES",       "Kaç farklı soy imzası olabilir"),
        ("SCENT_WEIGHT_MEMBRANE",   "Zarın koku puanına katkısı"),
        ("SPECTRUM_MUTATION_SIGMA", "Koku eşiklerinin mutasyonda ne kadar kaydığı (0-100 ekseninde)"),
        ("SCENT_DIVERGENCE_THRESHOLD","AKRABALIK imzasının değişmesi için birikmesi gereken kalıtsal değişim"),
        ("DIVERGENCE_NEW_ORGAN",    "Yeni organ kazanmanın ıraksamaya kattığı ağırlık"),
        ("DIVERGENCE_UPGRADE",      "Bir gen kademesinin ıraksamaya kattığı ağırlık"),
        ("SIGNATURE_COUPLED_RATIO", "Değişince kilit+anahtarın BİRLİKTE değişme oranı (kalanı kırık sinyalleşme)"),
        ("KAIROMONE_PER_KILL",      "Bir av yemenin sızdırdığı kairomon (avcıyı ele verir)"),
        ("KAIROMONE_DECAY",         "Sızıntının saniyede temizlenme hızı"),
        ("KAIROMONE_MAX",           "Sızıntı doyma tavanı"),
    ],
        "KOKU ALANI": [
        ("SCENT_CELL_SIZE",       "Izgara çözünürlüğü px (küçük = net ama yavaş)"),
        ("SCENT_EVAP_RATE",       "Buharlaşma /sn (yüksek = dar, keskin koku bulutu)"),
        ("SCENT_DIFF_RATE",       "Yayılma hızı /sn"),
        ("SCENT_MAX",             "Bir hücredeki en yüksek koku yoğunluğu"),
        ("FOOD_SCENT_EMISSION",   "Besin yarıçapı başına salınan koku /sn"),
        ("SCENT_HEATMAP_INTERVAL","Isı haritası kaç sn'de bir yeniden çizilsin"),
    ],
        "KOKU TAKİBİ (KEMOTAKSİ)": [
        ("SCENT_SENSITIVITY_BASE","Algı eşiği = bu / burun uzunluğu"),
        ("CHEMO_SAMPLE_INTERVAL", "Algı penceresi sn (kare başına ölçüm işe yaramaz)"),
        ("TUMBLE_GAIN_POSITIVE",  "Koku ARTARKEN koşuyu ne kadar uzatsın"),
        ("TUMBLE_GAIN_NEGATIVE",  "Koku AZALIRKEN koşuyu ne kadar kısaltsın"),
        ("CHEMO_RUN_CLAMP",       "Koşu en fazla kaç kat uzayıp kısalabilir"),
        ("TUMBLE_ANGLE_SIGMA",    "Dönüş açısı dağılımı derece (düzgün dağılım yön hafızasını siler)"),
        ("SPATIAL_CHEMO_MIN",     "2+ burunla uzamsal gradyan için gereken en az kontrast"),
        ("LEVY_ALPHA",            "Arama deseni (düşük = uzun atılımlar). Koku bunun ÜSTÜNE eğilim ekler"),
        ("LEVY_MIN_STEP",         "En kısa düz gidiş"),
        ("LEVY_MAX_DURATION",     "En uzun düz gidiş sn"),
    ],
        "EVRİM": [
        ("ORGAN_GAIN_RATE",     "Bölünme başına YENİ yapı (organ ya da katman) olasılığı"),
        ("ORGAN_LOSS_RATE",     "Bölünme başına yapı KAYBI olasılığı"),
        ("ORGAN_ANGLE_RATE",    "Bölünme başına organ AÇISININ kayma olasılığı"),
        ("ORGAN_ANGLE_SIGMA",   "Açı kaymasının genişliği (derece)"),
        ("BEHAVIOR_MUTATION_RATE","Davranış tablosu girdisi başına mutasyon"),
        ("SOSYAL_ESIK",         "Sosyal öncelik geninin koku şiddetiyle karşılaştırıldığı ölçek"),
        ("PREY_BIOMASS_YIELD",  "Trofik verim: avın enerjisinin ne kadarı yiyene geçer"),
        ("CORPSE_FOOD_MAX",     "Bir leşten çıkabilecek en fazla besin"),
        ("TOXIN_ALLELES",       "Kaç farklı bakteriosin varyantı (bağışıklık ona özgü)"),
        ("TOXIN_ALLELE_MUTATION","Bölünmede toksin varyantının değişme olasılığı"),
        ("FOOD_PATCH_SIZE",     "Bir besin yamasındaki besin sayısı"),
        ("FOOD_PATCH_SIGMA",    "Yamanın yarıçapı px"),
        ("TRAIL_RATE",          "İz bırakma hızı (nokta/sn)"),
    ],
        "BAKIM MALİYETLERİ (birim/sn)": [
        ("COST_FLAGELLA",       "Kamçı: uzunluk başına"),
        ("COST_CILIA",          "Sil: uzunluk başına"),
        ("COST_CHEMORECEPTOR",  "Burun: uzunluk başına"),
        ("COST_MECHANORECEPTOR","Kulak: hassasiyet başına"),
        ("COST_PHOTORECEPTOR",  "Göz: (menzil x açı) başına"),
        ("COST_CYTOPLASM",      "Gövde: boyutun karesi başına"),
        ("COST_DIGESTION",      "Sindirim enzimi: 1/süre başına"),
        ("COST_VACUOLE",        "Depo: alan başına"),
        ("COST_RIBOSOME",       "Ribozom: 1/üretim süresi başına"),
        ("COST_MEMBRANE",       "Zar/ETC: verim başına"),
        ("COST_MEMORY",         "Hafıza: kapasite başına"),
    ],
        "GELİŞİM ADIMLARI (gen puanı başına)": [
        ("GROW_FLAGELLA",     "Kamçı uzunluğu +"),
        ("GROW_CILIA",        "Sil uzunluğu +"),
        ("GROW_SMELL",        "Burun uzunluğu +"),
        ("GROW_SOUND",        "Kulak (ŞU AN OKUNMUYOR - kod sabit 0.2 kullanıyor)"),
        ("GROW_VISION_RANGE", "Görüş menzili +"),
        ("GROW_VISION_ANGLE", "Görüş açısı + (radyan)"),
        ("GROW_BODY",         "Gövde boyutu +"),
        ("GROW_MAX_ENERGY",   "Vakuol boyutu +"),
        ("GROW_ENERGY_REGEN", "ETC verimi + (kod varsayılanı 0.1)"),
        ("GROW_MEMORY",       "Hafıza kapasitesi +"),
        ("GROW_DIGESTION",    "Sindirim süresi - (taban 1.0)"),
        ("GROW_RIBOSOME",     "Üretim süresi - (taban 1.0)"),
    ],
        "ORGAN TEMELLERİ": [
        ("DIGESTION_TIME",       "Başlangıç sindirim süresi sn"),
        ("RIBOSOME_TIME",        "Başlangıç üretim süresi sn"),
        ("CILIA_SPEED_MULTI",    "Sil itme çarpanı"),
        ("FLAGELLA_SPEED_MULTI", "Kamçı itme çarpanı"),
        ("CILIA_TURN_MULTI",     "Sil dönüş çarpanı"),
        ("FLAGELLA_TURN_MULTI",  "Kamçı dönüş çarpanı"),
        ("CYTOSKELETON_AREA",    "İskeletin kapladığı alan"),
        ("RIBOSOME_AREA",        "Ribozomun kapladığı alan"),
        ("VACUOLE_AREA",         "Vakuolün temel alanı"),
    ],
}


# Turkce harfleri sadelestirerek karsilastirma: "İ".lower() -> "i̇" (nokta
# birlesik) oldugu icin duz "i" ile eslesmiyordu. Ayrica kullanicinin
# aksansiz yazmasina da izin verir ("maliyet" -> "MALİYETLERİ" bulur).
_TR_MAP = str.maketrans({
    "İ": "i", "I": "i", "ı": "i", "Ş": "s", "ş": "s", "Ğ": "g", "ğ": "g",
    "Ü": "u", "ü": "u", "Ö": "o", "ö": "o", "Ç": "c", "ç": "c",
})

def _norm(text):
    return text.translate(_TR_MAP).lower()


class ToggleBox:
    """Bool ayarlar icin ac/kapa dugmesi (InputBox yalnizca rakam kabul eder)."""
    def __init__(self, x, y, w, h, attr, font):
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.attr = attr
        self.font = font
        self.active = False

    @property
    def value(self):
        return bool(getattr(game_settings, self.attr))

    def handle_event(self, event, scroll_y=0):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.move(0, int(scroll_y)).collidepoint(event.pos):
                game_settings.set_value(self.attr, not self.value)

    def update_text(self):
        pass

    def draw(self, screen, scroll_y=0, screen_height=1080):
        r = self.rect.move(0, int(scroll_y))
        if r.bottom < 80 or r.top > screen_height: return
        on = self.value
        col = SUCCESS if on else GRAY
        pygame.draw.rect(screen, col, r, 1)
        knob = pygame.Rect(r.x + (r.width // 2 if on else 2), r.y + 2,
                           r.width // 2 - 2, r.height - 4)
        pygame.draw.rect(screen, col, knob)
        txt = self.font.render("ACIK" if on else "KAPALI", True, BG_COLOR if on else TEXT_COLOR)
        screen.blit(txt, txt.get_rect(center=knob.center))


class ModernLauncher:
    def __init__(self):
        pygame.init()
        # Pencere boyutu
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Evolution Engine - Lab Edition")
        self.clock = pygame.time.Clock()
        self.font_main = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 22)
        self.font_title = pygame.font.Font(None, 48)
        self.font_tiny = pygame.font.Font(None, 18)   # satir aciklamalari

        self.state = "DASHBOARD"
        self.sidebar_width = 220
        self.tabs = ["DASHBOARD", "ENTITIES", "HARITA", "SETTINGS"]

        # --- HARITA DUZENLEYICI ---
        # Yamalar DUNYA koordinatlarinda saklanir: [x, y, adet, yaricap].
        self.harita_yamalar = [list(y) for y in
                               getattr(game_settings, 'HARITA_YAMALARI', [])]
        self.harita_adet = 26          # firca: bir yamaya kac besin
        self.harita_yaricap = 45.0     # firca: yamanin dagilma yaricapi
        self.harita_siliyor = False    # sag tik / silgi kipi
        self.harita_suruklu = False
        # UC KATMAN, TEK TUVAL. Besin nerede, isik nerede ve kurucularin
        # nereden basladigi ayni haritanin uc katmani; hepsi ekolojiyi
        # birlikte belirliyor, ayri ekranlara bolmek karsilastirmayi
        # zorlastirirdi.
        self.harita_kip = "besin"      # besin | isik | baslangic
        self.harita_isiklar = [list(k) for k in
                               (getattr(game_settings, 'HARITA_ISIKLARI', []) or [])]
        self.harita_baslangic = [list(b) for b in
                                 (getattr(game_settings, 'HARITA_BASLANGIC', []) or [])]
        self.isik_guc = 1.0            # firca: isik gucu
        self.isik_erim = 0.0           # 0 = varsayilan (yukseklik/2)

        self.scroll_y = 0
        self.max_scroll = 0
        self.total_content_height = 0
        self.dragging_scroll = False
        self.entity_ui_elements = []

        # Preview panel ayarları
        self.preview_scale = 4.0
        self._onizleme_yarikenar = 140
        # Katman secimi ORGAN secimiyle ayni alani paylasamaz: negatif
        # sentinel indeks kullanmak tehlikeli olurdu, entity.organs[-2]
        # Python'da HATA VERMEZ, baska bir organi dondurur ve kullanici
        # yanlis organi duzenler. Bu yuzden ayri bir kanal.
        self.selected_layer = None      # katman ADI ya da None
        self.preview_panel_height = 380

        # Organ editör ayarları
        self.selected_organ = None
        self.selected_organ_index = -1
        self.dragging_organ = False
        self.drag_start_angle = 0
        self.organ_editor_mode = False  # True = organ düzenleme modu aktif
        self.hover_organ_index = -1
        self.add_organ_menu_open = False
        self.organ_overlap_warning = False
        self.preview_center_x = 0
        self.preview_center_y = 0

        # Organ editör butonları
        self.remove_btn_rect = None
        self.add_organ_btns = []
        self.organ_param_inputs = {}  # Seçili organ için parametre input'ları

        # Entity editör pop-up
        self.entity_popup_open = False
        self.popup_close_btn = None
        self.popup_entity = None  # Popup'ta düzenlenen varlık

        # Entity editör için varsayılanlar
        self.selected_entity = None
        self.dummy_optropis = []
        self.dummy_notropi = None
        self.dummy_kaotropi = None

        self.settings_categories = SETTINGS_SCHEMA
        self.search = ""
        self.search_active = False
        self.reset_buttons = []
        # draw_settings icinde guncellenir; olaylar cizimden once islendigi
        # icin baslangic degeri gerekli
        self.search_rect = pygame.Rect(0, 0, 0, 0)        
        self.setup_ui()

    def setup_ui(self):
        self.ui_elements = []
        if self.state == "SETTINGS":
            self.scroll_y = 0
            self._layout_settings()
        
        elif self.state == "ENTITIES":
            self.dummy_optropis = [Optropi(i, 0, 0, c) for i, c in enumerate([(255,0,255), (255,255,0), (0,255,0), (255,165,0)])]
            self.dummy_notropi = Notropi(0, 0, 0)
            self.dummy_kaotropi = Kaotropi(0, 0, 0)
            self.selected_entity = self.dummy_optropis[0]
            self.create_entity_editor()

    ROW_H = 52          # iki satirlik kutu: isim + aciklama
    CAT_H = 58

    def _visible_settings(self):
        """Arama filtresinden gecen (kategori -> [(anahtar, aciklama)]) listesi."""
        q = _norm(self.search.strip())
        out = []
        for cat, rows in self.settings_categories.items():
            if q:
                rows = [r for r in rows
                        if q in _norm(r[0]) or q in _norm(r[1]) or q in _norm(cat)]
            if rows:
                out.append((cat, rows))
        return out

    def _layout_settings(self):
        """Gorunur satirlar icin kutulari olustur ve toplam yuksekligi hesapla."""
        self.ui_elements = []
        self.reset_buttons = []
        y = 100
        for cat, rows in self._visible_settings():
            y += self.CAT_H
            for attr, _desc in rows:
                default = game_settings.get_default(attr)
                if isinstance(default, bool):
                    box = ToggleBox(self.screen_width - 200, y + 6, 110, 30, attr, self.font_small)
                else:
                    box = InputBox(self.screen_width - 200, y + 6, 110, 30, attr, self.font_small)
                self.ui_elements.append(box)
                self.reset_buttons.append(
                    (pygame.Rect(self.screen_width - 78, y + 6, 30, 30), attr))
                y += self.ROW_H
            y += 14
        self.total_content_height = max(1, y - 100)
        self.max_scroll = min(0, (self.screen_height - 100) - self.total_content_height)
        if self.scroll_y < self.max_scroll:
            self.scroll_y = self.max_scroll

    def handle_settings_events(self, event, m_pos):
        """Arama kutusu ve satir sifirlama dugmeleri."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.search_rect.collidepoint(m_pos):
                self.search_active = True
                return True
            self.search_active = False
            for rect, attr in self.reset_buttons:
                if rect.move(0, int(self.scroll_y)).collidepoint(m_pos):
                    game_settings.reset_value(attr)
                    return True
        if event.type == pygame.KEYDOWN and self.search_active:
            if event.key == pygame.K_BACKSPACE:
                self.search = self.search[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.search_active = False
            elif event.unicode and event.unicode.isprintable():
                self.search += event.unicode
            self._layout_settings()
            return True
        return False

    def _sync_organ_config_with_genes(self, ent_id):
        """Skaler gen değerlerini kaydedilmiş organ düzenine yansıtır.

        Burada eskiden clear_entity_organs çağrılıyordu: tek bir gen değeri
        değiştirildiğinde kullanıcının TÜM organ yerleşimi siliniyor ve
        entity varsayılan organlarla yeniden kuruluyordu. Onun yerine düzen
        korunur, yalnızca organ config'inin gölgelediği değerler güncellenir.

        Düzenlenebilir skalerlerden memory / ribosome_area / vacuole_area
        zaten her yüklemede cfg'den okunuyor; organ config tarafından
        gölgelenen tek değer Cytoplasm'ın "size" alanı.
        """
        organs_config = game_settings.get_entity_organs(ent_id)
        if not organs_config:
            return
        cfg = game_settings.ENTITY_CONFIGS[ent_id]
        changed = False
        for organ_cfg in organs_config:
            if organ_cfg.get("type") == "Cytoplasm" and "size" in organ_cfg:
                if organ_cfg["size"] != cfg["cytoplasm"]:
                    organ_cfg["size"] = cfg["cytoplasm"]
                    changed = True
        if changed:
            game_settings.set_entity_organs(ent_id, organs_config)

    def refresh_selected_entity(self):
        """Seçili entity'yi güncel config ile yeniden oluşturur."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return

        # Gen kutusu hucreyi yeniden kurmadan once mevcut organ plani ve
        # henuz Enter'lanmamis organ degeri kayda gecmeli.
        self.commit_organ_inputs()
        self.save_entity_organ_config(entity)

        # Seçili entity'nin index ve rengini sakla
        if isinstance(entity, Kaotropi):
            self._sync_organ_config_with_genes("kaotropi")
            self.dummy_kaotropi = Kaotropi(0, 0, 0)
            self.selected_entity = self.dummy_kaotropi
            if self.entity_popup_open:
                self.popup_entity = self.dummy_kaotropi
        elif isinstance(entity, Notropi):
            ent_id = "notropi"
            # Organ düzeni korunur; yalnızca gölgelenen değerler güncellenir
            self._sync_organ_config_with_genes(ent_id)
            # Notropi'yi yeniden oluştur
            self.dummy_notropi = Notropi(0, 0, 0)
            self.selected_entity = self.dummy_notropi
            if self.entity_popup_open:
                self.popup_entity = self.dummy_notropi
        else:
            idx = entity.index
            color = entity.color
            ent_id = f"optropi_{idx}"
            # Organ düzeni korunur; yalnızca gölgelenen değerler güncellenir
            self._sync_organ_config_with_genes(ent_id)
            # Optropi'yi yeniden oluştur
            self.dummy_optropis[idx] = Optropi(idx, 0, 0, color)
            self.selected_entity = self.dummy_optropis[idx]
            if self.entity_popup_open:
                self.popup_entity = self.dummy_optropis[idx]

        # Detay paneli eski hucrenin organini gostermeye devam etmesin.
        if 0 <= self.selected_organ_index < len(self.selected_entity.organs):
            self.selected_organ = self.selected_entity.organs[self.selected_organ_index]
        else:
            self.selected_organ = None
            self.selected_organ_index = -1
        self.organ_param_inputs = {}
        self.dragging_organ = False

    def get_organ_angular_width(self, organ):
        """Organın zar üzerinde kapladığı açısal genişliği hesaplar (derece)."""
        organ_name = organ.__class__.__name__
        base_width = ORGAN_TYPES.get(organ_name, {}).get("base_width", 10)

        # Organa özel genişlik hesabı
        if isinstance(organ, Photoreceptor):
            # Görüş açısı ne kadar genişse o kadar yer kaplar
            return max(15, math.degrees(organ.logic.angle) * 0.5 + base_width)
        elif isinstance(organ, Mechanoreceptor):
            # Size'a göre genişlik
            return base_width + organ.logic.size * 5
        elif isinstance(organ, Chemoreceptor):
            return base_width + organ.logic.length * 0.5
        elif isinstance(organ, Flagella):
            return base_width + organ.logic.length * 0.3
        elif isinstance(organ, Cilia):
            return base_width + organ.logic.length * 0.2
        # Silahlar: AYAK IZI base_width kalir. Atis yayi ayri bir seydir
        # (nerede ates edebilir) ve ayrica cizilir - bir kez ayak izi
        # yerine yay kullanilinca 180 derecelik toksin butun zari
        # "kapliyor" sayildi ve editor toksin/lizin eklemeyi reddetti.

        return base_width

    def check_organ_overlap(self, organ_index, new_angle):
        """
        Belirli bir açıda organ örtüşmesi olup olmadığını kontrol eder.
        Returns: (overlap_exists, overlapping_organ_index)
        """
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return False, -1

        organ = entity.organs[organ_index]
        organ_name = organ.__class__.__name__

        # İç organlar için örtüşme kontrolü yapma
        if ORGAN_TYPES.get(organ_name, {}).get("internal", True):
            return False, -1

        new_angle_deg = math.degrees(new_angle) % 360
        organ_width = self.get_organ_angular_width(organ)

        for i, other in enumerate(entity.organs):
            if i == organ_index:
                continue

            other_name = other.__class__.__name__
            if ORGAN_TYPES.get(other_name, {}).get("internal", True):
                continue

            other_angle_deg = math.degrees(other.attachment_angle) % 360
            other_width = self.get_organ_angular_width(other)

            # İki organın arasındaki açısal mesafe
            diff = abs(new_angle_deg - other_angle_deg)
            if diff > 180:
                diff = 360 - diff

            # Minimum mesafe = her iki organın yarı genişliklerinin toplamı
            min_distance = (organ_width + other_width) / 2

            if diff < min_distance:
                return True, i

        return False, -1

    def get_organ_at_position(self, screen_x, screen_y, preview_center_x, preview_center_y):
        """Ekran koordinatında bir organ var mı kontrol eder."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return -1

        # Preview merkezine göre offset
        dx = screen_x - preview_center_x
        dy = screen_y - preview_center_y

        # Tıklama noktasının açısı
        click_angle = math.atan2(dy, dx)
        click_dist = math.sqrt(dx*dx + dy*dy)

        # Büyütülmüş yarıçap. Organlar ZARFIN DISINA cizildigi icin
        # tiklama testi de o yaricapi kullanmali; cekirdek yaricapiyla
        # olculunce kalin zarli hucrede organlar gorundugu yerde
        # tiklanamiyordu.
        scaled_radius = getattr(self, '_onizleme_organ_r', None) \
            or entity.radius * self.preview_scale

        # Zar yakınında mı? (±50 piksel tolerans)
        if abs(click_dist - scaled_radius) > 50:
            return -1

        # En yakın organı bul
        best_match = -1
        best_diff = float('inf')

        for i, organ in enumerate(entity.organs):
            organ_name = organ.__class__.__name__
            # İç organları atla
            if ORGAN_TYPES.get(organ_name, {}).get("internal", True):
                continue

            # Organın açısı (entity sağa baktığı için düzeltme yapmaya gerek yok)
            organ_angle = organ.attachment_angle

            # Açı farkı
            diff = abs(math.atan2(math.sin(click_angle - organ_angle),
                                  math.cos(click_angle - organ_angle)))
            diff_deg = math.degrees(diff)

            # Organın genişliği kadar tolerans
            organ_width = self.get_organ_angular_width(organ)

            if diff_deg < organ_width and diff < best_diff:
                best_diff = diff
                best_match = i

        return best_match

    def add_organ_to_entity(self, organ_type, angle=0):
        """Entity'ye yeni organ ekler."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return False

        # Organ türüne göre yeni organ oluştur
        if organ_type == "Photoreceptor":
            new_organ = Photoreceptor(attachment_angle=angle, range=30, angle=0.3)
        elif organ_type == "Mechanoreceptor":
            new_organ = Mechanoreceptor(attachment_angle=angle, size=1.0)
        elif organ_type == "Chemoreceptor":
            new_organ = Chemoreceptor(attachment_angle=angle, length=5.0)
        elif organ_type == "Flagella":
            new_organ = Flagella(attachment_angle=angle, length=10.0)
        elif organ_type == "Cilia":
            new_organ = Cilia(attachment_angle=angle, length=3.0)
        elif organ_type in WEAPON_CLASSES:
            new_organ = WEAPON_CLASSES[organ_type](attachment_angle=angle)
        else:
            # IC ORGANLAR da eklenebilmeli. Once buraya dusup `return False`
            # veriyorlardi, yani Cytoplasm/Membrane/Vacuole/Ribosome/
            # Cytoskeleton hic eklenemiyordu. Varliklarin organ listesi
            # bosaltilinca bu, hucreye SITOPLAZMA bile ekleyememek demekti -
            # boyutu ve gorunurlugu belirleyen organ o.
            try:
                from organs.registry import make_organ
                new_organ = make_organ(organ_type)
            except Exception:
                return False

        ic = ORGAN_TYPES.get(organ_type, {}).get("internal", False)
        if not ic:
            # Ortusme kontrolu yalnizca KONUMU olan organlar icin anlamli
            temp_index = len(entity.organs)
            entity.organs.append(new_organ)
            overlap, _ = self.check_organ_overlap(temp_index, angle)
            entity.organs.pop()
            if overlap:
                return False

        # `entity.organs.append` yerine add_organ: yan etkileri o yapiyor
        # (membrane/body/vacuole atamalari, cilia yonleri, kuresel olcek).
        # Dogrudan append edilince Membrane eklense bile entity.membrane
        # atanmiyordu.
        entity.add_organ(new_organ)
        entity.recalculate_physics()
        self.save_entity_organ_config(entity)
        return True

    def remove_selected_organ(self):
        """Seçili organı entity'den kaldırır."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity or self.selected_organ_index < 0:
            return False

        organ = entity.organs[self.selected_organ_index]
        organ_name = organ.__class__.__name__

        # Kritik organları kaldırma
        if not kaldirilabilir(organ_name):
            return False

        entity.organs.pop(self.selected_organ_index)
        self.selected_organ = None
        self.selected_organ_index = -1
        entity.recalculate_physics()
        self.save_entity_organ_config(entity)
        return True

    def extract_organ_config(self, entity):
        """Entity'den organ konfigürasyonunu çıkarır."""
        organs_config = []
        for organ in entity.organs:
            organ_name = organ.__class__.__name__
            config = {
                "type": organ_name,
                "angle": organ.attachment_angle
            }
            # Silahin tasiyici/yuk/belirtec secimi de KAYDEDILMELI, yoksa
            # editorde yapilan secim oyuna hic ulasmaz.
            if organ_name in WEAPON_CLASSES:
                for alan in ("carrier", "payload", "marker"):
                    if hasattr(organ.logic, alan):
                        config[alan] = int(getattr(organ.logic, alan))

            # Organa özel parametreler
            if organ_name == "Photoreceptor":
                config["range"] = organ.logic.range
                config["angle_val"] = organ.logic.angle
            elif organ_name == "Mechanoreceptor":
                config["sensitivity"] = organ.logic.sensitivity
            elif organ_name == "Chemoreceptor":
                config["length"] = organ.logic.length
            elif organ_name == "Flagella":
                config["length"] = organ.logic.length
            elif organ_name == "Cilia":
                config["length"] = organ.logic.length
            elif organ_name == "Cytoplasm":
                config["size"] = organ.logic.size
            elif organ_name == "Vacuole":
                config["size"] = organ.logic.size
            elif organ_name == "Ribosome":
                config["time"] = organ.logic.base_production_time
            elif organ_name in WEAPON_CLASSES:
                config["power"] = organ.logic.power
            elif organ_name == "Membrane":
                # Zar savunmalari nitelik oldugu icin organ config'inde tasinir
                lg = organ.logic
                config["integrity"] = lg.max_integrity
                for d in ("wall", "outer", "capsule", "efflux", "repair",
                          "slip", "mucus", "slayer",
                          # katman VARLIGI da kaydedilmeli, yoksa editorde
                          # kaldirilan duvar oyunda geri gelir
                          "var_mucus", "var_capsule", "var_slayer", "var_wall"):
                    config[d] = getattr(lg, d)
                # KATMAN KALINLIKLARI da kaydedilir: yeni kazanilan katman
                # ince baslar, kullanici kalinlastirir - bu deger oyuna
                # ulasmazsa her yuklemede varsayilana donerdi.
                _kal = getattr(organ.logic, "kalinlik", None)
                if isinstance(_kal, dict):
                    config["kalinlik"] = {k: float(v) for k, v in _kal.items()}

            organs_config.append(config)

        return organs_config

    @staticmethod
    def entity_id(entity):
        """Entity -> settings.json kimligi. Tur ozel dallari tek yerde tutar."""
        if isinstance(entity, Kaotropi):
            return "kaotropi"
        if isinstance(entity, Notropi):
            return "notropi"
        return f"optropi_{entity.index}"

    def editable_entities(self):
        """Editorde gorunen tum varliklar (kaotropi dahil)."""
        out = list(self.dummy_optropis)
        if self.dummy_notropi:
            out.append(self.dummy_notropi)
        if self.dummy_kaotropi:
            out.append(self.dummy_kaotropi)
        return out

    def commit_organ_inputs(self):
        """Secim/pencere kapanmadan once kutudaki son degeri organa uygula."""
        for input_key, inp in self.organ_param_inputs.items():
            if not inp["active"]:
                continue
            inp["active"] = False
            if input_key.startswith(("katman_", "kalinlik_")):
                self.update_katman_param(inp["param"], inp["text"])
            else:
                self.update_organ_param(inp["param"], inp["text"])

    def save_entity_organ_config(self, entity):
        """Tamamlanan duzenlemeyi hemen kaydet; ayni veriyi tekrar yazma."""
        if entity is None:
            return
        ent_id = self.entity_id(entity)
        config = self.extract_organ_config(entity)
        if game_settings.get_entity_organs(ent_id) != config:
            game_settings.set_entity_organs(ent_id, config)

    def save_all_organ_configs(self):
        """Acik kutular dahil tum entity'lerin organ planlarini kaydet."""
        self.commit_organ_inputs()
        for _, ibox in self.entity_ui_elements:
            if ibox.active:
                ibox.active = False
                ibox.submit()
        for entity in self.editable_entities():
            self.save_entity_organ_config(entity)

    def close_entity_editor(self):
        self.save_all_organ_configs()
        self.entity_popup_open = False
        self.popup_entity = None
        self.selected_organ = None
        self.selected_organ_index = -1
        self.selected_layer = None
        self.organ_editor_mode = False
        self.organ_param_inputs = {}
        self.dragging_organ = False
        self.organ_overlap_warning = False

    def create_entity_editor(self):
        self.entity_ui_elements = []
        if not self.selected_entity:
            return
        ent_id = self.entity_id(self.selected_entity)
        cfg = game_settings.ENTITY_CONFIGS[ent_id]

        # InputBox'lar draw_entities'de pozisyonlanacak
        # Organ editöründe düzenlenen parametreleri atla
        skip_keys = [
            "name", "organs",
            # Organ parametreleri (artık organ editöründe düzenleniyor)
            "smell", "sound", "vision_range", "vision_angle", "flagella", "cilia"
        ]
        for key in cfg.keys():
            if key in skip_keys:
                continue
            ibox = InputBox(0, 0, 80, 28, key, self.font_small, ent_id=ent_id,
                           on_change=self.refresh_selected_entity)
            self.entity_ui_elements.append((key, ibox))

    def set_state(self, state):
        if self.state == state:
            return
        # ENTITIES sekmesinden ayrılırken organ düzenini kalıcılaştır
        if self.state == "ENTITIES":
            self.close_entity_editor()
        if self.state == "HARITA" and state != "HARITA":
            self.harita_kaydet()
        self.state = state
        self.setup_ui()

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, (0, 0, self.sidebar_width, self.screen_height))
        self.screen.blit(self.font_title.render("EVO", True, ACCENT_COLOR), (30, 40))
        self.screen.blit(self.font_small.render("DESIGNER v4.1", True, TEXT_COLOR), (30, 85))
        for i, tab in enumerate(self.tabs):
            y = 180 + i * 60
            rect = pygame.Rect(0, y, self.sidebar_width, 50)
            color = ACCENT_COLOR if tab == self.state else (WHITE if rect.collidepoint(pygame.mouse.get_pos()) else GRAY)
            if tab == self.state: pygame.draw.rect(self.screen, ACCENT_COLOR, (0, y, 5, 50))
            self.screen.blit(self.font_main.render(tab, True, color), (30, y + 12))

    # ================================================================
    # HARITA DUZENLEYICI
    #
    # Besin, dunyanin belli yerlerinde OBEKLER halinde bulunur ve nerede
    # oldugu ekolojinin en belirleyici parametresidir: yamalarin sayisi ve
    # araligi, koklamanin ise yarayip yaramayacagini, populasyonun kurulup
    # kurulamayacagini, hatta avlanmanin baslayip baslamayacagini belirler.
    # Bunu rastgeleye birakmak yerine elle kurabilmek gerekiyordu.
    #
    # Cizilen duzen KALICIDIR: hem baslangic besini hem de sonradan dogan
    # besin yalnizca bu yamalarda olusur (bkz. Dunya.besin_yamasi).
    # ================================================================

    def _harita_tuval(self):
        """Tuvalin ekrandaki dikdortgeni ve dunya -> ekran olcegi."""
        from entities.entity import WIDTH as DW, HEIGHT as DH
        x0 = self.sidebar_width + 30
        y0 = 196                       # iki sira dugme sigsin
        gen = self.screen_width - x0 - 40
        yuk = self.screen_height - y0 - 40
        k = min(gen / DW, yuk / DH)
        return pygame.Rect(x0, y0, int(DW * k), int(DH * k)), k, DW, DH

    def _harita_dunyaya(self, ekran_pos):
        r, k, DW, DH = self._harita_tuval()
        return ((ekran_pos[0] - r.x) / k, (ekran_pos[1] - r.y) / k)

    def harita_dugmeleri(self):
        """[(dikdortgen, etiket, eylem)] - iki siralik dugme seridi.

        Ust sira KIP secer (hangi katman duzenleniyor), alt sira o kipin
        fircasini ayarlar. Kip degisince alt sira da degisir; boylece
        "adet" dugmesi isik kipindeyken anlamsizca durmaz.
        """
        out = []
        x = self.sidebar_width + 30
        for etiket, eylem, gen in (("BESIN", "kip:besin", 100),
                                   ("ISIK", "kip:isik", 90),
                                   ("BASLANGIC", "kip:baslangic", 130)):
            out.append((pygame.Rect(x, 100, gen, 34), etiket, eylem))
            x += gen + 8
        x += 18
        for etiket, eylem, gen in (("SILGI", "silgi", 90),
                                   ("TEMIZLE", "temizle", 110)):
            out.append((pygame.Rect(x, 100, gen, 34), etiket, eylem))
            x += gen + 8

        x = self.sidebar_width + 30
        if self.harita_kip == "besin":
            firca = (("- ADET", "adet-", 90), ("+ ADET", "adet+", 90),
                     ("- YARICAP", "yari-", 110), ("+ YARICAP", "yari+", 110),
                     ("RASTGELE", "rastgele", 120))
        elif self.harita_kip == "isik":
            firca = (("- GUC", "guc-", 90), ("+ GUC", "guc+", 90),
                     ("- ERIM", "erim-", 100), ("+ ERIM", "erim+", 100))
        else:
            firca = ()
        for etiket, eylem, gen in firca:
            out.append((pygame.Rect(x, 142, gen, 34), etiket, eylem))
            x += gen + 8
        return out

    def _isik_erim(self):
        """Fircanin erimi; 0 ise varsayilan (harita yuksekliginin yarisi)."""
        if self.isik_erim > 0.0:
            return self.isik_erim
        from systems import isik as _isik
        return _isik.varsayilan_erim()

    def draw_harita(self):
        r, k, DW, DH = self._harita_tuval()
        sx = self.sidebar_width + 30

        self.screen.blit(self.font_title.render("HARITA", True, ACCENT_COLOR),
                         (sx, 35))
        toplam = sum(int(y[2]) for y in self.harita_yamalar)
        bilgi = ("%d yama / %d besin   %d isik   %d baslangic   |   "
                 "sol tik: koy, sag tik: sil, surukle: boya"
                 % (len(self.harita_yamalar), toplam,
                    len(self.harita_isiklar), len(self.harita_baslangic)))
        self.screen.blit(self.font_small.render(bilgi, True, TEXT_COLOR), (sx, 78))

        # dugmeler
        fare = pygame.mouse.get_pos()
        for rect, etiket, eylem in self.harita_dugmeleri():
            secili = ((eylem == "silgi" and self.harita_siliyor)
                      or eylem == "kip:" + self.harita_kip)
            renk = (DANGER if eylem in ("temizle",) else
                    (SUCCESS if secili else
                     (WHITE if rect.collidepoint(fare) else GRAY)))
            pygame.draw.rect(self.screen, renk, rect, 2 if not secili else 0)
            t = self.font_small.render(etiket, True,
                                       BG_COLOR if secili else renk)
            self.screen.blit(t, t.get_rect(center=rect.center))
        # Firca degerleri alt seridin SAGINA yazilir.
        if self.harita_kip == "besin":
            _fm = "firca: %d besin / %.0f px" % (self.harita_adet, self.harita_yaricap)
        elif self.harita_kip == "isik":
            _fm = "firca: guc %.2f / erim %.0f px" % (self.isik_guc, self._isik_erim())
        else:
            _fm = "tikla: kurucularin dogacagi nokta"
        d = self.font_small.render(_fm, True, ACCENT_COLOR)
        _alt = [r for r, _e, _a in self.harita_dugmeleri() if r.y == 142]
        _sx2 = (max(r.right for r in _alt) + 16) if _alt else (self.sidebar_width + 30)
        self.screen.blit(d, (min(_sx2, self.screen_width - d.get_width() - 20), 150))

        # tuval
        pygame.draw.rect(self.screen, (10, 14, 20), r)
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, r, 2)
        # dunya izgarasi (dortte bir cizgileri)
        for i in (1, 2, 3):
            pygame.draw.line(self.screen, (26, 32, 42),
                             (r.x + r.w * i / 4, r.y),
                             (r.x + r.w * i / 4, r.y + r.h))
            pygame.draw.line(self.screen, (26, 32, 42),
                             (r.x, r.y + r.h * i / 4),
                             (r.x + r.w, r.y + r.h * i / 4))

        # KATMANLAR TUVALIN ICINDE KALIR. Erim halkasi tuvalden tasinca
        # baslik ve dugmelerin uzerine tasiyordu.
        self.screen.set_clip(r)

        # yamalar
        for wx, wy, adet, yari in self.harita_yamalar:
            px = int(r.x + wx * k)
            py = int(r.y + wy * k)
            pr = max(3, int(yari * k))
            hale = pygame.Surface((pr * 4, pr * 4), pygame.SRCALPHA)
            pygame.draw.circle(hale, (60, 220, 120, 40), (pr * 2, pr * 2), pr * 2)
            pygame.draw.circle(hale, (80, 240, 140, 70), (pr * 2, pr * 2), pr)
            self.screen.blit(hale, (px - pr * 2, py - pr * 2))
            # besin sayisini nokta yogunlugu olarak goster
            n = min(40, int(adet))
            rnd = __import__("random").Random(int(wx) * 7919 + int(wy))
            for _ in range(n):
                ax = px + rnd.gauss(0, pr * 0.6)
                ay = py + rnd.gauss(0, pr * 0.6)
                pygame.draw.circle(self.screen, (90, 235, 130),
                                   (int(ax), int(ay)), 1)
            self.screen.blit(self.font_tiny.render(str(int(adet)), True,
                                                   (150, 245, 190)),
                             (px + pr + 3, py - 7))

        # ISIKLAR. Erim halkasi isigin BITTIGI yeri gosterir (siddet
        # ISIK_KESIM'e duser); ic dolgu ussel profili kabaca izler.
        from systems import isik as _isik
        for _k in self.harita_isiklar:
            wx, wy = float(_k[0]), float(_k[1])
            guc = float(_k[2]) if len(_k) > 2 else 1.0
            erim = float(_k[3]) if len(_k) > 3 else self._isik_erim()
            px = int(r.x + wx * k); py = int(r.y + wy * k)
            pr = max(4, int(erim * k))
            hale = pygame.Surface((pr * 2 + 2, pr * 2 + 2), pygame.SRCALPHA)
            _lam = _isik.lambda_px(erim)
            # Basamak sayisi PIKSEL yaricapina baglanir: kucuk halede az,
            # buyuk halede cok - sabit 10 basamakta halkalar sayiliyordu.
            _adim = max(12, min(64, pr))
            for i in range(_adim, 0, -1):
                _d = erim * i / float(_adim)
                _s = guc * math.exp(-_d / _lam)
                pygame.draw.circle(hale, (255, 232, 150, max(1, int(120 * _s))),
                                   (pr + 1, pr + 1), max(1, int(_d * k)))
            self.screen.blit(hale, (px - pr - 1, py - pr - 1))
            pygame.draw.circle(self.screen, (255, 210, 90), (px, py), pr, 1)
            pygame.draw.circle(self.screen, (255, 240, 190), (px, py), 4)
            self.screen.blit(self.font_tiny.render("%.2f" % guc, True,
                                                   (255, 226, 140)),
                             (px + 7, py - 7))

        # BASLANGIC NOKTALARI: kuruculari nereye birakiyoruz.
        for i, _b in enumerate(self.harita_baslangic):
            px = int(r.x + float(_b[0]) * k); py = int(r.y + float(_b[1]) * k)
            pygame.draw.circle(self.screen, (90, 220, 255), (px, py), 7, 2)
            pygame.draw.line(self.screen, (90, 220, 255), (px - 10, py), (px + 10, py))
            pygame.draw.line(self.screen, (90, 220, 255), (px, py - 10), (px, py + 10))
            self.screen.blit(self.font_tiny.render(str(i + 1), True, (150, 235, 255)),
                             (px + 9, py - 16))

        # firca onizlemesi
        if r.collidepoint(fare):
            if self.harita_kip == "isik":
                pr = max(4, int(self._isik_erim() * k))
                onizleme = (255, 210, 90)
            elif self.harita_kip == "baslangic":
                pr = 8
                onizleme = (90, 220, 255)
            else:
                pr = max(3, int(self.harita_yaricap * k))
                onizleme = ACCENT_COLOR
            pygame.draw.circle(self.screen,
                               DANGER if self.harita_siliyor else onizleme,
                               fare, pr, 1)
        self.screen.set_clip(None)

        _aciklama = {
            "besin": ("Cizilen duzen KALICI: sonradan dogan besin de yalnizca bu "
                      "yamalarda olusur. Bos birakilirsa besin rastgele dogar."),
            "isik": ("Isik suda USSEL zayiflar; erim, siddetin %%%d'e dustugu "
                     "uzakliktir. Erim %d px (yukseklik/2) olan bir isik en uste "
                     "konursa haritanin ortasinda biter. Isikli bolgede besin %.1f kat."
                     % (int(getattr(game_settings, 'ISIK_KESIM', 0.02) * 100),
                        int(DH * 0.5),
                        float(getattr(game_settings, 'ISIK_BESIN_CARPANI', 2.0)))),
            "baslangic": ("Kurucular bu noktalarda SIRAYLA dogar. Bos birakilirsa "
                          "rastgele bir besin yamasinin cevresine birakilirlar."),
        }[self.harita_kip]
        # Aciklama tek satira sigmiyorsa BOLUNUR; onceden sagdan kesiliyordu.
        _tam = "Dunya %dx%d px - %s" % (DW, DH, _aciklama)
        _en = self.screen_width - sx - 20
        _satir, _kelime = [], ""
        for _k in _tam.split(" "):
            _deneme = (_kelime + " " + _k).strip()
            if self.font_tiny.size(_deneme)[0] > _en and _kelime:
                _satir.append(_kelime); _kelime = _k
            else:
                _kelime = _deneme
        if _kelime:
            _satir.append(_kelime)
        for _i, _st in enumerate(_satir[:3]):
            self.screen.blit(self.font_tiny.render(_st, True, GRAY),
                             (sx, r.y + r.h + 12 + _i * 15))

    def handle_harita_events(self, event, m_pos):
        r, k, DW, DH = self._harita_tuval()
        if event.type == pygame.MOUSEBUTTONDOWN:
            for rect, _etiket, eylem in self.harita_dugmeleri():
                if rect.collidepoint(m_pos):
                    if eylem == "adet-":
                        self.harita_adet = max(1, self.harita_adet - 5)
                    elif eylem == "adet+":
                        self.harita_adet = min(200, self.harita_adet + 5)
                    elif eylem == "yari-":
                        self.harita_yaricap = max(10.0, self.harita_yaricap - 10)
                    elif eylem == "yari+":
                        self.harita_yaricap = min(400.0, self.harita_yaricap + 10)
                    elif eylem == "silgi":
                        self.harita_siliyor = not self.harita_siliyor
                    elif eylem.startswith("kip:"):
                        self.harita_kip = eylem[4:]
                    elif eylem == "guc-":
                        self.isik_guc = max(0.1, round(self.isik_guc - 0.1, 2))
                    elif eylem == "guc+":
                        self.isik_guc = min(3.0, round(self.isik_guc + 0.1, 2))
                    elif eylem == "erim-":
                        self.isik_erim = max(50.0, self._isik_erim() - 50.0)
                    elif eylem == "erim+":
                        self.isik_erim = min(4000.0, self._isik_erim() + 50.0)
                    elif eylem == "temizle":
                        # Yalnizca ACIK KATMAN temizlenir; besin cizerken
                        # isiklarin da silinmesi kullaniciyi sasirtirdi.
                        if self.harita_kip == "besin":
                            self.harita_yamalar = []
                        elif self.harita_kip == "isik":
                            self.harita_isiklar = []
                        else:
                            self.harita_baslangic = []
                    elif eylem == "rastgele":
                        self._harita_rastgele()
                    self.harita_kaydet()
                    return True
            if r.collidepoint(m_pos):
                self.harita_suruklu = True
                self._harita_bas(m_pos, event.button)
                # Her tikta kaydedilir. Once yalnizca fare BIRAKILDIGINDA
                # kaydediliyordu; tek tikla konan bir yama, pencere baska
                # bir yoldan kapanirsa kayboluyordu.
                self.harita_kaydet()
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.harita_suruklu:
                self.harita_suruklu = False
                self.harita_kaydet()
        elif event.type == pygame.MOUSEMOTION and self.harita_suruklu:
            if r.collidepoint(m_pos):
                dugmeler = pygame.mouse.get_pressed()
                self._harita_bas(m_pos, 3 if dugmeler[2] else 1, surukleme=True)
            return True
        return False

    def _harita_bas(self, m_pos, dugme, surukleme=False):
        wx, wy = self._harita_dunyaya(m_pos)
        sil = (dugme == 3) or self.harita_siliyor

        if self.harita_kip == "isik":
            if sil:
                for i, _k in enumerate(self.harita_isiklar):
                    _e = float(_k[3]) if len(_k) > 3 else self._isik_erim()
                    if (float(_k[0]) - wx) ** 2 + (float(_k[1]) - wy) ** 2 <= _e * _e:
                        del self.harita_isiklar[i]
                        return
                return
            if surukleme:
                return          # isik surukleyerek YIGILMAZ: tek tek konur
            self.harita_isiklar.append([round(wx, 1), round(wy, 1),
                                        round(float(self.isik_guc), 2),
                                        round(float(self._isik_erim()), 1)])
            return

        if self.harita_kip == "baslangic":
            if sil:
                for i, _b in enumerate(self.harita_baslangic):
                    if (float(_b[0]) - wx) ** 2 + (float(_b[1]) - wy) ** 2 <= 40 ** 2:
                        del self.harita_baslangic[i]
                        return
                return
            if surukleme:
                return
            self.harita_baslangic.append([round(wx, 1), round(wy, 1)])
            return

        if sil:
            # En yakin yamayi kaldir (fircanin icindeyse)
            for i, (x, y, _a, yari) in enumerate(self.harita_yamalar):
                if (x - wx) ** 2 + (y - wy) ** 2 <= (yari + 10) ** 2:
                    del self.harita_yamalar[i]
                    return
            return
        # Suruklerken ust uste yigilmasin: fircanin yarisi kadar mesafe sart
        if surukleme:
            for x, y, _a, _r in self.harita_yamalar:
                if (x - wx) ** 2 + (y - wy) ** 2 < (self.harita_yaricap) ** 2:
                    return
        self.harita_yamalar.append([round(wx, 1), round(wy, 1),
                                    int(self.harita_adet),
                                    float(self.harita_yaricap)])

    def _harita_rastgele(self):
        """FOOD_MAX kadar besini rastgele yamalara dagit (eski davranis)."""
        import random as _r
        from entities.entity import WIDTH as DW, HEIGHT as DH
        self.harita_yamalar = []
        kalan = int(game_settings.FOOD_MAX)
        adet = max(1, int(game_settings.FOOD_PATCH_SIZE))
        while kalan > 0:
            n = min(adet, kalan)
            self.harita_yamalar.append([
                round(_r.uniform(80, DW - 80), 1),
                round(_r.uniform(80, DH - 80), 1),
                n, float(game_settings.FOOD_PATCH_SIGMA)])
            kalan -= n

    def harita_kaydet(self):
        """Yamalari settings.json'a yaz.

        Toplam besin sayisi FOOD_MAX'i asarsa tavan da yukseltilir; aksi
        halde kullanicinin koydugu besinin bir kismi hic olusmaz ve
        "koydum ama gorunmuyor" durumu ortaya cikar.
        """
        game_settings.HARITA_YAMALARI = [list(y) for y in self.harita_yamalar]
        game_settings.HARITA_ISIKLARI = [list(k) for k in self.harita_isiklar]
        game_settings.HARITA_BASLANGIC = [list(b) for b in self.harita_baslangic]
        toplam = sum(int(y[2]) for y in self.harita_yamalar)
        if toplam > int(game_settings.FOOD_MAX):
            game_settings.FOOD_MAX = toplam
        if toplam:
            game_settings.FOOD_COUNT = toplam
        game_settings.save_all()

    def draw_dashboard(self):
        rect = pygame.Rect(self.sidebar_width + 100, self.screen_height//2 - 40, 400, 80)
        color = SUCCESS if rect.collidepoint(pygame.mouse.get_pos()) else ACCENT_COLOR
        pygame.draw.rect(self.screen, color, rect, 2)
        txt = self.font_title.render("START WORLD", True, color)
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_scrollbar(self):
        if self.max_scroll >= 0: return
        tx, ty, th = self.screen_width - 25, 100, self.screen_height - 120
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, (tx, ty, 12, th))
        thumb_h = max(30, th * ((self.screen_height - 120) / self.total_content_height))
        thumb_y = ty + (th - thumb_h) * (self.scroll_y / self.max_scroll)
        pygame.draw.rect(self.screen, GRAY, (int(tx + 2), int(thumb_y), 8, int(thumb_h)))

    def draw_settings(self):
        sw, sx = self.screen_width, self.sidebar_width
        cy = 100 + self.scroll_y
        idx = 0
        mouse = pygame.mouse.get_pos()

        for cat, rows in self._visible_settings():
            if cy + self.CAT_H > 80:
                pygame.draw.line(self.screen, HIGHLIGHT,
                                 (sx + 40, int(cy + 26)), (sw - 40, int(cy + 26)), 1)
                self.screen.blit(self.font_main.render(cat, True, ACCENT_COLOR),
                                 (sx + 40, int(cy)))
            cy += self.CAT_H

            for attr, desc in rows:
                if idx >= len(self.ui_elements):
                    break
                box = self.ui_elements[idx]
                rrect, _ = self.reset_buttons[idx]
                idx += 1

                if 60 < cy + self.ROW_H < self.screen_height + 60:
                    row = pygame.Rect(sx + 30, int(cy), sw - sx - 70, self.ROW_H - 6)
                    hovered = row.collidepoint(mouse)
                    if hovered:
                        pygame.draw.rect(self.screen, (40, 50, 70), row)

                    cur = getattr(game_settings, attr, None)
                    default = game_settings.get_default(attr)
                    changed = default is not None and cur != default

                    # Degistirilmis ayarlar solda sari cizgiyle isaretlenir
                    if changed:
                        pygame.draw.rect(self.screen, WARNING, (sx + 30, int(cy), 3, self.ROW_H - 6))

                    name_col = WARNING if changed else TEXT_COLOR
                    self.screen.blit(self.font_small.render(attr, True, name_col),
                                     (sx + 48, int(cy + 5)))
                    self.screen.blit(self.font_tiny.render(desc, True, GRAY),
                                     (sx + 48, int(cy + 26)))

                    # Varsayilan degeri, yalnizca degistirilmisse goster
                    if changed:
                        dtxt = f"varsayılan: {default}"
                        surf = self.font_tiny.render(dtxt, True, GRAY)
                        self.screen.blit(surf, (sw - 200 - surf.get_width() - 12, int(cy + 12)))

                    # Sifirla dugmesi (yalnizca degistirilmisse aktif)
                    rr = rrect.move(0, int(self.scroll_y))
                    if changed:
                        rcol = ACCENT_COLOR if rr.collidepoint(mouse) else GRAY
                        pygame.draw.rect(self.screen, rcol, rr, 1)
                        # Geri-al ikonu cizilir: varsayilan fontta ok glifi yok
                        cxp, cyp, rad = rr.centerx, rr.centery, 7
                        pygame.draw.arc(self.screen, rcol,
                                        (cxp - rad, cyp - rad, rad * 2, rad * 2),
                                        -0.6, 4.2, 2)
                        pygame.draw.polygon(self.screen, rcol,
                                            [(cxp + rad - 1, cyp - 5),
                                             (cxp + rad + 3, cyp + 1),
                                             (cxp + rad - 5, cyp + 1)])

                box.update_text()
                box.draw(self.screen, self.scroll_y, self.screen_height)
                cy += self.ROW_H
            cy += 14

        # --- ust bar: baslik + arama + degistirilmis sayisi ---
        pygame.draw.rect(self.screen, BG_COLOR, (sx, 0, sw, 92))
        self.screen.blit(self.font_main.render("WORLD & EVOLUTION PARAMETERS", True, WHITE),
                         (sx + 40, 22))

        total = sum(len(v) for v in self.settings_categories.values())
        shown = sum(len(v) for _, v in self._visible_settings())
        changed_n = sum(1 for v in self.settings_categories.values() for a, _ in v
                        if game_settings.get_default(a) is not None
                        and getattr(game_settings, a, None) != game_settings.get_default(a))
        info = f"{shown}/{total} ayar   ·   {changed_n} tanesi varsayılandan farklı"
        self.screen.blit(self.font_tiny.render(info, True, GRAY), (sx + 40, 58))

        self.search_rect = pygame.Rect(sw - 340, 24, 300, 32)
        pygame.draw.rect(self.screen, ACCENT_COLOR if self.search_active else HIGHLIGHT,
                         self.search_rect, 1)
        placeholder = self.search if self.search else "ara: isim veya açıklama…"
        col = TEXT_COLOR if self.search else GRAY
        self.screen.blit(self.font_small.render(placeholder, True, col),
                         (self.search_rect.x + 8, self.search_rect.y + 7))

        if shown == 0:
            self.screen.blit(self.font_main.render("eşleşen ayar yok", True, GRAY),
                             (sx + 60, 160))
        self.draw_scrollbar()

    def draw_organ_highlights(self, center_x, center_y):
        """Seçili ve hover organları vurgular. Membran üzerinde tüm organların pozisyonlarını gösterir."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return

        scaled_radius = entity.radius * self.preview_scale

        # Önce membran çemberini çiz (organ editör modundayken)
        if self.organ_editor_mode:
            # Dış çember (membran)
            pygame.draw.circle(self.screen, HIGHLIGHT, (int(center_x), int(center_y)),
                             int(scaled_radius + 15), 1)

            # Açı göstergeleri (her 45 derecede)
            for angle_deg in range(0, 360, 45):
                angle_rad = math.radians(angle_deg)
                inner_x = center_x + math.cos(angle_rad) * (scaled_radius + 5)
                inner_y = center_y + math.sin(angle_rad) * (scaled_radius + 5)
                outer_x = center_x + math.cos(angle_rad) * (scaled_radius + 15)
                outer_y = center_y + math.sin(angle_rad) * (scaled_radius + 15)
                pygame.draw.line(self.screen, GRAY, (int(inner_x), int(inner_y)),
                               (int(outer_x), int(outer_y)), 1)

        for i, organ in enumerate(entity.organs):
            organ_name = organ.__class__.__name__
            if ORGAN_TYPES.get(organ_name, {}).get("internal", True):
                continue

            # Organın pozisyonu
            angle = organ.attachment_angle
            pos_x = center_x + math.cos(angle) * scaled_radius
            pos_y = center_y + math.sin(angle) * scaled_radius

            organ_color = ORGAN_TYPES.get(organ_name, {}).get("color", WHITE)

            # Editor modunda tüm organların pozisyonlarını göster
            if self.organ_editor_mode:
                # ATIS YAYI (yalnizca silahlar): organin nereye ates
                # EDEBILECEGI. Ayak izinden ayri: nematosistin dar 30
                # derecelik yayi ile toksinin 180 derecelik yonsuz salimi
                # burada gorunur. Hucre ava onden gider; yana takili dar
                # bir silah hedefe nadiren bakar (olculdu: onde 67 atis,
                # yanda 46, arkada 35). Yay can_hit'in acisinin kendisi.
                _lg = getattr(organ, 'logic', None)
                if organ_name in WEAPON_CLASSES and _lg is not None and hasattr(_lg, 'arc'):
                    try:
                        _yay = math.radians(float(_lg.arc))
                    except Exception:
                        _yay = 0.0
                    if 0.0 < _yay < math.pi:
                        _r_yay = scaled_radius + 22
                        _yay_rect = pygame.Rect(int(center_x - _r_yay), int(center_y - _r_yay),
                                                int(_r_yay * 2), int(_r_yay * 2))
                        _yay_renk = tuple(min(255, c // 2 + 40) for c in organ_color)
                        pygame.draw.arc(self.screen, _yay_renk, _yay_rect,
                                        -(angle + _yay), -(angle - _yay), 1)
                        for _kenar in (angle - _yay, angle + _yay):
                            pygame.draw.line(self.screen, _yay_renk,
                                             (int(pos_x), int(pos_y)),
                                             (int(center_x + math.cos(_kenar) * _r_yay),
                                              int(center_y + math.sin(_kenar) * _r_yay)), 1)
                # Açısal genişlik yayı
                width_deg = self.get_organ_angular_width(organ)
                width_rad = math.radians(width_deg)

                # Her organın kapladığı alanı göster (yarı saydam)
                if i != self.selected_organ_index:
                    # Yay çiz
                    arc_rect = pygame.Rect(
                        int(center_x - scaled_radius - 8),
                        int(center_y - scaled_radius - 8),
                        int((scaled_radius + 8) * 2),
                        int((scaled_radius + 8) * 2)
                    )
                    arc_color = tuple(c // 2 for c in organ_color)  # Daha koyu
                    pygame.draw.arc(self.screen, arc_color, arc_rect,
                                  -(angle + width_rad/2), -(angle - width_rad/2), 2)

            # Seçili organ için
            if i == self.selected_organ_index:
                # Parlak daire
                pygame.draw.circle(self.screen, SUCCESS, (int(pos_x), int(pos_y)), 14, 3)

                # Açısal genişlik göstergesi (parlak)
                width_deg = self.get_organ_angular_width(organ)
                width_rad = math.radians(width_deg)
                arc_rect = pygame.Rect(
                    int(center_x - scaled_radius - 10),
                    int(center_y - scaled_radius - 10),
                    int((scaled_radius + 10) * 2),
                    int((scaled_radius + 10) * 2)
                )
                pygame.draw.arc(self.screen, SUCCESS, arc_rect,
                              -(angle + width_rad/2), -(angle - width_rad/2), 4)

            # Hover organ için
            elif i == self.hover_organ_index:
                pygame.draw.circle(self.screen, ACCENT_COLOR, (int(pos_x), int(pos_y)), 12, 2)

    def _sigdir(self, metin, genislik):
        """Etiketi verilen piksel genisligine kirp - kutunun altina girmesin."""
        if self.font_small.size(metin)[0] <= genislik:
            return metin
        while metin and self.font_small.size(metin + "..")[0] > genislik:
            metin = metin[:-1]
        return metin + ".."

    def teslimat_ozeti(self, organ):
        """Silahin secili tasiyici+yuk ikilisinin olculmus teslimat notu.

        Bunu bir "parametre" olarak listeye koymak yanlisti: parametre
        satirlari duzenlenebilir kutu ve (min-max) cizer, oysa bu SONUC.
        Ayri bir bilgi satiri olarak ciziliyor.
        """
        if organ is None or organ.__class__.__name__ not in WEAPON_CLASSES:
            return []
        lg = getattr(organ, "logic", None)
        if lg is None or not hasattr(lg, "carrier"):
            return []
        import lab as _lab
        out = []
        # TASIYICININ MEKANIZMASI. Molekuler tasiyicilar (0-2) uc AYRI
        # sistemdir ve laboratuvarda ayri ayri ifade edilmistir: difuzyon
        # yon vermeden cevreye sizdirir, yonlu bosaltma bir bolgeden
        # birakir (fiskirtmaz), fiskirtma molekulleri hizla ileri atar.
        # Editorde yalnizca adlari goruunuyordu; hangisinin ne yaptigi
        # ancak oyunda deneyerek anlasiliyordu. Fark bir katsayi degil
        # SACILMA ACISI ve BASLANGIC HIZIDIR - ikisi de burada yazili.
        ci = int(getattr(lg, 'carrier', 0))
        if 0 <= ci < len(_lab.CARRIERS):
            aciklama = _lab.CARRIERS[ci][2]
            if ci < 3:
                out.append("* %s" % aciklama)
                out.append("  sacilma +-%.0f der, erim %.0f px"
                           % (_lab.CARRIER_SPREAD[ci], _lab.CARRIER_REACH[ci]))
            else:
                out.append("* %s" % aciklama)
        # IGNELI SILAH: yuku hucredeki URETICIDEN alir. Uretici yoksa
        # igne bosa gider - bunu editorde gormek gerekiyor.
        if not getattr(lg, 'URETICI', False) and ci >= 3:
            _ent = getattr(self, 'popup_entity', None) or getattr(self, 'selected_entity', None)
            _ureticiler = [o for o in (getattr(_ent, 'organs', None) or ())
                           if getattr(getattr(o, 'logic', None), 'URETICI', False)]
            if _ureticiler:
                _adlar = ", ".join(_lab.PAYLOADS[int(o.logic.payload)][0]
                                   for o in _ureticiler)
                out.append("  yuk: ureticiden (%s)" % _adlar)
                _pi_ozet = int(_ureticiler[0].logic.payload)
            else:
                out.append("  URETICI YOK - igne yuksuz gider (Toksin/Lizin ekle)")
                _pi_ozet = 0
            metin = _lab.kombinasyon_ozeti(lg.carrier, _pi_ozet)
        else:
            metin = _lab.kombinasyon_ozeti(lg.carrier, lg.payload)
        # Panel dar: bolmeden sigmayacak satirlari ikiye ayir.
        if len(metin) > 34 and " / " in metin:
            sol, sag = metin.split(" / ", 1)
            out += ["-> " + sol, "   / " + sag]
        else:
            out.append("-> " + metin)
        return out

    def get_organ_editable_params(self, organ):
        """Organın düzenlenebilir parametrelerini döndürür."""
        organ_name = organ.__class__.__name__
        params = {}

        if organ_name == "Photoreceptor":
            params["range"] = ("Range", organ.logic.range, 5, 100)
            params["angle"] = ("Angle", math.degrees(organ.logic.angle), 1, 180)
        elif organ_name == "Mechanoreceptor":
            # sensitivity = size * 30, kullanıcıya sensitivity göster
            params["sensitivity"] = ("Sensitivity", organ.logic.sensitivity, 3, 150)
        elif organ_name == "Chemoreceptor":
            params["length"] = ("Length", organ.logic.length, 1, 20)
        elif organ_name == "Flagella":
            params["length"] = ("Length", organ.logic.length, 1, 50)
        elif organ_name == "Cilia":
            params["length"] = ("Length", organ.logic.length, 1, 20)
        elif organ_name in WEAPON_CLASSES:
            # Silahlarda gelisim carpani: hasar/menzil bununla olceklenir
            params["power"] = ("Power", organ.logic.power, 0.2, 10.0)
            # Silah = TASIYICI + YUK + BELIRTEC. Bunlar laboratuvarda
            # ayri ayri secilebiliyordu ama oyunda sabit bir eslemeye
            # mahkumdu; artik editorden secilebiliyor ve teslimat orani
            # SECILEN kombinasyondan hesaplaniyor.
            import lab as _lab
            ci, pi, mi = (organ.logic.carrier, organ.logic.payload,
                          organ.logic.marker)
            # Tasiyici adlari "3. Fiskirtma" gibi sirali yazilidir; sira
            # zaten kutudaki sayidir, etikette tekrarina gerek yok.
            _ta = _lab.CARRIERS[ci][0].split('. ', 1)[-1]
            params["carrier"] = ("Tasiyici: " + _ta, ci, 0, len(_lab.CARRIERS) - 1)
            # YUK YALNIZCA URETICININ GENIDIR. Igneli silah (stilet,
            # harpun, nematosist) yuk sentezlemez; atarken hucredeki
            # ureticiden (Toksin/Lizin) ceker. Editor igneye de bir yuk
            # kutusu gosteriyordu ve secim hicbir seye baglanmiyordu -
            # kullanici nematosiste yuk secip oyunda hic etki gormuyordu.
            if getattr(organ.logic, 'URETICI', False):
                params["payload"] = ("Yuk: " + _lab.PAYLOADS[pi][0],
                                     pi, 0, len(_lab.PAYLOADS) - 1)
            params["marker"] = ("Belirtec: " + _lab.MARKERS[mi][0],
                                mi, 0, len(_lab.MARKERS) - 1)
        elif organ_name == "Membrane":
            # Zar savunmalari ORGAN degil NITELIKTIR (karar 3): kapsul tum
            # hucreyi sarar, konumu yoktur. Bu yuzden organ editorunde
            # Membrane secilince buradan duzenlenirler.
            lg = organ.logic
            params["integrity"] = ("Max Integrity", lg.max_integrity, 20, 2000)
            # Katman KALINLIKLARI artik katmanin kendi panelinde (HUCRE
            # YAPISI > KATMANLAR). Burada yalnizca plazma zarina ait olan
            # ve katman olmayan mekanizmalar kaliyor - biri eklenip
            # cikarilamaz, otekiler zarin ayarlari.
            params["outer"] = ("Hucre zari (kimya)", lg.outer, 0, 30)
            params["efflux"] = ("Efflux (toksin at)", lg.efflux, 0, 30)
            params["slip"] = ("Kayganlik (tutma)", lg.slip, 0, 30)
            params["repair"] = ("Onarim", lg.repair, 0, 30)

        return params

    def update_katman_param(self, param, deger):
        """Katman degerini yaz: `kalinlik:<alan>` ya da yatirim alani."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        zar = getattr(getattr(entity, 'membrane', None), 'logic', None)
        if zar is None:
            return
        try:
            v = float(deger)
        except (TypeError, ValueError):
            return
        if param.startswith("kalinlik:"):
            zar.katman_kalinligi_ayarla(param.split(":", 1)[1], v)
        else:
            setattr(zar, param, max(0.0, min(30.0, v)))
        entity.recalculate_physics()
        self.save_entity_organ_config(entity)

    def update_organ_param(self, param_name, new_value):
        """Seçili organın parametresini günceller."""
        if not self.selected_organ:
            return

        organ_name = self.selected_organ.__class__.__name__
        if organ_name in WEAPON_CLASSES and param_name in ('carrier', 'payload',
                                                           'marker'):
            import lab as _lab
            ust = {'carrier': len(_lab.CARRIERS), 'payload': len(_lab.PAYLOADS),
                   'marker': len(_lab.MARKERS)}[param_name]
            try:
                setattr(self.selected_organ.logic, param_name,
                        max(0, min(ust - 1, int(round(float(new_value))))))
            except (TypeError, ValueError, OverflowError):
                return
            entity = self.popup_entity if self.entity_popup_open else self.selected_entity
            self.save_entity_organ_config(entity)
            return

        try:
            if organ_name == "Photoreceptor":
                if param_name == "range":
                    self.selected_organ.logic.range = float(new_value)
                elif param_name == "angle":
                    self.selected_organ.logic.angle = math.radians(float(new_value))
            elif organ_name == "Mechanoreceptor":
                if param_name == "sensitivity":
                    # sensitivity = size * 30, yani size = sensitivity / 30
                    self.selected_organ.logic.size = float(new_value) / 30.0
            elif organ_name == "Chemoreceptor":
                if param_name == "length":
                    self.selected_organ.logic.length = float(new_value)
            elif organ_name == "Flagella":
                if param_name == "length":
                    self.selected_organ.logic.length = float(new_value)
                    self.selected_organ.logic.recalculate_boosts()
            elif organ_name == "Cilia":
                if param_name == "length":
                    self.selected_organ.logic.length = float(new_value)
                    self.selected_organ.logic.recalculate_boosts()
            elif organ_name in WEAPON_CLASSES:
                if param_name == "power":
                    self.selected_organ.logic.power = float(new_value)
            elif organ_name == "Membrane":
                lg = self.selected_organ.logic
                v = float(new_value)
                if param_name == "integrity":
                    lg.max_integrity = v
                    lg.integrity = v
                elif param_name in ("wall", "outer", "capsule", "efflux",
                                    "repair", "slip", "mucus", "slayer"):
                    setattr(lg, param_name, v)

            # Fiziği yeniden hesapla
            entity = self.popup_entity if self.entity_popup_open else self.selected_entity
            if entity:
                entity.recalculate_physics()
        except:
            return
        self.save_entity_organ_config(entity)

    def draw_entity_popup(self):
        """Varlık düzenleme için tam ekran popup çizer."""
        if not self.entity_popup_open or not self.popup_entity:
            return

        # Yarı saydam arka plan
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Popup ana panel (ekranın büyük kısmını kaplar)
        margin = 30
        popup_rect = pygame.Rect(margin, margin,
                                  self.screen_width - margin * 2,
                                  self.screen_height - margin * 2)
        pygame.draw.rect(self.screen, CARD_COLOR, popup_rect)
        pygame.draw.rect(self.screen, ACCENT_COLOR, popup_rect, 2)

        # Başlık
        entity_name = "Notropi" if isinstance(self.popup_entity, Notropi) else f"Optropi #{self.popup_entity.index + 1}"
        title = f"EDITING: {entity_name}"
        self.screen.blit(self.font_title.render(title, True, ACCENT_COLOR),
                        (popup_rect.x + 20, popup_rect.y + 15))

        # Kapatma butonu (sağ üst)
        close_size = 40
        self.popup_close_btn = pygame.Rect(popup_rect.right - close_size - 10,
                                            popup_rect.y + 10,
                                            close_size, close_size)
        close_hover = self.popup_close_btn.collidepoint(pygame.mouse.get_pos())
        close_color = DANGER if close_hover else GRAY
        pygame.draw.rect(self.screen, close_color, self.popup_close_btn)
        pygame.draw.rect(self.screen, WHITE, self.popup_close_btn, 1)
        # X işareti
        cx, cy = self.popup_close_btn.center
        pygame.draw.line(self.screen, WHITE, (cx - 10, cy - 10), (cx + 10, cy + 10), 3)
        pygame.draw.line(self.screen, WHITE, (cx - 10, cy + 10), (cx + 10, cy - 10), 3)

        # İçerik alanı
        content_y = popup_rect.y + 70
        content_height = popup_rect.height - 90

        # === UC SUTUN ===
        #
        # Eski duzen: sol sutunda onizleme (350) + organ editoru (280),
        # ortada dar bir istatistik kutusu, sagda genler. Editor o 280 px'e
        # sigmiyordu - hem parametreleri hem 16 dugmelik paleti tasiyordu ve
        # popup'in altindan tasiyordu. Ustelik sag sutunun yarisi bostu.
        #
        # Yeni duzen bos alani kullanir:
        #   A) onizleme + ORGAN EKLE paleti     (genis, dugmeler icin)
        #   B) ORGAN EDITOR - tam boy tek sutun (uzun parametre listesi icin)
        #   C) istatistikler + baslangic genleri
        left_section_x = popup_rect.x + 20
        left_section_width = 430

        # Preview Panel
        # KATMANLAR grubu palete bes grup yapti; SILAH satiri panelin
        # altindan tasiyordu. Onizlemeden 40 px alindi.
        preview_height = 300
        preview_rect = pygame.Rect(left_section_x, content_y, left_section_width, preview_height)
        self.popup_preview_rect = preview_rect      # olaylar bunu kullanir
        border_color = SUCCESS if self.organ_editor_mode else HIGHLIGHT
        pygame.draw.rect(self.screen, (20, 25, 35), preview_rect)
        pygame.draw.rect(self.screen, border_color, preview_rect, 2 if self.organ_editor_mode else 1)

        # Preview başlık
        preview_title = "ORGANISM PREVIEW" + (" [EDIT MODE]" if self.organ_editor_mode else "")
        self.screen.blit(self.font_small.render(preview_title, True, SUCCESS if self.organ_editor_mode else ACCENT_COLOR),
                         (preview_rect.x + 10, preview_rect.y + 8))

        # Preview merkezi
        self.preview_center_x = preview_rect.x + preview_rect.width // 2
        self.preview_center_y = preview_rect.y + preview_rect.height // 2 + 15
        # Katman halkalari bu yariCapa sigdirilir
        self._onizleme_yarikenar = min(preview_rect.width,
                                       preview_rect.height - 30) // 2 - 6

        # OLCEK sabit 4.0x idi ve ayarlanabilir degildi: kucuk sitoplazmali
        # bir hucre 430x340'lik panelin ortasinda bezelye buyuklugunde
        # kaliyor, katmanlari da onunla birlikte kuculuyordu. Panele
        # SIGDIR - hucre neyse o kadar buyur.
        # OLCEK YALNIZCA CEKIRDEGE gore alinir. Zarfi da hesaba katinca
        # her eklenen katman olcegi kucultuyor, sitoplazma ekranda
        # kuculuyordu - kullanicinin gordugu "katman ekledikce zar iceri
        # itiliyor" etkisi buydu. Cekirdek sabit kalir, zarf disariya
        # dogru buyur; asiri kalin zarf panelin kenarinda kirpilir.
        # OLCEK SITOPLAZMAYA gore alinir, dis yaricapa gore DEGIL.
        #
        # Dis yaricap zarfla birlikte buyuyor; ona sigdirinca her eklenen
        # katman olcegi kucultuyor ve sitoplazma ekranda yeniden
        # kuculuyordu - duzeltmeye calistigimiz sorunun ta kendisi.
        # Cekirdek sabit kalir, zarf disari dogru buyur; asiri kalin zarf
        # panelin kenarinda kirpilir.
        # Cekirdek DOGRUDAN sitoplazmadan alinir: `radius / zarf_orani`
        # ile turetmek bayat deger uretiyordu (radius bir onceki katman
        # yapilandirmasindan, oran yenisinden geliyordu; olcek her
        # degisiklikte ziplyordu).
        _govde = getattr(getattr(self.popup_entity, 'body', None), 'logic', None)
        _cek = max(1.0, getattr(_govde, 'radius', self.popup_entity.radius))
        self.preview_scale = max(1.0, min(12.0,
            (self._onizleme_yarikenar * 0.30) / _cek))

        # Varlığı çiz
        self.screen.set_clip(pygame.Rect(preview_rect.x + 2, preview_rect.y + 28,
                                          preview_rect.width - 4, preview_rect.height - 32))
        self.draw_entity_preview(self.popup_entity, self.preview_center_x, self.preview_center_y, self.preview_scale)
        if self.organ_editor_mode:
            self.draw_organ_highlights(self.preview_center_x, self.preview_center_y)
        self.screen.set_clip(None)

        # Scale bilgisi
        scale_text = f"Scale: {self.preview_scale:.1f}x"
        if self.organ_editor_mode:
            scale_text += " | Drag organs to reposition"
        self.screen.blit(self.font_small.render(scale_text, True, GRAY),
                         (preview_rect.x + 10, preview_rect.bottom - 22))

        # A-alt) ORGAN EKLE paleti - onizlemenin altinda, genis
        palette_y = preview_rect.bottom + 15
        palette_h = content_y + content_height - palette_y
        self.draw_organ_palette(left_section_x, palette_y,
                                left_section_width, palette_h)

        # B) ORGAN EDITOR - tam boy
        editor_x = left_section_x + left_section_width + 18
        editor_w = 300
        self.draw_popup_organ_editor(editor_x, content_y, editor_w, content_height)

        # === C) SAG SUTUN: istatistikler + genler ===
        middle_section_x = editor_x + editor_w + 18
        middle_section_width = popup_rect.right - middle_section_x - 20

        stats_rect = pygame.Rect(middle_section_x, content_y, middle_section_width, 245)
        pygame.draw.rect(self.screen, (25, 30, 40), stats_rect)
        pygame.draw.rect(self.screen, HIGHLIGHT, stats_rect, 1)

        self.screen.blit(self.font_main.render("STATISTICS", True, ACCENT_COLOR),
                        (stats_rect.x + 15, stats_rect.y + 10))

        self.popup_entity.recalculate_physics()
        stats = [
            ("Max Energy", f"{self.popup_entity.max_energy:.1f}"),
            ("Speed", f"{self.popup_entity.speed:.1f}"),
            ("Turn Rate", f"{self.popup_entity.max_turn_rate:.2f}"),
            ("Vision Range", f"{self.popup_entity.vision_range}"),
            ("Total Organs", f"{len(self.popup_entity.organs)}")
        ]

        sy = stats_rect.y + 45
        for k, v in stats:
            self.screen.blit(self.font_small.render(k, True, GRAY), (stats_rect.x + 20, sy))
            self.screen.blit(self.font_small.render(v, True, WHITE), (stats_rect.x + 150, sy))
            sy += 26

        # DOLULUK: besin ancak organlardan ARTAN yere sigarsa alinir
        # (Cytoplasm.can_fit_food). Organ yigmis kucuk bir hucre hicbir
        # besini alamaz ve bunun ekranda hicbir isareti yoktu - hucre
        # aclıktan olurken sebebi gorunmuyordu.
        govde = getattr(getattr(self.popup_entity, 'body', None), 'logic', None)
        if govde is not None:
            organ_alani = self.popup_entity.calculate_organ_area()
            kapasite = govde.total_area
            besin = getattr(govde, 'FOOD_AREA', 100.0)
            sigar = govde.can_fit_food(organ_alani)
            renk = SUCCESS if sigar else DANGER
            self.screen.blit(self.font_small.render("Doluluk", True, GRAY),
                             (stats_rect.x + 20, sy))
            self.screen.blit(self.font_small.render(
                "%.0f / %.0f" % (organ_alani, kapasite), True, renk),
                (stats_rect.x + 150, sy))
            sy += 22
            if not sigar:
                import math as _m
                gerek = _m.sqrt((organ_alani + besin) / _m.pi) / 10.0
                for sat in ("! BESIN ALAMAZ - organlar govdeye sigmiyor",
                            "  Sitoplazma size >= %.2f olmali" % gerek):
                    self.screen.blit(self.font_small.render(sat, True, WARNING),
                                     (stats_rect.x + 20, sy))
                    sy += 18

        # Genler ayni sutunda, istatistiklerin altinda
        right_section_x = middle_section_x
        right_section_width = middle_section_width

        genes_rect = pygame.Rect(right_section_x, stats_rect.bottom + 15,
                                 right_section_width,
                                 content_y + content_height - stats_rect.bottom - 15)
        pygame.draw.rect(self.screen, (25, 30, 40), genes_rect)
        pygame.draw.rect(self.screen, HIGHLIGHT, genes_rect, 1)

        self.screen.blit(self.font_main.render("STARTING GENES", True, SUCCESS),
                        (genes_rect.x + 15, genes_rect.y + 10))

        gy = genes_rect.y + 50
        for key, ibox in self.entity_ui_elements:
            if gy + 28 > genes_rect.bottom - 20:
                break
            # Label
            self.screen.blit(self.font_small.render(key.replace("_", " ").upper(), True, TEXT_COLOR),
                            (genes_rect.x + 15, gy + 3))
            # Input box
            ibox.rect.x = genes_rect.x + right_section_width - 100
            ibox.rect.y = gy
            ibox.rect.width = 80
            ibox.rect.height = 24
            ibox.update_text()
            ibox.draw(self.screen)
            gy += 30

        self.screen.blit(self.font_small.render("* Changes auto-save", True, GRAY),
                        (genes_rect.x + 15, genes_rect.bottom - 25))

    def _param_gruplari(self, organ, params):
        """Parametreleri SINIFLARINA ayir: [(baslik|None, [anahtar...])].

        Zarin dokuz ayari tek yigin halinde okunmuyordu; hangisinin
        katman, hangisinin mekanizma oldugu belli degildi.
        """
        ad = organ.__class__.__name__
        plan = PARAM_GRUPLARI.get("_silah" if ad in WEAPON_CLASSES else ad)
        if not plan:
            return [(None, list(params))]
        cikti, kullanilan = [], set()
        for baslik, anahtarlar in plan:
            var = [a for a in anahtarlar if a in params]
            if var:
                cikti.append((baslik, var))
                kullanilan.update(var)
        kalan = [a for a in params if a not in kullanilan]
        if kalan:
            cikti.append((None, kalan))
        return cikti

    def draw_popup_organ_editor(self, x, y, width, height):
        """Organ editoru: ustte HUCRE YAPISI listesi, secilince AYARLARI.

        Once yalnizca "onizlemede bir organa tikla" ile organ secilebiliyordu -
        ama `get_organ_at_position` IC organlari atliyor. Yani zar, sitoplazma,
        koful, iskelet ve ribozom hicbir sekilde secilemiyordu; zarin altindaki
        KATMAN ayarlarina ulasmanin bir yolu yoktu. Artik hucrenin butun
        organlari sinif sinif listeleniyor ve listeden seciliyor.
        """
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (25, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, ACCENT_COLOR if self.organ_editor_mode else HIGHLIGHT,
                         panel_rect, 2)

        title_color = SUCCESS if self.organ_editor_mode else ACCENT_COLOR
        self.screen.blit(self.font_main.render("ORGAN EDITOR", True, title_color),
                         (x + 15, y + 10))

        toggle_rect = pygame.Rect(x + width - 90, y + 10, 75, 28)
        pygame.draw.rect(self.screen, SUCCESS if self.organ_editor_mode else GRAY,
                         toggle_rect)
        text = self.font_small.render("ON" if self.organ_editor_mode else "OFF",
                                      True, BLACK if self.organ_editor_mode else WHITE)
        self.screen.blit(text, text.get_rect(center=toggle_rect.center))
        # Olay isleyicisi bu dikdortgeni YENIDEN HESAPLIYORDU; duzen
        # degisince tiklanabilir alan yerinden oynuyordu.
        self.popup_toggle_rect = toggle_rect

        ic_x = x + 14
        ic_g = width - 28
        cy = y + 48
        pygame.draw.line(self.screen, HIGHLIGHT, (ic_x, cy), (x + width - 14, cy))
        cy += 10

        self.organ_list_rows = []
        self.organ_back_rect = None
        self.remove_btn_rect = None
        self.katman_kaldir_rect = None
        self.organ_prev_rect = self.organ_next_rect = None

        if not self.organ_editor_mode:
            self.screen.blit(self.font_small.render("Duzenlemek icin ON'a bas",
                                                    True, GRAY), (ic_x, cy))
            return

        if self.selected_layer is not None:
            self._draw_katman_detay(x, y, width, height, ic_x, ic_g, cy)
            return

        if self.selected_organ is None:
            self._draw_organ_listesi(ic_x, cy, ic_g, y + height - cy - 14)
            return

        # ---- DETAY: secili organin ayarlari ----
        self.organ_back_rect = pygame.Rect(ic_x, cy, 96, 20)
        geri_hover = self.organ_back_rect.collidepoint(pygame.mouse.get_pos())
        self.screen.blit(self.font_small.render(
            "< TUM ORGANLAR", True, WHITE if geri_hover else GRAY), (ic_x, cy))
        cy += 26

        organ_name = self.selected_organ.__class__.__name__
        organ_color = ORGAN_TYPES.get(organ_name, {}).get("color", WHITE)
        pygame.draw.rect(self.screen, organ_color, (ic_x, cy + 1, 14, 14))
        self.screen.blit(self.font_small.render(
            ORGAN_ADLARI.get(organ_name, organ_name), True, WHITE), (ic_x + 22, cy))

        # Ayni turden birden fazla organ varsa aralarinda gezin. Listeye
        # donup tekrar tiklamak ise yaramiyordu: detay acikken liste
        # cizilmiyor, dolayisiyla "ayni satira tekrar tikla" diye bir sey yok.
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        kardes = [i for i, o in enumerate(entity.organs)
                  if o.__class__.__name__ == organ_name] if entity else []
        self.organ_prev_rect = self.organ_next_rect = None
        if len(kardes) > 1:
            sira = kardes.index(self.selected_organ_index) + 1
            et = self.font_small.render("%d/%d" % (sira, len(kardes)), True, GRAY)
            sag = x + width - 14
            self.organ_next_rect = pygame.Rect(sag - 18, cy - 1, 18, 18)
            self.organ_prev_rect = pygame.Rect(sag - 40, cy - 1, 18, 18)
            self.screen.blit(et, (self.organ_prev_rect.x - et.get_width() - 6, cy))
            for r, im in ((self.organ_prev_rect, "<"), (self.organ_next_rect, ">")):
                h = r.collidepoint(pygame.mouse.get_pos())
                pygame.draw.rect(self.screen, ACCENT_COLOR if h else HIGHLIGHT, r, 1)
                t = self.font_small.render(im, True, WHITE if h else TEXT_COLOR)
                self.screen.blit(t, t.get_rect(center=r.center))
        cy += 20
        if not kaldirilabilir(organ_name):
            self.screen.blit(self.font_small.render(
                "temel yapi - kaldirilamaz", True, GRAY), (ic_x + 22, cy))
        else:
            aci = math.degrees(self.selected_organ.attachment_angle) % 360
            self.screen.blit(self.font_small.render(
                "Konum: %.1f\u00b0" % aci, True, GRAY), (ic_x + 22, cy))
        cy += 24

        params = self.get_organ_editable_params(self.selected_organ)
        if params:
            kutu_g, aralik_g = 50, 62
            kutu_x = x + width - 14 - aralik_g - kutu_g
            for baslik, anahtarlar in self._param_gruplari(self.selected_organ, params):
                if baslik:
                    self.screen.blit(self.font_small.render(baslik, True, ACCENT_COLOR),
                                     (ic_x, cy))
                    cy += 19
                for param_key in anahtarlar:
                    param_label, param_value, min_val, max_val = params[param_key]
                    satir = pygame.Rect(ic_x - 4, cy - 2, ic_g + 8, 26)
                    if satir.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(self.screen, (34, 42, 56), satir)
                    self.screen.blit(self.font_small.render(
                        self._sigdir(param_label, kutu_x - ic_x - 10),
                        True, TEXT_COLOR), (ic_x + 8, cy + 3))

                    input_rect = pygame.Rect(kutu_x, cy, kutu_g, 22)
                    input_key = f"{self.selected_organ_index}_{param_key}"
                    if input_key not in self.organ_param_inputs:
                        self.organ_param_inputs[input_key] = {
                            "rect": input_rect, "text": f"{param_value:.1f}",
                            "active": False, "param": param_key}
                    else:
                        self.organ_param_inputs[input_key]["rect"] = input_rect
                        if not self.organ_param_inputs[input_key]["active"]:
                            self.organ_param_inputs[input_key]["text"] = f"{param_value:.1f}"

                    inp = self.organ_param_inputs[input_key]
                    if inp["active"]:
                        pygame.draw.rect(self.screen, (0, 50, 60), input_rect)
                    pygame.draw.rect(self.screen,
                                     ACCENT_COLOR if inp["active"] else HIGHLIGHT,
                                     input_rect, 1)
                    self.screen.blit(self.font_small.render(inp["text"], True, WHITE),
                                     (input_rect.x + 5, input_rect.y + 3))
                    self.screen.blit(self.font_small.render(
                        "%g-%g" % (min_val, max_val), True, GRAY),
                        (input_rect.right + 6, cy + 3))
                    cy += 26
                cy += 4

            for _sat in self.teslimat_ozeti(self.selected_organ):
                renk = (WARNING if "TASIMAZ" in _sat or "uyumsuz" in _sat
                        else (GRAY if _sat.startswith(("*", "  ")) else ACCENT_COLOR))
                self.screen.blit(self.font_small.render(
                    self._sigdir(_sat, ic_g), True, renk), (ic_x, cy))
                cy += 18

        if self.organ_overlap_warning:
            self.screen.blit(self.font_small.render("! Organlar ust uste",
                                                    True, WARNING), (ic_x, cy + 4))

        if kaldirilabilir(organ_name):
            self.remove_btn_rect = pygame.Rect(ic_x, y + height - 38, ic_g, 28)
            hover = self.remove_btn_rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, DANGER if hover else (120, 50, 50),
                             self.remove_btn_rect)
            pygame.draw.rect(self.screen, WHITE if hover else GRAY,
                             self.remove_btn_rect, 1)
            t = self.font_small.render("ORGANI KALDIR", True, WHITE)
            self.screen.blit(t, t.get_rect(center=self.remove_btn_rect.center))

    def _draw_katman_detay(self, x, y, width, height, ic_x, ic_g, cy):
        """Secili KATMANIN ayarlari: kalinlik yatirimi + kaldirma.

        Katman bir organ degil, zarin bir parcasi. Bu yuzden ayri bir
        panel durumu var - organ detayindaki konum/gezinme/kaldirma
        mantiginin hicbiri katmana uymuyor.
        """
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        zar = getattr(getattr(entity, 'membrane', None), 'logic', None)
        alan = self.selected_layer
        ad = KATMAN_ADI.get(alan, alan)

        self.organ_back_rect = pygame.Rect(ic_x, cy, 96, 20)
        geri_hover = self.organ_back_rect.collidepoint(pygame.mouse.get_pos())
        self.screen.blit(self.font_small.render(
            "< TUM ORGANLAR", True, WHITE if geri_hover else GRAY), (ic_x, cy))
        cy += 26

        pygame.draw.rect(self.screen, KATMAN_RENK.get(ad, WHITE),
                         (ic_x, cy + 1, 14, 14))
        self.screen.blit(self.font_small.render(ad, True, WHITE), (ic_x + 22, cy))
        cy += 20
        self.screen.blit(self.font_small.render("zar katmani", True, GRAY),
                         (ic_x + 22, cy))
        cy += 24

        if zar is None:
            return

        # Kalinlik: TABAN + yatirim. Ikisi de gosterilir ki "6 yazdim ama
        # 4.7 cikti" sorusu ortada kalmasin.
        try:
            import lab as _lab
            prof = {a: (k, v) for a, k, _r, v in _lab.katman_kalinliklari(zar)}
            taban = {l.name: l.t for l in _lab.default_layers()}
        except Exception:
            prof, taban = {}, {}

        self.screen.blit(self.font_small.render("KALINLIK", True, ACCENT_COLOR),
                         (ic_x, cy))
        cy += 20
        kutu_g, aralik_g = 50, 62
        kutu_x = x + width - 14 - aralik_g - kutu_g

        # Iki ayri sayi: KALINLIK katmanin kendi kalinligi (yeni kazanilan
        # katman ince baslar, buradan kalinlastirilir), YATIRIM ise onun
        # uzerine eklenen guclendirmedir.
        satirlar = [
            ("kalinlik_%s" % alan, "Kalinlik", "kalinlik:" + alan,
             zar.katman_kalinligi(alan), "0.2-20"),
            ("katman_%s" % alan, "Yatirim", alan,
             getattr(zar, alan, 0.0), "0-30"),
        ]
        for anahtar, etiket, param, deger, aralik in satirlar:
            satir = pygame.Rect(ic_x - 4, cy - 2, ic_g + 8, 26)
            if satir.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.screen, (34, 42, 56), satir)
            self.screen.blit(self.font_small.render(etiket, True, TEXT_COLOR),
                             (ic_x + 8, cy + 3))
            input_rect = pygame.Rect(kutu_x, cy, kutu_g, 22)
            if anahtar not in self.organ_param_inputs:
                self.organ_param_inputs[anahtar] = {
                    "rect": input_rect, "text": "%.1f" % deger,
                    "active": False, "param": param}
            else:
                self.organ_param_inputs[anahtar]["rect"] = input_rect
                self.organ_param_inputs[anahtar]["param"] = param
                if not self.organ_param_inputs[anahtar]["active"]:
                    self.organ_param_inputs[anahtar]["text"] = "%.1f" % deger
            inp = self.organ_param_inputs[anahtar]
            if inp["active"]:
                pygame.draw.rect(self.screen, (0, 50, 60), input_rect)
            pygame.draw.rect(self.screen,
                             ACCENT_COLOR if inp["active"] else HIGHLIGHT,
                             input_rect, 1)
            self.screen.blit(self.font_small.render(inp["text"], True, WHITE),
                             (input_rect.x + 5, input_rect.y + 3))
            self.screen.blit(self.font_small.render(aralik, True, GRAY),
                             (input_rect.right + 6, cy + 3))
            cy += 26
        cy += 2
        if ad in prof:
            self.screen.blit(self.font_small.render(
                "toplam kalinlik %.1f" % prof[ad][0], True, GRAY), (ic_x + 8, cy))
            cy += 20

        # Ne ise yaradigi
        aciklama = {
            'mucus':   ["yapismayi zorlastirir", "tutulmaya karsi direnc"],
            'capsule': ["temasli saldiriya karsi", "tutulmaya karsi direnc"],
            'slayer':  ["mekanik direnc", "SERT YUZEY: fagosite edilemez"],
            'wall':    ["mekanik direnc", "SERT YUZEY: fagosite edilemez"],
        }.get(alan, [])
        for sat in aciklama:
            self.screen.blit(self.font_small.render(sat, True, ACCENT_COLOR),
                             (ic_x, cy))
            cy += 17

        self.katman_kaldir_rect = pygame.Rect(ic_x, y + height - 38, ic_g, 28)
        hover = self.katman_kaldir_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(self.screen, DANGER if hover else (120, 50, 50),
                         self.katman_kaldir_rect)
        pygame.draw.rect(self.screen, WHITE if hover else GRAY,
                         self.katman_kaldir_rect, 1)
        t = self.font_small.render("KATMANI KALDIR", True, WHITE)
        self.screen.blit(t, t.get_rect(center=self.katman_kaldir_rect.center))

    def _draw_organ_listesi(self, x, y, width, height):
        """Hucrenin organlari, sinif sinif. Bir TUR = bir satir.

        Once her organ ayri satirdi; 40 organli bir hucrede liste panele
        sigmiyordu (ve kirpma kosullari yanlisti - ekran koordinatiyla
        yuksekligi karsilastiriyorlardi). Artik ayni turden organlar tek
        satirda sayilariyla gorunur; satira tekrar tiklamak bir sonraki
        ornege gecer, secili ornek "3/6" olarak yazilir.
        """
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        alt = y + height              # panelin gercek alt siniri
        self.screen.blit(self.font_small.render("HUCRE YAPISI", True, ACCENT_COLOR),
                         (x, y))
        y += 20
        if not entity:
            return

        yerler = {}
        for i, o in enumerate(entity.organs):
            yerler.setdefault(o.__class__.__name__, []).append(i)

        sinifta = {ad for _, liste in ORGAN_SINIFLARI for ad in liste}
        gruplar = list(ORGAN_SINIFLARI)
        bilinmeyen = sorted(ad for ad in yerler if ad not in sinifta)
        if bilinmeyen:
            gruplar = gruplar + [("DIGER", bilinmeyen)]

        m_pos = pygame.mouse.get_pos()
        kesildi = 0

        # KATMANLAR once: hucrenin zarfini olusturan yapilar. Bunlar
        # entity.organs'ta DEGIL, zarin varlik maskesinde durur - o yuzden
        # burada ayri bir dongu.
        zar = getattr(getattr(entity, 'membrane', None), 'logic', None)
        if zar is not None:
            mevcut = [(a, ad) for a, ad, _k in KATMAN_ALANLARI if zar.katman_var(a)]
            self.screen.blit(self.font_small.render("KATMANLAR", True, GRAY), (x, y))
            y += 17
            if not mevcut:
                self.screen.blit(self.font_small.render(
                    "  (yok - ciplak plazma zari)", True, GRAY), (x, y))
                y += 18
            for alan, ad in mevcut:
                if y + 18 > alt:
                    kesildi += 1
                    continue
                r = pygame.Rect(x, y, width, 18)
                secili = self.selected_layer == alan
                if secili:
                    pygame.draw.rect(self.screen, (30, 55, 70), r)
                elif r.collidepoint(m_pos):
                    pygame.draw.rect(self.screen, (34, 42, 56), r)
                pygame.draw.rect(self.screen, KATMAN_RENK.get(ad, WHITE),
                                 (x + 4, y + 4, 10, 10))
                self.screen.blit(self.font_small.render(
                    self._sigdir(ad, width - 26), True,
                    WHITE if secili else TEXT_COLOR), (x + 20, y + 2))
                self.organ_list_rows.append(("katman", alan, r))
                y += 18
            # Plazma zari zorunlu: listede ama tiklanmaz
            if y + 18 <= alt:
                pygame.draw.rect(self.screen, KATMAN_RENK.get("Hucre zari", WHITE),
                                 (x + 4, y + 4, 10, 10))
                self.screen.blit(self.font_small.render(
                    "Hucre zari (zorunlu)", True, GRAY), (x + 20, y + 2))
                y += 18
            y += 6

        for baslik, adlar in gruplar:
            var = [ad for ad in adlar if ad in yerler]
            if not var:
                continue
            if y + 17 + 18 > alt:
                kesildi += sum(len(yerler[a]) for a in var)
                continue
            self.screen.blit(self.font_small.render(baslik, True, GRAY), (x, y))
            y += 17
            for ad in var:
                if y + 18 > alt:
                    kesildi += len(yerler[ad])
                    continue
                idxler = yerler[ad]
                r = pygame.Rect(x, y, width, 18)
                secili = self.selected_organ_index in idxler
                if secili:
                    pygame.draw.rect(self.screen, (30, 55, 70), r)
                elif r.collidepoint(m_pos):
                    pygame.draw.rect(self.screen, (34, 42, 56), r)
                renk = ORGAN_TYPES.get(ad, {}).get("color", WHITE)
                pygame.draw.rect(self.screen, renk, (x + 4, y + 4, 10, 10))
                etiket = ORGAN_ADLARI.get(ad, ad)
                if len(idxler) > 1:
                    etiket += ("  %d/%d" % (idxler.index(self.selected_organ_index) + 1,
                                            len(idxler))
                               if secili else "  x%d" % len(idxler))
                self.screen.blit(self.font_small.render(
                    self._sigdir(etiket, width - 26), True,
                    WHITE if secili else TEXT_COLOR), (x + 20, y + 2))
                self.organ_list_rows.append(("organ", idxler, r))
                y += 18
            y += 6

        if kesildi:
            self.screen.blit(self.font_small.render(
                "... %d organ daha (panele sigmadi)" % kesildi, True, WARNING),
                (x, min(y, alt - 16)))

    def draw_organ_palette(self, x, y, width, height):
        """Yeni organ ekleme paleti - SINIF SINIF, onizlemenin altinda.

        Temel yapilar (zar, sitoplazma) burada YOKTUR: onlar dogustan var.
        """
        panel = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (25, 30, 40), panel)
        pygame.draw.rect(self.screen, HIGHLIGHT, panel, 1)
        self.screen.blit(self.font_small.render("ORGAN EKLE", True, ACCENT_COLOR),
                         (x + 14, y + 10))

        self.add_organ_btns = []
        if not self.organ_editor_mode:
            self.screen.blit(self.font_small.render(
                "Once ORGAN EDITOR'u ac", True, GRAY), (x + 14, y + 34))
            return

        bw, bh, bg = 78, 24, 5
        sutun = max(1, (width - 28 + bg) // (bw + bg))
        m_pos = pygame.mouse.get_pos()
        cy = y + 32

        # Zaten var olan katman tekrar eklenemez; dugmesi soluk cizilir.
        zar = getattr(getattr(self.popup_entity, 'membrane', None), 'logic', None)
        gruplar = list(PALET_SINIFLARI)
        gruplar.insert(0, ("KATMANLAR", [ad for _a, ad, _k in KATMAN_ALANLARI]))

        for baslik, adlar in gruplar:
            if cy + 16 + bh > y + height - 24:
                break
            self.screen.blit(self.font_small.render(baslik, True, GRAY), (x + 14, cy))
            cy += 17
            katman_grubu = baslik == "KATMANLAR"
            for i, organ_type in enumerate(adlar):
                r = pygame.Rect(x + 14 + (i % sutun) * (bw + bg),
                                cy + (i // sutun) * (bh + bg), bw, bh)
                if katman_grubu:
                    alan = KATMAN_ALANI_ADI[organ_type]
                    zaten = zar is not None and zar.katman_var(alan)
                    renk = KATMAN_RENK.get(organ_type, WHITE)
                    # Dugme TURUYLE saklanir: 'Duvar' ile 'Cilia' ikisi de
                    # birer metin, ayirt edilmezlerse katman dugmesi organ
                    # ekleme yoluna girip son organi seciyordu.
                    self.add_organ_btns.append(("katman", organ_type, r))
                else:
                    zaten = False
                    renk = ORGAN_TYPES.get(organ_type, {}).get("color", WHITE)
                    self.add_organ_btns.append(("organ", organ_type, r))
                hover = r.collidepoint(m_pos) and not zaten
                if zaten:
                    renk = tuple(c // 3 for c in renk)
                pygame.draw.rect(self.screen,
                                 tuple(min(255, c + 40) for c in renk) if hover else renk, r)
                pygame.draw.rect(self.screen, WHITE if hover else GRAY, r, 1)
                etk = ORGAN_SHORT_NAMES.get(organ_type, organ_type[:7])
                t = self.font_small.render(etk, True,
                                           GRAY if zaten else BLACK)
                self.screen.blit(t, t.get_rect(center=r.center))
            cy += ((len(adlar) - 1) // sutun + 1) * (bh + bg) + 6

        self.screen.blit(self.font_small.render(
            "Zar, sitoplazma ve plazma zari dogustan var", True, GRAY),
            (x + 14, y + height - 22))

    def zarf_kalinligi(self, entity, cekirdek_r):
        """Zarfin piksel kalinligi. lab.py ile AYNI oran.

        Laboratuvarda cekirdek 110 px ve PX_PER_UNIT 9.0; yani bir kalinlik
        birimi cekirdek yaricapinin 9/110'u kadar yer kaplar. Onizleme de
        ayni orani kullanir, boylece iki gorunum ayni hucreyi ayni bicimde
        gosterir.
        """
        try:
            import lab as _lab
            zar = getattr(getattr(entity, 'membrane', None), 'logic', None)
            birim = cekirdek_r * (_lab.PX_PER_UNIT / 110.0)
            return sum(k for _ad, k, _r, var in _lab.katman_kalinliklari(zar)
                       if var) * birim
        except Exception:
            return 0.0

    def draw_zar_katmanlari(self, entity, cx, cy, cekirdek_r, etiketle=False):
        """Zarfi cekirdegin DISINA halka halka ciz; dis yaricapi dondur.

        Onceki surumde halkalar govdenin ICINE ciziliyordu ve sitoplazmanin
        dis bandini yiyordu - hucre ayni boyda kalip sitoplazma kuculmus
        gibi gorunuyordu. lab.py'de zarf cekirdegin DISINDADIR ve zar
        uzerindeki organlar da o dis yuzeye tasinir; onizleme artik ayni.
        """
        try:
            import lab as _lab
        except Exception:
            return cekirdek_r
        zar = getattr(getattr(entity, 'membrane', None), 'logic', None)
        if zar is None:
            return cekirdek_r
        # Cizimin kendisi lab.zarf_ciz'de - oyun, editor ve kesit ayni
        # uygulamayi kullansin diye.
        r = _lab.zarf_ciz(self.screen, zar, (cx, cy), cekirdek_r)
        cizilen = [(ad, kal, renk)
                   for ad, kal, renk, var in _lab.katman_kalinliklari(zar) if var]
        cizilen.reverse()          # icten disa (efsane tersine cevirir)
        pygame.draw.circle(self.screen, (90, 100, 115), (int(cx), int(cy)),
                           int(r), 1)

        if etiketle and cizilen:
            gen, sat = 104, 15
            kutu = pygame.Rect(cx + self._onizleme_yarikenar - gen - 2,
                               cy - self._onizleme_yarikenar + 2,
                               gen, sat * (len(cizilen) + 1) + 8)
            arka = pygame.Surface(kutu.size, pygame.SRCALPHA)
            arka.fill((18, 22, 30, 220))
            self.screen.blit(arka, kutu.topleft)
            pygame.draw.rect(self.screen, (60, 70, 85), kutu, 1)
            ty = kutu.y + 4
            self.screen.blit(self.font_small.render("katman kalinligi", True, GRAY),
                             (kutu.x + 6, ty))
            ty += sat
            for ad, kal, renk in reversed(cizilen):     # distan ice yaz
                pygame.draw.rect(self.screen, renk, (kutu.x + 6, ty + 3, 9, 9))
                self.screen.blit(self.font_small.render(
                    "%s %.1f" % (ad, kal), True, TEXT_COLOR), (kutu.x + 20, ty))
                ty += sat
        return r

    def draw_entity_preview(self, entity, center_x, center_y, scale):
        """Varlığı büyütülmüş olarak çizer - tüm organeller orantılı."""
        if not entity:
            return

        # Orijinal değerleri sakla
        original_radius = entity.radius
        original_pos = pygame.math.Vector2(entity.pos)
        original_direction = pygame.math.Vector2(entity.direction)

        # Organ orijinal değerlerini sakla
        organ_originals = []
        for organ in entity.organs:
            orig = {}
            if hasattr(organ.logic, 'length'):
                orig['length'] = organ.logic.length
                organ.logic.length *= scale
            if hasattr(organ.logic, 'size'):
                orig['size'] = organ.logic.size
                organ.logic.size *= scale
            # Vacuole area'sını scale et (alan = scale^2 ile büyür)
            if hasattr(organ.logic, 'area'):
                orig['area'] = organ.logic.area
                organ.logic.area *= (scale * scale)
            # Görüş menzilini scale et (clip region taşmayı önlüyor)
            if hasattr(organ.logic, 'range'):
                orig['range'] = organ.logic.range
                organ.logic.range *= scale
            # sensitivity bir property (size * 30), size zaten büyütüldü
            organ_originals.append(orig)

        # Büyütülmüş değerleri uygula
        entity.radius = original_radius * scale
        entity.pos = pygame.math.Vector2(center_x, center_y)

        # Yön vektörünü sağa doğru ayarla (güzel görünsün)
        entity.direction = pygame.math.Vector2(1, 0)

        # GOVDE TABANI: govdeyi Cytoplasm organi ciziyor, dolayisiyla
        # sitoplazmasi olmayan varlik editorde TAMAMEN gorunmez oluyordu -
        # organ eklemek icin tiklanacak bir sey bile kalmiyordu. Konum ve
        # yaricap organlardan bagimsiz vardir.
        if not any(o.__class__.__name__ == 'Cytoplasm' for o in entity.organs):
            _r = max(4, int(entity.radius))
            _p = (int(entity.pos.x), int(entity.pos.y))
            _g = pygame.Surface((_r * 2 + 4,) * 2, pygame.SRCALPHA)
            pygame.draw.circle(_g, (*entity.color, 60), (_r + 2, _r + 2), _r)
            self.screen.blit(_g, (_p[0] - _r - 2, _p[1] - _r - 2))
            pygame.draw.circle(self.screen, entity.color, _p, _r, 2)

        # CIZIM SIRASI hucrenin gercek yapisini izler:
        #   1) IC organlar govde yaricapinda,
        #   2) ZAR KATMANLARI onlarin disinda halka halka,
        #   3) DIS organlar (alicilar, motorlar, silahlar) en distaki
        #      yuzeyde - kamci mukusun altindan degil, uzerinden cikar.
        from organs.registry import ic_organ as _ic_organ
        ic = [o for o in entity.organs if _ic_organ(o.__class__.__name__)]
        dis = [o for o in entity.organs if o not in ic]

        # 1) IC organlar CEKIRDEK yaricapinda. Zarf entity.radius'un ICINE
        #    oturur (oyunla ayni model): dis sinir = temas yaricapi,
        #    sitoplazma da zarfin icinde kalir. Onizleme bunu oyundan
        #    farkli hesaplarsa editorde gordugun hucre ekosistemdekinden
        #    baska bir sey olur.
        import lab as _l
        dis_sinir = entity.radius
        cekirdek_r = _l.cekirdek_yaricapi_ham(dis_sinir, entity)
        entity.radius = cekirdek_r
        for organ in ic:
            organ.draw(self.screen, entity)

        # 2) ZARF cekirdegin disinda
        _secili_zar = (self.selected_organ is not None and
                       self.selected_organ.__class__.__name__ == 'Membrane')
        self.draw_zar_katmanlari(entity, center_x, center_y, cekirdek_r,
                                 etiketle=_secili_zar)
        dis_r = dis_sinir

        # 3) DIS organlar zarfin DIS yuzeyinde. Organ gorunumleri boyutlarini
        #    kendi alanlarindan alir (mekanoreseptorun cemberi size*30,
        #    kamcinin uzunlugu length); parent.radius yalnizca KONUM icin
        #    kullanilir - bu yuzden disari tasimak hicbir organi sismez.
        entity.radius = dis_r
        self._onizleme_organ_r = dis_r
        for organ in dis:
            organ.draw(self.screen, entity)
        entity.radius = dis_sinir

        # Orijinal değerleri geri yükle
        entity.radius = original_radius
        entity.pos = original_pos
        entity.direction = original_direction

        for i, organ in enumerate(entity.organs):
            orig = organ_originals[i]
            if 'length' in orig:
                organ.logic.length = orig['length']
            if 'size' in orig:
                organ.logic.size = orig['size']
            if 'area' in orig:
                organ.logic.area = orig['area']
            if 'range' in orig:
                organ.logic.range = orig['range']

    def draw_entities(self):
        # Popup açıksa, popup'ı çiz
        if self.entity_popup_open:
            self.draw_entity_popup()
            return

        # Ana panel başlığı
        self.screen.blit(self.font_title.render("SPECIES EDITOR", True, ACCENT_COLOR),
                        (self.sidebar_width + 40, 30))
        self.screen.blit(self.font_small.render("Select a species to edit its organs and genes", True, GRAY),
                        (self.sidebar_width + 40, 75))

        # Varlık kartları - grid düzeni
        card_width = 280
        card_height = 200
        cards_per_row = 3
        start_x = self.sidebar_width + 40
        start_y = 120
        gap = 25

        all_entities = self.editable_entities()

        for idx, ent in enumerate(all_entities):
            row = idx // cards_per_row
            col = idx % cards_per_row

            card_x = start_x + col * (card_width + gap)
            card_y = start_y + row * (card_height + gap)

            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            is_hover = card_rect.collidepoint(pygame.mouse.get_pos())

            # Kart arka planı
            bg_color = HIGHLIGHT if is_hover else CARD_COLOR
            pygame.draw.rect(self.screen, bg_color, card_rect)
            pygame.draw.rect(self.screen, ACCENT_COLOR if is_hover else GRAY, card_rect, 2 if is_hover else 1)

            # Varlık adı
            name = "Notropi" if isinstance(ent, Notropi) else f"Optropi #{idx + 1}"
            self.screen.blit(self.font_main.render(name, True, ent.color), (card_x + 15, card_y + 12))

            # Varlık preview (küçük)
            preview_center_x = card_x + card_width // 2
            preview_center_y = card_y + 95
            mini_scale = 2.0

            # Clip region
            self.screen.set_clip(pygame.Rect(card_x + 5, card_y + 40, card_width - 10, 100))
            self._onizleme_yarikenar = 46      # kartin kirpma yuksekligine gore
            self.draw_entity_preview(ent, preview_center_x, preview_center_y, mini_scale)
            self.screen.set_clip(None)

            # İstatistikler
            ent.recalculate_physics()
            stats_y = card_y + 150
            stats_text = f"Organs: {len(ent.organs)}  |  Energy: {ent.max_energy:.0f}  |  Speed: {ent.speed:.1f}"
            self.screen.blit(self.font_small.render(stats_text, True, GRAY), (card_x + 15, stats_y))

            # Edit butonu
            edit_btn = pygame.Rect(card_x + card_width - 80, card_y + card_height - 40, 65, 28)
            edit_hover = edit_btn.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, ACCENT_COLOR if edit_hover else HIGHLIGHT, edit_btn)
            pygame.draw.rect(self.screen, WHITE if edit_hover else GRAY, edit_btn, 1)
            edit_text = self.font_small.render("EDIT", True, BLACK if edit_hover else WHITE)
            self.screen.blit(edit_text, edit_text.get_rect(center=edit_btn.center))

    def handle_entity_list_events(self, event, m_pos):
        """Varlık listesi ve popup olaylarını işler."""
        if self.state != "ENTITIES":
            return

        # Popup kapatma
        if self.entity_popup_open:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.popup_close_btn and self.popup_close_btn.collidepoint(m_pos):
                    # Popup kapanırken organ düzenini kalıcılaştır
                    self.close_entity_editor()
                    return
            return  # Popup açıkken diğer olayları organ editöre aktar

        # Varlık kartlarına tıklama
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            card_width = 280
            card_height = 200
            cards_per_row = 3
            start_x = self.sidebar_width + 40
            start_y = 120
            gap = 25

            all_entities = self.editable_entities()

            for idx, ent in enumerate(all_entities):
                row = idx // cards_per_row
                col = idx % cards_per_row

                card_x = start_x + col * (card_width + gap)
                card_y = start_y + row * (card_height + gap)

                # Edit butonuna tıklama
                edit_btn = pygame.Rect(card_x + card_width - 80, card_y + card_height - 40, 65, 28)
                if edit_btn.collidepoint(m_pos):
                    self.popup_entity = ent
                    self.selected_entity = ent
                    self.entity_popup_open = True
                    self.selected_organ = None
                    self.selected_organ_index = -1
                    self.organ_param_inputs = {}
                    self.create_entity_editor()
                    return

                # Kart alanına tıklama (edit butonu dışında)
                card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
                if card_rect.collidepoint(m_pos):
                    self.popup_entity = ent
                    self.selected_entity = ent
                    self.entity_popup_open = True
                    self.selected_organ = None
                    self.selected_organ_index = -1
                    self.organ_param_inputs = {}
                    self.create_entity_editor()
                    return

    def handle_entity_editor_event(self, event, m_pos):
        was_open = self.entity_popup_open
        self.handle_entity_list_events(event, m_pos)
        if not was_open or not self.entity_popup_open:
            return
        # Organ kutusunu once tamamla; gen kutusu hucreyi yenileyebilir.
        self.handle_organ_editor_events(event, m_pos)
        for _, ibox in self.entity_ui_elements:
            ibox.handle_event(event)

    def handle_organ_editor_events(self, event, m_pos):
        """Organ editör olaylarını işler."""
        if self.state != "ENTITIES":
            return

        # Popup kapalıysa işleme
        if not self.entity_popup_open or not self.popup_entity:
            return

        # Yerlesim CIZIMDE belirlenir, burada tekrarlanmaz. Eskiden bu blok
        # popup'in olculerini (450 genislik, 350 onizleme, editor konumu)
        # ikinci kez hesapliyordu; duzen degisince olaylar eski koordinatlara
        # bakmaya devam etti - ON/OFF dugmesi ve onizleme alani kaydi.
        preview_rect = getattr(self, 'popup_preview_rect', None)
        toggle_rect = getattr(self, 'popup_toggle_rect', None)
        if preview_rect is None or toggle_rect is None:
            return          # daha ilk kare cizilmedi

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Toggle butonu
            if toggle_rect.collidepoint(m_pos):
                self.commit_organ_inputs()
                self.save_entity_organ_config(self.popup_entity)
                self.organ_editor_mode = not self.organ_editor_mode
                self.selected_organ = None
                self.selected_organ_index = -1
                self.selected_layer = None
                self.organ_param_inputs = {}  # Input'ları temizle
                return

            # Organ parametre input'ları
            if self.organ_editor_mode and self.organ_param_inputs:
                clicked_input = False
                for input_key, inp in self.organ_param_inputs.items():
                    if inp["rect"].collidepoint(m_pos):
                        inp["active"] = True
                        clicked_input = True
                    else:
                        # Başka yere tıklandıysa, aktif input'u kaydet
                        if inp["active"]:
                            inp["active"] = False
                            if input_key.startswith(("katman_", "kalinlik_")):
                                self.update_katman_param(inp["param"], inp["text"])
                            else:
                                self.update_organ_param(inp["param"], inp["text"])
                if clicked_input:
                    return

            # HUCRE YAPISI listesinden secim: ic organlara (zar, sitoplazma,
            # koful, iskelet, ribozom) ulasmanin TEK yolu bu - onizlemede
            # tiklanabilir bir konumlari yok.
            if self.organ_editor_mode:
                for tur, yuk, r in getattr(self, 'organ_list_rows', []):
                    if not r.collidepoint(m_pos):
                        continue
                    if tur == "katman":
                        self.selected_layer = yuk
                        self.selected_organ = None
                        self.selected_organ_index = -1
                        self.organ_param_inputs = {}
                        return
                    yeni_i = yuk[0]
                    if yeni_i != self.selected_organ_index:
                        self.organ_param_inputs = {}
                    self.selected_layer = None
                    self.selected_organ_index = yeni_i
                    self.selected_organ = self.popup_entity.organs[yeni_i]
                    return
                # Ayni turden organlar arasinda gezinme (detay basligindaki < >)
                for r, yon in ((getattr(self, 'organ_prev_rect', None), -1),
                               (getattr(self, 'organ_next_rect', None), 1)):
                    if r is not None and r.collidepoint(m_pos) and self.selected_organ:
                        ad = self.selected_organ.__class__.__name__
                        kardes = [i for i, o in enumerate(self.popup_entity.organs)
                                  if o.__class__.__name__ == ad]
                        if self.selected_organ_index in kardes:
                            k = (kardes.index(self.selected_organ_index) + yon) % len(kardes)
                            self.selected_organ_index = kardes[k]
                            self.selected_organ = self.popup_entity.organs[kardes[k]]
                            self.organ_param_inputs = {}
                        return
                geri = getattr(self, 'organ_back_rect', None)
                if geri is not None and geri.collidepoint(m_pos):
                    self.selected_organ = None
                    self.selected_organ_index = -1
                    self.selected_layer = None
                    self.organ_param_inputs = {}
                    return

                # KATMANI KALDIR
                kk = getattr(self, 'katman_kaldir_rect', None)
                if (kk is not None and kk.collidepoint(m_pos)
                        and self.selected_layer):
                    zar = getattr(getattr(self.popup_entity, 'membrane', None),
                                  'logic', None)
                    if zar is not None:
                        zar.katman_cikar(self.selected_layer)
                        self.popup_entity.recalculate_physics()
                        self.save_entity_organ_config(self.popup_entity)
                    self.selected_layer = None
                    self.organ_param_inputs = {}
                    return

            # Organ ekleme ve kaldırma butonları
            if self.organ_editor_mode:
                # Kaldır butonu - önce kontrol et
                if hasattr(self, 'remove_btn_rect') and self.remove_btn_rect and self.selected_organ:
                    if self.remove_btn_rect.collidepoint(m_pos):
                        self.remove_selected_organ()
                        self.organ_param_inputs = {}  # Input'ları temizle
                        return

                # Organ ekleme butonları
                if hasattr(self, 'add_organ_btns'):
                    for _tur, organ_type, btn_rect in self.add_organ_btns:
                        if not btn_rect.collidepoint(m_pos):
                            continue
                        if _tur == "katman":
                            # Katman entity.organs'a girmez: zarin varlik
                            # maskesine yazilir. Aci arama dongusu, ortusme
                            # kontrolu ve "son organi sec" adimi katmana
                            # uygulanmamali.
                            zar = getattr(getattr(self.popup_entity, 'membrane',
                                                  None), 'logic', None)
                            if zar is not None:
                                alan = KATMAN_ALANI_ADI[organ_type]
                                zar.katman_ekle(alan)
                                self.popup_entity.recalculate_physics()
                                self.save_entity_organ_config(self.popup_entity)
                                self.selected_layer = alan
                                self.selected_organ = None
                                self.selected_organ_index = -1
                                self.organ_param_inputs = {}
                            return
                        if True:
                            # Organ türüne göre başlangıç açısı belirle
                            if organ_type == "Flagella":
                                start_angle = 180  # Arka
                            elif organ_type == "Photoreceptor":
                                start_angle = 0  # Ön
                            elif organ_type == "Chemoreceptor":
                                start_angle = 135  # Arka-yan
                            elif organ_type == "Mechanoreceptor":
                                start_angle = 45  # Ön-yan
                            elif organ_type == "Cilia":
                                start_angle = 90  # Yan
                            else:
                                start_angle = 0

                            # Başlangıç açısından başlayarak boş yer ara
                            added = False
                            for offset in range(0, 360, 10):
                                test_angle = (start_angle + offset) % 360
                                test_rad = math.radians(test_angle)
                                if self.add_organ_to_entity(organ_type, test_rad):
                                    added = True
                                    break
                            if not added:
                                # Daha ince adımlarla tekrar dene
                                for offset in range(0, 360, 5):
                                    test_angle = (start_angle + offset) % 360
                                    test_rad = math.radians(test_angle)
                                    if self.add_organ_to_entity(organ_type, test_rad):
                                        break
                            # Yeni organ dogrudan secilsin: eklendigi anda
                            # ayarlari acilir, listeden tekrar aranmaz.
                            if self.popup_entity.organs:
                                self.selected_layer = None
                                self.selected_organ_index = len(self.popup_entity.organs) - 1
                                self.selected_organ = self.popup_entity.organs[-1]
                                self.organ_param_inputs = {}
                            return

            # Preview alanında organ seçimi
            if self.organ_editor_mode and preview_rect.collidepoint(m_pos):
                organ_idx = self.get_organ_at_position(
                    m_pos[0], m_pos[1],
                    self.preview_center_x, self.preview_center_y
                )
                if organ_idx >= 0:
                    # Yeni organ seçildiğinde input'ları temizle
                    if organ_idx != self.selected_organ_index:
                        self.organ_param_inputs = {}
                    self.selected_organ_index = organ_idx
                    self.selected_organ = self.popup_entity.organs[organ_idx]
                    self.dragging_organ = True
                    self.drag_start_angle = self.selected_organ.attachment_angle
                else:
                    self.selected_organ = None
                    self.selected_organ_index = -1
                    self.organ_param_inputs = {}

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging_organ:
                self.dragging_organ = False
                self.organ_overlap_warning = False
                self.save_entity_organ_config(self.popup_entity)

        elif event.type == pygame.MOUSEMOTION:
            # Hover kontrolü
            if self.organ_editor_mode and preview_rect.collidepoint(m_pos) and not self.dragging_organ:
                self.hover_organ_index = self.get_organ_at_position(
                    m_pos[0], m_pos[1],
                    self.preview_center_x, self.preview_center_y
                )
            else:
                self.hover_organ_index = -1

            # Sürükleme
            if self.dragging_organ and self.selected_organ_index >= 0:
                # Yeni açıyı hesapla
                dx = m_pos[0] - self.preview_center_x
                dy = m_pos[1] - self.preview_center_y
                new_angle = math.atan2(dy, dx)

                # Örtüşme kontrolü
                overlap, _ = self.check_organ_overlap(self.selected_organ_index, new_angle)

                if not overlap:
                    # Pozisyonu güncelle
                    organ = self.popup_entity.organs[self.selected_organ_index]
                    organ.attachment_angle = new_angle
                    # Flagella ise thrust açısını da güncelle
                    if hasattr(organ, 'sync_thrust_to_attachment'):
                        organ.sync_thrust_to_attachment()
                    self.selected_organ = organ
                    self.organ_overlap_warning = False
                    self.popup_entity.recalculate_physics()
                else:
                    self.organ_overlap_warning = True

        # Klavye olayları (organ parametre input'ları için)
        elif event.type == pygame.KEYDOWN:
            if self.organ_editor_mode and self.organ_param_inputs:
                for input_key, inp in self.organ_param_inputs.items():
                    if inp["active"]:
                        if event.key == pygame.K_RETURN:
                            inp["active"] = False
                            if input_key.startswith(("katman_", "kalinlik_")):
                                self.update_katman_param(inp["param"], inp["text"])
                            else:
                                self.update_organ_param(inp["param"], inp["text"])
                        elif event.key == pygame.K_BACKSPACE:
                            inp["text"] = inp["text"][:-1]
                        elif event.unicode in "0123456789.-":
                            inp["text"] += event.unicode
                        break

    def run(self):
        while True:
            self.screen.fill(BG_COLOR)
            m_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Organ düzeni eskiden yalnızca "simülasyonu başlat"
                    # düğmesinde kaydediliyordu; pencereyi kapatan kullanıcı
                    # tüm düzenlemesini kaybediyordu.
                    self.save_all_organ_configs()
                    if self.state == "HARITA":
                        self.harita_kaydet()
                    sys.exit()
                # Popup arka plandaki sekmeleri ortuyor. Ayni tiklama
                # hem organa hem sekmeye giderse setup_ui hucreyi siler.
                if self.entity_popup_open:
                    self.handle_entity_editor_event(event, m_pos)
                    continue
                if event.type == pygame.MOUSEWHEEL and self.state == "SETTINGS":
                    self.scroll_y = min(0, max(self.max_scroll, self.scroll_y + event.y * 30))
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "SETTINGS" and m_pos[0] > self.screen_width - 30: self.dragging_scroll = True
                    for i, tab in enumerate(self.tabs):
                        if pygame.Rect(0, 180 + i * 60, self.sidebar_width, 50).collidepoint(event.pos): self.set_state(tab)
                    if self.state == "DASHBOARD" and pygame.Rect(self.sidebar_width + 100, self.screen_height//2 - 40, 400, 80).collidepoint(event.pos):
                        # Organ konfigürasyonlarını kaydet
                        self.save_all_organ_configs()
                        pygame.quit(); run_simulation(); sys.exit()
                if event.type == pygame.MOUSEBUTTONUP: self.dragging_scroll = False
                if self.dragging_scroll and event.type == pygame.MOUSEMOTION:
                    self.scroll_y = ((max(0, min(self.screen_height-120, m_pos[1]-100))) / (self.screen_height-120)) * self.max_scroll
                
                if self.state == "SETTINGS":
                    # Once arama kutusu ve sifirlama dugmeleri; biri olayi
                    # tuketirse deger kutularina gitmesin
                    if not self.handle_settings_events(event, m_pos):
                        for el in self.ui_elements: el.handle_event(event, self.scroll_y)
                elif self.state == "HARITA":
                    self.handle_harita_events(event, m_pos)
                elif self.state == "ENTITIES":
                    self.handle_entity_editor_event(event, m_pos)

            self.draw_sidebar()
            if self.state == "DASHBOARD": self.draw_dashboard()
            elif self.state == "SETTINGS": self.draw_settings()
            elif self.state == "HARITA": self.draw_harita()
            elif self.state == "ENTITIES": self.draw_entities()
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    ModernLauncher().run()

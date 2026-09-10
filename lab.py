"""LABORATUVAR MODU — elektron mikroskobu görünümü.

Hücreleri devasa çizer ki zar katmanları, taşıyıcılar, yükler ve bir merminin
katmanlardan geçişi tek tek izlenebilsin.

Görünür olan fizik:
  - Her katman kendi rengi, kalınlığı ve GÖZENEK dokusuyla çizilir
  - Çarpma açısı GEOMETRİDEN gelir: kenara nişan al, seker
  - Mermi her katmanda yavaşlar (hız ~ sqrt(kalan enerji))
  - Elekten geçen molekül hiç yavaşlamaz, yarmak zorunda kalan yavaşlar
  - YÜK doğru bölgeye bırakılırsa etkisi canlandırılır, yanlış yerde hiçbir şey olmaz

Çalıştırma:  python lab.py
"""

import math
import random

import pygame

from organs.registry import all_organ_names, make_organ
from systems.physics.penetration import (
    Layer, Penetrator, cross_layer, try_bite, bite_angle_limit,
    SIEVE, BREACH, BLOCKED, GLANCE, DOCK)

# TASARIM olcusu. Duzen, yazi boyutlari ve hucre yaricapi bu olcuye gore
# ayarlandi. Tam ekranda sabitleri buyutmek denendi ve KOTU sonuc verdi:
# 2560x1440'ta yazilar okunmuyor, hucre ekranin kucuk bir kosesinde
# kaliyor, saldirgan hedeften 754 px uzakta kalip menzilsiz kaliyordu.
# Bunun yerine tasarim olcusunde bir TUVALE cizip ekrana olcekleyerek
# basiyoruz - oranlar korunuyor, her sey buyuyor.
WIDTH, HEIGHT = 1500, 900
PANEL_W = 400
VIEW_W = WIDTH - PANEL_W


def _screen_fit(win_w, win_h):
    """Tuvali pencereye sigdiran olcek ve ortalama kaymasi."""
    k = min(win_w / WIDTH, win_h / HEIGHT)
    return k, ((win_w - WIDTH * k) * 0.5, (win_h - HEIGHT * k) * 0.5)
PX_PER_UNIT = 9.0
E_REF = 0.08               # KÜÇÜK: üstel kapı KESKİN çalışır.
# 0.5 iken sınırdaki bir stilet zarı p=0.449 ile geçiyordu — enerjisi
# gerekenin üçte biriyken yazı-tura. 0.08'de aynı açık p=0.006'ya iner.
# Moleküler yerleşme etkilenmez, çünkü orada deneme sayısı devasa.

BG = (10, 12, 18)
PANEL_BG = (18, 21, 30)
FG = (222, 226, 235)
DIM = (118, 126, 143)
ACCENT = (120, 220, 180)
WARN = (255, 170, 90)
BAD = (255, 110, 110)
INFO = (140, 200, 255)

# Yükün etki edebilmesi için ulaşılması gereken derinlik
Z_SURFACE = 'yuzey'
Z_WALL = 'duvar'
Z_MEMBRANE = 'zar'
Z_CYTO = 'ic'

# Yükün etki edebilmesi için ULAŞILMASI gereken katman.
# depth = başarıyla geçilen katman sayısı; o katmana "ulaşmak" için
# ondan öncekilerin hepsinin geçilmiş olması yeter.
ZONE_TARGET = {Z_WALL: 'Duvar', Z_SURFACE: 'Hucre zari',
               Z_MEMBRANE: 'Hucre zari', Z_CYTO: None}   # None = hepsini geç

# Yükün o bölgede ETKİ edebilmesi için tam orada mı bırakılması gerekiyor?
#
#   'tam'    : yükün o KATMANIN İÇİNE yerleşmesi gerekir. Taşıyıcı fazla
#              güçlüyse delip geçer ve yükü yanlış bölmede bırakır - gözenek
#              açıcı sitoplazmada işe yaramaz, çünkü yerleşeceği çift katman
#              artık arkasında kalmıştır.
#   'enaz'   : yüzeye TEMAS yeter. Delip geçmiş olmak temasi ortadan
#              kaldırmaz; kanal blokeri yolda zaten yüzeye değmiştir.
ZONE_MODE = {Z_WALL: 'tam', Z_MEMBRANE: 'tam',
             Z_SURFACE: 'enaz', Z_CYTO: 'enaz'}


def zone_min_depth(zone, active_layers):
    """Bu bölgeye ulaşmak için kaç katman geçilmiş olmalı.

    Hedef katman hucrede YOKSA None doner. Eskiden bu durumda
    len(active_layers) donuyordu - yani Z_CYTO ile ayni sayi. Duvarsiz bir
    hucreye atilan lizozim boylece "sitoplazmaya nisan alan" bir yuke
    donusuyor, sitoplazmada baglanip olmayan bir duvari eritiyordu.
    """
    target = ZONE_TARGET[zone]
    if target is None:
        return len(active_layers)
    for i, l in enumerate(active_layers):
        if l.name == target:
            return i
    return None
ZONE_LABEL = {Z_SURFACE: 'zar yuzeyi', Z_WALL: 'duvar ici',
              Z_MEMBRANE: 'zar ici', Z_CYTO: 'sitoplazma'}


def default_layers():
    return [
        # porosity = acik alan orani, viscosity = jel surtunmesi
        Layer('Mukus',      mesh=50.0, B=0.02, t=7.0, friction=0.15, elastic=0.9,
              color=(70, 130, 150),  porosity=0.85, viscosity=0.12),
        Layer('Kapsul',     mesh=20.0, B=0.05, t=5.0, friction=0.25, elastic=0.6,
              color=(95, 165, 185),  porosity=0.70, viscosity=0.08),
        Layer('S-layer',    mesh=4.0,  B=0.30, t=2.0, friction=0.10, elastic=0.1,
              color=(205, 200, 120), porosity=0.45, viscosity=0.02),
        Layer('Duvar',      mesh=2.2,  B=20.0, t=6.0, friction=0.55, elastic=0.15,
              color=(215, 160, 85),  porosity=0.55, viscosity=0.03),
        Layer('Hucre zari', mesh=0.0,  B=6.00, t=1.5, friction=0.45, elastic=0.7,
              color=(235, 115, 145), porosity=0.00, viscosity=0.01),
    ]


# --------------------------------------------------------------- TAŞIYICILAR
#
# ENERJI OLCEGI: bariyerlerle AYNI mertebede olmali. Onceki degerlerde
# (12/16/90/400) butun zarfin maliyeti ~8 birimdi; guclu stiletin 11 kat
# fazla enerjisi vardi ve KALINLIK HIC FARK ETMIYORDU. Kalinlik gerekeni
# dogrusal artiriyordu ama hep enerjinin cok altinda kaliyordu.
#
# Simdi duvar B=20, zar B=6 ve enerjiler bariyerlere yakin secildi; boylece
# katman kalinlastirmak her mermi icin gercekten belirleyici oluyor.
# MENZIL: asamalari asil ayiran sey.
#
# Difuzyon her yone yayilir; derisim 1/r^2 ile duser, uzakta hicbir sey
# ulasmaz - ancak BITISIKTE ise etkilidir. Yonlu bosaltma ayni kimyayi
# hedefe dogru bosaltir, seyrelme azalir, menzil artar. Filament fiziksel
# olarak UZANIR. T6SS ve stilet TEMAS ister. Nematosist firlatir.
CARRIER_REACH = [45.0, 170.0, 320.0, 35.0, 35.0, 700.0, 500.0, 400.0, 600.0]
CONTACT_ONLY = (3, 4)     # T6SS ve stilet: bitisik olmadan calismaz
STYLET_INDEX = 4          # stilet oldurmez, EMER (mizositoz)

# ------------------------------------------------------------ ENERJI BEDELI
#
# Enerji gerektiren HER surece bedel: yapiyi kurmak, ates etmek, yuku
# sentezlemek, proteini acmak, hareket etmek.
#
# Gercekteki karsiliklari:
#   - Nematosist 150 atm ozmotik basinc yukler ve TEK KULLANIMLIKTIR;
#     her atistan sonra yenisi insa edilir. En pahali silah budur.
#   - T6SS kasilan kilifi ClpV ATPazi ile SOKUP yeniden kurar - tekrar
#     kullanilabilir ama her atis ATP yakar.
#   - Stilet hucre iskeletiyle itilir; uzatildigi surece maliyet surer.
#   - Difuzyon en ucuzu: makine yok, sadece molekulu salarsin.
#
# (kurulum/sn bakim, atis basina, tek kullanimlik mi)
CARRIER_COST = [
    (0.2,  0.5,  False),   # 1 Difuzyon
    (0.6,  1.2,  False),   # 2 Yonlu bosaltma
    (1.2,  3.0,  False),   # 3 Fiskirtma
    (4.0,  8.0,  False),   # 4 T6SS  - kilif yeniden kurulur (ClpV ATPaz)
    (3.0,  4.0,  False),   # 5 Stilet - uzatma + emis suresince maliyet
    (10.0, 25.0, True),    # 6 Penetrant - 150 atm yukleme, TEK KULLANIMLIK
    (7.0,  14.0, True),    # 7 Volvent   - delmez, daha ucuz
    (5.0,  10.0, True),    # 8 Glutinant - en ucuz nematosist
    (6.0,  12.0, True),    # 9 Izoriza   - hareket icin
]
STYLET_FEED_COST = 2.0     # emis surerken saniyelik gider

# Yuk sentezi kutleyle orantili. Katalitik toksinler AYRICA bagisiklik
# proteini ister - uretici kendi DNA'sini parcalamasin diye. Bu bir ek
# gen ve ek bakim demektir; por toksinleri bundan muaftir cunku hucre
# disinda, hedefin zarinda calisirlar.
PAYLOAD_SYNTH_PER_KDA = 0.15
IMMUNITY_SURCHARGE = 0.6          # katalitik yuklerde sentez ustune oran
CATALYTIC = ('sabotaj', 'duvar_eri')

# ACMA BEDELI: protein katlanmis halde lumenden gecmez. T3SS'te efektorleri
# acik tutan SAPERONLAR ve onlari igneye besleyen bir ATPaz vardir. Acilma
# kendiliginden olmaz - enerji ve ayri bir makine ister.
UNFOLD_PER_KDA = 0.08
MOVE_COST = 0.25                  # ok tusuyla her adim (yuzmek bedava degil)

# METABOLIZMA GELIRI: bakim giderini ekledim ama GELIR tarafini koymamistim -
# nematosist secili bir saldirgan 10 saniyede sifirlaniyor ve bir daha hicbir
# sey atesleyemiyordu. Gercek oyunda enerji besinden gelir; laboratuvarda
# besin olmadigi icin sabit bir metabolik gelir gerekiyor.
BASE_REGEN = 25.0

# ---------------------------------------------------------------- DOZ-TEPKI
#
# Ayni molekul, farkli MIKTARDA farkli sey yapar. Toksikolojinin temeli budur:
# esigin altinda hicbir sey, biraz ustunde islev bozulmasi, daha ustunde felc,
# en ustunde olum. Difuzyonla ortama sacan biri ile hedefin icine enjekte eden
# birinin ayni sonucu vermesi anlamsizdi.
#
# Cizilen her nokta BIR MOLEKULDUR. Arka planda "yogunluk" diye bir sayi
# yoktur; doz, hedefe FIILEN VARAN molekullerin SAYISIDIR. Bunun iki
# kazanimi var: molekulun yolunu gozle takip edebiliyoruz, ve "1 tanesi
# varirsa su olur, 3 tanesi varirsa su olur" gibi okunur bir esik sistemi
# kurabiliyoruz.
#
# Difuzyonun zayifligi artik bir KATSAYIDAN degil GEOMETRIDEN geliyor:
# 180 dereceye sacilan 26 molekulun ancak birkaci hucrenin gordugu aciya
# denk gelir. Fiskirtma ayni 26 molekulu 8 derecelik bir jete sikistirir.
CARRIER_EMIT = [26, 26, 26, 12, 12, 12, 0, 0, 0]     # atis basina molekul
CARRIER_SPREAD = [180.0, 32.0, 8.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # yari-aci
MOLECULE_SPEED = 150.0
MOLECULE_LIFE = 9.0
# VISKOZ SURTUNME: dusuk Reynolds rejiminde molekul atildigi hizi korumaz,
# ustel olarak yavaslar. MENZIL bunun sonucudur - ayrica uygulanan bir
# kural degil. Mermi yaratmayan molekuler tasiyicilarda eski menzil
# kontrolu hic calismiyordu; molekuller 900 px ucup gidiyordu.
MOL_DRAG = 0.15                      # bir saniye sonra kalan hiz orani
_DRAG_K = -math.log(MOL_DRAG)        # menzil = v0 / _DRAG_K
# ISIL CALKANTI: molekul asla durmaz. Surtunme YONLU hizi sondurur ama
# Brown hareketi sicakligin kendisidir - sonmez. Ilk denemede sekme hizin
# %90'ini yok ediyordu, yani tek carpisma molekulu olduruyordu ve hicbiri
# delik arayacak kadar yasamiyordu. Menzil, yonlu hizin ISIL tabana
# inmesiyle biter; molekul orada yok olmaz, sadece artik yon tutmaz.
THERMAL = 240.0
# Isil bilesenin YON HAFIZASI ne kadar surer. Ilk denemede isil hiz sabit
# bir buyukluk olarak eklenmisti ama yonu korudugu icin molekul bir kez
# sekince duz bir cizgide sonsuza gidiyordu - o difuzyon degil, savrulma.
# Gercek Brown hareketinde yon surekli yeniden ornekleniyor.
TUMBLE = 0.09

# YUZEYE TUTUNMA: gecemeyen molekul savrulup gitmez, arayuzde kalir ve
# yuzey boyunca SUPURUR. Gercekte bir molekul gozenekli bir yuzeye saniyede
# milyarlarca kez carpar; simulasyonda karede bir kez deneyebiliyoruz, o
# yuzden temas suresince teget kayarak ayni isi yapiyor. Gorsel olarak da
# istedigimiz sey bu: molekulun duvar boyunca kayip bir delige kayivermesi
# EKRANDA izlenebiliyor.
HUG_TIME = 0.55

# ------------------------------------------------------- GERCEK GOZENEKLER
#
# Elek artik "cap <= mesh" karsilastirmasi degil: her katmanin GERCEK
# delikleri var ve molekul onlardan birini BULMAK zorunda. Elektron
# mikroskobundan bakiyormus gibi - cizilen geometri fizigin kendisidir.
#
# mesh molekul-capi birimindedir (molekuller 1.1 - 3.1 arasi). Ekranda
# gormek icin piksele cevirmek gerekiyor:
# Olcek 4.6 iken molekuller 5-15 px kaliyordu; tam sayiya yuvarlanan
# yaricaplar 5.1 px'lik peptit ile 6.1 px'lik norotoksini ayni gosteriyordu.
# Bu carpan HEM delikleri HEM molekulleri olcekler - buyutmek oranlari
# bozmaz, yalnizca cozunurlugu artirir.
PORE_PX = 7.0
PORE_COL = (19, 25, 42)      # delik: elektron-gecirgen, koyu gorunur

# DUZEN: katmanin yapisi ne kadar kristalimsi?
#   S-layer gercekte iki boyutlu bir PROTEIN KRISTALIDIR - delikleri
#   duzenli bir orgu olusturur, ust uste de hizalanir. Mukus ise rastgele
#   bir jeldir: delikleri dagiiniktir ve alt tabakalari hizalanmaz, bu
#   yuzden molekul dolambacli bir yol izlemek zorunda kalir.
LAYER_ORDER = {'Mukus': 0.0, 'Kapsul': 0.18, 'S-layer': 1.0,
               'Duvar': 0.45, 'Hucre zari': 1.0}

# Bir katman kalinligi boyunca kac ALT TABAKA? Kalin ve ince delikli bir
# katman cok tabakalidir; molekul her birinde ayri bir delik bulmalidir.
# Bu, eski porosity^(t/mesh) formulunun geometrik karsiligidir.
MAX_SHEETS = 4
BOUNCE_TRAP = 26          # bu kadar carpip gecemeyen molekul sikisti sayilir


class Sheet:
    """Bir katmanin kalinligi icindeki TEK bir gozenekli tabaka."""

    __slots__ = ('r', 'pores', 'solid')

    def __init__(self, r, pores, solid):
        self.r = r
        self.pores = pores        # [(merkez_aci, genislik_px), ...]
        self.solid = solid        # delik yok - hicbir sey gecemez

    def opening_for(self, ang, dia_px):
        """Bu acida, bu capa yetecek bir delik var mi?"""
        if self.solid:
            return False
        for a, w in self.pores:
            if w < dia_px:
                continue
            d = abs((ang - a + math.pi) % (2 * math.pi) - math.pi)
            if d * self.r <= (w - dia_px) * 0.5:
                return True
        return False

# ESIKLER: kac molekul VARIRSA ne olur. (dusuk, orta, olumcul)
# alfa-hemolizin'in 7'si gercek bir sayidir: yedi monomer birlesip BIR
# gozenek olusturur. Bir gozenek sizdirir, ikisi sisirir, dordu patlatir.
# Sayilar olculerek ayarlandi: difuzyon ~7, yonlu bosaltma ~21, fiskirtma
# ~26, enjeksiyon ~12 molekul ulastiriyor. Esikler oyle secildi ki HER
# tasiyici farkli bir kademeye dussun - aksi halde (norotoksin ilk denemede
# 1/2/4 idi) difuzyon bile oldurup butun gradyani yok ediyordu.
PAYLOAD_THRESHOLD = {
    'Norotoksin':            (3, 8, 16),   # molekul basina en etkilisi
    'Antimikrobiyal peptit': (6, 15, 30),  # zayif, cok gerekir
    'Amoebapor':             (4, 11, 22),
    'Lizozim':               (4, 11, 22),  # katalitik ama molekul basina zayif
    'alfa-hemolizin':        (7, 14, 28),  # 7 monomer = 1 gozenek (gercek sayi)
    'T3SS efektoru':         (1, 3, 6),    # sadece enjeksiyonla varabilir
    'Perforin':              (6, 14, 28),
}

# TEMIZLENME: baglanan molekul sonsuza kadar orada durmaz - hucre onarir,
# pompalar disari atar. Bagli molekul suresi dolunca EKRANDAN da silinir;
# boylece gorunen nokta sayisi ile sayac her an birebir ayni kalir.
# Etkiler geri alinmaz: kademe bir kez yukseldiyse hasar olmustur.
CLEARANCE = 16.0

# STOK: molekuller firlatilmadan ONCE de fiziksel olarak vardir - hucrenin
# icinde tasinirlar. Bu sadece susleme degil: hucre patlarsa bu stok
# oldugu gibi ortama sacilir ve cevresine ne yaptigi gozle gorulur.
STOCK_MAX = 44
STOCK_REGEN = 9.0        # molekul / saniye (sentez hizi)

# ORGANELLERIN LABA BAGLANMASI
#
# logic_membrane'de zaten wall/outer/capsule/efflux/repair savunmalari var
# ve bunlar lab'in katmanlariyla birebir ortusuyor. Iki ayri "duvar"
# kavrami tutmak yerine zar organi lab'in ZIRHINI SURUYOR.
DEFENCE_PER_POINT = 0.45   # bir savunma puani kac kalinlik birimi ekler
EFFLUX_GAIN = 0.28         # efflux+onarim molekul temizligini ne kadar hizlandirir
ESCAPE_BASE = 22.0         # motorsuz hedefin kacis hizi
ORGAN_ALPHA = 150          # organ katmaninin saydamligi

# SITOSTOM
#
# Agzin acisal yari genisligi. Bu pencereye giren molekul yutulur.
MOUTH_HALF = math.radians(20)
# Kesenin sitoplazmaya inip sindirilmesi
KESE_HIZ = 48.0            # px/sn iceri dogru (siklozis)
KESE_SINDIRIM = 4.5        # sn - bu surede kucululup kaybolur

# FAGOSITOZ SERT YUZEYDE OLMAZ.
#
# Kadehin olusabilmesi icin zarin esneyip parcacigi sarmasi gerekir; sert
# bir peptidoglikan duvar ya da kristal S-layer buna izin vermez. Bakterinin
# yutmamasinin, okaryotun duvari birakmasinin standart aciklamasi budur.
SERT_KATMANLAR = ('Duvar', 'S-layer')
SERT_ESIK = 1.0            # bu kalinligin ustunde katman SERT sayilir

# ORGANIN ZARFTAKI YERI
#
# Once butun dis organlar zarfin EN USTUNE ciziliyordu - mukusun uzerinde
# duruyorlardi. Gercekte bakteride hemen hicbir makine disariya yapisik
# degildir; neredeyse hepsi IC ZARA cakilidir ve disari dogru UZANIR:
#
#   Kemoreseptor (MCP)  : zari boydan boya gecer; algilama ucu periplazmada,
#                         sinyal ucu SITOPLAZMADA. Disariya cikmaz.
#   Mekano/Fotoreseptor : ayni sekilde zar proteinleri.
#   Kamci               : MS halkasi IC ZARDA, cubuk duvari deler, P halkasi
#                         duvarda, L halkasi dis zarda; yalnizca FILAMENT
#                         disarida. Yani zarfi bastan sona geciyor.
#   T6SS / zipkin       : tabani ic zarin SITOPLAZMA yuzunde, kilifi
#                         sitoplazmada; atesleyince boru disari firlar.
#   Nematosist          : ateslenene kadar TAMAMEN sitoplazmada duran bir
#                         kapsuldur - ipligi bosalinca disari cikar.
#   Stilet              : sitoplazmadan iskeletle itilen bir boru.
#
# (capa katmani, zarfi kesip disari uzaniyor mu)   None = sitoplazma
ORGAN_CAPA = {
    'Chemoreceptor':   ('Hucre zari', False),
    'Mechanoreceptor': ('Hucre zari', False),
    'Photoreceptor':   ('Hucre zari', False),
    'Flagella':        ('Hucre zari', True),
    'Cilia':           (None,         True),
    'Stylet':          (None,         True),
    'Harpoon':         (None,         True),
    'Nematocyst':      (None,         False),   # atesleninceye kadar iceride
    'Toxin':           ('Hucre zari', True),
    'Lysin':           ('Hucre zari', True),
    'Phagocytosis':    (None,         True),    # sitostom: agiz zarfi keser
    'Membrane':        ('Hucre zari', False),
    'Cytoplasm':       (None,         False),
    'Vacuole':         (None,         False),
    'Cytoskeleton':    (None,         False),
    'Ribosome':        (None,         False),
}
ESCAPE_PER_THRUST = 0.9    # itki basina eklenen kacis hizi
ALARM_PER_SENSOR = 0.55    # her receptor kacis suresini bu kadar uzatir

TIER_NONE, TIER_SLOW, TIER_MID, TIER_LETHAL = 0, 1, 2, 3
TIER_COLOR = [(120, 128, 145), (150, 200, 255), (255, 210, 120), (255, 110, 110)]

# ETKI SINIFI: her molekulun kendi merdiveni vardir. Tek bir "yavaslatma ->
# felc -> olum" merdivenini hepsine uygulamak yanlisti - gozenek acici bir
# peptit iyon kanali bloke etmez, zari sizdirir; lizozim siniri degil DUVARI
# cozer. Orta doz etkisi molekule gore bambaska bir seydir.
#
# sinif -> (dusuk doz, orta doz, olumcul) etiketleri ve orta dozun MEKANIGI
EFFECT_CLASS = {
    'norotoksin': (('yavaslama', 'FELC', 'olum'), 'paralyze',
                   'kanal blokeri - motor proteinleri durdurur'),
    'gozenek':    (('sizdiran zar', 'SISME', 'ozmotik lizis'), 'swell',
                   'zarda gozenek - su girer, hucre siser'),
    'litik':      (('duvar zayifladi', 'DUVAR INCELDI', 'duvar coktu'), 'weaken',
                   'duvari cozer - mekanik savunma duser'),
    'sabotaj':    (('metabolik yavaslama', 'UREME DURDU', 'ic cokus'), 'halt',
                   'nukleaz/NADaz - ic makineyi bozar'),
}

# ZARIN HANGI YUZUNDEN ETKI EDER?
#
# Zar ASIMETRIKTIR ve bu asimetri ATP harcayan flippazlarla aktif olarak
# korunur: iki yaprak farkli lipid tasir. Dolayisiyla taraf seciciligi
# molekulun NEYI TANIDIGINDAN gelir.
#
#   'dis' : yalnizca dis yuzden. alfa-hemolizin fosfokolin baslarina ve
#           ADAM10'a baglanir - ikisi de dis yaprakta. Perforin'in C2
#           domaini Ca-bagimlidir; sitozolde Ca ~100 nM, disarida ~1-2 mM,
#           on binde bir - baglanamaz. Bu bir kaza degil, guvenlik
#           mekanizmasi: sitotoksik hucre kendi perforiniyle olmesin diye.
#           Ayrica yerlesim yonludur (monomer -> halka -> beta-varil) ve
#           salgilanan toksinlerin disulfitleri indirgeyici sitoplazmada
#           acilir.
#   'her'  : iki yuzden de. Kucuk katyonik peptitlerin itici gucu basit yuk
#           cekimidir ve anyonik lipid iki yaprakta da bulunur.
#   'ic'   : yalnizca ic yuzden. Gercek ornegi gasdermin D: sitozolde
#           kesilir, IC YAPRAK lipidlerini (PIP2, PS) tanir ve iceriden
#           gozenek acar. Henuz boyle bir yukumuz yok ama yer hazir.
#
# Zar disi hedefler icin taraf kavrami anlamsizdir -> 'her'.
PAYLOAD_SIDE = {
    'Norotoksin':            'dis',   # kanalin DIS agzini tikar
    'Antimikrobiyal peptit': 'her',   # katyonik, yuk surucusu
    'Amoebapor':             'her',   # anyonik lipide baglanir
    'Lizozim':               'her',   # hedefi zar degil, duvar
    'alfa-hemolizin':        'dis',
    'T3SS efektoru':         'her',   # hedefi sitoplazma, yaprak yok
    'Perforin':              'dis',
}

# HIDROFOBIK UYUMSUZLUK
#
# "Zar yuzeyi" ile "zar ici" arasindaki fark buraya kadar yalnizca bir
# etiketti; olcum, ZONE_MODE'un 42 kombinasyonda yalnizca 3 sonucu
# degistirdigini gosterdi. Farki FIZIKSEL yapan sey su:
#
# Yuzeye baglanan molekul (norotoksin) cift katmana hic girmez - kanalin
# dis agzindaki bir reseptore yapisir, zar kalinligi onu ilgilendirmez.
# YERLESEN molekul (gozenek acicilar) ise zari bastan sona gecen bir yapi
# kurar ve bu yapinin boyu, cift katmanin hidrofobik cekirdegiyle
# ESLESMEK zorundadir. Uyusmazsa yerlesme enerjik olarak pahalidir ve
# gerceklesmez - buna hidrofobik uyumsuzluk denir, ve iki yonlu calisir:
# zar hem cok kalin hem cok ince olursa yerlesme bozulur.
#
# Sonuc: ZAR KALINLIGI gozenek acicilara karsi gercek bir savunma olur.
# Bedeli de var - ince zar mekanik delmeye karsi zayiftir (bariyer B*t).
#
# span : molekulun zari gecen parcasinin boyu (katman kalinligi birimi)
# tol  : uyumsuzluga tahammul. Toroidal gozenek kuran kucuk peptitler
#        esnektir; buyuk beta-varil kuranlar degildir.
PAYLOAD_SPAN = {
    'Antimikrobiyal peptit': 1.4,   # toroidal gozenek - lipidle birlikte buker
    'Amoebapor':             1.5,
    'alfa-hemolizin':        1.5,   # beta-varil, normal cift katmana uyumlu
    'Perforin':              1.9,   # MACPF, daha uzun - kolesterolce zengin
}                                   # (dolayisiyla daha KALIN) zara uyumlu
PAYLOAD_TOL = {
    'Antimikrobiyal peptit': 0.55,
    'Amoebapor':             0.42,
    'alfa-hemolizin':        0.25,
    'Perforin':              0.22,
}
INSERT_TRIES = 5        # bu kadar denemeden sonra molekul yuzeyde takilir


def insertion_p(pi, zar_t):
    """Bu kalinliktaki zara yerlesme olasiligi."""
    nm = PAYLOADS[pi][0]
    span = PAYLOAD_SPAN.get(nm)
    if span is None or zar_t is None:
        return 1.0
    tol = PAYLOAD_TOL.get(nm, 0.3)
    mis = abs(zar_t - span) / span
    return math.exp(-(mis / tol) ** 2)


# Hangi yuk hangi sinifa girer
PAYLOAD_CLASS = {
    'Norotoksin':            'norotoksin',
    'Antimikrobiyal peptit': 'gozenek',
    'Amoebapor':             'gozenek',
    'alfa-hemolizin':        'gozenek',
    'Perforin':              'gozenek',
    'Lizozim':               'litik',
    'T3SS efektoru':         'sabotaj',
}


def effect_class(pi):
    return PAYLOAD_CLASS.get(PAYLOADS[pi][0])


def tier_label(pi, tier):
    """Bu MOLEKUL icin bu dozun etiketi."""
    if tier == TIER_NONE:
        return 'etki yok'
    cls = effect_class(pi)
    if cls is None:
        return ['etki yok', 'hafif', 'orta', 'agir'][tier]
    return EFFECT_CLASS[cls][0][tier - 1]


def count_tier(pi, n):
    """Kac molekul vardi -> hangi kademe. Doz artik bir SAYIM."""
    th = PAYLOAD_THRESHOLD.get(PAYLOADS[pi][0])
    if not th or n <= 0:
        return TIER_NONE
    if n >= th[2]:
        return TIER_LETHAL
    if n >= th[1]:
        return TIER_MID
    if n >= th[0]:
        return TIER_SLOW
    return TIER_NONE


def payload_cost(payload):
    nm, z, kda, d, eff, col, ch, slf = payload
    if z is None:
        return 0.0, 0.0
    synth = kda * PAYLOAD_SYNTH_PER_KDA
    imm = synth * IMMUNITY_SURCHARGE if eff in CATALYTIC else 0.0
    return synth, imm


def unfold_cost(payload, carrier_params):
    """Yuk bir LUMENDEN geciyorsa acilmasi gerekir - bu bedava degil."""
    nm, z, kda, d, eff, col, ch, slf = payload
    if z is None or carrier_params is None:
        return 0.0
    if carrier_params.get('diameter') is None:
        return 0.0          # molekuler teslimat: kanal yok, acilma yok
    return kda * UNFOLD_PER_KDA


def shot_total_cost(ci, pi):
    build, shot, once = CARRIER_COST[ci]
    synth, imm = payload_cost(PAYLOADS[pi])
    unf = unfold_cost(PAYLOADS[pi], CARRIERS[ci][1])
    return shot + synth + imm + unf, dict(atis=shot, sentez=synth,
                                          bagisiklik=imm, acma=unf)
DRAIN_RATE = 0.16         # saniyede emilen sitoplazma orani

CARRIERS = [
    # 1-3 hepsi MOLEKULER teslimattir: yuk KENDI capiyla gider, delmeyi
    # kendi yapar. Aralarindaki fark YON ve MENZIL - hicbiri delici degil.
    ('1. Difuzyon',        dict(energy=0.35, tip_area=0.30, diameter=None, attempts=1e6),
     'yon yok, seyrelir - sadece bitisikte etkili'),
    ('2. Yonlu bosaltma',  dict(energy=2.0,  tip_area=0.30, diameter=None, attempts=5e4),
     'hedef tarafa sikar - parfum gibi, koni halinde'),
    ('3. Fiskirtma',       dict(energy=8.0,  tip_area=0.30, diameter=None, attempts=1e4),
     'molekulleri hedefe DOGRU firlatir - daha uzak, daha derisik'),
    # 4-6 gercek DELICILER
    ('4. T6SS mizragi',    dict(energy=140.0, tip_area=0.70, diameter=6.0, attempts=1),
     'kasilmali tup - kilifa BAGLI kalir, temas ister'),
    ('5. Stilet',          dict(energy=110.0, tip_area=0.40, diameter=5.0, attempts=1),
     'UZATILIR, firlatilmaz - govdeye bagli, dar lumen'),
    # 6-9: NEMATOSIST'in dort tipi. Evrimde birine RASTGELE gecilir.
    # Dordunden yalnizca biri zehir tasir; otekiler tutar, yapistirir,
    # ya da hic avlanmaz - savunma ve HAREKET icin kullanilir.
    ('6. Nematosist: penetrant', dict(energy=400.0, tip_area=1.20, diameter=9.0, attempts=1),
     'stenotel - deler ve yuku enjekte eder'),
    ('7. Nematosist: volvent',   dict(energy=120.0, tip_area=2.40, diameter=9.0, attempts=1),
     'desmonem - DELMEZ, ipligini ava SARAR, hareketsiz birakir'),
    ('8. Nematosist: glutinant', dict(energy=90.0,  tip_area=2.80, diameter=9.0, attempts=1),
     'YAPISKAN - delmez, yuzeye tutunur, sonraki atislari garantiler'),
    ('9. Nematosist: izoriza',   dict(energy=150.0, tip_area=2.00, diameter=9.0, attempts=1),
     'avlanma DEGIL - tutunup kendini ceker (hareket organi)'),
]

# Zehirsiz nematosist tipleri: delme yerine TUTMA isi gorurler
VOLVENT, GLUTINANT, ISORHIZA = 6, 7, 8

# Duvarin eleme siniri belgede ~22-24 kDa, gozenek capi 2.2 birim.
# Cap kutleyle degil KUTLENIN KUP KOKUYLE olceklenir (hacim ~ kutle):
#     cap = MESH_REF * (kDa / KDA_REF)^(1/3)
# Boylece 23 kDa tam sinirda kalir ve tablodaki her molekul belgedeki
# "duvari gecer mi" sutunuyla kendiliginden tutarli olur.
KDA_REF = 23.0
MESH_REF = 2.2


def dia_from_kda(kda):
    """KATLANMIS cap: gozenekten suzulurken gecerli olan."""
    return MESH_REF * (max(0.01, kda) / KDA_REF) ** (1.0 / 3.0)


# --- LUMEN: tasiyicinin ic kanali ---
#
# Enjekte edilen protein KATLANMIS halde gecmez, ACILIR. T3SS efektorleri
# ignenin ~2.5 nm lumeninden gecebilmek icin lineer hale getirilir; sistemin
# calisma sebebi budur. Bu yuzden yukun IKI capi vardir:
#
#   dia_folded : gozenekten suzulurken (yukarida, kDa'nin kup koku)
#   dia_chain  : lumenden gecerken - acilmis zincirin kesiti
#
# Acilmis bir polipeptit zinciri kutleden bagimsiz olarak incedir; buyuk
# proteinlerde biraz artar cunku bazi alanlar acilmaya direnir.
CHAIN_BASE = 0.90
CHAIN_PER_KDA = 0.004

# tip_area enerji formulunun birimlerinde, yuk capi ise duvar gozenegine
# kalibre. Ikisini baglamak icin ACIK bir olcek sabiti gerekiyor - bunu
# turetilmis gibi gostermek yerine kalibrasyon oldugunu soyluyoruz.
# 1.55 iken guclu stilet norotoksini bile kil payi tasiyamiyordu (zincir 0.92
# vs lumen 0.917) - kisit anlamli olmaktan cikip felc edici oluyordu.
# 1.75'te sivri uc kucuk/orta yukleri tasiyor ama en buyuklerini tasimiyor:
# gercek bir odunlesim, kullanilamaz bir tasiyici degil.
LUMEN_SCALE = 1.75


def dia_chain(kda):
    """Acilmis zincirin kesiti - lumenden gecerken gecerli olan."""
    return CHAIN_BASE + CHAIN_PER_KDA * max(0.0, kda)


def lumen_of(tip_area):
    """Tasiyicinin ic kanal capi.

    Sivri uc (kucuk kesit) daha iyi deler ama icine daha az sey sigar.
    Gercek bir muhendislik gerilimi: en iyi delici en kotu tasiyicidir.
    """
    return LUMEN_SCALE * math.sqrt(max(0.01, tip_area))


# KENDI HEDEFINI BULABILIR MI?
#
# Kucuk molekul nereye birakilirsa birakilsin difuzyonla hedefine varir -
# sitoplazmaya birakilan bir gozenek acici zara birkac yuz nanometre
# uzaktadir ve savrularak oraya ulasir. Buyuk molekul bunu yapamaz: hem
# yavas difuze olur hem de baglanacagi reseptor yanlis tarafta kalir.
#
# Esik ~20 kDa: duvarin eleme sinirinin biraz altinda.
# Bir molekul disariya birakilsa da hedefine varir mi? Belirleyici olan
# BOYUT degil, HEDEFIN NEREDE oldugudur. Yuzeyde is goren molekuller
# (gozenek acicilar, kanal blokerleri, duvar enzimleri) disariya
# birakildiginda da hedefine varir: baglandiklari yapi zaten distadir ve
# baglanma afinitesi onlari oraya ceker. Perforin 67 kDa ile listenin en
# irisidir ama zari GECMESI gerekmez - ustune oturur. Nukleaz ondan
# kucuktur ama substrati sitoplazmadadir, gecmek ZORUNDADIR. Igneli
# salgi sistemlerinin var olma sebebi tam olarak bu tek satirdir.
#
# NOT: 'hedefini bulur' demek 'her engeli asar' demek DEGILDIR. Molekul
# yine de katmanlarin ELEGINDEN gecmek zorundadir - alfa-hemolizin zara
# oturmak ISTER ama capi duvar gozeneginden buyukse duvarda takilir.
SURFACE_ACTING = {Z_SURFACE, Z_WALL, Z_MEMBRANE}

# (ad, hedef bolge, kDa, etki, renk)
_PAYLOAD_DEFS = [
    ('Yok (saf mekanik)',      None,       0,  None,        (150, 150, 160)),
    ('Norotoksin',             Z_SURFACE,  5,  'felc',      (255, 220, 120)),
    ('Antimikrobiyal peptit',  Z_MEMBRANE, 3,  'gozenek',   (150, 230, 255)),
    ('Amoebapor',              Z_MEMBRANE, 8,  'gozenek',   (150, 230, 255)),
    ('Lizozim',                Z_WALL,     14, 'duvar_eri', (255, 190, 110)),
    ('alfa-hemolizin',         Z_MEMBRANE, 33, 'gozenek',   (150, 230, 255)),
    ('T3SS efektoru',          Z_CYTO,     50, 'sabotaj',   (220, 130, 255)),
    ('Perforin',               Z_MEMBRANE, 67, 'gozenek',   (150, 230, 255)),
]
# (ad, bolge, kDa, katlanmis_cap, etki, renk, zincir_capi)
# (ad, bolge, kDa, katlanmis_cap, etki, renk, zincir_capi, kendi_hedefini_bulur)
PAYLOADS = [(nm, z, k, dia_from_kda(k) if z else 0.0, e, c,
             dia_chain(k) if z else 0.0, z in SURFACE_ACTING)
            for nm, z, k, e, c in _PAYLOAD_DEFS]
PAYLOAD_KEYS = 'QWERTYUI'

# ------------------------------------------------------------- BELIRTECLER
#
# Silahin ucuna takilan TANIMA modulu. Gercekte T3SS ignesinin ucundaki
# kompleks (IpaD+IpaB) tam olarak budur: konak zarindaki KOLESTEROLE ve
# CD44'e baglanir, translokon gozenegini kurar ve igne ona kenetlenir.
# Igne zari HIC GECMEZ - durdugu yeri enerjisinin bitmesi degil, molekuler
# TANIMA belirler.
#
# Belirtecsiz silah saf BALISTIKTIR (nematosist gibi): nereye kadar giderse
# orada durur, bazen yetisemez bazen delip gecer.
#
# Belirtec bir KATMANI tanir - bolgeyi degil. Gercekte de oyledir: tanima
# alani belirli bir molekule baglanir ve o molekul belirli bir katmandadir.
#
# TUTUNMA GUCU: molekuler tanima ANLIK DEGILDIR, bagin kurulmasi icin kalis
# suresi gerekir. Cok hizli giden mermi, belirtec isini bitiremeden bir
# sonraki katmana gecer. Kanonik ornek lokosit yuvarlanmasi: akyuvarlar
# damar duvarina selektinlerle tutunur ama yuksek akista tutunamazlar.
# Bell modeli: bagin omru uygulanan kuvvetle USTEL olarak azalir.
#
# Basarisiz deneme bedava degildir: bag kisa sureligine kuruldu ve koparildi,
# bu gercek bir istir - mermi bir miktar yavaslar.
#
# (ad, tanidigi katman, renk, tanidigi molekul, tutunma gucu)
MARKERS = [
    ('Yok (balistik)',      None,         (150, 150, 160), 'tanima yok',              0.0),
    ('Polisakkarit tan.',   'Kapsul',     (150, 255, 190), 'kapsul sekerleri',       45.0),
    ('S-layer tanıyıcı',    'S-layer',    (220, 220, 140), 'kristal yuzey proteini', 70.0),
    ('Peptidoglikan tan.',  'Duvar',      (255, 200, 120), 'duvar peptidoglikani',   95.0),
    ('Kolesterol tanıyıcı', 'Hucre zari', (255, 150, 210), 'IpaB gibi - zar steroli', 60.0),
]
# Basarisiz tutunma denemesinin goturdugu enerji orani (tutunma gucunun kati)
GRIP_FAIL_LOSS = 0.35
MARKER_KEYS = 'ZXCVB'


GRAB_LABEL = {6: 'sardi', 7: 'yapisti', 8: 'tutundu'}

# Sonuc turlerinin TEK merkezi tablosu. Daginik sozlukler yeni bir sonuc
# eklendiginde birer birer unutuluyordu (KeyError); artik hepsi burada.
OUTCOME_STYLE = {
    SIEVE:      ('ELEK',   INFO,             (10, 60, 90)),
    BREACH:     ('YARDI',  ACCENT,           (10, 70, 45)),
    BLOCKED:    ('DURDU',  BAD,              (110, 10, 10)),
    GLANCE:     ('SEKTI',  WARN,             (120, 70, 0)),
    DOCK:       ('KENET',  (255, 150, 210),  (95, 25, 70)),
    'sardi':    ('SARDI',  (235, 225, 170),  (90, 80, 20)),
    'yapisti':  ('YAPIS',  (200, 235, 140),  (60, 90, 25)),
    'tutundu':  ('TUTUN',  (180, 210, 245),  (30, 55, 95)),
}


def outcome_style(outcome):
    return OUTCOME_STYLE.get(outcome, ('?', FG, (60, 60, 60)))


class GrabRecord:
    """Zehirsiz nematosist: delme yok, TUTMA var."""

    def __init__(self, layer, ci):
        self.layer = layer
        self.outcome = GRAB_LABEL[ci]
        self.energy_before = self.energy_after = self.required = 0.0
        self.probability = 1.0
        self.penetration = 0.35
        self.passed = False


class DockRecord:
    """Belirtec kenetlenmesi - delme formulune hic girilmedi."""

    def __init__(self, layer):
        self.layer = layer
        self.outcome = DOCK
        self.energy_before = self.energy_after = self.required = 0.0
        self.probability = 1.0
        self.penetration = 0.5
        self.passed = False


class GlanceRecord:
    """Sekme kaydı — delme formülüne hiç girilmedi."""

    def __init__(self, layer, angle):
        self.layer = layer
        self.outcome = GLANCE
        self.angle = angle
        self.energy_before = self.energy_after = self.required = 0.0
        self.probability = 0.0
        self.passed = False


class Shot:
    def __init__(self, cell, pos, direction, carrier, payload, marker=None,
                 carrier_index=None):
        self.cell = cell
        self.pos = pygame.math.Vector2(pos)
        self.dir = pygame.math.Vector2(direction).normalize()
        self.carrier_name, cparams, _ = carrier
        self.payload = payload
        pname, zone, kda, pdia, eff, pcol, pchain, pself = payload

        # LUMEN KONTROLU: yuk tasiyicinin ic kanalindan gecebiliyor mu?
        # Gecemiyorsa mermi YUKSUZ gider - sadece mekanik hasar verir.
        # Lumen kisiti yalnizca DELICI tasiyicilar icin: molekuler teslimatta
        # (1-3) yuk bir kanaldan gecmiyor, dogrudan ortama birakiliyor.
        self.lumen_blocked = False
        if zone is not None and cparams.get('diameter') is not None:
            if pchain > lumen_of(cparams['tip_area']):
                self.lumen_blocked = True

        prm = dict(cparams)
        if prm.get('diameter') is None:
            # MOLEKULER teslimat: yuk KENDI capiyla gider. Tasiyici yalnizca
            # yonu ve menzili degistirir, delmeyi yuk kendi yapar.
            prm['diameter'] = max(0.5, pdia)
        self.pen = Penetrator(self.carrier_name, **prm)

        self.e0 = self.pen.energy
        self.speed = self._v(self.pen.energy)
        # HIZ OLCEGI. Mermi hizi laboratuvar hucresi (cekirdek 110 px)
        # icin secildi: 560 px/sn = karede 18.7 px. Oyun hucresi 22 px
        # yaricapli - mermi bir karede hucrenin obur tarafindan cikip
        # yuku DISARIDA birakiyordu. Molekuller zaten geometriyle ayni
        # oranda yavasliyordu (hiz_olcegi); mermi de oyle.
        self.vs = float(getattr(cell, 'hiz_olcegi', 1.0))
        self.layer_idx = -1
        self.log = []
        self.dead = False
        self.glanced = False
        self.impact_angle = None
        self.trail = [pygame.math.Vector2(pos)]
        self.delivered = None
        self.miss_reason = None
        self.embed_r = None      # gomulup duracagi yaricap
        # Sitoplazmaya girdikten sonra kat edecegi mesafe. Merkeze YAKINLIK
        # testi egik yorungede hic tetiklenmiyordu - mermi butun katmanlari
        # gecip hucreyi bastan sona delip cikiyordu. Oysa sitoplazma dusuk
        # Reynolds rejiminde son derece viskozdur: iceri giren durur.
        self.cyto_travel = None
        self.feeding = False
        # BELIRTEC: hangi katmana kenetlenecek. None = balistik.
        self.marker = marker or MARKERS[0]
        mlayer = self.marker[1]
        self.grip = self.marker[4]
        self.grip_failed = False
        self.dock_p = None       # son kenetlenme denemesinin olasiligi
        self.dock_E = None
        self.marker_target = None
        if mlayer is not None:
            for i, l in enumerate(cell.active()):
                if l.name == mlayer:
                    self.marker_target = i
                    break
        self.docked = False
        self._pi = PAYLOADS.index(payload)
        self.released = []       # bu merminin ortama biraktigi molekuller
        self._pending = False    # yuk birakilmayi bekliyor
        # MENZIL: hedefin dis yuzeyine olan mesafe tasiyicinin erisimini
        # asiyorsa atis bosa gider. Difuzyon seyrelir, temas silahi ulasamaz.
        self.out_of_reach = False
        self.ci = carrier_index if carrier_index is not None else 0
        self.origin = pygame.math.Vector2(pos)
        self.reach = CARRIER_REACH[self.ci] if carrier_index is not None else 1e9
        gap = self.pos.distance_to(cell.center) - cell.outer_r
        self.gap_at_fire = gap
        if gap > self.reach:
            self.out_of_reach = True
            self.dead = True

    @staticmethod
    def _v(e):
        return 40.0 + 26.0 * math.sqrt(max(0.0, e))

    def _band_kalinlik(self, idx):
        """Bandin piksel kalinligi - ZARFIN olceginden (boundaries).
        `layer.t * PX_PER_UNIT` oyun hucresinde bes kat fazlaydi."""
        bounds = self.cell.boundaries()
        if idx < 0 or idx >= len(bounds):
            return 0.0
        inner = bounds[idx + 1] if idx + 1 < len(bounds) else self.cell.core_r
        return max(0.0, bounds[idx] - inner)

    def _geometric_angle(self):
        """Çarpma açısı GEOMETRİDEN: hız ile yüzey normali arasındaki açı.

        Merkeze nişan alırsan 0 (dik çarpma). Kenara nişan alırsan 90'a
        yaklaşır ve sekme kaçınılmaz olur. Elle ayarlanan bir sayı değildir.
        """
        n = self.pos - self.cell.center
        if n.length() < 1e-6:
            return 0.0
        n = n.normalize()
        c = max(-1.0, min(1.0, (-self.dir).dot(n)))
        return math.degrees(math.acos(c))

    def update(self, dt):
        # Hucreye SAPLANMIS ya da EMEN mermi de hedefiyle birlikte hareket
        # eder; yoksa hedef kacarken igne havada asili kaliyor.
        if (self.feeding or self.docked or self.embed_r is not None
                or self.cyto_travel is not None):
            self.pos += self.cell.motion
        if self.dead:
            self._emit()    # guvenlik agi: baska bir yolla olduyse de biraksin
            return
        if self.feeding:
            self._emit()    # emen stilet yerinde durur, yukunu orada birakir
            return
        if self.cyto_travel is not None:
            # Sitoplazmada viskoz yavaslama
            if self.cyto_travel <= 0.5 * self.vs or self.speed < 12.0:
                self.dead = True
                self._emit()
                return
            step = self.speed * self.vs * dt
            self.cyto_travel -= step
            self.speed *= 0.965
            self.pos += self.dir * step
            # TASMA KORUMASI: sitoplazmada ilerleyen mermi hucreden
            # CIKAMAZ. Kare adimi cekirdege gore buyukse obur taraftan
            # firlayip yuku disarida birakiyordu; cekirdek sinirinda durur.
            _r = self.pos.distance_to(self.cell.center)
            if _r > self.cell.core_r * 0.9:
                _n = (self.pos - self.cell.center)
                if _n.length() > 1e-6:
                    self.pos = self.cell.center + _n.normalize() * self.cell.core_r * 0.9
                self.dead = True
                self._emit()
                return
            if len(self.trail) < 500:
                self.trail.append(pygame.math.Vector2(self.pos))
            return
        if self.embed_r is not None:
            # GOMULME: hedef derinlige yaklastikca yavasla ve orada dur.
            # Sabit carpanla yavaslatmak hedefe VARMADAN hizi sifirliyordu -
            # mermi kalinligin %60'ina girecekken %10'unda kaliyordu.
            remaining = self.pos.distance_to(self.cell.center) - self.embed_r
            if remaining <= 0.6 * self.vs:
                self.dead = True
                self._emit()
                return
            self.speed = max(18.0, remaining * 5.0)
            self.pos += self.dir * self.speed * self.vs * dt
            if len(self.trail) < 500:
                self.trail.append(pygame.math.Vector2(self.pos))
            return
        self.pos += self.dir * self.speed * self.vs * dt
        if len(self.trail) < 500:
            self.trail.append(pygame.math.Vector2(self.pos))

        d = self.pos.distance_to(self.cell.center)
        bounds = self.cell.boundaries()
        nxt = self.layer_idx + 1
        if nxt < len(bounds) and d <= bounds[nxt]:
            self._enter(nxt)

        if not self.cell.sinir_icinde(self.pos):
            self._deliver(max(0, self.layer_idx + (0 if self.glanced else 1)))
            self.dead = True

    def _enter(self, idx):
        acts = self.cell.active()
        layer = acts[idx]
        if self.impact_angle is None:
            self.impact_angle = self._geometric_angle()
        self.cell.alarm = 3.0        # saldiri algilandi: kacmaya calisir

        # ZEHIRSIZ NEMATOSISTLER delmez: dis yuzeye varinca isleri biter.
        # Dort tipten yalnizca penetrant zehir tasir; otekiler TUTAR.
        if idx == 0 and self.ci in (VOLVENT, GLUTINANT, ISORHIZA):
            self.log.append(GrabRecord(layer, self.ci))
            self.layer_idx = 0
            self.delivered = 0
            bounds = self.cell.boundaries()
            self.embed_r = bounds[0] - 0.35 * self._band_kalinlik(0)
            if self.ci == VOLVENT:
                self.cell.tethered = True
            elif self.ci == GLUTINANT:
                self.cell.sticky = True
            else:
                self.cell.pulling = self          # izoriza: kendini ceker
            return

        # BELIRTEC bu katmani TANIDI. Ama tanima ANLIK DEGIL: bagin
        # kurulmasi kalis suresi ister. Mermi cok hizliysa (enerjisi tutunma
        # gucunu asiyorsa) bag kurulmadan kopar ve mermi devam eder - yalnizca
        # basarisiz denemenin isi kadar yavaslayarak.
        # idx > 0 sarti vardi: laboratuvar hucresinin hep >= 2 katmani
        # oldugu icin fark edilmemisti. Oyunda cogu hucre CIPLAKTIR - zar
        # 0. katmandir - ve kolesterol belirteci hicbir zaman
        # kenetlenemiyordu. Tanima temasla olur; en dis katman da tanınır.
        if self.marker_target == idx and idx >= 0:
            # BELL MODELI. Yorumda zaten "bagin omru kuvvetle USTEL azalir"
            # yaziyordu ama uygulama sert bir esikti: enerji <= guc ise
            # kesin tutar, bir birim fazlaysa hic tutmaz. Sonucu, kenetlenme
            # penceresinin absurt derecede dar olmasiydi - T6SS icin duvar
            # kalinligi 4-6 arasi. Oyuncunun hedefin duvar kalinligi
            # uzerinde hicbir kontrolu yok, dolayisiyla belirtec kendi
            # hatasi olmadan ise yaramiyordu.
            #
            # Gercek molekuler tanima olasiliksaldir: bag kurulma sansi
            # uygulanan kuvvetle ustel olarak duser, ama SIFIRLANMAZ.
            self.dock_p = math.exp(-self.pen.energy / max(1e-6, self.grip))
            self.dock_E = self.pen.energy
            if random.random() < self.dock_p:
                self.log.append(DockRecord(layer))
                self.layer_idx = idx
                self.docked = True
                self._deliver(idx)
                bounds = self.cell.boundaries()
                self.embed_r = bounds[idx] - 0.5 * self._band_kalinlik(idx)
                return
            # Tutunamadi: bag koptu, bir miktar enerji goturdu
            self.grip_failed = True
            loss = self.grip * GRIP_FAIL_LOSS
            self.pen.energy = max(0.0, self.pen.energy - loss)
            self.speed = self._v(self.pen.energy)

        if (idx == 0 and not self.cell.sticky
                and not try_bite(layer, self.impact_angle, self.pen.tip_area,
                                 self.pen.energy, self.pen.attempts)):
            self.log.append(GlanceRecord(layer, self.impact_angle))
            self.glanced = True
            n = self.pos - self.cell.center
            if n.length() > 0:
                n = n.normalize()
                self.dir = (self.dir - 2 * self.dir.dot(n) * n).normalize()
            self.speed *= 0.55
            self.layer_idx = 0
            return

        # DIFUZYONLA gelen yuk etki edecegi katmana varinca ORADA KALIR.
        # Balistik tasiyici yuku yorungesinin SONUNDA birakir (nematosist
        # tupten enjekte eder), ama difuze olan molekul kendi hedefine
        # yerlesir ve icinden gecip gitmez.
        zone = self.payload[1]
        if (zone is not None and self.pen.attempts > 100
                and idx == zone_min_depth(zone, acts)
                and ZONE_MODE[zone] == 'tam'):
            step = cross_layer(self.pen, layer, E_REF, self.impact_angle, random)
            self.log.append(step)
            self.layer_idx = idx
            self._deliver(idx)
            self.dead = True
            return

        step = cross_layer(self.pen, layer, E_REF, self.impact_angle, random)
        self.log.append(step)
        self.layer_idx = idx
        if step.passed:
            self.pen.energy = step.energy_after
            self.speed = (self._v(self.e0) if step.outcome == SIEVE
                          else self._v(self.pen.energy))
            if idx == len(acts) - 1:
                # Son katman da gecildi: artik SITOPLAZMADAYIZ.
                self._deliver(len(acts))
                if self.ci == STYLET_INDEX:
                    # MIZOSITOZ: stilet oldurucu degil, BESLEYICIDIR.
                    # Vampyrella ve Pfiesteria pedunkulu delip sitoplazmayi
                    # emer; olum zehirden degil TUKENMEDEN gelir. Boru
                    # govdeye bagli kaldigi icin emis yolu da hazirdir.
                    self.feeding = True
                    self.cell.feeder = self
                    self.dead = False
                    self.cyto_travel = None
                    self.embed_r = None
                    return
                self.cyto_travel = min(self.cell.core_r * 1.3,
                                       10.0 + 0.5 * self.pen.energy)
        else:
            # Delemedi ama YUZEYDE DURMAZ: enerjisi oraninda gomulur.
            bounds = self.cell.boundaries()
            outer = bounds[idx]
            self.embed_r = outer - step.penetration * self._band_kalinlik(idx)
            self._deliver(idx)

    def _deliver(self, depth_reached):
        """Yuku ulasilan derinlikte BIRAK - molekul olarak.

        Burada artik doz hesaplanmiyor ve bolge kontrolu yapilmiyor. Igne
        yalnizca yuku bir DERINLIGE tasir; oradan sonrasini molekullerin
        kendi fizigi belirler. Hedef katmana kac tanesi varirsa doz odur.
        Eski 'tam/enaz derinlik' kapisi, off-by-one hatalarinin kaynagiydi.
        """
        if self.delivered is not None:
            return
        name, zone, kda, dia, eff, col, chain, surf = self.payload
        self.delivered = depth_reached
        if zone is None or eff is None:
            return
        if self.glanced:
            self.miss_reason = 'sekti - yuk birakilmadi'
            return
        if self.lumen_blocked:
            self.miss_reason = 'yuk lumenden gecmedi'
            return
        # Yuk merminin DURDUGU yerde birakilir, delme aninda degil.
        # Ikisi ayni sey degildi: igne zari deldigi anda r=122'deydi ama
        # sitoplazma r<110'da basliyor. Molekuller "derinlik 5" diye
        # kaydedilip geometrik olarak zarin DIS tarafinda doguyor, deliksiz
        # zardan geri sizip gidiyorlardi. Mermi hala yol alacaksa
        # (cyto_travel) beklenir; birakma noktasi ucun son konumudur.
        self._pending = True

    def _emit(self):
        """Bekleyen yükü merminin şu anki konumunda serbest bırak.

        Derinlik merminin sayacindan degil KONUMDAN turetilir; iki
        muhasebenin ayrisabildigi tek yer burasiydi.
        """
        if not self._pending:
            return
        self._pending = False
        for _ in range(CARRIER_EMIT[self.ci]):
            a = random.uniform(0, 2 * math.pi)
            sp = random.uniform(0.25, 0.9) * MOLECULE_SPEED * self.vs
            v = pygame.math.Vector2(math.cos(a), math.sin(a)) * sp
            m = Molecule(self.cell, self.pos, v, self._pi)
            m.depth = m.band()
            self.released.append(m)

    def draw(self, s, donustur=None, olcek=1.0):
        """Her tasiyici KENDI mermisiyle cizilir - hepsi ayni nokta degil.

        `donustur` verilirse dunya konumlari ekrana onunla tasinir (oyunun
        kamera gorunumu), `olcek` cizgi kalinligi/yaricap carpani. Lab
        ikisini de vermez - orada birebir eski cizim.
        """
        sv = float(getattr(self, 'vs', 1.0))     # mermi olcegi (hedef zarfina gore)
        ks = float(olcek) * sv                   # ekran olcegi
        def T(v):
            if donustur is None:
                return (int(v.x), int(v.y))
            q = donustur(v)
            return (int(q[0]), int(q[1]))
        def L(n):
            return max(1, int(round(n * ks)))
        p = T(self.pos)
        pcol = self.payload[5]
        dead = self.dead
        col = ((255, 150, 210) if self.docked else
               (ACCENT if not dead else (WARN if self.glanced else BAD)))
        ci = self.ci

        if len(self.trail) > 1 and ci not in (3, 4):
            # 3-4 govdeye BAGLI uzayan yapilar; ayrica iz cizmeye gerek yok
            pygame.draw.lines(s, (85, 95, 125), False,
                              [T(q) for q in self.trail], L(2))

        ang = math.atan2(self.dir.y, self.dir.x)
        cs, sn = math.cos(ang), math.sin(ang)

        def rot(dx, dy):
            # lab piksel ofsetleri mermi olcegiyle (vs) ve kamerayla kuculur
            return T(pygame.math.Vector2(self.pos.x + (dx * cs - dy * sn) * sv,
                                         self.pos.y + (dx * sn + dy * cs) * sv))

        if ci == 0:
            # DIFUZYON: dagilmis molekul bulutu
            rnd = random.Random(int(self.pos.x) // 7)
            for _ in range(9):
                s.set_at((p[0] + int(rnd.randint(-11, 11) * ks), p[1] + int(rnd.randint(-11, 11) * ks)), pcol)
            pygame.draw.circle(s, pcol, p, L(3))
        elif ci == 1:
            # YONLU BOSALTMA: parfum gibi. Cikistan itibaren genisleyen bir
            # KONI, seyrelerek dagilir - fiskirtma degil, sikma.
            travelled = self.origin.distance_to(self.pos)
            spread = 6 + travelled * 0.35
            rnd = random.Random(7)
            for k in range(34):
                t = rnd.random()
                dx = -travelled * t
                dy = rnd.uniform(-1, 1) * spread * (1.0 - t) ** 0.5
                fade = int(70 + 150 * (1.0 - t))
                cc = (min(255, pcol[0] * fade // 220), min(255, pcol[1] * fade // 220),
                      min(255, pcol[2] * fade // 220))
                pygame.draw.circle(s, cc, rot(dx, dy), L(2))
        elif ci == 2:
            # FISKIRTMA: molekulleri hedefe DOGRU firlatir. Bagli boru YOK -
            # dar, hizli, derisik bir jet. Yonlu bosaltmadan farki: dagilmiyor.
            travelled = min(90.0, self.origin.distance_to(self.pos))
            rnd = random.Random(11)
            for k in range(22):
                t = rnd.random()
                dx = -travelled * t
                dy = rnd.uniform(-1, 1) * (3 + t * 5)
                pygame.draw.circle(s, pcol, rot(dx, dy), L(3))
            pygame.draw.circle(s, (245, 240, 255), p, L(4))
        elif ci == 3:
            # T6SS: tup FIRLATILMAZ, kilifa bagli kalir - piston gibi.
            # Govdeye bagli govde + uc. Temas sartinin sebebi bu.
            o = T(self.origin)
            pygame.draw.line(s, (140, 158, 175), o, p, L(9))
            pygame.draw.line(s, (75, 90, 105), o, p, L(2))
            pygame.draw.polygon(s, (215, 220, 225),
                                [rot(12, 0), rot(-6, -7), rot(-6, 7)])
            pygame.draw.polygon(s, (90, 105, 120),
                                [rot(12, 0), rot(-6, -7), rot(-6, 7)], L(2))
        elif ci == 4:
            # STILET: FIRLATILMAZ, UZATILIR. Vampyrella ve Pfiesteria
            # pedunkulu gibi hucre iskeletiyle itilen, govdeye BAGLI bir yapi.
            # Menzili = uzayabildigi boy.
            o = T(self.origin)
            pygame.draw.line(s, (215, 208, 185), o, p, L(5))
            pygame.draw.line(s, (120, 114, 98), o, p, L(1))
            pygame.draw.polygon(s, (245, 240, 220),
                                [rot(14, 0), rot(2, -4), rot(2, 4)])
        elif ci == VOLVENT:
            # VOLVENT: dikensiz, duz, ELASTIK iplik - sarmal olarak ucar
            for k in range(7):
                t = k / 6.0
                pygame.draw.circle(s, (235, 225, 170),
                                   rot(-22 * t, 9 * math.sin(t * 7)), L(3))
            pygame.draw.circle(s, (245, 240, 200), p, L(5))
        elif ci == GLUTINANT:
            # GLUTINANT: yapiskan damla, arkasinda uzayan tel
            pygame.draw.line(s, (170, 210, 120), rot(-26, 0), p, L(3))
            pygame.draw.circle(s, (200, 235, 140), p, L(8))
            pygame.draw.circle(s, (90, 130, 60), p, L(8), L(2))
        elif ci == ISORHIZA:
            # IZORIZA: tutunma kancasi - avlanma degil, HAREKET
            pygame.draw.line(s, (180, 200, 235), rot(-24, 0), p, L(2))
            pygame.draw.polygon(s, (200, 220, 245),
                                [rot(9, 0), rot(0, -7), rot(0, 7)])
            pygame.draw.line(s, (200, 220, 245), rot(0, -7), rot(-8, -10), L(2))
            pygame.draw.line(s, (200, 220, 245), rot(0, 7), rot(-8, 10), L(2))
        else:
            # PENETRANT: dikenli tup + sarmal iz
            pygame.draw.line(s, (205, 195, 140), rot(10, 0), rot(-22, 0), L(5))
            for k in range(3):
                bx = -4 - k * 7
                pygame.draw.line(s, (225, 215, 165), rot(bx, 0), rot(bx - 5, -7), L(2))
                pygame.draw.line(s, (225, 215, 165), rot(bx, 0), rot(bx - 5, 7), L(2))
            pygame.draw.polygon(s, (240, 230, 180),
                                [rot(14, 0), rot(4, -5), rot(4, 5)])

        # yuk gostergesi: mermi ne tasiyor
        if self.payload[4] and not self.lumen_blocked and ci >= 2:
            pygame.draw.circle(s, pcol, rot(-2, 0), L(4))
        if dead and ci >= 3:
            pygame.draw.circle(s, col, p, L(8), L(2))


class Kese:
    """Fagositozla oluşan BESİN VAKUOLÜ.

    Konumu hucreye GORE saklanir (aci + yaricap), boylece hucre yuzerken
    kese de onunla tasinir - bagli molekullerdeki capa ile ayni gerekce.
    """

    __slots__ = ('cell', 'ang', 'r', 'pi', 'yas', 'teslim')

    def __init__(self, cell, ang, r, pi):
        self.cell = cell
        self.ang = ang
        self.r = r
        self.pi = pi
        self.yas = 0.0
        self.teslim = False

    @property
    def bitti(self):
        return self.teslim and self.yas > KESE_SINDIRIM

    def update(self, dt):
        # Sindirim ancak kese sitoplazmaya VARDIKTAN sonra baslar. Once
        # yolculuk da ayni sayaci yiyordu; duvarsiz hucrede yol 6.5 sn
        # suruyor, omur 4.5 sn idi - kese hedefe varamadan olup yukunu
        # hic teslim etmiyordu (yutulan 155, varan 0).
        hedef = self.cell.core_r * 0.45
        if self.r > hedef:
            self.r = max(hedef, self.r - KESE_HIZ * dt)
        elif not self.teslim:
            # FAGOZOM BIR TUZAKTIR. Kese asitlesir, lizozomla kaynasir ve
            # yukunu SINDIRIR. Yalnizca gozenek acici bir yuk keseyi delip
            # sitoplazmaya kacabilir - Listeria'nin listeriolizini tam
            # olarak bunun icindir. Otekiler yok edilir.
            #
            # Bu, ignelerin neden var oldugunu da acikliyor: T3SS/T6SS
            # yuku dogrudan sitoplazmaya birakarak keseyi ATLAR.
            self.teslim = True
            if effect_class(self.pi) == 'gozenek':
                self.cell.receive(self.pi)
                self.cell.kacan += 1
            else:
                self.cell.sindirilen += 1
        if self.teslim:
            self.yas += dt

    def konum(self):
        return self.cell.center + pygame.math.Vector2(
            math.cos(self.ang), math.sin(self.ang)) * self.r

    def draw(self, s):
        p = self.konum()
        k = max(0.0, 1.0 - self.yas / KESE_SINDIRIM)
        rr = int(4 + 9 * (k if self.teslim else 1.0))
        if rr < 2:
            return
        col = (PAYLOADS[self.pi][5] if not self.teslim else
               ((150, 230, 255) if effect_class(self.pi) == 'gozenek'
                else (150, 120, 90)))     # kacan mavi, sindirilen kahve
        yuz = pygame.Surface((rr * 2 + 4,) * 2, pygame.SRCALPHA)
        pygame.draw.circle(yuz, (100, 200, 255, 120), (rr + 2, rr + 2), rr)
        pygame.draw.circle(yuz, (190, 235, 255, 220), (rr + 2, rr + 2), rr, 1)
        pygame.draw.circle(yuz, col + (200,), (rr + 2, rr + 2), max(1, rr // 2))
        s.blit(yuz, (int(p.x) - rr - 2, int(p.y) - rr - 2))


class Molecule:
    """TEK bir molekul. Ekranda gordugun her nokta bunlardan biridir.

    Arka planda derisim hesabi yoktur. Molekul ya hedefine varir ya
    varmaz; doz, varanlarin SAYISIDIR.

    Katmanlardan gecisi ELEK belirler: capi katmanin gozeneginden
    buyukse orada TAKILIR ve bir daha ilerleyemez. Nukleazin fiskirtma
    ile ise yaramamasinin sebebi kodda ayri bir kontrol degil, bu tek
    fiziksel kuraldir - 50 kDa'lik enzimin capi 2.85, duvar gozenegi 2.2.
    """

    __slots__ = ('hedef_yok', 'vs',
                 'cell', 'pos', 'vel', 'pi', 'dia', 'zone', 'col', 'depth',
                 'state', 'age', 'surface', 'need', 'mode', 'blocked_by',
                 'bounces', 'jig', 'tumble', 'hug_t', 'hug_r', 'hug_sh',
                 'hug_bi', 'gen', 'rad', 'hug_side',
                 'anch_ang', 'anch_bi', 'anch_frac', 'side', 'insert_fail',
                 'disarida')

    def __init__(self, cell, pos, vel, pi, depth=-1):
        # HIZ OLCEGI en basta atanmali: jig daha ilk satirlarda kuruluyor.
        # Geometri hucreyle birlikte kuculuyor (oyunda cekirdek 20 px,
        # laboratuvarda 110); termal ajitasyon olceklenmezse kucuk hucrede
        # molekul zarfin disina savruluyor ve hicbiri varamiyordu
        # (olculdu: katmanli hedefe 400 karede 0 varis). Hizlar da ayni
        # oranda kucultulunce fizik OLCEKTEN BAGIMSIZ kalir.
        self.vs = float(getattr(cell, 'hiz_olcegi', 1.0))
        nm, zone, kda, dia, eff, col, chain, surf = PAYLOADS[pi]
        self.cell = cell
        self.pos = pygame.math.Vector2(pos)
        self.vel = pygame.math.Vector2(vel)
        self.pi = pi
        self.dia = dia
        self.zone = zone
        self.col = col
        self.surface = surf
        self.side = PAYLOAD_SIDE.get(nm, 'her')
        self.insert_fail = 0
        self.depth = depth
        self.state = 'free'          # free | stuck | arrived | lost
        self.age = 0.0
        self.blocked_by = None
        self.bounces = 0
        self.jig = pygame.math.Vector2(THERMAL * self.vs, 0).rotate(random.uniform(0, 360))
        self.tumble = TUMBLE * random.uniform(0.5, 1.5)
        self.gen = cell.generation
        self.rad = max(2, int(round(dia * PORE_PX * 0.5)))
        self.hug_t = 0.0
        self.hug_r = 0.0
        self.hug_sh = None
        self.hug_bi = -1
        self.hug_side = 1.0      # +1 disaridan tutunuyor, -1 iceriden
        self.anch_ang = 0.0
        self.anch_bi = None      # bagliysa: kilitlendigi bant
        self.anch_frac = 0.5
        act = cell.active()
        _n = zone_min_depth(zone, act) if zone else 0
        # Hedef katman bu hucrede YOKSA yuk hicbir yere "varamaz". need'i
        # sayi olarak tutmaya devam ediyoruz (geometri matematigi onu
        # kullaniyor) ama varis testi bastan basarisiz.
        self.hedef_yok = _n is None
        self.need = len(act) if _n is None else _n
        self.mode = ZONE_MODE[zone] if zone else 'enaz'
        # KOKEN: hedef bandin DISINDAN mi geliyor (ya da tam o bantta mi
        # birakildi), yoksa daha ICERIDE mi dogdu? Yuzey toksini (side
        # 'dis') yalnizca dis yuzden etki eder: sitoplazmaya enjekte
        # edilmis norotoksin zar bandina surtundugunde "disaridan geldi"
        # sayilmamali. `depth < need` olcutu bunu ayirt edemiyordu - tek
        # katmanli hucrede need = 0 ve iceriden zara varan her molekul
        # bagl aniyordu. Kokene bakmak durumu degil TARIHI sorar.
        self.disarida = self.band() <= self.need

    # -------------------------------------------------------------- konum
    def band(self):
        """Su an kacinci katmanin icinde? -1 = disarida, N = sitoplazma.

        Bant yaricaplari ZARFIN kendi olcegiyle (boundaries) okunur.
        Eskiden `l.t * PX_PER_UNIT` ile hesaplaniyordu - laboratuvar
        hucresinde (cekirdek 110 px) ayni sey, ama oyun hucresinde
        (22 px) bantlar bes kat kalin saniliyordu: sitoplazmanin dibindeki
        molekul "duvar bandinda" cikiyor ve orada baglaniyordu.
        """
        d = self.pos.distance_to(self.cell.center)
        bounds = self.cell.boundaries()
        if not bounds:
            return -1 if d > self.cell.outer_r else 0
        if d > bounds[0]:
            return -1
        core = self.cell.core_r
        for i, outer in enumerate(bounds):
            inner = bounds[i + 1] if i + 1 < len(bounds) else core
            if d >= inner:
                return i
        return len(bounds)

    def _band_radii(self, bi):
        """Bir bandın [iç, dış] yarıçapı - GUNCEL geometriye göre."""
        bounds = self.cell.boundaries()
        if bi < 0:
            return self.cell.outer_r, self.cell.outer_r * 2.0
        if bi >= len(bounds):
            return 0.0, self.cell.core_r
        outer = bounds[bi]
        inner = bounds[bi + 1] if bi + 1 < len(bounds) else self.cell.core_r
        return inner, outer

    def _anchor(self):
        """Bağlı molekülü hücreye KİLİTLE.

        Konumu mutlak degil, hucreye GORE saklanir: hangi bant, bandin
        neresinde ve hangi acida. Boylece hucre yuzerken de siserken de
        duvari erirken de molekul baglandigi yerde kalir. Mutlak konumla
        tutulunca hucre kacarken katmanlar molekulun ustunden supuruyor,
        sitoplazmadaki molekul hicbir delikten gecmeden kendini duvarda
        buluyordu.
        """
        d = self.pos - self.cell.center
        self.anch_ang = math.atan2(d.y, d.x)
        bi = self.band()
        self.anch_bi = bi
        lo, hi = self._band_radii(bi)
        # Oran tam 0 ya da 1 olursa molekul iki bandin TAM sinirinda kalir
        # ve band() sinifi her karede degisebilir. Bandin icine cekiyoruz.
        self.anch_frac = 0.5 if hi - lo < 1e-6 else max(0.06, min(0.94,
                                                                  (hi - d.length()) / (hi - lo)))

    def _apply_anchor(self):
        if self.anch_bi is None:
            return
        lo, hi = self._band_radii(self.anch_bi)
        r = hi - self.anch_frac * (hi - lo)
        self.pos = self.cell.center + pygame.math.Vector2(
            math.cos(self.anch_ang), math.sin(self.anch_ang)) * r

    def _membrane_t(self):
        for l in self.cell.active():
            if l.name == 'Hucre zari':
                return l.t
        return None

    def _bind(self, bi, pos=None):
        """Bağlanmayı dene. Yerleşen molekül için hidrofobik uyumsuzluk.

        Konum ANCAK basarida islenir. Once tentatif konumu pesin yazip
        basarisizlikta geri almiyordum; molekul zarin otesinde kaliyor ama
        `depth` eski degerde duruyor, bir sonraki karede "disaridan
        geliyor" sanilip yanlis yuzden baglanabiliyordu (68 vaka).
        """
        if PAYLOAD_SPAN.get(PAYLOADS[self.pi][0]) is not None:
            if random.random() >= insertion_p(self.pi, self._membrane_t()):
                self.insert_fail += 1
                if self.insert_fail >= INSERT_TRIES:
                    # Yuzeye adsorbe oldu ama YERLESEMEDI - islevsiz.
                    self.state = 'stuck'
                    self.blocked_by = 'Hucre zari (yerlesemedi)'
                    self.depth = max(-1, bi - 1)
                    self._anchor()
                return False
        # BELIRLI BIR KATMANA baglanan yuk, o katmana capalanir.
        # 'enaz' modunda (norotoksin gibi yuzeye degmesi yeten yukler)
        # kosul "band >= hedef" oldugu icin, disaridan hizla gelip tek
        # karede zari asan molekul SITOPLAZMADA baglanmis sayiliyordu ve
        # capasini oraya kuruyordu - kanal blokeri sitoplazmada yuzuyordu.
        # Hedefi bir katman olan yuk her zaman O KATMANDA durur; yalnizca
        # sitoplazma hedefli yuk (ZONE_TARGET None) iceride kalir.
        if pos is not None:
            self.pos = pos
        if self.zone is not None and ZONE_TARGET[self.zone] is not None:
            bi = self.need
            lo, hi = self._band_radii(bi)
            d = self.pos - self.cell.center
            if d.length_squared() > 1e-9:
                self.pos = self.cell.center + d.normalize() * (lo + hi) * 0.5
        self.depth = bi
        self.state = 'arrived'
        self.age = 0.0
        self._anchor()
        self.cell.receive(self.pi)
        return True

    def _arrived_here(self, band, inward=True):
        """Bu bantta, bu yönden gelirken bağlanabilir mi?

        Elek simetriktir (delik iki yonu de kisitlar) ama BAGLANMA
        taraflidir. Ikisi ayri sorulardir; onceden tek yerde
        cozuluyordu ve sitoplazmaya bosaltilan bir gozenek acici
        zarin IC yuzunden etki edip hucreyi olduruyordu.
        """
        if self.zone is None:
            return False
        if self.hedef_yok:
            return False          # nisan alinan katman bu hucrede yok
        ok = band == self.need if self.mode == 'tam' else band >= self.need
        if not ok:
            return False
        if self.side == 'her':
            return True
        # inward=True -> disaridan geliyor, DIS yuze denk gelir
        return (self.side == 'dis') == bool(inward)

    # ------------------------------------------------------------ hareket
    def update(self, dt):
        # NOT: burada bir zamanlar "zarfin icindekini hucre ile birlikte
        # tasi" kurali vardi. Carpisma testi hucrenin cercevesine tasininca
        # o kural hem GEREKSIZ hem ZARARLI oldu: hareket iki kez sayiliyor,
        # molekul asiriya kayiyordu (olcum: tasima acikken 10/12, kapaliyken
        # 12/12 sitoplazmada kaliyor). Kayan hucre molekulu artik gercekten
        # ITEREK tasiyor - duvar ona carpiyor.
        if self.gen != self.cell.generation:
            # Hucre yenilendi - bu molekul eski nesle ait. Sayaci
            # dusurmeden yok olur; sayaclar zaten sifirlandi.
            self.state = 'cleared'
            return
        if self.state == 'arrived':
            self._apply_anchor()
            self.age += dt
            # EFFLUX POMPASI: bagli molekul daha cabuk temizlenir. Pompa
            # molekulu iceri sokmaz - baglandiktan sonra atar.
            sure = CLEARANCE / (1.0 + getattr(self.cell, 'efflux', 0.0) * EFFLUX_GAIN)
            if self.age > sure:
                self.state = 'cleared'
                self.cell.clear_one(self.pi)
            return
        if self.state == 'stuck':
            self._apply_anchor()
            return
        if self.state in ('lost', 'cleared'):
            return
        self.age += dt
        if self.age > MOLECULE_LIFE:
            self.state = 'lost'          # ortamda seyreldi, gitti
            return
        # HIZ IKI BILESENDEN olusur:
        #   drift : firlatmadan gelen YONLU hiz - surtunmeyle soner
        #   jig   : isil calkanti - sonmez ama YONU surekli degisir
        # Toplamlari net yer degistirmeyi verir. Drift bitince molekul
        # hicbir yere gitmez, sadece bulundugu yerde delik arar.
        self.vel *= MOL_DRAG ** dt
        self.tumble -= dt
        if self.tumble <= 0.0:
            self.tumble = TUMBLE * random.uniform(0.5, 1.5)
            self.jig = pygame.math.Vector2(THERMAL * self.vs, 0).rotate(
                random.uniform(0, 360))

        c = self.cell.center
        if self.hug_t > 0.0:
            if self._hug_step(c, dt):
                return
        # BAGIL hareket: d0 hucrenin ONCEKI merkezine, d1 YENISINE gore.
        # Ikisini de yeni merkeze gore olcmek, hucrenin o karede yaptigi
        # yer degistirmeyi hesabin disinda birakiyordu; kayan hucre
        # katmanlarini molekulun ustunden gecirip butun gozenek fizigini
        # atlatabiliyordu. Simdi hucrenin hareketi de bir gecis denemesi
        # uretiyor - duvar molekule carpiyor.
        d0 = self.pos.distance_to(self.cell.prev_center)
        nxt = self.pos + (self.vel + self.jig) * dt
        d1 = nxt.distance_to(c)
        # Molekul capi, HEDEF ZARFIN gozenek olceginde: zarf kuculunce
        # delikler de kuculur (Zarf.pore_px); cap global PORE_PX ile
        # alininca oyun hucresinde her molekul delikten 5 kat buyuk
        # cikiyor, duvar HERKESE kapaniyordu - peptit bile gecemiyordu.
        dia_px = self.dia * getattr(self.cell, 'pore_px', PORE_PX)
        # HANGI TARAFTAN geliyor? Bunu karedeki hareket yonunden turetmek
        # yanlisti: sitoplazmada zipzip gezen bir molekul bazi karelerde
        # iceri dogru gider ve "disaridan geliyor" sayilirdi. Dogru olcut
        # su an HANGI BANTTA oldugu - hedef banttan disaridaysa dis yuze,
        # icerideyse ic yuze denk gelir.
        dis_taraf = self.disarida

        if d1 != d0:
            # Elek CIFT YONLUDUR. Once yalnizca iceri girisi test ediyordum;
            # o zaman molekul disari bedavaya cikiyor, zarfin icinde
            # tutunamiyor ve arama sansi bulamadan kayboluyordu. Gercek bir
            # gozenek her iki yonu de ayni sekilde kisitlar - molekulun
            # katmanda HAPSOLMASI aramayi mumkun kilan sey.
            lo, hi = (d1, d0) if d1 < d0 else (d0, d1)
            inward = d1 < d0
            crossings = [(rr, bi, sh) for rr, bi, sh in self.cell.flat_sheets()
                         if lo <= rr < hi]
            if not inward:
                crossings.reverse()          # disari cikarken icten disa
            for rr, bi, sh in crossings:
                # Varis her iki yonde de gecerli: hedef katmanina icerden
                # ulasan bir molekul de oraya baglanir.
                if self._arrived_here(bi, dis_taraf):
                    # Molekul BAGLANDIGI TABAKANIN uzerine konur, gitmek
                    # uzere oldugu noktaya degil. `nxt` cogu zaman tabakayi
                    # asmis oluyordu (r=108, zar 110-124) ve capa bir sonraki
                    # bandi kaydediyordu - molekul zara baglandi diye
                    # sayilirken sitoplazmada gorunuyordu.
                    yon = nxt - c
                    bind_pos = (c + yon.normalize() * rr
                                if yon.length_squared() > 1e-9 else nxt)
                    if self._bind(bi, bind_pos):
                        return
                    if self.state == 'stuck':
                        return
                    # Yerlesemedi: konum ISLENMEDI, zarin yuzunde kalir ve
                    # asagidaki elege dusup seker; sonra tekrar dener.
                if sh.opening_for(self._angle_at(nxt, c), dia_px):
                    continue                      # delikten gecti
                # KATI KISMA CARPTI: geldigi tarafa seker, aramaya devam.
                self._bounce(c, rr, dia_px, 1.0 if inward else -1.0)
                self.hug_sh, self.hug_bi = sh, bi
                return
        self.pos = nxt
        ag = self.cell.agza_girdi(self.pos)
        if ag is not None:
            # SITOSTOM YUTTU: molekul dunyadan cikar, keseyle iceri gider.
            d = self.pos - self.cell.center
            self.cell.yut(self.pi, math.atan2(d.y, d.x), d.length())
            self.state = 'cleared'
            return
        b = self.band()
        if b != self.depth and b >= -1:
            self.depth = b
        # Koken guncellenir: hucreden cikan artik DISARIDADIR, hedef
        # bandi asip iceri gecen artik ICERIDEDIR.
        if b == -1:
            self.disarida = True
        elif b > self.need:
            self.disarida = False
        if self._arrived_here(self.depth, self.disarida):
            self._bind(self.depth)

    @staticmethod
    def _angle_at(pos, c):
        return math.atan2(pos.y - c.y, pos.x - c.x) % (2 * math.pi)

    def _olcek(self):
        """Zarfin piksel olcegi (lab hucresi = 1). Son piksel sabiti olan
        0.4 px'lik tutunma payi da geometriyle birlikte kuculsun."""
        return getattr(self.cell, 'pore_px', PORE_PX) / PORE_PX

    def _hug_step(self, c, dt):
        """Yüzeye tutunmuş: teğet süpürerek delik arar.

        Her karede BASKA bir aciyi dener. Delik bulursa iceri gecer;
        sure dolarsa yuzeyden ayrilir ve ortama geri karisir.
        True donerse bu kare islendi demektir.
        """
        self.hug_t -= dt
        sh, bi = self.hug_sh, self.hug_bi
        if sh is None:
            self.hug_t = 0.0
            return False
        n = self.pos - c
        if n.length_squared() < 1e-9:
            n = pygame.math.Vector2(1, 0)
        n = n.normalize()
        tang = pygame.math.Vector2(-n.y, n.x)
        if self.vel.dot(tang) < 0:
            tang = -tang
        # Molekul capi, HEDEF ZARFIN gozenek olceginde: zarf kuculunce
        # delikler de kuculur (Zarf.pore_px); cap global PORE_PX ile
        # alininca oyun hucresinde her molekul delikten 5 kat buyuk
        # cikiyor, duvar HERKESE kapaniyordu - peptit bile gecemiyordu.
        dia_px = self.dia * getattr(self.cell, 'pore_px', PORE_PX)
        # yuzey boyunca kay - BULUNDUGU tarafta kalarak
        yuzey = self.hug_r + self.hug_side * (dia_px * 0.5 + 0.4 * self._olcek())
        self.pos = c + (n * yuzey + tang * self.vel.length() * dt)
        self.pos = c + (self.pos - c).normalize() * yuzey
        if sh.opening_for(self._angle_at(self.pos, c), dia_px):
            # DELIGI BULDU: KARSI tarafa gecer (hangi yonden geldiyse)
            karsi = self.hug_r - self.hug_side * dia_px * 0.6
            yon = (self.pos - c).normalize()
            self.pos = c + yon * karsi
            self.hug_t = 0.0
            self.vel = yon * (-self.hug_side) * max(THERMAL * self.vs, self.vel.length())
            self.depth = self.band()
            bi = self.depth
            # Tutunurken delikten gectiyse: hug_side +1 ise disaridan
            # iceri gecmistir.
            if self._arrived_here(bi, self.hug_side > 0):
                # Konum ZATEN dogru: molekul delikten gecip karsi tarafa
                # yerlesti ve bi onun BULUNDUGU banttan turetildi. Buraya
                # hug_r'yi (yeni gecilen tabakanin yaricapi) yazmak ikisini
                # tutarsiz kiliyordu - zar bandina baglanip duvarda
                # gorunuyordu.
                self._bind(bi)
            return True
        if self.hug_t <= 0.0:
            self.bounces += 1
            if self.bounces >= BOUNCE_TRAP:
                self.state = 'stuck'
                self.blocked_by = self.cell.active()[bi].name
                self.depth = max(-1, bi - 1)
                self._anchor()
            else:
                # yuzeyden ayrildi, GELDIGI ortama geri karisiyor
                self.vel = n * self.hug_side * max(THERMAL * self.vs, self.vel.length()) * 0.6
        return True

    def _bounce(self, c, rr, dia_px, side):
        """Katı kısma çarptı: savrulmaz, yüzey boyunca KAYAR.

        Ilk surum molekulu radyal olarak geri firlatiyordu; acik alana
        donen molekul bir daha ayni tabakaya gelemiyor, delik aramasi
        tek denemede bitiyordu. Gercekte yogun bir jelde molekul
        sikisiktir: engele carpinca yuzey boyunca gezinir ve her karede
        BASKA bir aciyi dener. Delik bulmak boyle olur.
        """
        n = self.pos - c
        if n.length_squared() < 1e-9:
            n = pygame.math.Vector2(1, 0)
        n = n.normalize()
        tang = pygame.math.Vector2(-n.y, n.x) * random.choice((-1.0, 1.0))
        sp = max(THERMAL * self.vs, (self.vel + self.jig).length())
        # Hiz SAF TEGET yone doner. Ilk surumde kucuk bir DISARI bileseni
        # vardi; drift hala buyukken bu bilesen molekulu zarftan disari
        # itiyor ve tabakayi bir daha hic deneyemiyordu - S-layer toplam
        # BIR kez deneniyordu. Radyal ilerlemeyi artik yalniz isil
        # calkanti saglar, yani gercekten rastgele.
        self.vel = tang * sp
        self.jig = pygame.math.Vector2(THERMAL * self.vs, 0).rotate(random.uniform(0, 360))
        self.tumble = TUMBLE * random.uniform(0.5, 1.5)
        # GELDIGI TARAFA geri it. Once her zaman DIS tarafa itiliyordu;
        # iceriden gelen bir molekul engele carpinca duvarin obur yanina
        # irakliyor, yani tam da gecemedigi tabakadan gecmis oluyordu.
        # Elek boylece tek yonlu kaliyordu: disaridan iceri hicbir sey
        # giremiyor ama sitoplazmadaki her sey disari sizabiliyordu.
        self.pos = c + n * (rr + side * (dia_px * 0.5 + 0.4 * self._olcek()))
        self.hug_t = HUG_TIME
        self.hug_r = rr
        self.hug_side = side

    def draw(self, s):
        if self.state in ('lost', 'cleared'):
            return
        p = (int(self.pos.x), int(self.pos.y))
        # Yaricap GERCEK captan gelir. Onceden 3-4-5 px sabitti; 5.1 px'lik
        # peptit ile 14.5 px'lik perforin ekranda ayni buyuklukte
        # gorunuyordu, yani hangi molekulun neden gecemedigi gozle
        # anlasilmiyordu. Delikler de ayni PORE_PX olceginde uretiliyor,
        # dolayisiyla artik ikisi birebir orantili.
        r = self.rad
        if self.state == 'arrived':
            pygame.draw.circle(s, self.col, p, r)
            pygame.draw.circle(s, (255, 255, 255), p, r, 1)
        elif self.state == 'stuck':
            pygame.draw.circle(s, (110, 118, 135), p, r)
            pygame.draw.circle(s, (210, 95, 95), p, r + 2, 1)
        else:
            pygame.draw.circle(s, self.col, p, r)
            if r >= 4:
                pygame.draw.circle(s, tuple(min(255, c + 55) for c in self.col),
                                   (p[0] - r // 3, p[1] - r // 3), max(1, r // 3))


# Zar yatirimi -> KATMAN KALINLIGI. Kesitteki halkalar ile editordeki
# halkalarin ayni sayilardan cizilmesi icin kural tek yerde durur.
# (yatirim alani, katman adi, VARLIK alani). Varlik alani None ise katman
# ZORUNLUDUR: plazma zari olmayan hucre yoktur. Otekiler eklenip
# cikarilabilir - duvarsiz hucre (Mycoplasma, hayvan hucresi) gercektir.
KATMAN_ALANI = (('mucus', 'Mukus', 'var_mucus'),
                ('capsule', 'Kapsul', 'var_capsule'),
                ('slayer', 'S-layer', 'var_slayer'),
                ('wall', 'Duvar', 'var_wall'),
                ('outer', 'Hucre zari', None))

ZORUNLU_KATMAN = 'Hucre zari'


class Zarf:
    """Bir hucrenin katman + GOZENEK geometrisi.

    Bu makine LabCell'in icinde gomuluydu; oysa yalnizca uc seye bagli:
    katman listesi, hangilerinin acik oldugu ve cekirdek yaricapi. Disari
    cikarilinca oyundaki hucre de birebir AYNI gozeneklere sahip oluyor -
    ekosistemdeki molekul de laboratuvardaki delikten geciyor.

    Olcek: laboratuvarda cekirdek 110 px ve bir kalinlik birimi 9 px.
    Oyunda cekirdek ~20 px oldugu icin her sey `cekirdek_r / 110` ile
    orantili kuculur; gozenek genislikleri de. Boylece "hangi molekul
    hangi delikten gecer" sorusunun cevabi olcekten BAGIMSIZ kalir.
    """

    __slots__ = ('layers', 'enabled', 'core_r', 'ppu', 'pore_px',
                 '_sheets', '_flat', '_polys', 'key')

    def __init__(self, layers, enabled, core_r, ppu=None, pore_px=None):
        self.layers = layers
        self.enabled = list(enabled)
        self.core_r = float(core_r)
        olcek = self.core_r / 110.0
        self.ppu = PX_PER_UNIT * olcek if ppu is None else ppu
        self.pore_px = PORE_PX * olcek if pore_px is None else pore_px
        self.key = (tuple(self.enabled), round(self.core_r, 2),
                    tuple(round(l.t, 2) for l in layers))
        self._sheets = self._build_sheets()
        # LabCell.flat_sheets ile AYNI sozlesme: (yaricap, bant, tabaka),
        # disaridan ice sirali. Sirali olmasi sart - hizli bir molekul tek
        # karede birkac tabaka gecebilir; sirasiz bakinca duvari atlayip
        # sitoplazmaya "tunelleyebilir".
        fl = [(sh.r, bi, sh)
              for bi, band in enumerate(self._sheets) for sh in band]
        fl.sort(key=lambda x: -x[0])
        self._flat = fl
        self._polys = self._build_polys()

    # ---------- geometri ----------
    def active(self):
        return [l for l, e in zip(self.layers, self.enabled) if e]

    @property
    def outer_r(self):
        return self.core_r + sum(l.t for l in self.active()) * self.ppu

    def boundaries(self):
        r = self.outer_r
        out = []
        for l in self.active():
            out.append(r)
            r -= l.t * self.ppu
        return out

    def sheets(self):
        return self._sheets

    def flat_sheets(self):
        return self._flat

    def pore_polys(self):
        return self._polys

    # ---------- insa ----------
    def _build_sheets(self):
        out = []
        r = self.outer_r
        for l in self.active():
            inner = r - l.t * self.ppu
            if l.mesh <= 0 or l.porosity <= 0:
                out.append([Sheet((r + inner) * 0.5, [], True)])
                r = inner
                continue
            pw = l.mesh * self.pore_px
            order = LAYER_ORDER.get(l.name, 0.5)
            taban = 1 if order >= 0.9 else 3
            n_sheet = max(taban, min(MAX_SHEETS,
                                     int(round(l.t / max(l.mesh, 0.4)))))
            rnd = random.Random(sum(ord(c) for c in l.name) * 977)
            band = []
            for k in range(n_sheet):
                rr = inner + (r - inner) * (k + 0.5) / n_sheet
                n = max(3, int(2 * math.pi * rr * l.porosity / max(pw, 0.2)))
                pores = []
                for j in range(n):
                    a = 2 * math.pi * j / n
                    if order < 1.0:
                        a += (1 - order) * rnd.uniform(-math.pi / n, math.pi / n)
                        w = pw * (1 + (1 - order) * rnd.uniform(-0.4, 0.4))
                    else:
                        w = pw
                    pores.append((a % (2 * math.pi), w))
                band.append(Sheet(rr, pores, False))
            out.append(band)
            r = inner
        return out

    def _build_polys(self):
        out = []
        r = self.outer_r
        for l, band in zip(self.active(), self._sheets):
            inner = r - l.t * self.ppu
            n_sheet = len(band)
            for k, sh in enumerate(band):
                if sh.solid:
                    continue
                r1 = r - (r - inner) * k / n_sheet
                r0 = r - (r - inner) * (k + 1) / n_sheet
                order = LAYER_ORDER.get(l.name, 0.5)
                rnd = random.Random(int(sh.r * 31) + k)
                for a, w in sh.pores:
                    h = (w * 0.5) / max(sh.r, 0.001)
                    steps = max(3, min(9, int(w / 12) + 3))
                    ru = (1 - order) * (r1 - r0) * 0.22
                    pts = []
                    for j in range(steps + 1):
                        ang = a - h + 2 * h * j / steps
                        rr = r1 + (rnd.uniform(-ru, ru) if ru else 0.0)
                        pts.append((math.cos(ang) * rr, math.sin(ang) * rr))
                    for j in range(steps, -1, -1):
                        ang = a - h + 2 * h * j / steps
                        rr = r0 + (rnd.uniform(-ru, ru) if ru else 0.0)
                        pts.append((math.cos(ang) * rr, math.sin(ang) * rr))
                    out.append(pts)
            r = inner
        return out


_ZARF_ONBELLEK = {}


def zarf_geometrisi(zar_logic, cekirdek_r):
    """Bu zar + bu cekirdek icin Zarf nesnesi (onbellekli).

    Gozenek uretimi deterministik (sabit tohumlu) ama pahali; her karede
    yeniden kurmak yerine (katmanlar, kalinliklar, yaricap) anahtariyla
    saklanir. Kayit degisince kendiliginden yenilenir.
    """
    layers = default_layers()
    v = katman_varligi(zar_logic)
    b = katman_bonusu(zar_logic)
    _alan_of = {katman: alan for alan, katman, _vr in KATMAN_ALANI}
    for l in layers:
        t0 = katman_tabani(zar_logic, _alan_of.get(l.name), l.t)
        l.t = max(0.2, min(20.0, t0 + b.get(l.name, 0.0)))
    enabled = [bool(v.get(l.name, True)) for l in layers]
    anahtar = (tuple(enabled), round(float(cekirdek_r), 1),
               tuple(round(l.t, 2) for l in layers))
    z = _ZARF_ONBELLEK.get(anahtar)
    if z is None:
        if len(_ZARF_ONBELLEK) > 256:      # sinirsiz buyumesin
            _ZARF_ONBELLEK.clear()
        z = Zarf(layers, enabled, cekirdek_r)
        _ZARF_ONBELLEK[anahtar] = z
    return z


def zarf_ciz(screen, zar_logic, merkez, cekirdek_r, ince=False,
             gozenek=True, olcek=1.0, kaydir=(0.0, 0.0)):
    """Zarfi cekirdegin DISINA ciz; dis yaricapi dondur.

    `gozenek` acikken katmanlar GERCEK delikleriyle cizilir - cizilen
    delik, molekulun gectigi deligin ta kendisidir (lab.py'deki kesitle
    ayni geometri, yalnizca olcegi kucuk).

    `olcek` ve `kaydir` kamera icindir: yakinlastirinca ayni geometri
    daha buyuk cizilir, yeni bir temsil uretilmez.
    """
    if zar_logic is None or cekirdek_r <= 0:
        return cekirdek_r
    z = zarf_geometrisi(zar_logic, cekirdek_r)
    cx = merkez[0] * olcek + kaydir[0]
    cy = merkez[1] * olcek + kaydir[1]
    icx, icy = int(cx), int(cy)

    # Halkalar: distan ice, her katman kendi renginde
    r = z.outer_r
    halkalar = []
    for l in z.active():
        inner = r - l.t * z.ppu
        px = max(1, int(round((r - inner) * olcek)))
        pygame.draw.circle(screen, l.color, (icx, icy), int(r * olcek), px)
        halkalar.append((l, r * olcek, inner * olcek))
        r = inner

    if gozenek:
        # GERCEK GOZENEKLER. Cok kucukken (oyun olceginde ~1 px) poligon
        # cizmek anlamsiz; o durumda halkalar duz kalir ve yakinlasinca
        # delikler ortaya cikar.
        for pts in z.pore_polys():
            if len(pts) < 3:
                continue
            ekran = [(cx + px * olcek, cy + py * olcek) for px, py in pts]
            xs = [q[0] for q in ekran]; ys = [q[1] for q in ekran]
            if (max(xs) - min(xs)) < 1.2 and (max(ys) - min(ys)) < 1.2:
                continue
            pygame.draw.polygon(screen, PORE_COL, ekran)
        # Sinir cemberleri deliklerin USTUNE: acikligi yuksek katman
        # (mukus %85) yoksa kirik bir halka gibi gorunuyor.
        for l, dis, ic in halkalar:
            pygame.draw.circle(screen, tuple(max(0, c - 40) for c in l.color),
                               (icx, icy), int(dis), 1)
    return z.outer_r


class HedefZarf:
    """Bir Organism'i lab.Molecule'un bekledigi arayuze baglar.

    Molekul fizigi 500 satirlik tek bir sinifta ve yalnizca ON BIR sey
    okuyor: active, center, prev_center, core_r, outer_r, flat_sheets,
    generation, receive, clear_one, agza_girdi, yut. Bu kadarini bir
    adaptorle karsilamak, fizigi ikinci kez yazmaktan hem kisa hem de
    dogru: ekosistemdeki molekul ile laboratuvardaki molekul AYNI KODU
    calistirir, dolayisiyla ayni delikten gecer ya da ayni yerde takilir.

    Varis muhasebesi (`receive`) hasara cevrilir: yuke ulasan molekul
    sayisi PAYLOAD_THRESHOLD kademelerini asinca etki uygulanir.
    """

    __slots__ = ('org', '_zarf', '_key', 'arrived', 'tier_of', 'sahip',
                 'neden', 'feeder', 'alarm', 'pulling',
                 'keseler', 'kacan', 'sindirilen', 'yutulan')

    def __init__(self, org):
        self.org = org
        self._zarf = None
        self._key = None
        self.arrived = {}
        self.tier_of = {}
        self.sahip = None          # molekulu atan hucre (hasar sahibi)
        self.neden = None          # olum nedeni: hangi silah enjekte etti
        # lab.Shot'un yazdigi alanlar (mermi fizigi bunlari okur/yazar)
        self.feeder = None
        self.alarm = 0.0
        self.pulling = None        # izoriza: kendini ceken mermi
        # SITOSTOM: yutulan molekuller fagozoma (Kese) alinir
        self.keseler = []
        self.kacan = 0             # keseyi delip sitoplazmaya kacan (gozenek acici)
        self.sindirilen = 0        # fagozomda yok edilen
        self.yutulan = 0

    # ---- geometri (onbellekli) ----
    def _g(self):
        zar = getattr(getattr(self.org, 'membrane', None), 'logic', None)
        k = (round(self.org.radius, 2),
             tuple(bool(getattr(zar, v, True)) for v in
                   ('var_mucus', 'var_capsule', 'var_slayer', 'var_wall')),
             tuple(round(getattr(zar, a, 0.0), 2)
                   for a, _kt, _v in KATMAN_ALANI))
        if self._zarf is None or self._key != k:
            self._key = k
            self._zarf = zarf_geometrisi(zar, self.org.radius)
        return self._zarf

    @property
    def hiz_olcegi(self):
        """Molekul hizlari geometriyle AYNI oranda kuculur."""
        return max(0.05, self.org.radius / 110.0)

    @property
    def pore_px(self):
        """Gozenek/molekul cap olcegi - zarfin kendi olcegi."""
        return self._g().pore_px

    @property
    def efflux(self):
        """Pompa + onarim: bagli molekulu ne kadar cabuk atar.

        Molecule.update `self.cell.efflux` okuyor ama HedefZarf bunu HIC
        sunmuyordu; getattr varsayilani 0.0'a dusuyor ve pompa molekul
        yolunda OLU kaliyordu. Yani hucre efflux katmanini evrimlestirip
        bakim giderini oduyor, karsiliginda molekulle gelen toksine karsi
        hicbir sey almiyordu - oysa savunma tipinin ortaya cikmasi tam da
        buna bagli.

        Laboratuvarin kendi hucresiyle ayni bilesim (bkz. LabCell:
        efflux + repair): pompa molekulu disari atar, onarim da baglandigi
        yeri yeniler.
        """
        lg = getattr(getattr(self.org, 'membrane', None), 'logic', None)
        if lg is None:
            return 0.0
        return (float(getattr(lg, 'efflux', 0.0) or 0.0)
                + float(getattr(lg, 'repair', 0.0) or 0.0))

    def active(self):
        return self._g().active()

    def flat_sheets(self):
        return self._g().flat_sheets()

    def boundaries(self):
        return self._g().boundaries()

    @property
    def outer_r(self):
        return self._g().outer_r

    @property
    def core_r(self):
        return self.org.radius

    @property
    def center(self):
        return self.org.pos

    @property
    def prev_center(self):
        return getattr(self.org, 'onceki_pos', self.org.pos)

    @property
    def generation(self):
        # Geometri degisince ucustaki molekuller emekli olsun
        return getattr(self.org, 'zarf_nesli', 0)

    # ---- lab.Shot arayuzu ----
    # Mermi fizigi (delme, kenetlenme, lumen, yakalama) laboratuvarla
    # AYNI kod: Shot bir hucrede su alanlari okur/yazar. Burada hepsi
    # oyun hucresine baglanir; fizik ikinci kez yazilmaz.
    @property
    def motion(self):
        return self.org.pos - getattr(self.org, 'onceki_pos', self.org.pos)

    def sinir_icinde(self, pos):
        # Mermi hedefin cevresinde bir yerde olmali; dunya siniri degil,
        # hedefe gore uzaklik. Cok uzaga gitmis mermi bosa gitmistir.
        # Menzil zaten atis aninda sinanmis; hedefi iskalayan mermi
        # birkac hucre boyu sonra biter. 900 px, iskalayan mermiyi
        # saniyelerce yasatiyordu.
        return pos.distance_to(self.org.pos) <= self.outer_r + 130.0

    @property
    def tethered(self):
        return getattr(self.org, 'tether_timer', 0.0) > 0.0

    @tethered.setter
    def tethered(self, v):
        # VOLVENT: iplik ava sarilir, kacamaz. Oyunda karsiligi ip suresi.
        if v:
            import game_settings as _g
            self.org.tether_timer = _g.NEMATOCYST_TETHER_TIME
            self.org.tether_from = self.sahip

    @property
    def sticky(self):
        return getattr(self.org, 'yapiskan', 0.0) > 0.0

    @sticky.setter
    def sticky(self, v):
        # GLUTINANT: yuzey yapiskan - sonraki mermiler sekmez, tutunma
        # kolaylasir (fagositoz).
        if v:
            import game_settings as _g
            self.org.yapiskan = _g.STICKY_TIME

    # ---- SITOSTOM (LabCell ile ayni kurallar) ----
    #
    # Fagositoz organi bir AGIZDIR. Acisal penceresine giren molekul yutulur
    # ve fagozoma alinir; fagozom bir tuzaktir - asitlesir, lizozomla
    # kaynasir ve yuku sindirir. Yalnizca gozenek acici bir yuk keseyi
    # delip sitoplazmaya kacar (Listeria'nin listeriolizini). Igneler bu
    # yuzden vardir: keseyi ATLAYIP dogrudan sitoplazmaya birakirlar.
    @property
    def agizlar(self):
        return [o.aim_angle(self.org) for o in getattr(self.org, 'organs', ())
                if o.__class__.__name__ == 'Phagocytosis']

    @property
    def sert_yuzey(self):
        for l in self.active():
            if l.name in SERT_KATMANLAR and l.t > SERT_ESIK:
                return l.name
        return None

    @property
    def sitostom_aktif(self):
        return bool(self.agizlar) and self.sert_yuzey is None

    def agza_girdi(self, pos):
        if not self.sitostom_aktif:
            return None
        d = pos - self.center
        r = d.length()
        if r > self.outer_r or r < self.core_r * 0.55:
            return None
        a = math.atan2(d.y, d.x)
        for ag in self.agizlar:
            fark = abs((a - ag + math.pi) % (2 * math.pi) - math.pi)
            if fark <= MOUTH_HALF:
                return ag
        return None

    def yut(self, pi, ang, r):
        self.keseler.append(Kese(self, ang, min(r, self.outer_r * 0.95), pi))
        self.yutulan += 1
        return True

    # ---- varis muhasebesi ----
    def clear_one(self, pi):
        if self.arrived.get(pi):
            self.arrived[pi] -= 1

    def receive(self, pi):
        n = self.arrived.get(pi, 0) + 1
        self.arrived[pi] = n
        tier = count_tier(pi, n)
        if tier > self.tier_of.get(pi, TIER_NONE):
            self.tier_of[pi] = tier
            self._etki(pi, tier)

    def _etki(self, pi, tier):
        """Kademe yukseldi: LABORATUVARLA AYNI MEKANIZMA.

        Eskiden her kademe zar butunlugunu dusuruyordu; felc, sisme,
        duvar incelmesi oyunda yoktu. Simdi yukun sinifi (EFFECT_CLASS)
        ne diyorsa o olur - uygulama Organism.doz_etkisi'nde, cunku
        etkiler hucrenin motoruna, zarina ve yaricapina dokunur.
        """
        org = self.org
        if getattr(org, 'dead', False):
            return
        nm = PAYLOADS[pi][0]
        if PAYLOAD_THRESHOLD.get(nm) is None:
            return
        cls = effect_class(pi)
        mech = EFFECT_CLASS[cls][1] if cls in EFFECT_CLASS else 'halt'
        org.doz_etkisi(tier, mech, self.neden or 'molekul')


def zarf_orani(zar_logic):
    """Zarfin dis yaricapinin CEKIRDEK yaricapina orani (>= 1).

    Cizim ile fizigi ayni sayiya baglamak icin gerekli: hucrenin gercek
    dis siniri `entity.radius`tir (temas, ortusme, organ tutunmasi hep onu
    kullanir), zarf da onun ICINE oturmalidir. Zarfi cekirdegin disina
    ekleyince cizilen hucre yaricapinin 2.76 katina cikiyordu; besin
    temas ettiginde gorsel olarak coktan hucrenin icinde kaliyor, yalanci
    ayaklarin uzanacagi yer kalmiyordu.
    """
    if zar_logic is None:
        return 1.0
    # ONBELLEK: bu oran hucrenin YARICAPINI belirledigi icin fizik her
    # karede iki kez soruyor, ve her sorusta bes katmanin profili bastan
    # kuruluyordu. Oysa oran yalnizca katman varliklari, yatirimlar ve
    # kalinliklar degistiginde degisir - bunlar da bolunme/gelisim
    # anlarinda. Anahtar tam o degerlerden olusur, yani onbellek bayat
    # bir deger donduremez.
    anahtar = _zarf_anahtari(zar_logic)
    onbellek = getattr(zar_logic, '_zarf_onbellek', None)
    if onbellek is not None and onbellek[0] == anahtar:
        return onbellek[1]
    birim = PX_PER_UNIT / 110.0
    oran = 1.0 + sum(k for _a, k, _r, var in katman_kalinliklari(zar_logic)
                     if var) * birim
    try:
        zar_logic._zarf_onbellek = (anahtar, oran)
    except Exception:
        pass
    return oran


def _zarf_anahtari(zar_logic):
    """Zarf oranini belirleyen HER SEY. Degisirse onbellek dusar."""
    kal = getattr(zar_logic, 'kalinlik', None)
    return (
        tuple(getattr(zar_logic, alan, 0.0) for alan, _k, _v in KATMAN_ALANI),
        tuple(bool(getattr(zar_logic, v, True))
              for _a, _k, v in KATMAN_ALANI if v),
        tuple(sorted(kal.items())) if isinstance(kal, dict) else None,
    )


def cekirdek_yaricapi(entity):
    """Sitoplazmanin cizim yaricapi: dis yaricap / zarf orani."""
    return cekirdek_yaricapi_ham(entity.radius, entity)


def cekirdek_yaricapi_ham(dis_yaricap, entity):
    zar = getattr(getattr(entity, 'membrane', None), 'logic', None)
    return max(1.0, dis_yaricap / zarf_orani(zar))


def yalanci_ayak_ciz(screen, entity, merkez, olcek, dis_r, dunya_pos):
    """Sarmalanan besinin etrafinda kapanan YALANCI AYAKLAR.

    Fagositozun gercek mekanizmasi: hucre zari parcacigin iki yanindan
    uzanir, uclari bulusup kaynasir ve kapali bir kese (fagozom) olusur.
    Onceden ekranda bunun hicbir izi yoktu - besin yalnizca kuculuyordu.

    Ayaklar besinin YONUNDE, ona dogru acilan iki kol olarak cizilir;
    sarmalama ilerledikce kollar besinin etrafinda kapanir.
    """
    besin = getattr(entity, 'yutulan_besin', None)
    if besin is None or getattr(besin, 'yutan', None) is not entity:
        return
    t = getattr(besin, 'yutma_t', 0.0)
    kav = getattr(besin.__class__, 'KAVRAMA', 0.6)
    # DIKKAT: cizim sirasinda entity.pos EKRAN merkezine ayarlanmis
    # durumda; besin ise hala DUNYA koordinatinda. Ikisini cikarmak
    # anlamsiz bir yon ve devasa bir uzunluk uretiyordu (ekranin bir
    # ucundan otekine uzanan kollar). Yon dunyada olculur, sonra olceklenir.
    d = besin.pos - dunya_pos
    if d.length() < 1e-6:
        return
    yon = math.atan2(d.y, d.x)
    # Kapanma orani: sarmalama boyunca 0 -> 1, sonra kapali kalir
    k = min(1.0, t / max(1e-6, kav))
    br = max(1.0, besin.taban_r) * olcek
    renk = tuple(min(255, int(c * 0.85)) for c in entity.color)
    kalinlik = max(1, int(round(2.2 * olcek)))
    bp = (int(merkez[0] + d.x * olcek), int(merkez[1] + d.y * olcek))

    # ICERI CEKME asamasi: kollar kapandi, artik ortada bir FAGOZOM var.
    # Kese besinle birlikte sitoplazmaya yol alir; ekranda kaybolmasi
    # "besin isinlandi" izlenimi veriyordu.
    if t > kav:
        pygame.draw.circle(screen, renk, bp, max(2, int(br * 1.15)),
                           max(1, int(round(olcek))))
        return

    # Kolun boyu: besine kadar uzanir ve etrafini sarar
    uzanim = (d.length() * olcek - dis_r) + br * (0.4 + 1.6 * k)
    if uzanim <= 0:
        return
    # Iki kol: besinin iki yanindan. Acisal ayrim kapandikca daralir.
    ayrim = (br / max(br, dis_r)) * (1.15 - 0.75 * k)
    for isaret in (+1, -1):
        pts = []
        n = 8
        for i in range(n + 1):
            u = i / n
            # Kok zarda, uc besinin arkasinda: aci sarmaladikca kapanir
            a = yon + isaret * ayrim * (1.0 - u * u)
            r = dis_r + uzanim * u
            pts.append((merkez[0] + math.cos(a) * r,
                        merkez[1] + math.sin(a) * r))
        if len(pts) > 1:
            pygame.draw.lines(screen, renk, False, pts, kalinlik)
    # Kapanmaya yaklasirken keseyi belli eden ince halka
    if k >= 0.85:
        pygame.draw.circle(screen, renk, bp,
                           max(2, int(br * 1.25)), max(1, int(round(olcek))))


def sindirim_keseleri_ciz(screen, entity, merkez, olcek, cekirdek_r):
    """Sitoplazmadaki BESIN KESELERI - sindirilene kadar gorunurler.

    Alinan besin ekrandan siliniyordu; oysa fagozom sitoplazmada durur ve
    lizozomla kaynasip sindirilir. Kuyruktaki her besin bir kese;
    islenmekte olan kese ilerledikce kuculur ve rengi soner.
    """
    keseler = getattr(entity, 'sindirim_keseleri', None)
    if keseler is None:
        return
    liste = keseler()
    if not liste:
        return
    # lab.py game_settings'i ice aktarmiyor (bagimsiz calisabilsin diye);
    # yerel import.
    try:
        import game_settings as _gs
        _alan = getattr(_gs, 'FOOD_AREA', 100.0)
    except Exception:
        _alan = 100.0
    taban = max(1.5, math.sqrt(_alan / math.pi) * olcek)
    for i, (tohum, ilerleme) in enumerate(liste):
        # Sabit ama dagilmis yerlesim: her kese kendi yerinde durur
        a = (tohum * 2 * math.pi) + i * 2.399963      # altin aci
        rr = cekirdek_r * (0.30 + 0.42 * ((i * 0.53 + tohum) % 1.0))
        x = merkez[0] + math.cos(a) * rr
        y = merkez[1] + math.sin(a) * rr
        r = max(1, int(taban * (1.0 - 0.55 * ilerleme)))
        # Sindirildikce yesilden soluga
        c = (int(120 + 60 * ilerleme), int(220 - 90 * ilerleme),
             int(140 - 40 * ilerleme))
        pygame.draw.circle(screen, c, (int(x), int(y)), r)
        pygame.draw.circle(screen, (40, 60, 50), (int(x), int(y)), r,
                           max(1, int(round(olcek))))


def hucreyi_ciz(screen, entity, ekran_merkez, olcek=1.0, gozenek=True):
    """Bir hucreyi verilen ekran konumunda, verilen OLCEKTE ciz.

    TEK cizim yolu: oyun (olcek 1), kamera yakinlastirmasi (olcek > 1) ve
    editor onizlemesi hep buradan gecer. Yakinlastirma yeni bir temsil
    URETMEZ - ayni geometri daha buyuk cizilir, gozenekler de oyle.

    Organ gorunumleri boyutlarini KENDI alanlarindan alir (kamcinin
    `length`i, mekanoreseptorun `size`i, fotoreseptorun `range`i);
    parent.radius yalnizca KONUM icindir. Bu yuzden olcegi uygularken hem
    yaricap hem de o alanlar gecici olarak buyutulur, sonra geri alinir.
    """
    from organs.registry import ic_organ

    r0 = entity.radius
    p0 = pygame.math.Vector2(entity.pos)
    d0 = pygame.math.Vector2(entity.direction)
    yedek = []
    if olcek != 1.0:
        for o in entity.organs:
            y = {}
            lg = getattr(o, 'logic', None)
            for alan in ('length', 'size', 'range'):
                if hasattr(lg, alan):
                    y[alan] = getattr(lg, alan)
                    setattr(lg, alan, getattr(lg, alan) * olcek)
            if hasattr(lg, 'area'):          # alan olcegin KARESIYLE buyur
                y['area'] = lg.area
                lg.area = lg.area * olcek * olcek
            yedek.append(y)

    entity.pos = pygame.math.Vector2(ekran_merkez)
    # DIS SINIR entity.radius'tur; zarf onun icine oturur, sitoplazma da
    # zarfin icinde kalir. Boylece cizilen hucre ile temas/ortusme
    # yaricapi AYNI sayidir.
    dis_sinir = r0 * olcek
    entity.radius = cekirdek_yaricapi_ham(r0, entity) * olcek
    # Bazi organlar boyutunu KENDI alanindan degil sabit bir sayidan alir
    # (silahlarda DISPLAY_LENGTH, ucundaki daire yaricapi vs). Onlar
    # `length/size/range/area` olceklemesine takilmiyor ve olcek ne olursa
    # olsun ayni buyuklukte ciziliyorlardi. Cizim olcegini konaga
    # yaziyoruz; sabit olculu cizimler bunu okur.
    entity.ciz_olcegi = olcek
    try:
        ic = [o for o in entity.organs if ic_organ(o.__class__.__name__)]
        dis = [o for o in entity.organs if o not in ic]
        if not any(o.__class__.__name__ == 'Cytoplasm' for o in entity.organs):
            rr = max(3, int(entity.radius))
            pp = (int(entity.pos.x), int(entity.pos.y))
            g = pygame.Surface((rr * 2 + 4,) * 2, pygame.SRCALPHA)
            pygame.draw.circle(g, (*entity.color, 70), (rr + 2, rr + 2), rr)
            screen.blit(g, (pp[0] - rr - 2, pp[1] - rr - 2))
            pygame.draw.circle(screen, entity.color, pp, rr, 1)
        for o in ic:
            o.draw(screen, entity)
        # Sindirim keseleri sitoplazmanin ICINDE
        sindirim_keseleri_ciz(screen, entity, entity.pos, olcek, entity.radius)
        zar = getattr(getattr(entity, 'membrane', None), 'logic', None)
        cek = entity.radius
        dis_r = cek
        if zar is not None:
            dis_r = zarf_ciz(screen, zar, entity.pos, cek, ince=True,
                             gozenek=gozenek)
        # Sayisal yuvarlamalar birikmesin: dis sinir tanim geregi budur.
        dis_r = dis_sinir
        entity.radius = dis_r
        for o in dis:
            o.draw(screen, entity)
        # Yalanci ayaklar EN USTTE: sarmalama sirasinda zarin bu uzantisi
        # butun yuzey yapilarinin onunde durur. Organlarin altinda cizince
        # mekanoreseptorun algi dairesi onlari tamamen ortuyordu.
        yalanci_ayak_ciz(screen, entity, entity.pos, olcek, dis_r, p0)
    finally:
        entity.radius = r0
        entity.pos = p0
        entity.direction = d0
        entity.ciz_olcegi = 1.0
        if olcek != 1.0:
            for o, y in zip(entity.organs, yedek):
                lg = getattr(o, 'logic', None)
                for alan, deger in y.items():
                    setattr(lg, alan, deger)
    return dis_r


def zarf_yaricapi(zar_logic, cekirdek_r):
    """Zarfin DIS yaricapi - cizmeden. Organlarin tutundugu yer burasi."""
    if zar_logic is None or cekirdek_r <= 0:
        return cekirdek_r
    birim = cekirdek_r * (PX_PER_UNIT / 110.0)
    return cekirdek_r + sum(
        k for _ad, k, _r, var in katman_kalinliklari(zar_logic) if var) * birim


def katman_varligi(zar_logic):
    """Hangi katmanlar VAR: {katman adi: bool}.

    zar_logic yoksa hepsi var sayilir - `python lab.py` tek basina
    calistiginda davranis degismesin diye.
    """
    cikti = {}
    for _alan, katman, varlik in KATMAN_ALANI:
        if varlik is None:
            cikti[katman] = True
        elif zar_logic is None:
            cikti[katman] = True
        else:
            cikti[katman] = bool(getattr(zar_logic, varlik, True))
    return cikti


def katman_bonusu(zar_logic):
    """Zar yatirimlarinin katman basina EKLEDIGI kalinlik: {ad: bonus}."""
    if zar_logic is None:
        return {}
    return {katman: getattr(zar_logic, alan, 0.0) * DEFENCE_PER_POINT
            for alan, katman, _v in KATMAN_ALANI}


def katman_tabani(zar_logic, alan, varsayilan):
    """Bu katmanin TABAN kalinligi: zar tasiyorsa ondan, yoksa varsayilan.

    Kalinlik artik hucrenin kendi ozelligi (editorden ayarlanabilir ve
    yeni kazanilan katman ince baslar); default_layers() yalnizca
    laboratuvarin tek basina calistigi durum icin bir taban saglar.
    """
    f = getattr(zar_logic, 'katman_kalinligi', None)
    if callable(f) and alan:
        try:
            return f(alan)
        except Exception:
            pass
    return varsayilan


def katman_kalinliklari(zar_logic, taban=None):
    """Katman profili: [(ad, kalinlik, renk, var_mi)] distan ice.

    OLMAYAN katman da listede kalir (kalinligiyla birlikte) ki cizim
    tarafi zarfin ne kadar INCELDIGINI gosterebilsin ve katman geri
    eklendiginde eski kalinligi bilinsin. Tuketiciler `var_mi`ye bakmali.
    """
    layers = taban if taban is not None else default_layers()
    b = katman_bonusu(zar_logic)
    v = katman_varligi(zar_logic)
    alan_of = {katman: alan for alan, katman, _var in KATMAN_ALANI}
    out = []
    for l in layers:
        t0 = katman_tabani(zar_logic, alan_of.get(l.name), l.t)
        out.append((l.name, max(0.2, min(20.0, t0 + b.get(l.name, 0.0))),
                    l.color, v.get(l.name, True)))
    return out


class LabCell:
    def __init__(self, center, core_r=110):
        self.center = pygame.math.Vector2(center)
        self.base_core_r = core_r
        self.generation = 0
        self._reset_state(core_r)
        # KULLANICININ ayarladigi kalinliklar. Savas hasarindan AYRI
        # tutulmak zorunda: reset() eskiden o anki kalinligi anlik goruntu
        # alip geri yaziyordu, ama o kalinlik lizozimin yedigi kalinlikti.
        # Hucre her olumden sonra biraz daha sakat doguyordu; duvari bir
        # kez cokmus bir hucre bir daha asla duvarli dogmuyordu.
        self.layer_t0 = [l.t for l in self.layers]
        # HEDEFIN ORGANELLERI. Kullanicinin duzenidir; katman kalinliklari
        # gibi savas hasarindan ayri tutulur ve reset'te korunur.
        self.organ_cfg = []      # [(ad, takilma_acisi), ...]
        self.organs = []         # kurulmus organ nesneleri
        self.keseler = []        # fagositozla olusan besin vakuolleri
        self.yutulan = 0         # sitostomdan iceri alinan molekul sayisi
        self.kacan = 0           # keseyi delip sitoplazmaya kacan
        self.sindirilen = 0      # kesede sindirilip yok olan
        self._build_organs()     # efflux/integrity turetilen alanlari kurar

    def _reset_state(self, core_r):
        self.core_r = core_r
        self.layers = default_layers()
        self.enabled = [True] * len(self.layers)
        self.effect = None
        self.effect_t = 0.0
        self.effect_col = FG
        self.effect_name = ''
        self.pores = []
        self.burst = []
        self.feeder = None      # emen stilet
        self.tethered = False   # volvent sardi - kacamaz
        self.sticky = False     # glutinant yapisti - sonraki atislar ISIRIR
        self.pulling = None     # izoriza: saldirgani kendine ceker
        # KACIS: hedef saldiriyi fark edince uzaklasmaya calisir. Bagli
        # degilse kacar - iste o zaman volvent bir ise yarar. Kacmayan bir
        # avi baglamanin anlami yoktur; tethered bayragi bu eklenene kadar
        # hicbir yerde OKUNMUYORDU, yalnizca cizilliyordu.
        self.home = pygame.math.Vector2(self.center)
        self.alarm = 0.0        # saldiri algilandi, kacis durumu
        self.escaped = 0.0      # ne kadar uzaklasti
        self.slow_until = 0.0   # yavaslatildi (doz esigi 1)
        self.paralyzed = False  # felcli (doz esigi 2) - hic kacamaz
        self.arrived = {}       # yuk -> VARAN molekul sayisi (doz budur)
        self.tier_of = {}       # yuk -> o yukun ulastigi kademe
        self.last_pi = None
        self.last_tier = TIER_NONE
        # Hucrenin KENDI tasidigi molekuller. Patlayinca ortama sacilirlar -
        # toksin dolu bir hucreyi patlatmak onu kimyasal bombaya cevirir.
        self.stock_pi = None
        self.stock = []          # sitoplazmadaki TEKIL molekul ofsetleri
        self._synth = 0.0
        self.spilled = False
        # Bu karede hucre ne kadar yer degistirdi. Zarfin ICINDEKI her sey
        # bu kadar tasinir - aksi halde hucre kacarken katmanlar molekulun
        # ustunden supuruyor ve hicbir delik testi yapilmadan sitoplazmadaki
        # molekul kendini duvarda buluyordu.
        self.motion = pygame.math.Vector2(0, 0)
        self.prev_center = pygame.math.Vector2(self.center)
        self._geom_key = None    # gozenek geometrisi onbellegi
        self._sheets = []
        self._flat_key = object()
        self._flat = []
        self._poly_key = object()
        self._polys = []
        self.swelling = False   # gozenek acici orta doz: siser
        self.weakened = False   # litik enzim orta doz: duvar incelir
        self.halted = False     # ic sabotaj orta doz: ureme durur
        self.dead_cell = False  # olumcul doz: patlamasa da OLDU
        self.drained = 0.0      # 0..1 emilen sitoplazma orani
        self.flow = []          # boru boyunca akan sitoplazma zerrecikleri

    def reset(self):
        """Hücreyi yenile: KULLANICININ düzenlemesi korunur, HASAR silinir."""
        self.center = pygame.math.Vector2(self.home)
        en0 = list(self.enabled)
        t0 = list(self.layer_t0)
        org0 = list(self.organ_cfg)
        self._reset_state(self.base_core_r)
        for l, t in zip(self.layers, t0):
            l.t = t
        self.enabled = en0
        self.layer_t0 = t0
        self.organ_cfg = org0
        self.keseler = []
        self.yutulan = self.kacan = self.sindirilen = 0
        self._build_organs()
        # Onceki nesle ait molekuller gecersiz olsun: hucreye BAGLI 49
        # molekul hayatta kalirken sayac sifirlaniyordu, yani ekranda
        # gorunen nokta sayisi ile sayac birbirini tutmuyordu.
        self.generation += 1

    def count_of(self, pi):
        return self.arrived.get(pi, 0)

    def clear_one(self, pi):
        """Bagli bir molekul temizlendi. Sayac duser, ETKI kalir."""
        if self.arrived.get(pi):
            self.arrived[pi] -= 1

    def receive(self, pi):
        """Bir molekul hedefine vardi. Doz = varan sayisi."""
        n = self.arrived.get(pi, 0) + 1
        self.arrived[pi] = n
        self.last_pi = pi
        tier = count_tier(pi, n)
        self.last_tier = tier
        if tier > self.tier_of.get(pi, TIER_NONE):
            self.tier_of[pi] = tier
            self.apply_tier(pi, tier)

    def apply_tier(self, pi, tier):
        """Kademe yukseldi - MOLEKULUN SINIFINA gore etkiyi uygula."""
        nm, zone, kda, dia, eff, col, chain, surf = PAYLOADS[pi]
        cls = effect_class(pi)
        n = self.count_of(pi)
        if tier == TIER_LETHAL:
            # Olumcul: orta doz bayraklari SILINIR, aksi halde onceden orta
            # doz lizozim yemis bir hucrede duvar %35'te kilitli kalir ve
            # olumcul doz gelse bile cokmez.
            self.paralyzed = True
            self.swelling = self.weakened = self.halted = False
            self.dead_cell = True
            self.trigger(eff, col, f'{nm} x{n}')
            return
        if tier == TIER_MID and cls is not None:
            mech = EFFECT_CLASS[cls][1]
            lbl = f'{nm} x{n} ({tier_label(pi, tier)})'
            if mech == 'paralyze':
                self.paralyzed = True
                self.trigger('felc', TIER_COLOR[2], lbl)
            elif mech == 'swell':
                self.swelling = True
                self.slow_until = 12.0
                self.trigger('sisme', TIER_COLOR[2], lbl)
            elif mech == 'weaken':
                self.weakened = True
                self.trigger('duvar_eri', TIER_COLOR[2], lbl)
            else:
                self.halted = True
                self.slow_until = 15.0
                self.trigger('sabotaj', TIER_COLOR[2], lbl)
        elif tier == TIER_SLOW:
            self.slow_until = 8.0

    def synth(self, dt, pi):
        """Hedef hucre de kendi molekulunu SENTEZLER ve TASIR."""
        if pi != self.stock_pi:
            self.stock_pi = pi
            self.stock = []
            self._synth = 0.0
        if PAYLOADS[pi][1] is None or self.spilled:
            return
        self._synth += STOCK_REGEN * 0.5 * dt
        while self._synth >= 1.0 and len(self.stock) < STOCK_MAX:
            self._synth -= 1.0
            a = random.uniform(0, 2 * math.pi)
            rr = random.uniform(0, self.core_r * 0.8)
            self.stock.append([math.cos(a) * rr, math.sin(a) * rr])
        for g in self.stock:
            g[0] += random.uniform(-7, 7) * dt
            g[1] += random.uniform(-7, 7) * dt

    def spill(self):
        """Patladi: tasidigi molekuller ortama SACILIR.

        Stok bir sayi degil, dagilan noktalardir - patlayan bir hucrenin
        cevresine ne yaptigi boylece dogrudan gorunur hale gelir.
        """
        if self.spilled or not self.stock or self.stock_pi is None:
            return []
        self.spilled = True
        out = []
        for g in self.stock:
            start = self.center + pygame.math.Vector2(g[0], g[1])
            d = start - self.center
            if d.length() < 1e-6:
                d = pygame.math.Vector2(1, 0)
            v = d.normalize() * random.uniform(0.5, 1.3) * MOLECULE_SPEED
            out.append(Molecule(self, start, v, self.stock_pi,
                                depth=len(self.active())))
        self.stock = []
        return out

    def trigger(self, eff, col, name):
        self.effect = eff
        self.effect_t = 0.0
        self.effect_col = col
        self.effect_name = name
        if eff == 'gozenek':
            self.pores = [random.uniform(0, 2 * math.pi) for _ in range(14)]

    def active(self):
        return [l for l, e in zip(self.layers, self.enabled) if e]

    def boundaries(self):
        r = self.outer_r
        out = []
        for l in self.active():
            out.append(r)
            r -= l.t * PX_PER_UNIT
        return out

    # ------------------------------------------------------- ORGANELLER
    #
    # Organlar Organism icin yazildi ama tam bir Organism ornegi
    # gerektirmiyorlar: draw(screen, owner) yalnizca ALTI oznitelik
    # okuyor. Bunu tahmin etmek yerine her organi sahte bir konakla
    # cizdirerek olctum - asagidaki liste o olcumun sonucu.

    @property
    def pos(self):
        return self.center if self._pos_override is None else self._pos_override

    # Cizim sirasinda gecici yaricap/konum. Organlar ORGANISM olcegi icin
    # yazildi (yaricap ~40 px); laboratuvarin dev hucresinde (304 px)
    # dogrudan cizilince mekanoreseptor 110 px'lik bir top oluyordu.
    # Cozum: organlari NORMAL olcekte ayri bir yuzeye ciz, sonra hucrenin
    # buyutmesiyle AYNI oranda olcekle. Boylece oranlar launcher'daki
    # gorunumle birebir kalir.
    _r_override = None
    _pos_override = None
    ORGAN_NOMINAL = 90.0        # organlarin cizildigi referans yaricap

    @property
    def radius(self):
        return self.outer_r if self._r_override is None else self._r_override

    @property
    def _organ_scale(self):
        return self.outer_r / self.ORGAN_NOMINAL

    @property
    def angle(self):
        return 0.0

    @property
    def direction(self):
        # Hedef kacarken saga gider; organlar yonu buradan okur.
        return pygame.math.Vector2(1, 0)

    @property
    def color(self):
        return (120, 170, 200)

    @property
    def shutdown(self):
        return self.paralyzed

    def add_organ(self, name, angle=None):
        """Hedefe organ tak. Aci verilmezse esit araliklarla dagitilir."""
        if angle is None:
            n = sum(1 for a, _ in self.organ_cfg if a == name)
            angle = (len(self.organ_cfg) * 0.79 + n * 0.31) % (2 * math.pi)
        self.organ_cfg.append((name, angle))
        self._build_organs()

    def remove_organ(self, idx):
        if 0 <= idx < len(self.organ_cfg):
            del self.organ_cfg[idx]
            self._build_organs()

    def clear_organs(self):
        self.organ_cfg = []
        self._build_organs()

    def _apply_membrane_defence(self):
        """Zar organinin savunmalarini KATMAN KALINLIGINA yansit.

        Katkı `layer_t0` (kullanicinin ayari) uzerine EKLENIR, onun yerine
        gecmez - yoksa organ takip cikarmak kullanicinin kalinlik ayarini
        kalici olarak bozardi.
        """
        bonus = [0.0] * len(self.layers)
        self.efflux = 0.0
        self.integrity = 0.0
        m = next((o for o in self.organs
                  if o.__class__.__name__ == 'Membrane'), None)
        if m is not None:
            lg = m.logic
            yer = {l.name: i for i, l in enumerate(self.layers)}
            # Kural katman_bonusu()'nda; burasi yalnizca uygular.
            for katman, ek_kal in katman_bonusu(lg).items():
                if katman in yer:
                    bonus[yer[katman]] += ek_kal
            # VARLIK maskesi de zardan gelir. Kalinlik defteri TAM liste
            # uzerinde tutulur (katman geri eklenince eski kalinligini
            # bulsun diye); gorunurluk ayri bir maske.
            v = katman_varligi(lg)
            self.enabled = [bool(v.get(l.name, True)) for l in self.layers]
            for i, l in enumerate(self.layers):
                if l.name == ZORUNLU_KATMAN:
                    self.enabled[i] = True
            # Efflux pompasi ve onarim: molekulu KATMANDA durdurmaz,
            # baglandiktan sonra daha hizli TEMIZLER.
            self.efflux = getattr(lg, 'efflux', 0.0) + getattr(lg, 'repair', 0.0)
            self.integrity = getattr(lg, 'max_integrity', 0.0)
        # TABAN kalinlik da zardan gelebilir (editorden ayarlanabiliyor).
        _alan_of = {katman: alan for alan, katman, _v in KATMAN_ALANI}
        _zl = m.logic if m is not None else None
        for i, l in enumerate(self.layers):
            t0 = katman_tabani(_zl, _alan_of.get(l.name), self.layer_t0[i])
            l.t = max(0.2, min(20.0, t0 + bonus[i]))
        self._geom_key = None      # geometri degisti, gozenekler yeniden

    def set_layer_present(self, i, var):
        """Katmani ekle/cikar. `enabled`in tek yazicisi burasidir.

        Ham `enabled[i] = ...` yazmak uc seyi atliyordu: plazma zarini
        silmeyi engellemek, secimi zar organina geri yazmak (yoksa duzenleme
        kayda/evrime/savasa hic ulasmaz) ve gecmis nesli emekli etmek
        (ucus halindeki molekuller donmus katman indeksi tasiyor).
        """
        if not (0 <= i < len(self.layers)):
            return False
        if self.layers[i].name == ZORUNLU_KATMAN:
            return False
        var = bool(var)
        ad = self.layers[i].name
        alan = next((v for _a, k, v in KATMAN_ALANI if k == ad), None)
        m = next((o for o in self.organs
                  if o.__class__.__name__ == 'Membrane'), None)
        if m is not None and alan:
            setattr(m.logic, alan, var)
        self.enabled[i] = var
        self._apply_membrane_defence()
        self.generation += 1      # ucustaki molekuller emekli olsun
        return True

    def set_presence(self, maske):
        """Katman varligini toplu ayarla: {katman adi: bool}."""
        m = next((o for o in self.organs
                  if o.__class__.__name__ == 'Membrane'), None)
        for _alan, katman, varlik in KATMAN_ALANI:
            if varlik is None:
                continue
            if katman in maske and m is not None:
                setattr(m.logic, varlik, bool(maske[katman]))
        self._apply_membrane_defence()
        self.generation += 1

    @classmethod
    def from_organism(cls, org, center, core_r=110):
        """Bir Organism'den LABORATUVAR gorunumu kur.

        Ana oyundaki hucre 10 px cizilir; katman/gozenek yapisi o boyutta
        anlamsizdir. Dunyayi 30 kat buyutmek yerine (olculdu: cizim yuzeyi
        3.46 GB'a cikiyor) SECILEN hucreyi laboratuvar olceginde ayrica
        cizeriz. Ekosistem kendi olceginde kalir.
        """
        c = cls(center, core_r)
        cfg = []
        for o in getattr(org, 'organs', []):
            ad = o.__class__.__name__
            if ad in ORGAN_CAPA:
                cfg.append((ad, float(getattr(o, 'attachment_angle', 0.0) or 0.0)))
        c.organ_cfg = cfg
        c._build_organs()
        # Zar savunmalari organizmadan KOPYALANIR: lab kendi Membrane
        # organini varsayilan (hepsi 0) degerlerle kuruyor, oysa gorunmesi
        # gereken sey organizmanin GERCEK zirhi.
        kay = next((o for o in getattr(org, 'organs', [])
                    if o.__class__.__name__ == 'Membrane'), None)
        hed = next((o for o in c.organs
                    if o.__class__.__name__ == 'Membrane'), None)
        if kay is not None and hed is not None:
            for alan in ('wall', 'outer', 'capsule', 'efflux', 'repair',
                         'slip', 'mucus', 'slayer', 'max_integrity',
                         'integrity',
                         # VARLIK bayraklari: bunlar kopyalanmazsa kesit
                         # her hucreyi bes katmanli cizerdi.
                         'var_mucus', 'var_capsule', 'var_slayer', 'var_wall'):
                if hasattr(kay.logic, alan) and hasattr(hed.logic, alan):
                    try:
                        setattr(hed.logic, alan, getattr(kay.logic, alan))
                    except Exception:
                        pass
            c._apply_membrane_defence()
        return c

    # ------------------------------------------------------- SITOSTOM
    @property
    def agizlar(self):
        """Takili sitostomlarin acilari."""
        return [a for (ad, a) in self.organ_cfg if ad == 'Phagocytosis']

    @property
    def sert_yuzey(self):
        """Yuzey fagositoza izin vermeyecek kadar sert mi?"""
        # Katman VARSA ve kalinligi esigi asiyorsa yuzey serttir. Duvar
        # ya da S-layer kaldirilinca hucre yumusar: kendi sitostomunu
        # acabilir ve fagosite EDILEBILIR. Duvar hep var oldugu surece
        # fagositoz hicbir hucrede calismiyordu.
        for l, en in zip(self.layers, self.enabled):
            if en and l.name in SERT_KATMANLAR and l.t > SERT_ESIK:
                return l.name
        return None

    @property
    def sitostom_aktif(self):
        return bool(self.agizlar) and self.sert_yuzey is None

    def agza_girdi(self, pos):
        """Bu konum bir agzin acisal penceresinde ve zarfin ICINDE mi?"""
        if not self.sitostom_aktif:
            return None
        d = pos - self.center
        r = d.length()
        if r > self.outer_r or r < self.core_r * 0.55:
            return None
        a = math.atan2(d.y, d.x)
        for ag in self.agizlar:
            fark = abs((a - ag + math.pi) % (2 * math.pi) - math.pi)
            if fark <= MOUTH_HALF:
                return ag
        return None

    def yut(self, pi, ang, r):
        """Molekulu keseye al. Fagositoz bir GIRIS yoludur."""
        self.keseler.append(Kese(self, ang, min(r, self.outer_r * 0.95), pi))
        self.yutulan += 1

    @property
    def escape_speed(self):
        """Motor organlar hedefi hizlandirir - kacan hedefi vurmak zorlasir."""
        itki = 0.0
        for o in self.organs:
            ad = o.__class__.__name__
            if ad == 'Cilia':
                itki += getattr(o.logic, 'base_thrust_magnitude', 0.0)
            elif ad == 'Flagella':
                itki += getattr(o.logic, 'base_thrust', 0.0) * 0.25
        return ESCAPE_BASE + itki * ESCAPE_PER_THRUST

    @property
    def alarm_bonus(self):
        """Receptorler saldiriyi daha erken fark ettirir - kacis uzar."""
        return ALARM_PER_SENSOR * sum(
            1 for o in self.organs if o.__class__.__name__ in
            ('Photoreceptor', 'Mechanoreceptor', 'Chemoreceptor'))

    def _build_organs(self):
        """Yapilandirmadan organ nesnelerini kur."""
        self.organs = []
        for ad, aci in self.organ_cfg:
            try:
                try:
                    o = make_organ(ad, attachment_angle=aci)
                except TypeError:
                    o = make_organ(ad)       # ic organlarin acisi yok
            except Exception:
                continue                      # bozuk kayit atisi engellemesin
            self.organs.append(o)
        self._apply_membrane_defence()

    def _capa_r(self, katman):
        """Çapa katmanının NOMINAL ölçekteki yarıçapı."""
        k = self._organ_scale
        if katman is not None:
            r = self.outer_r
            for l in self.active():
                inner = r - l.t * PX_PER_UNIT
                if l.name == katman:
                    return (r + inner) * 0.5 / k
                r = inner
        return self.core_r * 0.72 / k        # sitoplazma

    def draw_organs(self, s):
        if not self.organs:
            return
        R = self.ORGAN_NOMINAL
        yan = int(R * 4)
        # IKI ayri tampon: dis organlarin duyu menzili gorselleri kesiti
        # boguyor, o yuzden onlar yari saydam. Ic organlarda boyle bir sorun
        # yok ve tek tampon kullanmak vakuolu gorunmez kiliyordu - kendi
        # alfasi 150, katmanin alfasi 150, etkin %35.
        buf = pygame.Surface((yan, yan), pygame.SRCALPHA)      # dis
        buf_ic = pygame.Surface((yan, yan), pygame.SRCALPHA)   # ic
        merkez = pygame.math.Vector2(yan * 0.5, yan * 0.5)
        self._pos_override = merkez
        aci_of = {i: a for i, (_ad, a) in enumerate(self.organ_cfg)}
        try:
            for i, o in enumerate(self.organs):
                ad = o.__class__.__name__
                katman, uzanir = ORGAN_CAPA.get(ad, (None, False))
                ar = self._capa_r(katman)
                if uzanir:
                    # ZARFI KESEN GOVDE: taban capa katmaninda, sap butun
                    # katmanlari delerek disari cikar. Kalin duvar yapinca
                    # sapin uzadigi - yani makinenin daha cok is yapmak
                    # zorunda kaldigi - gozle gorulur.
                    a = aci_of.get(i, 0.0)
                    yon = pygame.math.Vector2(math.cos(a), math.sin(a))
                    tab = merkez + yon * ar
                    uc = merkez + yon * R
                    dik = pygame.math.Vector2(-yon.y, yon.x)
                    if ad == 'Phagocytosis':
                        # SITOSTOM: disa dogru acilan bir huni. Bogazi
                        # sitoplazmada, agzi disarida - zarfi bastan basa
                        # deler, cunku bir AGIZ tam olarak budur.
                        pygame.draw.polygon(buf, (58, 58, 86),
                                            [tab + dik * 3, uc + dik * 15,
                                             uc - dik * 15, tab - dik * 3])
                        pygame.draw.lines(buf, (205, 205, 255), False,
                                          [uc + dik * 15, tab + dik * 3,
                                           tab - dik * 3, uc - dik * 15], 2)
                    else:
                        d2 = dik * 2.6
                        pygame.draw.polygon(buf, (188, 196, 214),
                                            [tab + d2, uc + d2, uc - d2, tab - d2])
                        pygame.draw.polygon(buf, (96, 104, 124),
                                            [tab + d2, uc + d2, uc - d2, tab - d2], 1)
                    # taban halkasi (kamcida MS halkasi, T6SS'te taban levhasi)
                    if ad != 'Phagocytosis':
                        pygame.draw.circle(buf, (210, 218, 236),
                                           (int(tab.x), int(tab.y)), 5)
                        pygame.draw.circle(buf, (70, 78, 96),
                                           (int(tab.x), int(tab.y)), 5, 1)
                    self._r_override = R          # gorunen ucu disarida
                else:
                    self._r_override = ar         # capa katmaninda durur
                hedef = buf if (uzanir or katman is not None) else buf_ic
                try:
                    o.draw(hedef, self)
                except Exception:
                    pass      # bir organ cizilmezse laboratuvar durmasin
        finally:
            self._r_override = None
            self._pos_override = None
        k = self._organ_scale
        yeni = max(2, int(yan * k))
        kose = (int(self.center.x - yeni * 0.5), int(self.center.y - yeni * 0.5))
        # IC organlar TAM alfayla - vakuol ve iskelet gorunsun
        s.blit(pygame.transform.smoothscale(buf_ic, (yeni, yeni)), kose)
        buf = pygame.transform.smoothscale(buf, (yeni, yeni))
        # Fotoreseptorun gorme konisi ve mekanoreseptorun isitme aurasi
        # DUYU MENZILI gorselleridir ve dev hucrede 47.000 pikseli
        # kapliyorlar - katman kesitini tamamen boguyorlardi. Organ katmani
        # yari saydam cizilir; laboratuvarin asil isi katmanlari gostermek.
        buf.set_alpha(ORGAN_ALPHA)
        s.blit(buf, kose)

    # --------------------------------------------------- gercek gozenekler
    def sheets(self):
        """Katman katman GERCEK delik geometrisi.

        Kalinlik degistiginde ya da katman acilip kapandiginda yeniden
        uretilir; aksi halde onbellekten gelir ki delikler her karede
        yerinden oynamasin.
        """
        key = (tuple(self.enabled), round(self.core_r, 1),
               tuple(round(l.t, 2) for l in self.layers))
        if key != self._geom_key:
            self._geom_key = key
            self._sheets = self._build_sheets()
        return self._sheets

    def flat_sheets(self):
        """Butun tabakalar DISARIDAN ICERI sirali: (yaricap, katman, tabaka).

        Sirali islemek onemli: hizli bir molekul tek karede birkac tabaka
        birden gecebilir; sirasiz bakarsak duvari atlayip sitoplazmaya
        'tunelleyebilir'.
        """
        self.sheets()
        if self._flat_key != self._geom_key:
            self._flat_key = self._geom_key
            fl = []
            for bi, band in enumerate(self._sheets):
                for sh in band:
                    fl.append((sh.r, bi, sh))
            fl.sort(key=lambda x: -x[0])
            self._flat = fl
        return self._flat

    def pore_polys(self):
        """Deliklerin cizim poligonlari. Geometri degisince yeniden uretilir."""
        self.sheets()
        if self._poly_key != self._geom_key:
            self._poly_key = self._geom_key
            self._polys = self._build_polys()
        return self._polys

    def _build_polys(self):
        out = []
        r = self.outer_r
        for l, band in zip(self.active(), self._sheets):
            inner = r - l.t * PX_PER_UNIT
            n_sheet = len(band)
            for k, sh in enumerate(band):
                if sh.solid:
                    continue
                # bu alt tabakanin radyal dilimi
                r1 = r - (r - inner) * k / n_sheet
                r0 = r - (r - inner) * (k + 1) / n_sheet
                order = LAYER_ORDER.get(l.name, 0.5)
                rnd = random.Random(int(sh.r * 31) + k)
                for a, w in sh.pores:
                    h = (w * 0.5) / sh.r          # yari aci
                    steps = max(3, min(9, int(w / 12) + 3))
                    # DUZENSIZ katmanda delik agzi pürüzlüdür - jel bir agin
                    # kesiti makineyle kesilmis gibi duz olmaz.
                    ru = (1 - order) * (r1 - r0) * 0.22
                    pts = []
                    for j in range(steps + 1):    # dis yay
                        ang = a - h + 2 * h * j / steps
                        rr_ = r1 - rnd.uniform(0, ru)
                        pts.append((math.cos(ang) * rr_, math.sin(ang) * rr_))
                    for j in range(steps + 1):    # ic yay (geri)
                        ang = a + h - 2 * h * j / steps
                        rr_ = r0 + rnd.uniform(0, ru)
                        pts.append((math.cos(ang) * rr_, math.sin(ang) * rr_))
                    out.append(pts)
            r = inner
        return out

    def _build_sheets(self):
        out = []
        r = self.outer_r
        for l in self.active():
            inner = r - l.t * PX_PER_UNIT
            if l.mesh <= 0 or l.porosity <= 0:
                # Lipit cift katmani: delik YOKTUR. Gecmek isteyen yarmak
                # ya da bir kanal proteini kullanmak zorundadir.
                out.append([Sheet((r + inner) * 0.5, [], True)])
                r = inner
                continue
            pw = l.mesh * PORE_PX
            order = LAYER_ORDER.get(l.name, 0.5)
            # Ince delikli kalin katman COK TABAKALIDIR: molekul her
            # tabakada ayri bir delik bulmak zorunda kalir.
            #
            # Kristal bir katman (S-layer) gercekte TEK bir tabakadir.
            # Duzensiz bir JEL ise uc boyutlu bir agdir; tek 2B tabaka
            # olarak cizince ekranda birkac dev bosluk gibi gorunuyordu.
            # En az uc tabaka hem dokuyu bir orgü gibi okutuyor hem de
            # fizikce daha dogru.
            taban = 1 if order >= 0.9 else 3
            n_sheet = max(taban, min(MAX_SHEETS,
                                     int(round(l.t / max(l.mesh, 0.4)))))
            rnd = random.Random(sum(ord(c) for c in l.name) * 977)
            band = []
            for k in range(n_sheet):
                rr = inner + (r - inner) * (k + 0.5) / n_sheet
                n = max(3, int(2 * math.pi * rr * l.porosity / pw))
                pores = []
                for j in range(n):
                    a = 2 * math.pi * j / n
                    if order < 1.0:
                        # Duzensiz katmanda delikler hem KAYAR hem de
                        # genislikleri degisir; alt tabakalar hizalanmaz.
                        a += (1 - order) * rnd.uniform(-math.pi / n, math.pi / n)
                        w = pw * (1 + (1 - order) * rnd.uniform(-0.4, 0.4))
                    else:
                        w = pw
                    pores.append((a % (2 * math.pi), w))
                band.append(Sheet(rr, pores, False))
            out.append(band)
            r = inner
        return out

    @property
    def outer_r(self):
        return self.core_r + sum(l.t for l in self.active()) * PX_PER_UNIT

    GHOST_BAND = 16      # kapali katmanlarin disarida gosterildigi serit

    def ghost_rings(self):
        """Kapalı katmanlar dışarıda ince hayalet halka olarak durur ki
        tıklayıp geri eklenebilsinler."""
        out = []
        r = self.outer_r + 14
        for i, l in enumerate(self.layers):
            if not self.enabled[i]:
                out.append((i, l, r, r + self.GHOST_BAND))
                r += self.GHOST_BAND + 4
        return out

    def hit_layer(self, pos):
        """Farenin üstünde hangi katman var? (indeks, kapalı mı) döndürür."""
        d = pygame.math.Vector2(pos).distance_to(self.center)
        for i, l, r0, r1 in self.ghost_rings():
            if r0 <= d <= r1:
                return i, True
        r = self.outer_r
        for l in self.active():
            inner = r - l.t * PX_PER_UNIT
            if inner <= d <= r:
                return self.layers.index(l), False
            r = inner
        return None, False

    def bump_thickness(self, idx, delta):
        # Kullanicinin ISTEDIGI kalinligi degistir, organ katkisini degil.
        # Once `l.t`yi okuyup layer_t0'a yaziyordum; zar organi takiliyken
        # bu, organ katkisini kullanicinin ayarina KALICI olarak gomuyordu.
        self.layer_t0[idx] = max(0.5, min(20.0, self.layer_t0[idx] + delta))
        self._apply_membrane_defence()

    # ------------------------------------------------------------ etkiler

    def update(self, dt):
        _p0 = pygame.math.Vector2(self.center)
        try:
            self._update(dt)
        finally:
            self.motion = self.center - _p0
            self.prev_center = _p0

    def _update(self, dt):
        # --- KACIS: bagli degilse uzaklasir
        if self.alarm > 0.0:
            self.alarm = max(0.0, self.alarm - dt)
            if not self.tethered and self.feeder is None and not self.paralyzed:
                # Kacis hizi 46 iken difuzyon (55 px/sn) hedefi hic
                # yakalayamiyordu - saniyede 9 px kazaniyordu. Molekuler
                # tasiyicilarin dozu hic teslim edilemiyordu. Hucre dusuk
                # Reynolds rejiminde zaten yavas yuzer.
                hiz = self.escape_speed
                if self.slow_until > 0.0:
                    self.slow_until = max(0.0, self.slow_until - dt)
                    hiz *= 0.30          # yavaslatildi
                self.center.x = min(VIEW_W - 60, self.center.x + hiz * dt)
                self.escaped = self.center.x - self.home.x

        # --- MIZOSITOZ: stilet sitoplazmayi cekiyor
        if self.burst and self.feeder is not None:
            # Hucre patladiysa emilecek sitoplazma kalmadi. Emis ile lizis
            # birbirini disliyor: gozenek acici bir yuk sectiysen stilet
            # yemegini kaybeder. Besleyici silaha PATLATAN yuk takmak yanlis.
            self.feeder.feeding = False
            self.feeder.dead = True
            self.feeder = None
            self.flow = []
        if self.feeder is not None and self.drained < 1.0:
            self.drained = min(1.0, self.drained + DRAIN_RATE * dt)
            self.core_r = self.base_core_r * (1.0 - 0.72 * self.drained)
            if random.random() < 0.5:
                self.flow.append([0.0, random.uniform(-4, 4)])
            for fl in self.flow:
                fl[0] += dt * 0.9
            self.flow = [fl for fl in self.flow if fl[0] < 1.0]
            if self.drained >= 1.0:
                self.effect = 'tukendi'
                self.effect_col = (255, 170, 90)
                self.effect_name = 'sitoplazma emildi'
        for kk in self.keseler:
            kk.update(dt)
        self.keseler = [kk for kk in self.keseler if not kk.bitti]
        if not self.effect:
            return
        self.effect_t += dt
        if self.effect == 'gozenek':
            # OZMOTIK COKUS: gozeneklerden su dolar, hucre siser, patlar
            if self.effect_t < 3.2:
                self.core_r = self.base_core_r * (1.0 + 0.32 * self.effect_t / 3.2)
            elif not self.burst:
                for _ in range(110):
                    a = random.uniform(0, 2 * math.pi)
                    sp = random.uniform(60, 280)
                    self.burst.append([pygame.math.Vector2(self.center),
                                       pygame.math.Vector2(math.cos(a), math.sin(a)) * sp,
                                       random.uniform(2, 6)])
        elif self.effect == 'duvar_eri':
            # DIS SINDIRIM: duvar kalinligi erir. ORTA dozda tamamen
            # cozulmez, yalnizca INCELIR - ama bu mekanik savunmayi dusurur,
            # yani sonraki delici saldiri icin kapi acar.
            hedef = 0.35 if self.weakened else 0.0
            # Katman ADIYLA bulunur: indeks 3 sabit yazilmisti, oysa
            # duvari olmayan hucrede o indeks baska bir katman. 6.0 da
            # sabit yazilmisti; kullanicinin kalinlastirdigi duvar
            # orantili erimeliydi.
            _duv = next((l for l in self.active() if l.name == 'Duvar'), None)
            if _duv is not None:
                _t0 = self.layer_t0[self.layers.index(_duv)]
                _duv.t = max(_t0 * hedef,
                             _t0 * max(0.0, 1.0 - self.effect_t / 3.0))
        elif self.effect == 'sisme':
            # OZMOTIK SISME: patlamiyor ama buyuyor - orta doz
            self.core_r = self.base_core_r * (1.0 + 0.18 * min(1.0, self.effect_t / 2.5))
        for b in self.burst:
            b[0] += b[1] * dt
            b[1] *= 0.97
        # Patlama animasyonu bitince hucre kendini yeniler ki deneye
        # devam edilebilsin. Laboratuvar; her seferinde elle sifirlamak
        # gereksiz surtunme yaratiyordu.
        if (self.burst or self.dead_cell) and self.effect_t > 6.0:
            self.reset()

    # ------------------------------------------------------------- cizim

    def draw(self, s, font, small):
        cx, cy = int(self.center.x), int(self.center.y)
        r = self.outer_r
        rings = []
        for l in self.active():
            inner = r - l.t * PX_PER_UNIT
            rings.append((l, r, inner))
            r = inner

        if self.burst:
            for b in self.burst:
                pygame.draw.circle(s, (235, 115, 145),
                                   (int(b[0].x), int(b[0].y)), int(b[2]))
            txt = font.render('OZMOTIK LYSIS — hucre patladi', True, BAD)
            s.blit(txt, (cx - txt.get_width() // 2, cy - 12))
            kalan = max(0.0, 6.0 - self.effect_t)
            t2 = font.render(f'yeni hucre {kalan:.1f} sn', True, DIM)
            s.blit(t2, (cx - t2.get_width() // 2, cy + 12))
            return

        for l, outer, inner in rings:
            pygame.draw.circle(s, l.color, (cx, cy), int(outer))
        core_col = (30, 34, 48)
        if self.effect == 'sabotaj':
            k = min(1.0, self.effect_t / 2.5)
            core_col = (int(30 + 60 * k), max(0, int(34 - 20 * k)), int(48 + 40 * k))
        pygame.draw.circle(s, core_col, (cx, cy), int(self.core_r))

        # GERCEK GOZENEKLER: cizilen delikler molekulun gectigi deliklerin
        # ta kendisidir. Onceki _pores() yalnizca dekoratif bir yaklasimdi
        # ve fizikle hicbir baglantisi yoktu.
        for pts in self.pore_polys():
            pygame.draw.polygon(s, PORE_COL,
                                [(cx + px, cy + py) for px, py in pts])
        # Sinir cemberleri deliklerin USTUNE cizilir: aksi halde acikligi
        # yuksek bir katman (mukus %90 acik) kirik bir halka gibi gorunuyor
        # ve hangi bandin nerede bittigi okunmuyordu.
        for l, outer, inner in rings:
            pygame.draw.circle(s, tuple(max(0, c - 40) for c in l.color),
                               (cx, cy), int(outer), 2)
            if inner > 2:
                pygame.draw.circle(s, tuple(max(0, c - 70) for c in l.color),
                                   (cx, cy), int(inner), 1)
        pygame.draw.circle(s, (70, 80, 110), (cx, cy), int(self.core_r), 2)

        self.draw_organs(s)          # organeller katmanlarin USTUNDE
        for kk in self.keseler:
            kk.draw(s)
        self._draw_stock(s, cx, cy)
        self._draw_effect(s, cx, cy, rings)

        # VOLVENT: ava sarilmis iplik
        if self.tethered:
            rnd = random.Random(3)
            for k in range(7):
                a0 = rnd.uniform(0, 2 * math.pi)
                rr = self.outer_r + 3
                pts = [(int(cx + math.cos(a0 + t * 0.9) * (rr - t * 3)),
                        int(cy + math.sin(a0 + t * 0.9) * (rr - t * 3)))
                       for t in range(9)]
                pygame.draw.lines(s, (235, 225, 170), False, pts, 2)
            t1 = small.render('BAGLANDI - kacamaz', True, (235, 225, 170))
            s.blit(t1, (cx - t1.get_width() // 2, cy - self.outer_r - 34))
        elif self.paralyzed:
            t1 = small.render('FELCLI - hic kacamiyor', True, TIER_COLOR[2])
            s.blit(t1, (cx - t1.get_width() // 2, cy - self.outer_r - 34))
        elif self.slow_until > 0.0:
            t1 = small.render(f'YAVASLADI  {self.escaped:+.0f} px', True, TIER_COLOR[1])
            s.blit(t1, (cx - t1.get_width() // 2, cy - self.outer_r - 34))
        elif self.alarm > 0.0:
            t1 = small.render(f'KACIYOR  {self.escaped:+.0f} px', True, BAD)
            s.blit(t1, (cx - t1.get_width() // 2, cy - self.outer_r - 34))
        # GLUTINANT: yapiskan yuzey
        if self.sticky:
            for k in range(26):
                a = 2 * math.pi * k / 26
                pygame.draw.circle(s, (200, 235, 140),
                                   (int(cx + math.cos(a) * (self.outer_r + 4)),
                                    int(cy + math.sin(a) * (self.outer_r + 4))), 4)
            t2 = small.render('YAPISKAN - atislar hep isirir', True, (200, 235, 140))
            s.blit(t2, (cx - t2.get_width() // 2, cy - self.outer_r - 18))

        # MIZOSITOZ: boru boyunca GERI akan sitoplazma
        if self.feeder is not None:
            a = self.feeder.origin
            b = self.feeder.pos
            for t, off in self.flow:
                px = b.x + (a.x - b.x) * t
                py = b.y + (a.y - b.y) * t + off
                pygame.draw.circle(s, (150, 220, 190), (int(px), int(py)), 3)
            bar = small.render(f'EMILIYOR  %{100*self.drained:.0f}', True, (255, 170, 90))
            s.blit(bar, (cx - bar.get_width() // 2, cy + 22))

        # kapali katmanlar: disarida ince hayalet halka (tiklanabilir)
        for i, l, r0, r1 in self.ghost_rings():
            pygame.draw.circle(s, tuple(c // 3 for c in l.color), (cx, cy), int(r1), 2)
            pygame.draw.circle(s, tuple(c // 4 for c in l.color), (cx, cy), int(r0), 1)
            tag = small.render(f'{l.name} (kapali)', True, tuple(c // 2 + 40 for c in l.color))
            s.blit(tag, (cx - tag.get_width() // 2, int(cy - (r0 + r1) / 2) - 7))

        lbl = small.render('sitoplazma', True, DIM)
        s.blit(lbl, (cx - lbl.get_width() // 2, cy - 8))

        top = cy - self.outer_r + 10
        for i, (l, outer, inner) in enumerate(rings):
            mid = (outer + inner) * 0.5
            ly, lx = top + i * 30, 24
            px = cx - mid
            pygame.draw.line(s, l.color, (lx + 205, ly + 7), (px, cy), 1)
            pygame.draw.circle(s, l.color, (int(px), cy), 3)
            pygame.draw.rect(s, (0, 0, 0), (lx - 4, ly - 3, 215, 26))
            s.blit(small.render(l.name, True, l.color), (lx, ly))
            s.blit(small.render(f"gozenek {l.mesh:g}   B {l.B:g}   kal {l.t:.1f}",
                                True, DIM), (lx, ly + 13))

    def _draw_stock(self, s, cx, cy):
        if not self.stock or self.stock_pi is None:
            return
        col = PAYLOADS[self.stock_pi][5]
        rad = max(2, int(round(PAYLOADS[self.stock_pi][3] * PORE_PX * 0.5)))
        for g in self.stock:
            pygame.draw.circle(s, col, (int(cx + g[0]), int(cy + g[1])), rad)
            pygame.draw.circle(s, (16, 20, 32),
                               (int(cx + g[0]), int(cy + g[1])), rad, 1)

    def _draw_effect(self, s, cx, cy, rings):
        if self.dead_cell and not self.burst:
            # PATLAMAYAN olum (norotoksin, ic sabotaj): hucre kararir ve
            # durur. Bu overlay olmadan olumcul doz, felc dozuyla birebir
            # ayni gorunuyordu - kademeler gorsel olarak ayirt edilemiyordu.
            veil = pygame.Surface((self.outer_r * 2 + 20,) * 2, pygame.SRCALPHA)
            pygame.draw.circle(veil, (8, 10, 16, 132),
                               (int(self.outer_r) + 10,) * 2, int(self.outer_r) + 8)
            s.blit(veil, (cx - int(self.outer_r) - 10, cy - int(self.outer_r) - 10))
            pygame.draw.circle(s, (170, 60, 60), (cx, cy), int(self.outer_r + 6), 3)
            lbl = pygame.font.Font(None, 26).render('OLDU', True, (255, 120, 120))
            s.blit(lbl, (cx - lbl.get_width() // 2,
                         cy - int(self.outer_r) - 32))
        if self.effect == 'gozenek' and rings:
            l, outer, inner = rings[-1]
            mid = (outer + inner) * 0.5
            for a in self.pores:
                px, py = cx + math.cos(a) * mid, cy + math.sin(a) * mid
                pygame.draw.circle(s, (18, 28, 58), (int(px), int(py)), 7)
                pygame.draw.circle(s, INFO, (int(px), int(py)), 7, 2)
                for k in range(3):        # iceri akan su
                    t = (self.effect_t * 95 + k * 24) % 66
                    ix, iy = cx + math.cos(a) * (mid - t), cy + math.sin(a) * (mid - t)
                    if (ix - cx) ** 2 + (iy - cy) ** 2 > (self.core_r * 0.28) ** 2:
                        pygame.draw.circle(s, INFO, (int(ix), int(iy)), 2)
        elif self.effect == 'sisme' and rings:
            # Zar YIRTILMIYOR - sadece sizdiriyor. Iceri dogru akan su
            # damlaciklari, patlamaya giden 'gozenek' gorselinden farkli
            # olarak DISARI dogru bir patlama halkasi cizmez.
            l, outer, inner = rings[-1]
            mid = (outer + inner) * 0.5
            for k in range(10):
                a = k * 2 * math.pi / 10 + self.effect_t * 0.4
                t = (self.effect_t * 60 + k * 17) % 55
                ix, iy = cx + math.cos(a) * (mid - t), cy + math.sin(a) * (mid - t)
                pygame.draw.circle(s, (140, 200, 255), (int(ix), int(iy)), 3)
            pygame.draw.circle(s, (140, 200, 255), (cx, cy), int(self.core_r), 2)
        elif self.effect == 'duvar_eri' and self.weakened:
            # INCELMIS duvar: coken duvardan farkli olarak hala orada,
            # ama artik delici bir saldiriyi durduramaz.
            pygame.draw.circle(s, (255, 200, 110), (cx, cy),
                               int(self.outer_r + 4), 1)
            s.blit(pygame.font.Font(None, 18).render('duvar zayif', True,
                   (255, 200, 110)), (cx - 34, cy - int(self.outer_r) - 24))
        elif self.effect == 'felc':
            w = 3 + int(2 * math.sin(self.effect_t * 6))
            pygame.draw.circle(s, (255, 220, 120), (cx, cy), int(self.outer_r + 7), w)
        elif self.effect == 'sabotaj':
            rnd = random.Random(7)
            for _ in range(26):
                a = rnd.uniform(0, 2 * math.pi)
                rr = rnd.uniform(0, self.core_r * 0.85)
                px, py = cx + math.cos(a) * rr, cy + math.sin(a) * rr
                pygame.draw.line(s, (220, 130, 255),
                                 (px - 6, py - 6), (px + 6, py + 6), 2)


def _labcell_sinir_icinde(self, pos):
    """Laboratuvarda mermi pencereden cikinca biter. Oyun hucresi
    (HedefZarf) kendi sinirini koyar - dunya 2400x1600, pencere degil."""
    return 0 < pos.x < VIEW_W and 0 < pos.y < HEIGHT


LabCell.sinir_icinde = _labcell_sinir_icinde


class Attacker:
    """Silahli hucre. Tasiyici, belirtec ve yuk GOVDESINDE gorunur."""

    def __init__(self, pos, r=82):
        self.pos = pygame.math.Vector2(pos)
        self.r = r
        self.recoil = 0.0          # ates ettiginde geri tepme
        self.filled = 0.0          # emilen sitoplazma (mizositoz)
        self.energy = 100.0        # enerji havuzu
        self.max_energy = 100.0
        self.spent = 0.0           # son atisin bedeli (gosterge)
        self.blocked = False       # enerji yetmedi
        self.unlimited = False     # E tusu: bedelleri yok say
        self.pi = 1
        self.stock_pi = None
        self.stock = []            # govdedeki TEKIL molekullerin ofsetleri
        self._synth = 0.0
        self.no_stock = False      # son atis stok yetmedigi icin olmadi

    def muzzle(self):
        """Silahin ucu - atisin ciktigi nokta."""
        return self.pos + pygame.math.Vector2(self.r + self.weapon_len(), 0)

    def weapon_len(self):
        return {0: 0, 1: 16, 2: 74, 3: 66, 4: 82,
                5: 46, 6: 44, 7: 42, 8: 44}.get(self.ci, 46)

    def update(self, dt, ci=0, feeding=False):
        if self.recoil > 0:
            self.recoil = max(0.0, self.recoil - dt * 60)
        # Metabolik gelir eksi surekli bakim: silahi TASIMAK bedava degil,
        # ama bos beklemek de oldurucu olmamali.
        if self.unlimited:
            self.energy = self.max_energy
        else:
            self.energy += (BASE_REGEN - CARRIER_COST[ci][0]) * dt
        if feeding:
            self.energy -= STYLET_FEED_COST * dt       # emis makinesi
            self.energy += 9.0 * dt                    # ama sitoplazma GELIR
        self.energy = max(0.0, min(self.max_energy, self.energy))

    def can_fire(self, ci, pi):
        return self.unlimited or self.energy >= shot_total_cost(ci, pi)[0]

    def synth(self, dt, pi):
        """Molekul sentezi. Yuk degisirse stok sifirdan kurulur - hucre
        elindeki toksini baska bir toksine ceviremez."""
        if pi != self.stock_pi:
            self.stock_pi = pi
            self.stock = []
            self._synth = 0.0
        if PAYLOADS[pi][1] is None:
            return
        self._synth += STOCK_REGEN * dt
        while self._synth >= 1.0 and len(self.stock) < STOCK_MAX:
            self._synth -= 1.0
            a = random.uniform(0, 2 * math.pi)
            rr = random.uniform(0, self.r * 0.72)
            self.stock.append([math.cos(a) * rr, math.sin(a) * rr])
        # Brown hareketi: tasinirken de duruyor degiller
        for g in self.stock:
            g[0] += random.uniform(-9, 9) * dt
            g[1] += random.uniform(-9, 9) * dt
            d = math.hypot(g[0], g[1])
            if d > self.r * 0.78:
                g[0] *= self.r * 0.78 / d
                g[1] *= self.r * 0.78 / d

    def has_stock(self, ci, pi):
        n = CARRIER_EMIT[ci]
        ok = not n or PAYLOADS[pi][1] is None or len(self.stock) >= n
        if ok:
            self.no_stock = False    # sentez yetisti, uyari kalkmali
        return ok

    def take(self, n):
        """Atis icin stoktan molekul cek. Yetmezse atis olmaz."""
        if len(self.stock) < n:
            self.no_stock = True
            return False
        del self.stock[:n]
        self.no_stock = False
        return True

    def pay_shot(self, ci, pi):
        cost, _parts = shot_total_cost(ci, pi)
        if self.unlimited:
            self.spent = cost
            self.blocked = False
            return True
        if self.energy < cost:
            self.blocked = True
            return False
        self.energy -= cost
        self.spent = cost
        self.blocked = False
        return True

    def draw(self, s, f, fs, ci, pi, mi, armed):
        self.ci, self.pi, self.mi = ci, pi, mi
        cx = int(self.pos.x - self.recoil)
        cy = int(self.pos.y)
        cname, cp, _cd = CARRIERS[ci]
        pcol = PAYLOADS[pi][5]
        mcol = MARKERS[mi][2]

        # --- govde: zar + sitoplazma
        pygame.draw.circle(s, (72, 96, 84), (cx, cy), self.r + 7)
        pygame.draw.circle(s, (52, 72, 62), (cx, cy), self.r + 7, 2)
        pygame.draw.circle(s, (34, 46, 42), (cx, cy), self.r)
        pygame.draw.circle(s, (95, 140, 115), (cx, cy), self.r, 2)

        # --- YUK: govdedeki her nokta STOKTAKI BIR MOLEKULDUR.
        # Once sabit 11 sussuz granul ciziliyordu; o, tam da kacindigimiz
        # "arka planda yogunluk" gosterimiydi. Simdi atis ettikce azalir.
        prad = max(2, int(round(PAYLOADS[pi][3] * PORE_PX * 0.5)))
        for g in self.stock:
            gx, gy = int(cx + g[0]), int(cy + g[1])
            pygame.draw.circle(s, pcol, (gx, gy), prad)
            pygame.draw.circle(s, (20, 25, 30), (gx, gy), prad, 1)

        # --- TASIYICI: her biri farkli cizilir
        self._draw_weapon(s, cx, cy, ci, mcol, armed, fs)

        # MIZOSITOZ ile dolan sitoplazma: govde iceriden yesillenir
        if self.filled > 0.0:
            fr = int(self.r * min(1.0, self.filled))
            pygame.draw.circle(s, (60, 110, 90), (cx, cy), fr)
            pygame.draw.circle(s, (120, 200, 160), (cx, cy), fr, 1)
            ft = fs.render(f'DOLU %{100*min(1.0, self.filled):.0f}', True, (150, 220, 190))
            s.blit(ft, (cx - ft.get_width() // 2, cy - self.r - 50))

        # ENERJI cubugu
        bw = int(self.r * 1.9)
        bx, by = cx - bw // 2, cy - self.r - 20
        pygame.draw.rect(s, (30, 34, 40), (bx, by, bw, 9))
        fw = int(bw * self.energy / self.max_energy)
        ecol = ((120, 220, 160) if self.energy > 40 else
                ((240, 200, 110) if self.energy > 15 else (240, 110, 110)))
        pygame.draw.rect(s, ecol, (bx, by, fw, 9))
        pygame.draw.rect(s, (70, 80, 95), (bx, by, bw, 9), 1)
        et = fs.render(f'{self.energy:.0f}', True, ecol)
        s.blit(et, (bx + bw + 5, by - 3))

        lbl = f.render('SALDIRGAN', True, (150, 200, 175))
        s.blit(lbl, (cx - lbl.get_width() // 2, cy - self.r - 32))
        for k, (txt, col) in enumerate((
                (cname.split(' (')[0], (200, 225, 210)),
                (PAYLOADS[pi][0], pcol))):
            wl = fs.render(txt, True, col)
            s.blit(wl, (cx - wl.get_width() // 2, cy + self.r + 12 + k * 16))

    def _draw_weapon(self, s, cx, cy, ci, mcol, armed, fs=None):
        L = self.weapon_len()
        tipx = cx + self.r + L
        if ci == 0:
            # DIFUZYON: silah yok, molekuller sizip yayiliyor
            for k in range(18):
                a = (k / 18) * 2 * math.pi
                d = self.r + 14 + (k % 3) * 11
                pygame.draw.circle(s, (150, 160, 175),
                                   (int(cx + math.cos(a) * d), int(cy + math.sin(a) * d)), 3)
            return
        if ci == 1:
            # YONLU BOSALTMA: hedefe dogru acilmis kese, moleküller sagda
            pygame.draw.arc(s, (170, 185, 195),
                            (cx + self.r - 18, cy - 26, 46, 52), -1.1, 1.1, 4)
            for k in range(10):
                dy = -22 + k * 5
                pygame.draw.circle(s, (150, 165, 185),
                                   (int(cx + self.r + 20 + (k % 4) * 9), int(cy + dy)), 3)
            return
        if ci == 2:
            # FILAMENT: esnek boru, ucundan fiskirtma
            pts = [(cx + self.r - 4 + i * 9,
                    cy + int(7 * math.sin(i * 0.9))) for i in range(9)]
            pygame.draw.lines(s, (185, 175, 205), False, pts, 7)
            pygame.draw.lines(s, (110, 100, 130), False, pts, 2)
            for k in range(6):
                pygame.draw.circle(s, (200, 190, 220),
                                   (int(tipx + 6 + k * 7), int(cy + (k % 3 - 1) * 5)), 3)
            return
        if ci == 3:
            # T6SS: kasilmali kilif + ic tup + mizrak ucu
            base = cx + self.r - 2
            pygame.draw.rect(s, (150, 170, 190), (base, cy - 13, 44, 26))
            pygame.draw.rect(s, (80, 95, 110), (base, cy - 13, 44, 26), 2)
            for k in range(5):
                pygame.draw.line(s, (95, 115, 130),
                                 (base + 6 + k * 8, cy - 13), (base + 6 + k * 8, cy + 13), 2)
            pygame.draw.rect(s, (205, 200, 180), (base + 44, cy - 5, 14, 10))
            pygame.draw.polygon(s, (225, 220, 200), [
                (base + 58, cy - 9), (tipx, cy), (base + 58, cy + 9)])
            return
        if ci in (5, 6, 7, 8):
            # NEMATOSIST ailesi: basincli kapsul. Tipe gore uc farkli.
            bx = cx + self.r + 18
            pygame.draw.circle(s, (200, 190, 130), (bx, cy), 22)
            pygame.draw.circle(s, (120, 110, 70), (bx, cy), 22, 2)
            for k in range(5):
                pygame.draw.circle(s, (150, 140, 95), (bx, cy), 19 - k * 4, 1)
            if ci == 5:      # penetrant: sivri delici
                pygame.draw.polygon(s, (215, 205, 150), [
                    (bx + 20, cy - 10), (tipx, cy), (bx + 20, cy + 10)])
            elif ci == 6:    # volvent: sarmal iplik
                for k in range(8):
                    t = k / 7.0
                    pygame.draw.circle(s, (235, 225, 170),
                                       (int(bx + 20 + t * (tipx - bx - 20)),
                                        int(cy + 8 * math.sin(t * 9))), 3)
            elif ci == 7:    # glutinant: yapiskan damla
                pygame.draw.circle(s, (200, 235, 140), (int(tipx) - 4, cy), 10)
                pygame.draw.circle(s, (90, 130, 60), (int(tipx) - 4, cy), 10, 2)
            else:            # izoriza: kanca
                pygame.draw.line(s, (200, 220, 245), (bx + 20, cy), (tipx, cy), 3)
                pygame.draw.line(s, (200, 220, 245), (tipx, cy), (tipx - 9, cy - 9), 3)
                pygame.draw.line(s, (200, 220, 245), (tipx, cy), (tipx - 9, cy + 9), 3)
        else:
            # STILET: sivrilik uc alanindan gelir
            half = 6      # stilet: sivri
            pygame.draw.polygon(s, (210, 200, 175), [
                (cx + self.r - 2, cy - half), (tipx, cy), (cx + self.r - 2, cy + half)])
            pygame.draw.polygon(s, (120, 115, 100), [
                (cx + self.r - 2, cy - half), (tipx, cy), (cx + self.r - 2, cy + half)], 1)
        # --- BELIRTEC: ucta renkli tanima basligi
        if MARKERS[self.mi][1] is not None:
            pygame.draw.circle(s, mcol, (int(tipx), cy), 9)
            pygame.draw.circle(s, (20, 25, 30), (int(tipx), cy), 9, 2)
            mlbl = fs.render(MARKERS[self.mi][0].split(' ')[0], True, mcol)
            s.blit(mlbl, (int(tipx) - mlbl.get_width() // 2, cy - 26))


def draw_cross_section(s, cell, shot, f, fs):
    x0, y0, w, h = 30, HEIGHT - 118, VIEW_W - 60, 74
    pygame.draw.rect(s, (20, 24, 34), (x0 - 6, y0 - 22, w + 12, h + 30))
    s.blit(f.render('KESIT — merminin katmanlardan gecisi', True, ACCENT), (x0, y0 - 20))
    acts = cell.active()
    total_t = sum(l.t for l in acts) or 1.0
    x = x0
    for l in acts:
        bw = w * (l.t / total_t)
        pygame.draw.rect(s, l.color, (int(x), y0, int(bw) + 1, h))
        pygame.draw.rect(s, tuple(max(0, c - 55) for c in l.color),
                         (int(x), y0, int(bw) + 1, h), 2)
        nm = fs.render(l.name, True, (15, 15, 20))
        if bw > nm.get_width() + 6:
            s.blit(nm, (int(x) + 4, y0 + 4))
        if shot is not None:
            for c in shot.log:
                if c.layer is l:
                    tag, _fg, col = outcome_style(c.outcome)
                    t2 = fs.render(tag, True, (255, 255, 255))
                    pygame.draw.rect(s, col, (int(x) + 4, y0 + h - 22,
                                              t2.get_width() + 8, 18))
                    s.blit(t2, (int(x) + 8, y0 + h - 21))
                    if c.outcome in (BREACH, SIEVE):
                        v = 40.0 + 26.0 * math.sqrt(max(0.0, c.energy_after))
                        s.blit(fs.render(f'v={v:.0f}', True, (25, 25, 30)),
                               (int(x) + 4, y0 + 20))
        x += bw


ORGAN_RENK = {
    'Photoreceptor': (255, 255, 0), 'Mechanoreceptor': (255, 100, 100),
    'Chemoreceptor': (100, 255, 100), 'Flagella': (100, 200, 255),
    'Cilia': (200, 150, 255), 'Membrane': (150, 150, 150),
    'Cytoplasm': (200, 200, 200), 'Vacuole': (100, 150, 200),
    'Cytoskeleton': (180, 180, 180), 'Ribosome': (255, 200, 100),
    'Stylet': (255, 210, 120), 'Harpoon': (150, 220, 255),
    'Nematocyst': (255, 120, 220), 'Toxin': (170, 255, 120),
    'Lysin': (255, 150, 90), 'Phagocytosis': (200, 200, 255),
}
# Duran (dinlenme halinde) bir gorunumu OLMAYAN organlar.
#   Zar        : zarfin kendisidir, lab zaten bes katmani ciziyor.
#   Fagositoz  : bir ORGANEL degil, bir SUREC. Zar bir parcacigin etrafinda
#                cukurlasip kadeh olusturur ve koparak besin vakuolu yapar;
#                dinlenirken ortada duran bir yapi yoktur. Gorunmemesi
#                eksiklik degil, gercegin kendisi.
# Duran gorunumu OLMAYAN organlar. Fagositoz once buradaydi ama yanlisti:
# amipteki GENELLESMIS fagositozun yapisi yoktur, ancak bizim modelledigimiz
# YERELLESMIS surumun (attachment_angle'i var, yani bir agzi var) yapisi
# kalicidir. Sitostom cizilmezse kullanici nereden yutacagini bilemez.
GORUNUMSUZ = ('Membrane',)

ORGAN_KISA = {
    'Photoreceptor': 'Goz', 'Mechanoreceptor': 'Kulak', 'Chemoreceptor': 'Burun',
    'Flagella': 'Kamci', 'Cilia': 'Sil', 'Membrane': 'Zar', 'Cytoplasm': 'Sitoplazma',
    'Vacuole': 'Vakuol', 'Cytoskeleton': 'Iskelet', 'Ribosome': 'Ribozom',
    'Stylet': 'Stilet', 'Harpoon': 'Zipkin', 'Nematocyst': 'Nematosist',
    'Toxin': 'Toksin', 'Lysin': 'Lizin', 'Phagocytosis': 'Fagositoz',
}
# Zar savunmalari ORGAN degil NITELIKTIR (launcher da boyle ele aliyor):
# kapsul tum hucreyi sarar, konumu yoktur. Bu yuzden zar secilince
# savunmalar buradan ayarlanir ve dogrudan lab'in KATMANLARINA yansir.
ZAR_SAVUNMA = [('capsule', 'Kapsul (temas)'), ('wall', 'Duvar (mekanik)'),
               ('outer', 'Dis zar (kimyasal)'), ('efflux', 'Efflux (pompa)'),
               ('repair', 'Onarim')]


def draw_organ_panel(screen, cell, f, f_s, mouse):
    """Organel paleti. Tiklanabilir satirlari dondurur.

    Sag surun zaten dolu oldugu icin palet ACILIR bir katman: O tusu ile
    acilip kapanir, gorunumun uzerine biner.
    """
    rows = []
    W, H = 640, 560
    x0, y0 = (VIEW_W - W) // 2, (HEIGHT - H) // 2 - 30
    panel = pygame.Surface((W, H), pygame.SRCALPHA)
    panel.fill((14, 18, 30, 246))
    screen.blit(panel, (x0, y0))
    pygame.draw.rect(screen, ACCENT, (x0, y0, W, H), 2)
    screen.blit(f.render('HEDEFIN ORGANELLERI', True, ACCENT), (x0 + 16, y0 + 12))
    screen.blit(f_s.render('tikla = tak  |  takililara tikla = cikar  |  O = kapat'
                           '  |  x = duran gorunumu yok',
                           True, DIM), (x0 + 16, y0 + 34))

    # --- palet: 16 organ, 4 sutun
    adlar = all_organ_names()
    bx, by, bw, bh = x0 + 16, y0 + 58, 148, 30
    for i, ad in enumerate(adlar):
        r = pygame.Rect(bx + (i % 4) * (bw + 4), by + (i // 4) * (bh + 4), bw, bh)
        uzerinde = r.collidepoint(mouse)
        pygame.draw.rect(screen, (34, 46, 66) if uzerinde else (22, 30, 46), r)
        pygame.draw.rect(screen, ORGAN_RENK.get(ad, DIM), r, 1)
        screen.blit(f_s.render(ORGAN_KISA.get(ad, ad)[:13], True,
                               FG if uzerinde else DIM), (r.x + 8, r.y + 8))
        rows.append((r, 'ekle', ad))
        if ad in GORUNUMSUZ:
            pygame.draw.line(screen, (110, 118, 138),
                             (r.right - 13, r.y + 6), (r.right - 6, r.y + 13), 1)
            pygame.draw.line(screen, (110, 118, 138),
                             (r.right - 6, r.y + 6), (r.right - 13, r.y + 13), 1)
    y = by + 4 * (bh + 4) + 10

    # --- takili organlar
    screen.blit(f_s.render(f'TAKILI ({len(cell.organ_cfg)})   tekerlek = CEVIR'
                           f'   (shift = ince)', True, ACCENT), (x0 + 16, y))
    y += 18
    for i, (ad, aci) in enumerate(cell.organ_cfg[:12]):
        r = pygame.Rect(x0 + 16, y, 300, 19)
        uzerinde = r.collidepoint(mouse)
        pygame.draw.rect(screen, (48, 26, 30) if uzerinde else (20, 26, 40), r)
        screen.blit(f_s.render(
            f'{"x" if uzerinde else "-"} {ORGAN_KISA.get(ad, ad)}  '
            f'{math.degrees(aci):.0f} derece', True,
            BAD if uzerinde else FG), (r.x + 6, r.y + 3))
        rows.append((r, 'cikar', i))
        y += 21
    if len(cell.organ_cfg) > 12:
        screen.blit(f_s.render(f'... +{len(cell.organ_cfg) - 12} tane daha',
                               True, DIM), (x0 + 22, y)); y += 18

    # --- zar savunmalari (organ degil NITELIK)
    zar = next((o for o in cell.organs
                if o.__class__.__name__ == 'Membrane'), None)
    sx, sy = x0 + 330, by + 4 * (bh + 4) + 28
    if zar is None:
        screen.blit(f_s.render('Zar takili degil - savunma ayarlanamaz',
                               True, DIM), (sx, sy))
    else:
        screen.blit(f_s.render('ZAR SAVUNMALARI  (sol/sag tik = -/+)', True, ACCENT),
                    (sx, sy - 18))
        for k, (alan, etiket) in enumerate(ZAR_SAVUNMA):
            r = pygame.Rect(sx, sy + k * 22, 290, 20)
            uzerinde = r.collidepoint(mouse)
            pygame.draw.rect(screen, (30, 40, 58) if uzerinde else (20, 26, 40), r)
            deger = getattr(zar.logic, alan, 0.0)
            screen.blit(f_s.render(f'{etiket:<20} {deger:.0f}', True,
                                   FG if uzerinde else DIM), (r.x + 6, r.y + 3))
            rows.append((r, 'zar', alan))
        screen.blit(f_s.render(
            f'-> duvar {cell.layers[3].t:.1f}  kapsul {cell.layers[1].t:.1f}  '
            f'zar {cell.layers[4].t:.1f}', True, INFO),
            (sx, sy + len(ZAR_SAVUNMA) * 22 + 6))
        screen.blit(f_s.render(
            f'-> temizlenme {CLEARANCE / (1 + cell.efflux * EFFLUX_GAIN):.1f} sn',
            True, INFO), (sx, sy + len(ZAR_SAVUNMA) * 22 + 22))

    # --- turetilen etkiler
    ty = y0 + H - 82
    screen.blit(f_s.render('ORGANLARIN LABA ETKISI', True, ACCENT), (x0 + 16, ty))
    screen.blit(f_s.render(
        f'kacis hizi {cell.escape_speed:.0f} px/sn (ciplak {ESCAPE_BASE:.0f})   '
        f'alarm +{cell.alarm_bonus:.1f} sn   efflux {cell.efflux:.0f}',
        True, FG), (x0 + 16, ty + 17))
    # SITOSTOM durumu
    if cell.agizlar:
        sert = cell.sert_yuzey
        if sert:
            screen.blit(f_s.render(
                f'SITOSTOM DEVRE DISI: {sert} sert - zar esneyip saramaz',
                True, WARN), (x0 + 16, ty + 34))
        else:
            screen.blit(f_s.render(
                f'sitostom acik ({len(cell.agizlar)} agiz)   yutulan '
                f'{cell.yutulan}   kacan {cell.kacan}   sindirilen '
                f'{cell.sindirilen}', True, (140, 220, 255)), (x0 + 16, ty + 34))
    r = pygame.Rect(x0 + W - 120, y0 + H - 34, 104, 24)
    pygame.draw.rect(screen, (60, 26, 30) if r.collidepoint(mouse) else (30, 20, 26), r)
    pygame.draw.rect(screen, BAD, r, 1)
    screen.blit(f_s.render('HEPSINI SIL', True, BAD), (r.x + 12, r.y + 5))
    rows.append((r, 'temizle', None))
    return rows


# ---------------------------------------------------------- TESLIMAT ORANI
#
# Ana oyun her saldiri icin 26 molekulu tek tek simule edemez - yuzlerce
# hucre var. Ama AYNI FIZIGI analitik olarak hesaplayabiliriz: elek, taraf
# ve hidrofobik uyumsuzluk kurallari burada bir ORAN uretir.
#
# Kurallarin tek kaynagi burasidir; laboratuvar onlari gorsel olarak
# molekul molekul isletir, oyun ayni kurallardan bir carpan alir.

# OLCULMUS TESLIMAT TABLOSU
#
# Once analitik turetmeyi denedim ve YANLIS cikti: molekullerin yuzeye
# tutunup delik ARAMASINI hesaba katmiyordu, carpim hepsini eziyordu
# (toksin duvar 0'da 0.001). Dogrusu laboratuvari OLCUP tablo cikarmak -
# lab zaten referans uygulama.
#
# Asagidaki sayilar 10 tohum x 220 kare gercek molekul simulasyonundan
# geldi. Ham olcumde tekduze olmayan noktalar vardi (toksin duvar 20'de
# 0.412, 30'da 0.762; stilet duvar 10'da 0.000). Zirhin saldirgana YARDIM
# etmesi fiziksel olarak imkansiz oldugu icin kumulatif minimum alinarak
# tekduzelik DAYATILDI. Bu bir duzeltme degil, bir SINIRLAMA: aykiriliklar
# aciklanmis degil, yalnizca zararsiz hale getirildi.
# OLCULMUS TESLIMAT IZGARASI  (tasiyici, yuk) -> zirh noktalarindaki oran
#
# Onceki surumde tablo SILAH ADINA gore tutuluyordu ve tekduzelik
# DAYATILMISTI. O kirpma bir gercegi ORTUYORMUS: T6SS duvar 0'da 0.00,
# duvar 15'te 0.48 veriyor. Bu gurultu degil - daha once belgelenen
# "ince zirhta igne asiri derine gidip yuku yanlis bolmeye birakir"
# olgusunun ta kendisi. Ham degerler artik kirpilmadan kullaniliyor.
#
# 4 tohum x 200 kare gercek molekul simulasyonu, 6 tasiyici x 7 yuk.
TESLIMAT_ZIRHLARI = [0, 6, 15, 30]
TESLIMAT_IZGARA = {
    (0, 1): [0.067, 0.106, 0.115, 0.087],
    (0, 2): [0.115, 0.144, 0.106, 0.077],
    (0, 3): [0.106, 0.154, 0.106, 0.087],
    (0, 4): [0.087, 0.096, 0.154, 0.173],
    (0, 5): [0.0, 0.0, 0.0, 0.0],
    (0, 6): [0.0, 0.0, 0.0, 0.0],
    (0, 7): [0.0, 0.0, 0.0, 0.0],
    (1, 1): [0.346, 0.442, 0.452, 0.49],
    (1, 2): [0.394, 0.567, 0.452, 0.423],
    (1, 3): [0.288, 0.481, 0.481, 0.356],
    (1, 4): [0.385, 0.519, 0.462, 0.442],
    (1, 5): [0.0, 0.0, 0.0, 0.0],
    (1, 6): [0.0, 0.0, 0.0, 0.0],
    (1, 7): [0.0, 0.0, 0.0, 0.0],
    (2, 1): [0.654, 0.856, 0.846, 0.779],
    (2, 2): [0.596, 0.904, 0.798, 0.721],
    (2, 3): [0.663, 0.923, 0.904, 0.683],
    (2, 4): [0.625, 0.779, 0.692, 0.538],
    (2, 5): [0.019, 0.0, 0.0, 0.0],
    (2, 6): [0.0, 0.0, 0.0, 0.0],
    (2, 7): [0.0, 0.0, 0.0, 0.0],
    (3, 1): [0.0, 0.708, 0.479, 0.292],
    (3, 2): [0.958, 0.646, 0.271, 0.229],
    (3, 3): [0.958, 0.583, 0.333, 0.208],
    (3, 4): [0.0, 1.0, 1.0, 1.0],
    (3, 5): [0.0, 0.938, 0.042, 0.0],
    (3, 6): [1.0, 0.0, 0.0, 0.0],
    (3, 7): [0.0, 0.583, 0.0, 0.0],
    (4, 1): [0.396, 0.312, 0.375, 0.562],
    (4, 2): [0.771, 0.667, 0.458, 0.438],
    (4, 3): [0.604, 0.625, 0.438, 0.5],
    (4, 4): [1.0, 1.0, 1.0, 1.0],
    (4, 5): [0.458, 0.667, 0.854, 0.0],
    (4, 6): [0.0, 0.0, 0.0, 0.0],
    (4, 7): [0.0, 0.0, 0.0, 0.0],
    (5, 1): [0.0, 0.0, 0.0, 0.375],
    (5, 2): [0.708, 0.875, 0.0, 0.396],
    (5, 3): [0.771, 0.854, 0.0, 0.438],
    (5, 4): [0.0, 0.0, 0.0, 1.0],
    (5, 5): [0.0, 0.0, 0.0, 0.0],
    (5, 6): [1.0, 1.0, 0.0, 0.0],
    (5, 7): [0.0, 0.0, 0.0, 0.0],
}


def _azalan_uydur(dizi):
    """Diziye AZALMAYAN olmayan (non-increasing) en yakin egriyi uydur.

    Havuzlama algoritmasi (PAVA): kurali bozan komsu ciftler ortalamalarina
    cekilir, ta ki dizi bastan sona azalan olana kadar. En kucuk kareler
    anlaminda en yakin cozumdur; yani olculen degerlerin SEVIYESINI korur.

    Basit bir "kosan minimum" bunu yapamaz: dizinin ilk elemani bir alt
    aykiri deger ise (orn. T6SS+lizozim zirhsizken 0.0 olculmus) butun
    satiri sifira duzler ve gercekten olculmus yuksek degerleri siler.
    """
    kume = [[v, 1] for v in dizi]      # [toplam, adet]
    i = 0
    while i < len(kume) - 1:
        if kume[i][0] / kume[i][1] < kume[i + 1][0] / kume[i + 1][1]:
            kume[i][0] += kume[i + 1][0]
            kume[i][1] += kume[i + 1][1]
            del kume[i + 1]
            if i > 0:
                i -= 1
        else:
            i += 1
    out = []
    for toplam, adet in kume:
        out.extend([round(toplam / adet, 4)] * adet)
    return out


def _izgarayi_monotonlastir(izgara):
    """Zirh arttikca teslimat AZALMALI - artamaz.

    Olculen tabloda bazi satirlar zirh 0'dan 6'ya cikarken YUKSELIYOR:
    orn. fiskirtma+norotoksin (toksin) 0.654 -> 0.856. Yani duvar
    ordurmek toksinden alinan hasari %30 ARTIRIYORDU. Bu fiziksel olarak
    savunulamaz ve oyunda TERS bir secilim uretir: zirh takan hucre daha
    cabuk oluyorsa savunma tipi hicbir zaman evrimlesemez.

    Olcum gurultusu, teslimat kapisinin fiziksel kisitini bozmamali.
    Satirlar en yakin azalan egriye cekilir; hicbir olcum atilmaz, yalnizca
    imkansiz olan yon kapatilir.
    """
    return {k: _azalan_uydur(v) for k, v in izgara.items()}


TESLIMAT_IZGARA = _izgarayi_monotonlastir(TESLIMAT_IZGARA)


def teslimat(ci, pi, zirh=0.0):
    """Bu tasiyici+yuk ikilisi, bu zirha karsi yukun kacta kacini ulastirir.

    Izgara olculen 6 tasiyici x 7 yuk icindir. Disinda kalan iki durum
    OLCUMLE degil, tanimla belirlenir:

    * pi = 0 -> ortada kimyasal yuk YOK. Silah saf mekaniktir; teslimat
      kapisi ona uygulanmaz (mekanik direnc zaten zarda isler). 1.0.
    * CARRIER_EMIT[ci] = 0 -> volvent/glutinant/izoriza. Bu uc nematosist
      atis basina SIFIR molekul birakir: sarar, yapistirir, tutunur ama
      enjekte etmez. Yanlarina bir yuk secilse bile o yuk hucreden hic
      cikmaz. 0.0.

    Bilinmeyen bir anahtar kalirsa 0.0 doneriz, 1.0 degil: eksik olcum
    sessizce EN GUCLU secenegi uretmemeli. Editor artik butun tasiyici ve
    yukleri sunuyor; eskiden ulasilamayan kombinasyonlar 1.0 fallback'i
    yuzunden "zirh delen mucize silah" haline geliyordu.
    """
    ci, pi = int(ci), int(pi)
    if pi == 0:
        return 1.0
    if 0 <= ci < len(CARRIER_EMIT) and CARRIER_EMIT[ci] == 0:
        return 0.0
    dizi = TESLIMAT_IZGARA.get((ci, pi))
    if dizi is None:
        return 0.0
    Z = TESLIMAT_ZIRHLARI
    if zirh <= Z[0]:
        return dizi[0]
    if zirh >= Z[-1]:
        return dizi[-1]
    for i in range(1, len(Z)):
        if zirh <= Z[i]:
            t = (zirh - Z[i - 1]) / (Z[i] - Z[i - 1])
            return dizi[i - 1] + t * (dizi[i] - dizi[i - 1])
    return dizi[-1]


def kombinasyon_ozeti(ci, pi):
    """Editorde gosterilecek kisa not: bu ikili ne yapar, ne yapmaz.

    Secim ekraninda tasiyici ve yuk ayri ayri listeleniyordu; hangisinin
    hangisiyle ise yaradigi ancak oyunda deneyerek anlasiliyordu. Oysa
    bunlarin cogu OLCULMUS: burada dogrudan sayiyi gosteriyoruz.
    """
    ci, pi = int(ci), int(pi)
    if pi == 0:
        return 'saf mekanik - kimyasal yuk yok'
    if 0 <= ci < len(CARRIER_EMIT) and CARRIER_EMIT[ci] == 0:
        return 'BU TASIYICI YUK TASIMAZ - yuk bosa gider'
    z0 = teslimat(ci, pi, 0.0)
    z15 = teslimat(ci, pi, 15.0)
    not_ = ''
    if ci >= 3 and PAYLOAD_SIDE.get(PAYLOADS[pi][0]) == 'dis':
        # Igne yuku ICERI birakir; dis yuzden etki eden yuk orada islemez.
        not_ = ' [igne+dis-yuz: uyumsuz]'
    return 'zirhsiz %.2f / duvar15 %.2f%s' % (z0, z15, not_)


def etkin_zirh(duvar=0.0, kapsul=0.0, dis_zar=0.0):
    """Zar savunmalarini tek bir mekanik zirh degerinde topla."""
    return max(0.0, duvar + 0.5 * kapsul + 0.5 * dis_zar)


def silah_teslimat(silah_adi, duvar=0.0, kapsul=0.0, dis_zar=0.0,
                   carrier=None, payload=None):
    """Silahin teslimat orani. carrier/payload verilirse ONLAR kullanilir.

    Silah artik sabit bir eslemeye mahkum degil; editorde secilen
    tasiyici ve yuk dogrudan fizige giriyor.
    """
    if carrier is None or payload is None:
        e = SILAH_ESLEME.get(str(silah_adi).lower())
        if e is None:
            return 1.0
        carrier, payload = e
    return teslimat(carrier, payload, etkin_zirh(duvar, kapsul, dis_zar))


# Yuk secimi FIZIKSEL olarak tutarli olmali: igneli tasiyicilar yuku
# ICERI birakir, dolayisiyla dis yuzden etki eden bir yuk (norotoksin)
# igneyle bosa gider. Ilk eslemede nematosiste norotoksin verilmisti ve
# olcumde her zirhta 0.000 cikti - hatanin ta kendisi.
SILAH_ESLEME = {
    'toxin':        (2, 1),   # Fiskirtma + Norotoksin (dis yuzey)
    'lysin':        (2, 4),   # Fiskirtma + Lizozim (duvari cozer)
    'stylet':       (4, 2),   # Stilet + Antimikrobiyal peptit (her iki yuz)
    'harpoon':      (3, 6),   # T6SS + T3SS efektoru (sitoplazma)
    'nematocyst':   (5, 6),   # Nematosist + T3SS efektoru (sitoplazma)
    'phagocytosis': (2, 3),   # Amoebapor (her iki yuz)
}


def spawn_shot(cell, atk, ci, pi, mi, shots):
    """Ates edildi. Tasiyici turune gore MERMI mi MOLEKUL BULUTU mu?

    Molekuler tasiyicilar (difuzyon / yonlu bosaltma / fiskirtma) bir mermi
    firlatmaz - molekulleri dogrudan ortama salar. Aralarindaki tek fark
    SACILMA ACISIDIR; difuzyonun zayifligi bir katsayidan degil bundan
    gelir. Delici tasiyicilar mermi yollar, yuku iceride birakirlar.
    """
    # STOKTAN CEK: molekul yoksa atis da yok. Yuk artik soyut bir
    # secim degil, govdede fiilen tasinan bir madde.
    need = CARRIER_EMIT[ci]
    if need and PAYLOADS[pi][1] is not None and not atk.take(need):
        return []
    muzzle = atk.muzzle()
    if ci >= 3:
        shots.append(Shot(cell, muzzle, (1, 0), CARRIERS[ci],
                          PAYLOADS[pi], MARKERS[mi], ci))
        return []
    if PAYLOADS[pi][1] is None:
        return []
    aim = cell.center - muzzle
    aim = aim.normalize() if aim.length() > 1e-6 else pygame.math.Vector2(1, 0)
    half = math.radians(CARRIER_SPREAD[ci])
    base = math.atan2(aim.y, aim.x)
    # Menzil bir kontrol degil, baslangic hizinin sonucudur: v0 / _DRAG_K
    # kadar yol alip durur. Difuzyon yavas birakir, fiskirtma hizli.
    v0 = CARRIER_REACH[ci] * _DRAG_K
    out = []
    for _ in range(CARRIER_EMIT[ci]):
        a = base + random.uniform(-half, half)
        sp = v0 * random.uniform(0.8, 1.2)
        v = pygame.math.Vector2(math.cos(a), math.sin(a)) * sp
        out.append(Molecule(cell, muzzle, v, pi))
    return out


def main():
    pygame.init()
    tam_ekran = True
    window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    # Butun cizim TUVALE gider; tuval her karede pencereye olceklenir.
    screen = pygame.Surface((WIDTH, HEIGHT))
    olcek, kayma = _screen_fit(*window.get_size())

    def ekran_konumu(p):
        """Pencere koordinatini TUVAL koordinatina cevir.

        Olcekleme yapinca fare olaylari da cevrilmek zorunda; yoksa
        tiklamalar goruntudeki yere denk gelmez.

        Sonuc YUVARLANIR: kesirli birakinca satir sinirlarinda 0.1 px
        kacirma oluyor (361.875, sinir 362) ve tiklama/tekerlek hedefi
        isabet etmiyordu."""
        return (round((p[0] - kayma[0]) / olcek),
                round((p[1] - kayma[1]) / olcek))
    pygame.display.set_caption('EVRIM — Laboratuvar: katman/igne fizigi ve yuk teslimi')
    clock = pygame.time.Clock()
    f_h = pygame.font.Font(None, 26)
    f = pygame.font.Font(None, 21)
    f_s = pygame.font.Font(None, 18)

    cell = LabCell((VIEW_W * 0.62, HEIGHT * 0.47))
    atk = Attacker((135, HEIGHT * 0.44))
    shots, last_shot = [], None
    mols = []                 # dunyadaki TEKIL molekuller
    son_nesil = cell.generation
    seyrelen = 0              # hedefe varamadan ortamda kaybolanlar
    atilan = 0                # toplam atilan molekul
    rows = []      # (rect, tur, indeks) - panelde tiklanabilir satirlar
    organ_acik = False     # O tusu: organel paleti
    organ_rows = []
    panel_kaydirma = 0     # sag panelin dikey kaydirmasi
    panel_max = 0
    ci, pi, mi = 3, 2, 0

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        mouse = ekran_konumu(pygame.mouse.get_pos())
        for ev in pygame.event.get():
            _ep = ekran_konumu(ev.pos) if hasattr(ev, 'pos') else (0, 0)
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                elif pygame.K_1 <= ev.key <= pygame.K_9:
                    ci = ev.key - pygame.K_1
                elif ev.key == pygame.K_SPACE:
                    if not atk.has_stock(ci, pi):
                        atk.no_stock = True
                    elif atk.pay_shot(ci, pi):
                        _new = spawn_shot(cell, atk, ci, pi, mi, shots)
                        mols += _new
                        atilan += len(_new) or CARRIER_EMIT[ci]
                        atk.recoil = 14.0
                elif ev.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    atk.unlimited = not atk.unlimited
                elif ev.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                    # Sifirlama R'daydi ama R bir YUK tusu (Amoebapor) -
                    # calindigi icin o yuk hic secilemiyordu. W de ayni sekilde
                    # saldirgani yukari tasidigi icin Norotoksin secilemiyordu.
                    # Hareket artik SADECE ok tuslarinda.
                    shots.clear(); mols.clear(); seyrelen = atilan = 0
                    last_shot = None; cell.reset(); atk.filled = 0.0; atk.energy = atk.max_energy
                elif ev.key == pygame.K_UP:
                    atk.pos.y = max(70, atk.pos.y - 18); atk.energy -= MOVE_COST
                elif ev.key == pygame.K_DOWN:
                    atk.pos.y = min(HEIGHT - 190, atk.pos.y + 18); atk.energy -= MOVE_COST
                elif ev.key == pygame.K_LEFT:
                    atk.pos.x = max(100, atk.pos.x - 22); atk.energy -= MOVE_COST
                elif ev.key == pygame.K_RIGHT:
                    # YATAY hareket sart: temas silahlarinin menzili 35 px,
                    # sabit konumda hedefe 80 px vardi - hicbiri kullanilamiyordu.
                    atk.pos.x = min(VIEW_W - 120, atk.pos.x + 22); atk.energy -= MOVE_COST
                elif ev.key == pygame.K_F11:
                    tam_ekran = not tam_ekran
                    window = pygame.display.set_mode(
                        (0, 0) if tam_ekran else (WIDTH, HEIGHT),
                        pygame.FULLSCREEN if tam_ekran else 0)
                    olcek, kayma = _screen_fit(*window.get_size())
                elif ev.key == pygame.K_o:
                    organ_acik = not organ_acik
                elif pygame.K_F1 <= ev.key <= pygame.K_F5:
                    # Ham `enabled[k] = ...` uc seyi atliyordu: F5 plazma
                    # zarini siliyordu, secim zar organina geri
                    # yazilmiyordu ve ucustaki molekuller donmus katman
                    # indeksiyle kaliyordu.
                    k = ev.key - pygame.K_F1
                    if 0 <= k < len(cell.enabled):
                        cell.set_layer_present(k, not cell.enabled[k])
                else:
                    ch = chr(ev.key).upper() if 32 < ev.key < 127 else ''
                    if ch in PAYLOAD_KEYS:
                        pi = PAYLOAD_KEYS.index(ch)
                    elif ch in MARKER_KEYS:
                        mi = MARKER_KEYS.index(ch)
            elif organ_acik and ev.type == pygame.MOUSEBUTTONDOWN:
                # Panel acikken BUTUN fare dugmeleri burada biter.
                # Once yalnizca 1 ve 3 yakalaniyordu; pygame tekerlek icin
                # hem MOUSEWHEEL hem de MOUSEBUTTONDOWN(4/5) uretiyor ve
                # 4/5 asagiya dusup panelin ARKASINDAKI katmani
                # kalinlastiriyordu - panelde kaydirirken hedefin zarfi
                # sessizce degisiyordu.
                if ev.button in (4, 5):
                    # Yalnizca YUT. Cevirme isini MOUSEWHEEL yapiyor; ikisi
                    # birden yapinca bir tik 15 yerine 30 derece cevirdi.
                    continue
                vuran = next((r for r in organ_rows if r[0].collidepoint(_ep)), None)
                if vuran is not None:
                    _r, tur, veri = vuran
                    if tur == 'ekle':
                        cell.add_organ(veri)
                    elif tur == 'cikar':
                        cell.remove_organ(veri)
                    elif tur == 'temizle':
                        cell.clear_organs()
                    elif tur == 'zar':
                        zar = next((o for o in cell.organs
                                    if o.__class__.__name__ == 'Membrane'), None)
                        if zar is not None:
                            d = 1.0 if ev.button == 1 else -1.0
                            yeni = max(0.0, min(30.0,
                                                getattr(zar.logic, veri, 0.0) + d))
                            setattr(zar.logic, veri, yeni)
                            cell._apply_membrane_defence()
                # Panel acikken gorunume DUSMEZ - tiklama burada biter.
            elif ev.type == pygame.MOUSEWHEEL and organ_acik:
                # Organel paneli acikken tekerlek TAKILI organi cevirir.
                vuran = next((r for r in organ_rows
                              if r[1] == 'cikar' and r[0].collidepoint(mouse)), None)
                if vuran is not None:
                    i = vuran[2]
                    if 0 <= i < len(cell.organ_cfg):
                        ad, aci = cell.organ_cfg[i]
                        adim = math.radians(5 if pygame.key.get_mods()
                                            & pygame.KMOD_SHIFT else 15)
                        cell.organ_cfg[i] = (ad, (aci + ev.y * adim) % (2 * math.pi))
                        cell._build_organs()
            elif ev.type == pygame.MOUSEWHEEL and mouse[0] >= VIEW_W:
                panel_kaydirma = max(0, min(panel_max, panel_kaydirma - ev.y * 40))
            elif ev.type == pygame.MOUSEWHEEL and mouse[0] < VIEW_W:
                idx, _ghost = cell.hit_layer(mouse)
                if idx is not None:
                    cell.bump_thickness(idx, ev.y * 0.5)
            elif (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3
                  and _ep[0] < VIEW_W):
                idx, _ghost = cell.hit_layer(_ep)
                if idx is not None:
                    cell.set_layer_present(idx, not cell.enabled[idx])
            elif (ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (4, 5)
                  and _ep[0] < VIEW_W):
                # Tekerlek icin pygame HEM MOUSEWHEEL HEM buton 4/5 uretir.
                # Ikisi de kalinligi degistirdigi icin bir tik 0.5 yerine
                # 1.0 degistiriyordu. Kalinlik isini yukaridaki MOUSEWHEEL
                # dali yapar; bu dal yalnizca olayi yutar.
                pass
            elif (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
                  and _ep[0] >= VIEW_W):
                # PANELE tikla -> saldirganin donanimini degistir
                for rect, kind, idx in rows:
                    if rect.collidepoint(_ep):
                        if kind == 'c': ci = idx
                        elif kind == 'm': mi = idx
                        else: pi = idx
                        break
            elif (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
                  and _ep[0] < VIEW_W):
                # Atis SALDIRGANIN NAMLUSUNDAN cikar. Saldirgana tikla ->
                # ates; baska yere tikla -> saldirgani o yukseklige tasi.
                # Atis yataydir, dolayisiyla saldirganin YUKSEKLIGI carpma
                # acisini belirler: hedefin ustune/altina al -> teget carpma.
                if pygame.math.Vector2(_ep).distance_to(atk.pos) <= atk.r + 70:
                    if not atk.has_stock(ci, pi):
                        atk.no_stock = True
                    elif atk.pay_shot(ci, pi):
                        _new = spawn_shot(cell, atk, ci, pi, mi, shots)
                        mols += _new
                        atilan += len(_new) or CARRIER_EMIT[ci]
                        atk.recoil = 14.0
                else:
                    atk.pos.y = max(70, min(HEIGHT - 190, _ep[1]))

        for sh in shots:
            sh.update(dt)
            if sh.released:
                mols += sh.released
                sh.released = []
            if sh.log or sh.out_of_reach:
                last_shot = sh
        shots = [s for s in shots if not s.dead][-6:]
        cell.update(dt)
        # PATLAYAN HUCRE KENDI YUKUNU SACAR: stok bir sayi degil, dagilan
        # noktalardir - kime ne yaptigi gozle gorulur.
        if cell.burst:
            mols += cell.spill()
        for m in mols:
            m.update(dt)
        if cell.generation != son_nesil:
            # Hucre yenilendi: eski nesil molekuller ve onlarin sayaclari
            # yeni deneye tasinmamali. Aksi halde olum aninda 'seyrelen'
            # sayaci sahte bir sicrama yapiyordu.
            son_nesil = cell.generation
            mols = [m for m in mols if m.gen == son_nesil]
            seyrelen = atilan = 0
        n_before = len(mols)
        mols = [m for m in mols if m.state not in ('lost', 'cleared')]
        seyrelen += n_before - len(mols)
        del mols[:-900]

        atk.update(dt, ci, cell.feeder is not None)
        atk.synth(dt, pi)
        cell.synth(dt, pi)
        if cell.feeder is not None:
            atk.filled = cell.drained
        if cell.pulling is not None:
            # IZORIZA: avlanma degil HAREKET - saldirgan kendini hedefe ceker
            d = cell.center.x - cell.outer_r - 60 - atk.pos.x
            if abs(d) > 2:
                atk.pos.x += max(-160 * dt, min(160 * dt, d))
            else:
                cell.pulling = None
        screen.fill(BG)
        cell.draw(screen, f, f_s)
        for m in mols:
            m.draw(screen)
        atk.draw(screen, f, f_s, ci, pi, mi, True)
        # nisan hatti + MENZIL gostergesi
        pygame.draw.line(screen, (48, 56, 76),
                         (int(atk.pos.x), int(atk.pos.y)),
                         (VIEW_W, int(atk.pos.y)), 1)
        mz = atk.muzzle()
        reach = CARRIER_REACH[ci]
        gap = mz.distance_to(cell.center) - cell.outer_r
        ok_reach = gap <= reach
        rc = ACCENT if ok_reach else BAD
        rx = min(VIEW_W - 4, mz.x + reach)
        pygame.draw.line(screen, rc, (int(mz.x), int(mz.y) - 16),
                         (int(rx), int(mz.y) - 16), 3)
        pygame.draw.line(screen, rc, (int(rx), int(mz.y) - 24),
                         (int(rx), int(mz.y) - 8), 3)
        rt = f_s.render(f'menzil {reach:.0f}  hedefe {gap:.0f}'
                        f'{"" if ok_reach else "  ULASAMAZ"}', True, rc)
        screen.blit(rt, (int(mz.x) + 4, int(mz.y) - 42))
        for sh in shots:
            sh.draw(screen)

        if True:
            my = atk.pos.y
            off = abs(my - cell.center.y)
            R = cell.outer_r
            if off < R:
                pa = math.degrees(math.asin(off / R))
                cp_ = CARRIERS[ci][1]
                lim = (bite_angle_limit(cell.active()[0].friction,
                                        cp_['tip_area'] if cp_ else 0.3,
                                        cp_['energy'] if cp_ else None)
                       if cell.active() else 0)
                if cp_ is None:
                    lim = 90.0      # difuzyon sekmez
                col = ACCENT if pa <= lim else WARN
                txt = f_s.render(f'aci ~{pa:.0f}  sinir {lim:.0f}  '
                                 f'{"isirir" if pa <= lim else "SEKER"}', True, col)
                screen.blit(txt, (int(atk.pos.x) + 70, int(my) - 22))
        # farenin ustundeki katmani vurgula
        hov, hov_ghost = cell.hit_layer(mouse) if mouse[0] < VIEW_W else (None, False)
        if hov is not None:
            hl = cell.layers[hov]
            if hov_ghost:
                for i, l, r0, r1 in cell.ghost_rings():
                    if i == hov:
                        pygame.draw.circle(screen, hl.color,
                                           (int(cell.center.x), int(cell.center.y)),
                                           int((r0 + r1) / 2), cell.GHOST_BAND)
            else:
                r = cell.outer_r
                for l in cell.active():
                    inner = r - l.t * PX_PER_UNIT
                    if l is hl:
                        pygame.draw.circle(screen, (255, 255, 255),
                                           (int(cell.center.x), int(cell.center.y)),
                                           int(r), 2)
                        pygame.draw.circle(screen, (255, 255, 255),
                                           (int(cell.center.x), int(cell.center.y)),
                                           max(1, int(inner)), 2)
                        break
                    r = inner
            tip = f'{hl.name}  kalinlik {hl.t:.1f}   [teker=kalinlik  sag tik='                   f'{"EKLE" if hov_ghost else "KALDIR"}]'
            box = f_s.render(tip, True, (15, 18, 25))
            bw, bh = box.get_width() + 10, 20
            # kutuyu gorunum icinde tut: sag kenardan tasarsa sola gecir
            bx = mouse[0] + 12
            if bx + bw > VIEW_W - 8:
                bx = mouse[0] - 12 - bw
            bx = max(8, bx)
            by = max(4, min(HEIGHT - bh - 4, mouse[1] - 10))
            pygame.draw.rect(screen, hl.color, (bx, by, bw, bh))
            pygame.draw.rect(screen, (15, 18, 25), (bx, by, bw, bh), 1)
            screen.blit(box, (bx + 5, by + 2))

        draw_cross_section(screen, cell, last_shot, f, f_s)

        # ---------------- panel ----------------
        pygame.draw.rect(screen, PANEL_BG, (VIEW_W, 0, PANEL_W, HEIGHT))
        pygame.draw.line(screen, (45, 52, 70), (VIEW_W, 0), (VIEW_W, HEIGHT), 2)
        rows = []
        # Panel icerigi ekrandan uzundu ve SECIM basligi asagida kaliyordu.
        # Kaydirma yoktu; artik tekerlek panelin uzerindeyken kaydiriyor.
        x, y = VIEW_W + 14, 16 - panel_kaydirma
        screen.blit(f_h.render('LABORATUVAR', True, FG), (x, y)); y += 27
        screen.blit(f_s.render('BOSLUK / saldirgana tikla = ATES', True, ACCENT), (x, y)); y += 13
        screen.blit(f_s.render('OK TUSLARI = saldirgani tasi (sag ok = YAKLAS)',
                               True, INFO), (x, y)); y += 13
        screen.blit(f_s.render('BACKSPACE = sifirla   O = ORGANELLER   ESC = cik',
                               True, DIM), (x, y)); y += 14
        screen.blit(f_s.render('atis YATAY - yukseklik acidir', True, WARN), (x, y)); y += 13
        screen.blit(f_s.render('kenara tikla -> SEKME', True, WARN), (x, y)); y += 13
        screen.blit(f_s.render('HEDEF KATMANA: teker=kalinlik  sag tik=ac/kapa',
                               True, INFO), (x, y)); y += 18
        pygame.draw.rect(screen, (30, 44, 38), (x - 6, y - 3, PANEL_W - 16, 20))
        screen.blit(f.render('SALDIRGANI DONAT  (tikla ya da tus)', True, ACCENT),
                    (x, y)); y += 24

        screen.blit(f.render('1) TASIYICI  (1-9)', True, ACCENT), (x, y)); y += 19
        for i, (nm, pr, desc) in enumerate(CARRIERS):
            sel = (i == ci)
            rect = pygame.Rect(x - 6, y - 2, PANEL_W - 16, 29)
            if sel:
                pygame.draw.rect(screen, (34, 46, 42), rect)
                pygame.draw.rect(screen, ACCENT, rect, 1)
            rows.append((rect, 'c', i))
            screen.blit(f_s.render(f"{'>' if sel else ' '} {i+1}. {nm}",
                                   True, FG if sel else DIM), (x, y)); y += 14
            if pr is None:
                info = '     yon yok - yuk KENDI capiyla gider'
            elif pr.get('diameter') is None:
                # Yonlu bosaltma molekuler kalir: capi yukten alir
                info = (f"     E={pr['energy']:g} cap=yukun uc={pr['tip_area']:g}"
                        f"  menzil {CARRIER_REACH[i]:.0f}")
            else:
                info = (f"     E={pr['energy']:g} cap={pr['diameter']:g}"
                        f" uc={pr['tip_area']:g}  menzil {CARRIER_REACH[i]:.0f}")
            screen.blit(f_s.render(info, True, DIM), (x, y)); y += 15
        y += 5

        screen.blit(f.render('2) BELIRTEC — nereye kenetlensin', True, ACCENT), (x, y)); y += 19
        for i, (nm, mlay, col, desc, grip) in enumerate(MARKERS):
            sel = (i == mi)
            on = mlay is None or mlay in [l.name for l in cell.active()]
            rect = pygame.Rect(x - 6, y - 2, PANEL_W - 16, 29)
            if sel:
                pygame.draw.rect(screen, (44, 34, 42), rect)
                pygame.draw.rect(screen, col, rect, 1)
            rows.append((rect, 'm', i))
            screen.blit(f_s.render(f"{'>' if sel else ' '} {MARKER_KEYS[i]} {nm}",
                                   True, (col if sel else DIM) if on else (90, 70, 70)),
                        (x, y)); y += 14
            tail = f'{desc}   guc {grip:.0f}' if on else 'katman kapali - kenetlenemez'
            screen.blit(f_s.render(f"     {mlay or 'balistik'} - {tail}",
                                   True, DIM), (x, y)); y += 15
        y += 5

        screen.blit(f.render('3) YUK — ne birakisin', True, ACCENT), (x, y)); y += 19
        for i, (nm, zone, kda, dia, eff, col, ch, slf) in enumerate(PAYLOADS):
            sel = (i == pi)
            rect = pygame.Rect(x - 6, y - 2, PANEL_W - 16, 29)
            if sel:
                pygame.draw.rect(screen, (30, 40, 50), rect)
                pygame.draw.rect(screen, col, rect, 1)
            rows.append((rect, 'p', i))
            screen.blit(f_s.render(f"{'>' if sel else ' '} {PAYLOAD_KEYS[i]} {nm}",
                                   True, col if sel else DIM), (x, y)); y += 14
            md = f" [{ZONE_MODE[zone]}]" if zone else ""
            cls = PAYLOAD_CLASS.get(nm)
            tf = PAYLOAD_SIDE.get(nm, 'her')
            screen.blit(f_s.render(f"     {ZONE_LABEL.get(zone, '-')}{md}  {kda} kDa  "
                                   f"katli {dia:.2f}  {cls or ''}"
                                   f"{'  [DIS YUZ]' if tf == 'dis' else ''}"
                                   f"{f'  zar~{PAYLOAD_SPAN[nm]}' if nm in PAYLOAD_SPAN else ''}",
                                   True, DIM), (x, y))
            y += 13
            # Uc kademenin tamami yalnizca SECILI yuk icin yazilir: hepsi
            # icin yazinca liste 16px uzayip SECIM panelini ekrandan atiyordu.
            if sel and cls:
                a, b, c2 = EFFECT_CLASS[cls][0]
                screen.blit(f_s.render(f"     {a} > {b} > {c2}", True,
                                       (150, 165, 190)), (x, y)); y += 13
        y += 6

        pn, pz, pk, pd, pe, pc, pch, pslf = PAYLOADS[pi]
        cn, cp, _ = CARRIERS[ci]
        screen.blit(f.render('SECIM', True, ACCENT), (x, y)); y += 18
        mn, mlay, mcol, _md, mgrip = MARKERS[mi]
        screen.blit(f_s.render(f'  {cn}', True, FG), (x, y)); y += 14
        screen.blit(f_s.render(f'  + {mn}', True, mcol), (x, y)); y += 14
        screen.blit(f_s.render(f'  + {pn}', True, pc), (x, y)); y += 14
        _cls = PAYLOAD_CLASS.get(pn)
        if _cls:
            screen.blit(f_s.render('    ' + EFFECT_CLASS[_cls][2], True, DIM),
                        (x, y)); y += 15
        _span = PAYLOAD_SPAN.get(pn)
        if _span is not None:
            _zt = next((l.t for l in cell.active() if l.name == 'Hucre zari'), None)
            if _zt is not None:
                _p = insertion_p(pi, _zt)
                _c = ((120, 220, 150) if _p > 0.6 else
                      WARN if _p > 0.2 else BAD)
                screen.blit(f_s.render(
                    f'  YERLESME: zar {_zt:.1f} / uyumlu {_span}  ->  %{_p*100:.0f}',
                    True, _c), (x, y)); y += 14
                if _p < 0.25:
                    screen.blit(f_s.render(
                        '  hidrofobik uyumsuzluk - zara giremez', True, DIM),
                        (x, y)); y += 14
        if PAYLOAD_SIDE.get(pn) == 'dis' and ci >= 3:
            screen.blit(f_s.render('  UYARI: bu yuk yalniz DIS yuzden etki eder',
                                   True, WARN), (x, y)); y += 14
            screen.blit(f_s.render('  derine enjekte etmek bosa gider - ic yuzde',
                                   True, DIM), (x, y)); y += 14
            screen.blit(f_s.render('  baglanacagi yapi yok', True, DIM), (x, y)); y += 15
        if ci == STYLET_INDEX and PAYLOADS[pi][4] == 'gozenek':
            screen.blit(f_s.render('  UYARI: stilet EMER; patlatan yuk yemegi yok eder',
                                   True, WARN), (x, y)); y += 16
        if mlay is not None and pz is not None:
            want = ZONE_TARGET[pz]
            uy = (mlay != want) if want else True
            if uy:
                screen.blit(f_s.render('  UYARI: belirtec yukun hedefi degil',
                                       True, WARN), (x, y)); y += 16
        if pz is None:
            screen.blit(f_s.render('  yuk yok - yalnizca mekanik', True, DIM), (x, y)); y += 17
        elif cp is not None and pch > lumen_of(cp['tip_area']):
            screen.blit(f_s.render(f'  zincir {pch:.2f} > lumen '
                                   f'{lumen_of(cp["tip_area"]):.2f}', True, BAD), (x, y)); y += 14
            screen.blit(f_s.render('  YUK LUMENE SIGMIYOR - yuksuz gider',
                                   True, BAD), (x, y)); y += 17
        elif cp is None and pd > cell.layers[3].mesh:
            screen.blit(f_s.render(f'  cap {pd:g} > duvar gozenegi {cell.layers[3].mesh:g}',
                                   True, BAD), (x, y)); y += 14
            screen.blit(f_s.render('  DIFUZYON YETMEZ - tasiyici sart', True, BAD), (x, y)); y += 17
        elif cp is None:
            screen.blit(f_s.render('  elekten gecer - tasiyici gerekmez', True, INFO), (x, y)); y += 17
        else:
            screen.blit(f_s.render(f'  tasiyici {ZONE_LABEL[pz]} bolgesine ulasmali',
                                   True, DIM), (x, y)); y += 17

        if cell.feeder is not None:
            pygame.draw.rect(screen, (44, 38, 26), (x - 6, y - 3, PANEL_W - 16, 34))
            screen.blit(f_s.render(f'MIZOSITOZ — sitoplazma emiliyor  '
                                   f'%{100*cell.drained:.0f}', True, WARN), (x, y)); y += 15
            screen.blit(f_s.render('stilet oldurmez: hedef TUKENEREK olur',
                                   True, DIM), (x, y)); y += 20

        # --- ENERJI BEDELI dokumu
        tot, parts = shot_total_cost(ci, pi)
        yeter = atk.energy >= tot
        pygame.draw.rect(screen, (26, 34, 30), (x - 6, y - 3, PANEL_W - 16, 76))
        screen.blit(f.render('ENERJI BEDELI', True, ACCENT), (x, y)); y += 17
        screen.blit(f_s.render(
            f"  atis {parts['atis']:.1f} + sentez {parts['sentez']:.1f}"
            f" + bagisiklik {parts['bagisiklik']:.1f} + acma {parts['acma']:.1f}",
            True, DIM), (x, y)); y += 14
        screen.blit(f_s.render(
            f"  TOPLAM {tot:.1f}   bakim {CARRIER_COST[ci][0]:.1f}/sn"
            f"{'   TEK KULLANIMLIK' if CARRIER_COST[ci][2] else ''}",
            True, FG if yeter else BAD), (x, y)); y += 14
        net = BASE_REGEN - CARRIER_COST[ci][0]
        screen.blit(f_s.render(
            f"  gelir {BASE_REGEN:.0f} - bakim {CARRIER_COST[ci][0]:.1f} = "
            f"NET {net:+.1f}/sn" + ("   [SINIRSIZ: SHIFT+E]" if atk.unlimited else ""),
            True, ACCENT if net > 0 else BAD), (x, y)); y += 14
        screen.blit(f_s.render(
            f"  enerji {atk.energy:.0f}/{atk.max_energy:.0f} -> "
            f"{int(atk.energy // tot) if tot > 0 else 99} atislik"
            f"{'' if yeter else '   YETMIYOR'}",
            True, ACCENT if yeter else BAD), (x, y)); y += 22

        screen.blit(f.render('SON ATIS', True, ACCENT), (x, y)); y += 19
        if last_shot is not None and last_shot.out_of_reach:
            screen.blit(f_s.render('  MENZIL DISI - atis hedefe ulasmadi',
                                   True, BAD), (x, y)); y += 15
            screen.blit(f_s.render(f'  mesafe {last_shot.gap_at_fire:.0f} > '
                                   f'menzil {last_shot.reach:.0f}', True, DIM), (x, y)); y += 15
        if last_shot is None:
            screen.blit(f_s.render('  (henuz atis yok)', True, DIM), (x, y))
        else:
            if last_shot.impact_angle is not None:
                lim = (90.0 if last_shot.pen.attempts > 100 else
                       (bite_angle_limit(cell.active()[0].friction,
                                         last_shot.pen.tip_area,
                                         last_shot.e0) if cell.active() else 0))
                ok = last_shot.impact_angle <= lim
                screen.blit(f_s.render(
                    f'  aci {last_shot.impact_angle:.0f} / sinir {lim:.0f} -> '
                    f'{"ISIRDI" if ok else "SEKTI"}', True, FG if ok else WARN), (x, y)); y += 16
            for c in last_shot.log:
                _tag, col, _bg = outcome_style(c.outcome)
                screen.blit(f_s.render(f"  {c.layer.name:<11} {c.outcome}", True, col), (x, y)); y += 14
                if c.outcome in (BREACH, BLOCKED):
                    screen.blit(f_s.render(
                        f"     E {c.energy_before:.1f}->{c.energy_after:.1f}"
                        f"  gereken {c.required:.1f}  p={c.probability:.3f}",
                        True, DIM), (x, y)); y += 14
                    if c.outcome == BLOCKED:
                        screen.blit(f_s.render(
                            f"     SAPLANDI: kalinligin %{100*c.penetration:.0f}'ine girdi",
                            True, WARN), (x, y)); y += 14
                elif c.outcome == SIEVE:
                    screen.blit(f_s.render('     capi gozenekten kucuk', True, DIM), (x, y)); y += 14
                elif c.outcome in ('sardi', 'yapisti', 'tutundu'):
                    aciklama = {'sardi': 'iplik ava sarildi - hareketsiz',
                                'yapisti': 'yuzeye yapisti - isirma garantili',
                                'tutundu': 'tutundu - saldirgan kendini ceker'}
                    screen.blit(f_s.render('     ' + aciklama[c.outcome],
                                           True, DIM), (x, y)); y += 14
                elif c.outcome == DOCK:
                    screen.blit(f_s.render('     BELIRTEC tanidi - enerjiye bakmadan durdu',
                                           True, DIM), (x, y)); y += 14
                else:
                    screen.blit(f_s.render('     aci isirma sinirini asti', True, DIM), (x, y)); y += 14
            y += 4
            if last_shot.dock_p is not None:
                _ok = last_shot.docked
                screen.blit(f_s.render(
                    f'  KENETLENME: E={last_shot.dock_E:.0f} / guc={last_shot.grip:.0f}'
                    f'  -> sans %{last_shot.dock_p*100:.0f}'
                    f'  {"TUTTU" if _ok else "KOPTU"}',
                    True, (120, 220, 150) if _ok else WARN), (x, y)); y += 15
            if pe and last_shot.miss_reason:
                screen.blit(f_s.render('  ' + last_shot.miss_reason.upper(),
                                       True, BAD), (x, y)); y += 15

        # ------------------------------------------- MOLEKUL SAYACI
        # Dozun ne oldugunu tahmin ettirmiyoruz: ekrandaki her nokta bir
        # molekul, sayac da o noktalarin sayimi. Ikisi her an birebir ayni.
        #
        # Sag surunun ALTINA konunca ekrandan tasiyordu; solda saldirganin
        # altindaki bos alanda hem sigiyor hem olan bitene yakin duruyor.
        # Sag panelin GERCEK icerik yuksekligi burada olculur; asagida
        # x,y molekul sayaci icin yeniden atandigi icin daha sonra olcmek
        # yanlis degeri veriyordu (panel hic kaydirilamiyordu).
        panel_ic = y + panel_kaydirma + 24
        panel_max = max(0, panel_ic - HEIGHT)
        panel_kaydirma = max(0, min(panel_kaydirma, panel_max))
        if panel_max > 0:
            oran = HEIGHT / panel_ic
            yuk = max(30, int(HEIGHT * oran))
            ust = int((HEIGHT - yuk) * (panel_kaydirma / panel_max))
            pygame.draw.rect(screen, (28, 36, 54), (WIDTH - 5, 0, 5, HEIGHT))
            pygame.draw.rect(screen, (95, 150, 135), (WIDTH - 5, ust, 5, yuk))

        x, y = 30, HEIGHT - 330
        pygame.draw.rect(screen, (16, 22, 38), (x - 12, y - 10, 430, 118))
        pygame.draw.rect(screen, (46, 56, 80), (x - 12, y - 10, 430, 118), 1)
        screen.blit(f.render('MOLEKUL SAYACI', True, ACCENT), (x, y)); y += 20
        if pz is None:
            screen.blit(f_s.render('  saf mekanik - yuk yok', True, DIM), (x, y))
        else:
            free = sum(1 for m in mols if m.state == 'free')
            stuck = [m for m in mols if m.state == 'stuck']
            n = cell.count_of(pi)
            th = PAYLOAD_THRESHOLD.get(pn, (0, 0, 0))
            tier = count_tier(pi, n)
            screen.blit(f_s.render(
                f'  stok {len(atk.stock)}/{STOCK_MAX}   atilan {atilan}   '
                f'yolda {free}   VARDI {n}   takili {len(stuck)}   '
                f'seyrelen {seyrelen}',
                True, FG if not atk.no_stock else WARN), (x, y)); y += 15
            screen.blit(f_s.render(
                f'  esik {th[0]} / {th[1]} / {th[2]}  ->  '
                f'{tier_label(pi, tier) if n else "henuz etki yok"}',
                True, TIER_COLOR[tier]), (x, y)); y += 15
            if stuck:
                nerede = {}
                for m in stuck:
                    nerede[m.blocked_by] = nerede.get(m.blocked_by, 0) + 1
                yer = ', '.join(f'{k} ({v})' for k, v in nerede.items())
                screen.blit(f_s.render(f'  ELEKTE TAKILDI: {yer}', True, BAD),
                            (x, y)); y += 14
                screen.blit(f_s.render(
                    f'  cap {pd:.2f} > o katmanin gozenegi', True, DIM),
                    (x, y)); y += 14
            _yerlesemedi = sum(1 for m in mols if m.state == 'stuck'
                               and m.blocked_by and 'yerlesemedi' in m.blocked_by)
            if _yerlesemedi:
                screen.blit(f_s.render(
                    f'  YERLESEMEDI: {_yerlesemedi} molekul zar yuzunde takildi',
                    True, WARN), (x, y)); y += 14
            _yanlis = sum(1 for m in mols
                          if m.state == 'free' and m.side == 'dis'
                          and m.depth >= m.need)
            if _yanlis:
                screen.blit(f_s.render(
                    f'  YANLIS YUZ: {_yanlis} molekul ic yuzde bekliyor',
                    True, WARN), (x, y)); y += 14
            if seyrelen and not stuck and not n:
                screen.blit(f_s.render(
                    '  MENZIL YETMEDI: hedefe varamadan ortamda seyreldiler',
                    True, WARN), (x, y)); y += 14
            if atk.no_stock:
                screen.blit(f_s.render('  STOK YETMEDI - sentez bekleniyor',
                                       True, WARN), (x, y)); y += 14
            if cell.spilled:
                screen.blit(f_s.render('  HUCRE PATLADI - stoku ortama sacildi',
                                       True, (255, 170, 90)), (x, y))

        if organ_acik:
            organ_rows = draw_organ_panel(screen, cell, f, f_s, mouse)
        else:
            organ_rows = []
        window.fill((0, 0, 0))
        window.blit(pygame.transform.smoothscale(
            screen, (int(WIDTH * olcek), int(HEIGHT * olcek))), kayma)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()

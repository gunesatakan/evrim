"""Katman-iğne etkileşimi: TEK formül.

Moleküler yerleşme ile mekanik delme ayrı sistemler DEĞİLDİR. İkisi de aynı
denklemin uçlarıdır; fark enerji miktarı ve deneme desenidir:

    moleküler yerleşme : düşük enerji (ısıl), devasa deneme sayısı
    mekanik delme      : yüksek enerji (kinetik), tek deneme

Bu yüzden difüzyonla sızan bir peptit ile 150 atmosferle çakılan bir zıpkın
aynı fonksiyondan geçer. Ayrıntı için manifesto/katman_igne_fizigi.md
"""

import math


# ---------------------------------------------------------------- katmanlar

class Layer:
    """Hücrenin dış katmanlarından biri.

    mesh : gözenek çapı. Bundan küçük şeyler BEDAVAYA geçer (elek).
           0 = delik yok, her şey yarmak zorunda.
    B    : birim alan-kalınlık başına bariyer enerjisi (mukavemet).
    t    : kalınlık. Hem bariyeri hem geçiş süresini büyütür.
    friction : yüzey sürtünmesi. ÇİFT YÖNLÜ - ısırmayı zorlaştırır ama
           ısırma başarılıysa şaft sürtünmesini azaltıp geçişi kolaylaştırır.
    elastic : esneklik. Deforme olarak darbeyi yayar, gereken enerjiyi artırır.
    """

    __slots__ = ('name', 'mesh', 'B', 't', 'friction', 'elastic', 'color',
                 'porosity', 'viscosity')

    def __init__(self, name, mesh, B, t, friction=0.5, elastic=0.0,
                 color=(180, 180, 180), porosity=0.5, viscosity=0.05):
        self.name = name
        self.mesh = mesh
        self.B = B
        self.t = t
        self.friction = friction
        self.elastic = elastic
        self.color = color
        # ACIK ALAN ORANI: yuzeyin ne kadari gozenek. Balistik bir cismin
        # duz bir kanal bulma sansini belirler.
        self.porosity = porosity
        # Ortam viskozitesi: elekten gecen cisim bile jel icinde surtunur.
        self.viscosity = viscosity

    def channel_probability(self, thickness_scale=None):
        """Balistik bir cismin bu katmanda HIZALANMIS kanal bulma olasiligi.

        Difuzyon icin gecerli DEGILDIR: molekul Brown hareketiyle dolambacli
        yol izler, gozeneklerin ust uste gelmesine ihtiyac duymaz. Balistik
        cisim ise duz gider; kalinlik boyunca her gozenek katmanini ust uste
        tutturmak zorundadir.

            p = gozeneklilik ^ (kalinlik / gozenek_capi)

        Kalin bir duvarda bu ustel olarak sifira gider - stilet gozenekten
        kucuk olsa bile kanal bulamaz, malzemeye carpar ve yarmak zorunda kalir.
        """
        if self.mesh <= 0.0:
            return 0.0
        n = max(1.0, self.t / self.mesh)
        return max(0.0, min(1.0, self.porosity)) ** n

    def required_energy(self, tip_area, angle_deg=0.0):
        """Bu katmanı yarmak için gereken enerji.

        Esneklik doğrudan çarpan: esnek katman deforme olup yükü yayar,
        delici aynı deliği açmak için daha çok iş yapmak zorunda kalır.

        EGIK GIRIS YOLU UZATIR: kalinligi t olan bir tabakayi theta aciyla
        gecmek t/cos(theta) yol demektir. EGIMLI ZIRHIN calisma sebebi tam
        olarak budur - mermi daha cok malzeme kat eder.

        Bu terim onceden EKSIKTI: yalnizca mevcut enerji azaltiliyordu
        (E*cos^2), gereken is sabit kaliyordu. Ikisi birlikte acinin etkisini
        cos^2 yerine ~cos^3 yapar.
        """
        c = math.cos(math.radians(max(-89.0, min(89.0, angle_deg))))
        path = self.t / max(0.02, c)
        return self.B * tip_area * path * (1.0 + self.elastic)


# --------------------------------------------------------------- deliciler

class Penetrator:
    """Bir katmanı geçmeye çalışan şey: molekül ya da mermi.

    energy    : taşıdığı enerji (aynı birimde; molekülde ısıl, mermide kinetik)
    tip_area  : uç kesit alanı - küçük olması basıncı artırır
    diameter  : etkin çap - elekten geçip geçmediğini belirler
    attempts  : saniyedeki deneme sayısı (difüzyonda çok büyük, atışta 1)
    """

    __slots__ = ('name', 'energy', 'tip_area', 'diameter', 'attempts', 'payload')

    def __init__(self, name, energy, tip_area, diameter, attempts=1.0, payload=None):
        self.name = name
        self.energy = energy
        self.tip_area = tip_area
        self.diameter = diameter
        self.attempts = attempts
        self.payload = payload


# ----------------------------------------------------------------- sonuçlar

SIEVE = 'elek'          # gözenekten bedavaya geçti
BREACH = 'yarma'        # enerjiyle yardı
BLOCKED = 'durduruldu'  # geçemedi
GLANCE = 'sekti'        # ısıramadı, açıyla savruldu
DOCK = 'kenetlendi'     # BELIRTEC katmani tanidi, enerjisine bakmadan durdu


class Crossing:
    """Tek bir katman geçişinin sonucu."""

    __slots__ = ('layer', 'outcome', 'probability', 'energy_before',
                 'energy_after', 'required', 'delay', 'penetration')

    def __init__(self, layer, outcome, probability, energy_before,
                 energy_after, required, delay, penetration=1.0):
        self.layer = layer
        self.outcome = outcome
        self.probability = probability
        self.energy_before = energy_before
        self.energy_after = energy_after
        self.required = required
        self.delay = delay
        # Katmanin NE KADARINA girildi (0..1). Gecenlerde 1.0; gecemeyen
        # mermi yuzeyde ZIPLAMAZ, enerjisi orantisinda GOMULUP kalir.
        self.penetration = penetration

    @property
    def passed(self):
        return self.outcome in (SIEVE, BREACH)

    def __repr__(self):
        return (f"<{self.layer.name}: {self.outcome} "
                f"E {self.energy_before:.1f}->{self.energy_after:.1f} "
                f"gereken {self.required:.1f} p={self.probability:.3f}>")


# ------------------------------------------------------------------ tutunma

# Sivriligin surtunmeye kattigi "kenetlenme" katsayisi. Keskin uc yalnizca
# basinci artirmakla kalmaz, yuzeye mekanik olarak kenetlenir; bu yuzden kut
# bir merminin kayacagi acida bile isirabilir.
BITE_SHARPNESS = 0.15      # sivriligin kenetlenme katkisi
BITE_REF_ENERGY = 16.0     # hiz teriminin referansi (sinirda stilet)
DIFFUSION_ATTEMPTS = 100.0 # bunun ustunde: balistik degil, difuzyon


def bite_angle_limit(friction, tip_area=1.0, energy=None):
    """Isirmanin mumkun oldugu en buyuk carpma acisi (derece).

    SURTUNME KONISI: temas noktasinda teget bilesen surtunmeyi asarsa mermi
    kayar. Klasik kosul  tan(theta) <= mu  ve buradan  theta_kritik = atan(mu).

    mu UC SEYE birden baglidir:

      1. YUZEY surtunmesi - kaygan yuzey mermiyi savurur
      2. UC SIVRILIGI     - keskin uc yuzeye mekanik olarak kenetlenir
      3. CARPMA HIZI      - hizli mermi daha egik acilarda bile isirir

    Ucuncusu sezgiye aykiri gorunur (temas suresi kisaliyor diye daha cok
    sekmesi beklenir) ama balistik olcumler tersini soyluyor: kritik sekme
    acisi hizla ARTAR. Betona carpan duz uclu mermilerde 800 m/s'de ~50 derece
    iken 1000 m/s'de 60-65 dereceye cikiyor.

        mu_etkin = (surtunme + SIVRILIK/uc_alani) * (E/E_ref)^0.25

    Us 0.25 cunku v ~ sqrt(E) ve kritik aci kabaca sqrt(v) ile olceklenir.
    """
    f = max(0.0, min(1.0, friction))
    mu = f + BITE_SHARPNESS / max(0.05, tip_area)
    if energy is not None and energy > 0.0:
        mu *= (energy / BITE_REF_ENERGY) ** 0.25
    return math.degrees(math.atan(mu))


def try_bite(surface_layer, impact_angle_deg, tip_area=1.0,
             energy=None, attempts=1.0):
    """Delici yüzeye tutunabildi mi?

    Bu bir ENERJI eşiği DEĞİLDİR - ön koşuldur. Isıramadıysa delicinin
    enerjisi anlamsızdır, delme formülü hiç çalışmaz.

    DIFUZYONA UYGULANMAZ. Sekme balistik bir olaydir: belirli bir yorunge,
    belirli bir carpma acisi gerektirir. Difuzyonla gelen molekulun yorungesi
    yoktur - yuzeye her acidan, saniyede milyonlarca kez carpar ve er gec dik
    yaklasir. Bu yuzden deneme sayisi buyukse isirma testi atlanir.
    """
    if attempts > DIFFUSION_ATTEMPTS:
        return True
    limit = bite_angle_limit(surface_layer.friction, tip_area, energy)
    return abs(impact_angle_deg) <= limit


# ------------------------------------------------------------- tek formül

def cross_layer(pen, layer, e_ref, angle_deg=0.0, rng=None):
    """Bir katmanı geçme denemesi. Belgedeki tek formül.

        1. ELEK  : d <= mesh -> bedavaya geçer, yalnızca t kadar gecikir
        2. YARMA : gereken = B * A * t * (1+esneklik)
                   P = 1                          eger E >= gereken
                   P = exp(-(gereken-E)/E_ref)    eger E < gereken
                   P_toplam = 1 - (1-P)^N

    e_ref KÜÇÜK olmalı: üstel kapı o zaman keskin çalışır ve "imkânsız"
    gerçekten imkânsız olur.

    Eğik çarpmada yalnızca dik bileşen delmeye katkı verir: E * cos^2(açı).
    """
    energy = pen.energy

    # 1. ELEK - boyut kapısı.
    #
    # Boyut YETERLI DEGIL: cismin gozenege DENK GELMESI de gerekir.
    # Difuzyonla gelen molekul dolambacli yol izleyip er gec bulur; balistik
    # cisim duz gider ve kalinlik boyunca hizalanmis bir kanal bulmak
    # zorundadir. Bulamazsa malzemeye carpar ve asagidaki YARMA'ya duser.
    if layer.mesh > 0.0 and pen.diameter <= layer.mesh:
        if pen.attempts > DIFFUSION_ATTEMPTS:
            return Crossing(layer, SIEVE, 1.0, energy, energy, 0.0, layer.t)
        p_ch = layer.channel_probability()
        if rng is None:
            hit_channel = p_ch >= 1.0
        else:
            hit_channel = rng.random() < p_ch
        if hit_channel:
            # Kanaldan gecti ama bedavaya degil: jel icinde viskoz surtunme
            drag = energy * layer.viscosity * layer.t / max(1.0, layer.mesh)
            return Crossing(layer, SIEVE, p_ch, energy,
                            max(0.0, energy - drag), 0.0, layer.t)
        # kanal bulunamadi -> malzemeye carpti, yarmak zorunda

    # 2. YARMA
    required = layer.required_energy(pen.tip_area, angle_deg)

    # Eğik çarpmada sadece dik bileşen iş görür
    c = math.cos(math.radians(max(-89.9, min(89.9, angle_deg))))
    effective = energy * c * c

    if effective >= required:
        p_single = 1.0
    else:
        gap = required - effective
        p_single = math.exp(-gap / max(1e-9, e_ref))

    n = max(1.0, pen.attempts)
    if p_single >= 1.0:
        p_total = 1.0
    elif p_single <= 0.0:
        p_total = 0.0
    else:
        # 1-(1-p)^N, çok büyük N'de taşmayı önlemek için log üzerinden
        p_total = -math.expm1(n * math.log1p(-p_single))

    roll = (rng.random() if rng is not None else None)
    success = (p_total >= 1.0) if roll is None else (roll < p_total)

    if not success:
        # KISMI PENETRASYON: delemedi ama saplandi. Girdigi derinlik,
        # tasidigi enerjinin gerekene oranidir - is = kuvvet x mesafe.
        frac = 0.0 if required <= 0 else min(0.98, effective / required)
        return Crossing(layer, BLOCKED, p_total, energy, 0.0, required,
                        0.0, frac)

    # Yarma enerjiyi tüketir. Sürtünme SONRASINDA ek kayıp getirir -
    # kaygan katman ısırmayı zorlaştırır ama geçişi ucuzlatır.
    spent = min(effective, required)
    drag = spent * 0.5 * (1.0 - layer.friction)
    remaining = max(0.0, energy - spent - drag)
    return Crossing(layer, BREACH, p_total, energy, remaining, required, layer.t)


def traverse(pen, layers, e_ref, angle_deg=0.0, rng=None):
    """Katmanları dıştan içe sırayla geç. Her adımın kaydını döndür.

    İlk katmanda ISIRMA testi yapılır: başarısızsa hiçbir katman denenmez.
    """
    log = []
    if not layers:
        return log

    if not try_bite(layers[0], angle_deg):
        log.append(Crossing(layers[0], GLANCE, 0.0, pen.energy, pen.energy, 0.0, 0.0))
        return log

    current = Penetrator(pen.name, pen.energy, pen.tip_area,
                         pen.diameter, pen.attempts, pen.payload)
    for layer in layers:
        step = cross_layer(current, layer, e_ref, angle_deg, rng)
        log.append(step)
        if not step.passed:
            break
        current.energy = step.energy_after
    return log


def reached_depth(log):
    """Kaç katman geçildi. len(layers) ise sitoplazmaya ulaşıldı."""
    return sum(1 for c in log if c.passed)

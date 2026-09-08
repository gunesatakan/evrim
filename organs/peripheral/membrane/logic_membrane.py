import game_settings
from .logic_electrone_transport import ElectronTransportChain

class MembraneLogic:
    """Zar: enerji üretimi (ETC), kalsiyum sinyali ve SAVUNMA.

    Savunma organ değil zar özelliğidir — kapsül/duvar/efflux hücrenin
    tamamını sarar, konumu yoktur ve iskelet geninde yer kaplamaz.

    Hasar üç KANAL'dan gelir (mekanik / kimyasal / yutma) ve her saldırının
    ayrıca TEMAS gerektirip gerektirmediği bilinir. Savunmaların hangi
    saldırıya karşı işe yaradığı bu ikiliden kendiliğinden çıkar:

      duvar   -> yalnızca mekanik      (litik enzim onu yok sayar)
      dış zar -> yalnızca kimyasal     (stilete karşı boş)
      efflux  -> yalnızca kimyasal     (mekaniğe karşı boş)
      kapsül  -> yalnızca TEMAS'lı     (menzilli nematosist üstünden geçer)

    Yani hiçbir savunma her şeye karşı iyi değildir; matris ayrıca
    kodlanmaz, bu kurallardan doğar.
    """

    def __init__(self):
        # Kalsiyum Patlaması Sistemi
        self.calcium_boost = 1.0
        # Enerji Üretim Sistemi (ETC)
        self.etc = ElectronTransportChain(efficiency=1.0)

        # --- Zar bütünlüğü ---
        self.max_integrity = game_settings.MEMBRANE_INTEGRITY_BASE
        self.integrity = self.max_integrity

        # --- Savunma yatırımları (0 = yok) ---
        self.wall = 0.0      # peptidoglikan  -> mekanik direnç
        self.outer = 0.0     # LPS / dış zar  -> kimyasal direnç
        self.capsule = 0.0   # glikokaliks    -> temaslı saldırıyı engeller
        self.efflux = 0.0    # pompa          -> kimyasalı dışarı atar
        self.repair = 0.0    # onarım hızı
        self.slip = 0.0      # kayganlık -> bağlanmaya direnç
        # Laboratuvar kesiti BES katman cizer; bunlardan mukus ve S-layer
        # oyunda hicbir seye baglı degildi. Digerleri gibi yatirim yapilan
        # birer savunma oldular: mukus tutunmayi zorlastirir, S-layer hem
        # mekanik zirh verir hem yuzeyi SERTLESTIRIR (sert yuzeyi olan
        # hucre fagosite edilemez ve kendisi de sitostom acamaz).
        self.mucus = 0.0     # slime tabakasi -> yapisma direnci
        self.slayer = 0.0    # kristal protein orgusu -> mekanik + yutulma

        # --- KATMAN VARLIGI ---
        #
        # Yatirimin 0 olmasi ile katmanin HIC OLMAMASI ayni sey degildi ve
        # kod ikisini ayirt edemiyordu: lab.default_layers() her katmana bir
        # TABAN kalinlik veriyor (duvar 6.0), yani yatirimsiz bir hucrenin
        # bile kesitte kalin bir duvari vardi. Duvarsiz hucre (Mycoplasma,
        # hayvan hucresi) ifade edilemiyordu - ve duvar hep var oldugu icin
        # `sert_yuzey` hep dolu donuyor, FAGOSITOZ hicbir hucrede
        # calismiyordu. Plazma zari (outer) ZORUNLUDUR, bayragi yoktur.
        self.var_mucus = True
        self.var_capsule = True
        self.var_slayer = True
        self.var_wall = True

        # --- KATMAN KALINLIKLARI (lab birimi) ---
        #
        # Kalinlik lab.default_layers()'ta SABIT bir sayiydi; her hucrenin
        # duvari 6.0, mukusu 7.0'di ve degistirilemiyordu. Oysa bunlar
        # olgun degerler: bir katman ilk kazanildiginda o kalinlikta
        # OLMAZ - ince baslar, yatirimla kalinlasir. Artik her hucre
        # kendi kalinliklarini tasiyor ve editorden ayarlanabiliyor.
        self.kalinlik = dict(self.VARSAYILAN_KALINLIK)

    #: yatirim alani -> varlik alani. Plazma zari (outer) listede YOK.
    KATMANLAR = {'mucus': 'var_mucus', 'capsule': 'var_capsule',
                 'slayer': 'var_slayer', 'wall': 'var_wall'}

    #: OLGUN kalinliklar (lab.default_layers() ile ayni). Plazma zari da
    #  burada: o kaldirilamaz ama kalinligi ayarlanabilir.
    VARSAYILAN_KALINLIK = {'mucus': 7.0, 'capsule': 5.0, 'slayer': 2.0,
                           'wall': 6.0, 'outer': 1.5}

    #: Yeni kazanilan katman bu kalinlikta dogar - olgun degerin degil.
    #  Bir hucre duvarini birden bire 6 birim kalinliginda edinmez;
    #  once ince bir tabaka salgilar, sonra kalinlastirir.
    YENI_KATMAN_KALINLIK = 0.6

    def katman_kalinligi(self, alan):
        """Bu katmanin TABAN kalinligi (yatirim haric)."""
        return float(self.kalinlik.get(alan, self.VARSAYILAN_KALINLIK.get(alan, 1.0)))

    def katman_kalinligi_ayarla(self, alan, deger):
        if alan in self.VARSAYILAN_KALINLIK:
            self.kalinlik[alan] = max(0.2, min(20.0, float(deger)))
            return True
        return False

    def katman_var(self, alan):
        """Bu katman hucrede var mi? Katman olmayan alanlar hep 'var'."""
        bayrak = self.KATMANLAR.get(alan)
        return True if bayrak is None else bool(getattr(self, bayrak, True))

    def katman_puani(self, alan):
        """Bu katmanin SAYILAN yatirimi. Katman yoksa 0.

        Yatirim sayisi katman kaldirilinca SILINMEZ (geri eklenirse eski
        kalinligini bulsun diye), bu yuzden ham `zar.wall` okumak yaniltir:
        duvari olmayan bir hucre depoda duran 12 puanlik duvar yatirimiyla
        zirhli gorunurdu. Disaridan okuyan herkes bu kapidan gecmeli.
        """
        return getattr(self, alan, 0.0) if self.katman_var(alan) else 0.0

    def katman_ekle(self, alan):
        """Katmani hucreye ekle. Yoktan var edilir, kalinligi tabandandir."""
        bayrak = self.KATMANLAR.get(alan)
        if bayrak is None or getattr(self, bayrak):
            return False
        setattr(self, bayrak, True)
        # Yeni katman OLGUN kalinlikta dogmaz.
        self.kalinlik[alan] = self.YENI_KATMAN_KALINLIK
        # VAR OLAN AMA SIFIR YATIRIMLI KATMAN BIR CELISKIDIR.
        #
        # `resistance` yalnizca YATIRIM sayisini okuyor. Mutasyonla yeni
        # kazanilan bir katmanin yatirimi 0 oldugu icin hicbir koruma
        # vermiyor, ama var oldugu icin bakim enerjisini (TABAN_COST_*) ve
        # yaricap artisini hemen goturuyordu. Yani yeni bir katman, ilgili
        # gen defalarca cekilip buyutulene kadar SAF ZARARDI - ve o
        # kadar dayanamadan eleniyordu. Savunma tipinin evrimlesmesinin
        # onundeki asil engel buydu (olculdu: katman orani 600 saniyede
        # 0.055'te kaldi).
        #
        # Gen ifade edildiyse ortada bir madde vardir: katman bir kademe
        # yatirimla dogar. Daha once tasinip birakilmis bir katman ise
        # eski birikimini korur.
        if getattr(self, alan, 0.0) <= 0.0:
            setattr(self, alan, float(game_settings.YENI_KATMAN_YATIRIM))
        return True

    def katman_cikar(self, alan):
        """Katmani kaldir. Yatirim SAYISI korunur - geri eklenirse geri gelir."""
        bayrak = self.KATMANLAR.get(alan)
        if bayrak is None or not getattr(self, bayrak):
            return False
        setattr(self, bayrak, False)
        return True

    # ---------- enerji ----------

    @property
    def energy_regen(self):
        return self.etc.efficiency

    @property
    def base_energy_cost(self):
        """ETC + savunma yatırımlarının SÜREKLİ bakım gideri.

        Karar: hasar almak enerji yakmaz; savunmayı ayakta tutmak yakar.
        """
        g = game_settings
        # Olmayan katman ne taban ne yatirim bedeli ister; olan katman
        # yatirimsiz bile TABAN bedelini oder. Kaldirmanin kazanci budur.
        kat = 0.0
        for alan, birim, taban in (('wall', g.COST_WALL, g.TABAN_COST_WALL),
                                   ('capsule', g.COST_CAPSULE, g.TABAN_COST_CAPSULE),
                                   ('mucus', g.COST_MUCUS, g.TABAN_COST_MUCUS),
                                   ('slayer', g.COST_SLAYER, g.TABAN_COST_SLAYER)):
            if self.katman_var(alan):
                kat += taban + getattr(self, alan) * birim
        return (self.etc.efficiency * g.COST_MEMBRANE
                + self.outer * g.COST_OUTER
                + self.efflux * g.COST_EFFLUX
                + self.repair * g.COST_REPAIR
                + self.slip * g.COST_SLIP
                + kat
                + self.max_integrity * g.COST_INTEGRITY)

    @property
    def binding_resistance(self):
        """Tutulmaya karşı direnç.

        Kapsül de katkı verir: mukuslu yüzeye tutunmak zordur. Böylece
        kapsül hem temaslı hasarı azaltır hem de yakalanmayı zorlaştırır -
        aynı yatırım iki farklı tehdide karşı işe yarar.
        """
        kaygan = self.slip
        if self.katman_var('capsule'):
            kaygan += self.capsule
        if self.katman_var('mucus'):
            kaygan += self.mucus
        return kaygan

    # ---------- hareket cezası ----------

    @property
    def speed_multiplier(self):
        """Duvar ve kapsül ağırlık yapar; hücre yavaşlar."""
        g = game_settings
        penalty = 0.0
        for alan, ceza in (('wall', g.WALL_SPEED_PENALTY),
                           ('capsule', g.CAPSULE_SPEED_PENALTY),
                           ('mucus', g.MUCUS_SPEED_PENALTY),
                           ('slayer', g.SLAYER_SPEED_PENALTY)):
            if self.katman_var(alan):
                penalty += getattr(self, alan) * ceza
        return max(0.25, 1.0 / (1.0 + penalty))

    # ---------- hasar ----------

    def resistance(self, channel, contact):
        """Verilen saldırıya karşı toplam direnç puanı."""
        r = 0.0
        if channel == 'mechanical':
            if self.katman_var('wall'):
                r += self.wall
            if self.katman_var('slayer'):
                r += self.slayer
        elif channel == 'chemical':
            # dis zar ve pompa PLAZMA ZARINA aittir, hep vardir
            r += self.outer + self.efflux
        if contact:
            if self.katman_var('capsule'):
                r += self.capsule
            if self.katman_var('mucus'):
                r += self.mucus
        return r

    def take_damage(self, amount, channel='mechanical', contact=True):
        """Hasarı savunmalardan geçirip zar bütünlüğünden düş.

        1/(1+direnç) kullanılır: azalan getiri verir ve hiçbir yatırım
        tam bağışıklık sağlamaz, ama yüksek yatırım hasarı sıfıra yaklaştırır.

        Uygulanan (azaltılmış) hasarı döndürür.
        """
        if amount <= 0:
            return 0.0
        applied = amount / (1.0 + self.resistance(channel, contact))
        self.integrity -= applied
        if self.integrity < 0:
            self.integrity = 0.0
        return applied

    @property
    def is_ruptured(self):
        return self.integrity <= 0

    def update_repair(self, dt):
        """Zarı yavaşça onar. Hasarı ÖNLEMEZ, sonradan kapatır."""
        if self.repair <= 0 or self.integrity >= self.max_integrity:
            return
        self.integrity = min(
            self.max_integrity,
            self.integrity + self.repair * game_settings.REPAIR_PER_POINT * dt)

    # ---------- büyüme ----------

    def set_calcium_signal(self, urgency_level):
        """Mekanoreseptörden gelen aciliyet sinyalini uygula."""
        self.calcium_boost = urgency_level

    KATMAN_ADI = (('wall', 'Duvar'), ('outer', 'Dis zar'),
                  ('capsule', 'Kapsul'), ('slayer', 'S-tabaka'),
                  ('mucus', 'Mukus'), ('efflux', 'Pompa'),
                  ('repair', 'Onarim'), ('slip', 'Kayganlik'))

    def gelisim(self):
    # GELISIM RAPORU
    #
    # Organin ne kadar gelistigini SORAN yer, organin ICINI bilmemeli.
    # Denetim paneli her organ turu icin ayri bir dal tutsaydi, yeni bir
    # organ eklemek paneli de duzenlemeyi gerektirirdi. Organ kendi
    # gelisimini kendi anlatir.
    #
    # Doner: [(eksen adi, 0..1 oran, gosterilecek metin)]
    #
    # ORAN yalnizca cubuk icindir. Gercek tavani olan eksenlerde
    # (kazanc, kapsama) gercek orandir; tavansiz eksenlerde (uzunluk,
    # guc) 10 yukseltme tam cubuk sayilir - METIN her zaman gercek
    # degeri tasir, cubuk yalnizca bir bakista fikir verir.
        g = game_settings
        ni = max(0.0, (self.max_integrity - g.MEMBRANE_INTEGRITY_BASE)
                 / max(1e-6, g.GROW_MEMBRANE_INTEGRITY))
        ne = max(0.0, (self.etc.efficiency - g.ENERGY_REGEN_BASE)
                 / max(1e-6, g.GROW_ENERGY_REGEN))
        out = [("Butunluk", min(1.0, ni / 10.0),
                "%.0f / %.0f" % (self.integrity, self.max_integrity)),
               ("ETC verimi", min(1.0, ne / 10.0),
                "x%.2f" % self.etc.efficiency)]
        # SAVUNMA KATMANLARI. Yalnizca VAR OLANLAR listelenir: sifir
        # kalinliktaki bir katmani gostermek "kapsulu var ama zayif"
        # izlenimi verirdi - oysa katman hic dogmamistir.
        for alan, ad in self.KATMAN_ADI:
            d = float(getattr(self, alan, 0.0) or 0.0)
            if d > 0.0:
                out.append((ad, min(1.0, d / 5.0), "%.1f" % d))
        return out

    def grow_etc(self):
        self.etc.grow()

    def grow_integrity(self):
        gain = game_settings.GROW_MEMBRANE_INTEGRITY
        self.max_integrity += gain
        self.integrity += gain      # yatırım anında dolu gelir

    def grow_defense(self, kind):
        """Savunmayi gelistir. OLMAYAN katman guclendirilemez.

        Gen genomda durur ama IFADE EDILMEZ: duvari olmayan hucrede duvar
        geni yatirimi artirirsa, sayi buyur, bakim gideri odenir ve
        karsiliginda hicbir katman ortaya cikmaz. Yeni katman ancak
        `katman_ekle` ile dogar.
        """
        if kind in self.KATMANLAR and not self.katman_var(kind):
            return False
        g = game_settings
        if kind == 'wall':      self.wall += g.GROW_WALL
        elif kind == 'outer':   self.outer += g.GROW_OUTER
        elif kind == 'capsule': self.capsule += g.GROW_CAPSULE
        elif kind == 'efflux':  self.efflux += g.GROW_EFFLUX
        elif kind == 'repair':  self.repair += g.GROW_REPAIR
        elif kind == 'slip':    self.slip += g.GROW_SLIP
        elif kind == 'mucus':   self.mucus += g.GROW_MUCUS
        elif kind == 'slayer':  self.slayer += g.GROW_SLAYER
        else:                   return False
        return True

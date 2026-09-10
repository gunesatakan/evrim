"""Saldırı organlarının mantığı.

Altı mekanizmanın hepsi gerçek mikrobiyal sistemlerden alındı ve hiçbiri
diğerinin üstün versiyonu değil — her birinin farklı bir üstünlüğü ve farklı
bir açığı var. Hangi savunmanın işe yaradığı burada değil, iki alandan
türetilir:

    channel : 'mechanical' | 'chemical' | 'engulf'
    contact : temas gerekiyor mu

Zar (logic_membrane.py) bu ikiliye bakarak direnç uygular. Yani matris hiçbir
yerde tablo olarak yazılı değil; kurallardan doğuyor.

Karar: hasar almak enerji yakmaz, saldırı KULLANMAK yakar.
"""
import random

import game_settings


class WeaponLogic:
    """Ortak silah mantığı: menzil, bekleme, kullanım enerjisi, gelişim."""

    KEY = None            # game_settings ön eki
    CHANNEL = 'mechanical'
    CONTACT = True
    CONTINUOUS = False    # True ise her kare çalışır (toksin)
    # Gercek mikrobiyal karsiliklarina gore: stilet ve fagositoz once
    # TUTUNMAK zorundadir (Vampyrella once yapisir, amip once adezyon
    # kurar). T6SS temas ister ama tutunmaz; nematosist ise onceden
    # baglanmaz, ISABET EDINCE ip kurar.
    REQUIRES_BIND = False
    CREATES_TETHER = False

    # Laboratuvardaki varsayilan (tasiyici, yuk) eslemesi. Silah artik
    # sabit bir eslemeye mahkum degil: editorde TASIYICI, YUK ve BELIRTEC
    # ayri ayri secilebiliyor. Sabit esleme yalnizca VARSAYILAN.
    VARSAYILAN_TASIYICI = 2      # Fiskirtma
    VARSAYILAN_YUK = 1           # Norotoksin
    # URETICI: yuku SENTEZLEYEN organ (Toksin, Lizin). Yalnizca ureticiler
    # stok tutar. Igneli silahlar uretmez, hucrenin ureticisinden yukler.
    URETICI = False
    # Bu tasiyicinin evrimde gecebilecegi varyantlar (lab CARRIERS indeksi)
    VARYANTLAR = ()

    def __init__(self, power=1.0):
        self.power = power        # gelişim çarpanı (gen ile artar)
        self.cooldown_timer = 0.0
        # UC AYRI GEN: tasiyici (bu organ), yuk, belirtec.
        # Igneli silah YUKSUZ dogar - yuk hucrenin ureticisinden gelir.
        # Uretici kendi yukuyle dogar: o zaten "ben bunu sentezlerim" genidir.
        self.carrier = (random.choice(self.VARYANTLAR) if self.VARYANTLAR
                        else self.VARSAYILAN_TASIYICI)
        self.payload = self.VARSAYILAN_YUK if self.URETICI else 0
        self.marker = 0           # 0 = belirtec yok (balistik)
        # STOK: ureticinin govdesinde fiilen tasinan molekul sayisi.
        self.stok = 0.0
        self._sentez = 0.0

    # ------------------------------------------------------------ YUK
    def sentezle(self, dt, hucre):
        """Uretici yukunu sentezler ve stoklar; her molekul enerji ister.

        lab.STOCK_REGEN hizinda, lab.payload_cost bedeliyle (sentez +
        katalitik yuklerde bagisiklik proteini). YUK_SENTEZ_OLCEK oyunun
        enerji olcegine indirger; oranlar labdaki gibi kalir - T3SS
        efektoru norotoksinden 16 kat pahalidir.
        """
        if not self.URETICI:
            return
        try:
            import lab as _lab
        except Exception:
            return
        pi = int(self.payload)
        if pi <= 0 or pi >= len(_lab.PAYLOADS) or _lab.PAYLOADS[pi][1] is None:
            return
        if self.stok >= _lab.STOCK_MAX:
            return
        synth, imm = _lab.payload_cost(_lab.PAYLOADS[pi])
        # Lab bedeli bir ATISLIK yuk icindir (igne 12 molekul): molekul
        # basina onun 1/12'si, oyun olcegiyle.
        bedel = (synth + imm) / 12.0 * game_settings.LAB_ENERJI_OLCEK
        self._sentez += _lab.STOCK_REGEN * dt
        while self._sentez >= 1.0 and self.stok < _lab.STOCK_MAX:
            if hucre.energy < bedel:
                break
            hucre.energy -= bedel
            self.stok += 1.0
            self._sentez -= 1.0

    def yuk_cek(self, n):
        """Atis icin stoktan n molekul cek. Yetmezse atis YUKSUZ gider."""
        if self.stok + 1e-9 < n:
            return False
        self.stok -= n
        return True

    # ------------------------------------------------------- MUTASYON
    def belirtec_mutasyonu(self, rng=random):
        import lab as _lab
        secim = [i for i in range(len(_lab.MARKERS)) if i != self.marker]
        self.marker = rng.choice(secim)
        return self.marker

    def varyant_mutasyonu(self, rng=random):
        if len(self.VARYANTLAR) < 2:
            return None
        secim = [c for c in self.VARYANTLAR if c != self.carrier]
        self.carrier = rng.choice(secim)
        return self.carrier

    def yuk_mutasyonu(self, rng=random):
        """Uretici baska bir yuk sentezlemeye baslar; eski stok gider."""
        if not self.URETICI:
            return None
        import lab as _lab
        secim = [i for i in range(1, len(_lab.PAYLOADS))
                 if i != self.payload and _lab.PAYLOADS[i][1] is not None]
        self.payload = rng.choice(secim)
        self.stok = 0.0
        return self.payload

    # --- ayarlardan okunan temel değerler ---
    def _s(self, field):
        return getattr(game_settings, f"{self.KEY}_{field}")

    # Bedeller LAB tablolarindan mi (Stylet/Harpoon/Nematocyst/Toxin/Lysin)
    # yoksa oyunun kendi ayarindan mi (Phagocytosis - lab tasiyicisi degil)?
    LAB_BEDEL = True

    def _olcek(self):
        return float(game_settings.LAB_ENERJI_OLCEK)

    @property
    def reach(self):
        return self._s("RANGE")

    @property
    def arc(self):
        """Etki yayı (yarı-açı, derece). 180 = yönsüz."""
        return self._s("ARC")

    @property
    def cooldown(self):
        return self._s("COOLDOWN")

    @property
    def energy_cost(self):
        """Atis basina enerji (surekli silahlarda saniyede).

        Lab: CARRIER_COST[ci][1]. Tek kullanimlik nematosist her atista
        yeniden kurulur - bedeli budur. Surekli puskurtme saniyede
        (4+3ci) molekul saliyor; labdaki atis 26 molekul, o oranla.
        """
        if not self.LAB_BEDEL:
            return self._s("ENERGY")
        import lab as _lab
        ci = int(self.carrier)
        if not (0 <= ci < len(_lab.CARRIER_COST)):
            return 0.0
        atis = _lab.CARRIER_COST[ci][1] * self._olcek()
        if self.CONTINUOUS:
            emit = max(1, _lab.CARRIER_EMIT[ci]) if ci < len(_lab.CARRIER_EMIT) else 26
            return atis * (4.0 + 3.0 * ci) / emit
        return atis

    @property
    def base_energy_cost(self):
        """Bakim (saniyede): tasiyici makinesini ayakta tutmak.
        Lab: CARRIER_COST[ci][0], gelisimle (guc) buyur."""
        if not self.LAB_BEDEL:
            return self.power * self._s("COST")
        import lab as _lab
        ci = int(self.carrier)
        if not (0 <= ci < len(_lab.CARRIER_COST)):
            return 0.0
        return _lab.CARRIER_COST[ci][0] * self._olcek() * max(0.0, self.power)

    def update(self, dt):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

    @property
    def ready(self):
        return self.cooldown_timer <= 0

    def trigger(self):
        self.cooldown_timer = self.cooldown

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
        n = max(0.0, (self.power - 1.0) / max(1e-6, self._s("GROW")))
        # Menzili 0 olan silah ATILMAZ, DEGDIRILIR; "menzil 0" yazmak
        # bozuk bir deger gibi okunuyordu.
        m = "temas" if self.reach <= 0.0 else "menzil %.0f" % self.reach
        # UCLU: tasiyici varyanti, belirtec, (ureticide) yuk ve stok.
        try:
            import lab as _lab
            ci = int(getattr(self, 'carrier', 0))
            mi = int(getattr(self, 'marker', 0))
            tas = _lab.CARRIERS[ci][0].split('. ', 1)[-1][:14] if 0 <= ci < len(_lab.CARRIERS) else '?'
            bel = _lab.MARKERS[mi][0][:12] if 0 <= mi < len(_lab.MARKERS) else '?'
            out = [("Guc", min(1.0, n / 10.0), "%s  %s" % (tas, m)),
                   ("Belirtec", 0.0 if mi == 0 else 1.0, bel)]
            if self.URETICI:
                pi = int(getattr(self, 'payload', 0))
                yuk = _lab.PAYLOADS[pi][0][:12] if 0 < pi < len(_lab.PAYLOADS) else 'yok'
                out.append(("Yuk / stok", min(1.0, self.stok / max(1.0, _lab.STOCK_MAX)),
                            "%s  %d/%d" % (yuk, int(self.stok), int(_lab.STOCK_MAX))))
            return out
        except Exception:
            return [("Guc", min(1.0, n / 10.0), m)]

    def grow(self):
        """Silahi gelistir: guc carpani artar (hasar = DAMAGE * power).

        Once artis HASARA BOLUNUYORDU:
            power += GROW / DAMAGE
        Stilet icin bu 0.25/25 = 0.01 eder - bir yukseltme hasari binde
        bir artiriyordu. Yani silahlar pratikte HIC gelismiyordu; oysa
        istenen sey "kompleks saldiri silahlariyla donanmis hucreler".
        Fagositoz ise DAMAGE = 0 oldugu icin tam GROW kadar buyuyordu;
        aralarindaki bu ucurumun bir gerekcesi de yoktu.

        Artik dogrudan: bir yukseltme gucu GROW kadar artirir (stilet icin
        %25). Bedeli de birlikte buyur - base_energy_cost power ile
        carpilir, yani guclu silah pahali silahtir.
        """
        self.power += self._s("GROW")

    def in_range(self, attacker, target):
        """Yalnızca MESAFE kontrolü. Yön kontrolü organ seviyesindedir
        (attachment_angle logic'te değil, organda tutulur)."""
        d = attacker.pos.distance_to(target.pos)
        return d <= attacker.radius + target.radius + self.reach


class StyletLogic(WeaponLogic):
    VARSAYILAN_TASIYICI = 4
    VARSAYILAN_YUK = 2
    """Delici stilet (Vampyrella, Pfiesteria peduncle).

    Ucuz, hızlı, yüksek tek hedef hasarı. Temas şart; kalın duvara takılır.
    """
    KEY = "STYLET"; CHANNEL = 'mechanical'; CONTACT = True; REQUIRES_BIND = True


class HarpoonLogic(WeaponLogic):
    VARSAYILAN_TASIYICI = 3
    VARSAYILAN_YUK = 6
    """Tip VI salgı sistemi — moleküler harpun.

    Çok hızlı ateş eder ama atış başına pahalıdır. Kapsül onu tamamen durdurur.
    """
    KEY = "HARPOON"; CHANNEL = 'mechanical'; CONTACT = True


class NematocystLogic(WeaponLogic):
    VARSAYILAN_TASIYICI = 5
    VARSAYILAN_YUK = 6
    """Nematosist / trikosist — patlayıcı mermi.

    Tek MENZİLLİ mekanik silah: kaçan avı vurabilir ve kapsülü aşar.
    Bedeli uzun yeniden dolum ve yüksek enerji.
    """
    KEY = "NEMATOCYST"; CHANNEL = 'mechanical'; CONTACT = False; CREATES_TETHER = True
    # Dort nematosist tipi: yalnizca penetrant (5) yuk tasir; volvent (6)
    # sarar, glutinant (7) yapistirir, izoriza (8) kendini ceker.
    VARYANTLAR = (5, 6, 7, 8)


class ToxinLogic(WeaponLogic):
    VARSAYILAN_TASIYICI = 2
    VARSAYILAN_YUK = 1
    """Bakteriosin — kimyasal savaş.

    ALAN etkilidir, temas gerekmez, kaçana da işler; ama yavaştır ve
    nişan alınamaz. Üretici kendi toksinine BAĞIŞIKTIR (bağışıklık
    proteini bakteriosin geniyle aynı operonda kodlanır).

    BAĞIŞIKLIK TÜRE ÖZGÜDÜR, "toksin taşımak" değil.

    Önceden bağışıklık `has_weapon(Toxin)` idi: toksin taşıyan herkes
    HER toksine bağışıktı. Bunun sonucu ölçüldü - toksinli hücreler
    birbirine dokunulmaz bir kartel kuruyor ve toksinsiz olan herkesi
    kırıyordu (32/32 sağ kalan toksinli, diğer bütün takımlar silinmiş).
    Böyle bir dünyada tek bir toksin soyu her şeyi süpürür; ne çeşitlilik
    kalır ne de savunma tiplerinin ortaya çıkacağı bir ortam.

    Gerçekte kolisin üreticisi YALNIZCA kendi kolisinine bağışıktır;
    başka bir varyantı üretenin toksini onu da öldürür. Bu yüzden her
    toksin geninin bir ALLELİ var: aynı alleli taşıyan bağışık, taşımayan
    değil. Allel bölünmede nadiren değişir - yeni bir bakteriosin varyantı
    doğduğunda üreticisi akrabalarının bağışıklığını yitirir.
    """
    KEY = "TOXIN"; CHANNEL = 'chemical'; CONTACT = False; CONTINUOUS = True
    URETICI = True
    VARYANTLAR = (0, 1, 2)      # difuzyon / yonlu bosaltma / fiskirtma

    def __init__(self, power=1.0):
        super().__init__(power)
        self.allel = random.randrange(int(game_settings.TOXIN_ALLELES))

    def allel_mutasyonu(self, rng=random):
        """Yeni bir bakteriosin varyanti: bagisiklik iliskileri degisir."""
        self.allel = rng.randrange(int(game_settings.TOXIN_ALLELES))
        return self.allel


class LysinLogic(WeaponLogic):
    VARSAYILAN_TASIYICI = 2
    VARSAYILAN_YUK = 4
    """Ekstraselüler litik enzim — ZIRHIN CEVABI.

    Kimyasal olduğu için hücre DUVARINI yok sayar; zırhlı bir popülasyonda
    işe yarayan tek silah odur. Ama bu rolü ancak hedefe ULAŞABİLİRSE
    oynayabilir.

    Önce 4 px menzilli, tek atışlık ve tutunmasız bir silahtı: hedefe
    değecek kadar yaklaşıp 5-10 saniye öyle kalması gerekiyordu, oysa
    tutunmadığı için av basitçe yüzüp gidiyordu. Ölçüldü - lizin taşıyan
    takım 3/32 sağ kalıyor, silahsız takım 10/32. Yani zırhın cevabı
    hiçbir zaman ortaya çıkamıyordu ve duvar mutlak bir üstünlüktü.

    Gerçekteki karşılığı da tutunmalı bir silah değil: Lysobacter ve
    miksobakteriler litik enzimi ORTAMA salar, çevrelerindeki hücreleri
    yavaşça eritir. Bu yüzden artık sürekli ve alan etkili - toksinle aynı
    mekanik, üç farkla:
      - duvarı yok sayar (toksin duvarın gözeneklerinde durur),
      - menzili kısadır (25'e karşı 60): yaklaşmak zorunda,
      - BAĞIŞIKLIĞI YOKTUR. Salınan enzim kendi soyunu da eritir; miks
        bakterilerin "dost ateşi" sorunu birebir budur.
    """
    KEY = "LYSIN"; CHANNEL = 'chemical'; CONTACT = True; CONTINUOUS = True
    URETICI = True
    VARYANTLAR = (0, 1, 2)


class PhagocytosisLogic(WeaponLogic):
    VARSAYILAN_TASIYICI = 2
    VARSAYILAN_YUK = 3
    """Fagositoz — yutma (amip).

    Hasar vermez: hedefi bütün alır. Yalnızca kendinden yeterince küçük
    hedefe işler ve yutarken avcı bir süre hareketsiz kalır.
    """
    KEY = "PHAGO"; CHANNEL = 'engulf'; CONTACT = True; REQUIRES_BIND = True
    LAB_BEDEL = False           # lab tasiyicisi degil: kendi ayarlari

    def can_engulf(self, attacker, target):
        """Gelişim (power) görece daha büyük avı yutabilmeyi sağlar.

        Boy tek kosul degil: yutmak, zarin avin etrafinda ESNEYIP
        kapanmasidir. Laboratuvarda bunun kurali zaten vardi - sert bir
        yuzey (kalin duvar ya da S-layer) sitostomu devre disi birakiyor.
        Ayni kural avin tarafinda da isler: kristal kabuklu bir hucre
        yutulmaz. Esik lab.py'den okunur, iki taraf ayrisamasin diye.
        """
        ratio = game_settings.PHAGO_SIZE_RATIO * self.power
        if target.radius > attacker.radius * min(0.95, ratio):
            return False
        return not self._sert_yuzey(target)

    @staticmethod
    def _sert_yuzey(target):
        """Hedefin yuzeyi zarin saramayacagi kadar sert mi?"""
        zar = getattr(getattr(target, 'membrane', None), 'logic', None)
        if zar is None:
            return False
        try:
            import lab
        except Exception:
            return False
        # Oyun ile laboratuvar ayni soruyu farkli cevapliyordu: burasi
        # yalnizca YATIRIMA bakiyordu (yatirimsiz duvar "yumusak"),
        # LabCell.sert_yuzey ise TABAN kalinligi da sayiyordu ("sert").
        # Artik ikisi de ayni sey: katman VAR MI ve toplam kalinligi
        # esigi asiyor mu.
        for ad, kal, _renk, var in lab.katman_kalinliklari(zar):
            if var and ad in lab.SERT_KATMANLAR and kal > lab.SERT_ESIK:
                return True
        return False

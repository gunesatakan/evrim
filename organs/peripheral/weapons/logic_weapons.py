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

    def __init__(self, power=1.0):
        self.power = power        # gelişim çarpanı (gen ile artar)
        self.cooldown_timer = 0.0
        # Hangi yapiyla, neyi, nereye birakiyor
        self.carrier = self.VARSAYILAN_TASIYICI
        self.payload = self.VARSAYILAN_YUK
        self.marker = 0           # 0 = belirtec yok (balistik)

    # --- ayarlardan okunan temel değerler ---
    def _s(self, field):
        return getattr(game_settings, f"{self.KEY}_{field}")

    @property
    def damage(self):
        return self._s("DAMAGE") * self.power

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
        """Kullanım başına (sürekli silahlarda saniyede) enerji."""
        return self._s("ENERGY")

    @property
    def base_energy_cost(self):
        """Sürekli bakım — silahlar için düşüktür; asıl gider kullanımda."""
        return self.power * self._s("COST")

    def update(self, dt):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt

    @property
    def ready(self):
        return self.cooldown_timer <= 0

    def trigger(self):
        self.cooldown_timer = self.cooldown

    def grow(self):
        self.power += self._s("GROW") / max(1e-6, self._s("DAMAGE") or 1.0) \
            if self._s("DAMAGE") else self._s("GROW")

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


class ToxinLogic(WeaponLogic):
    VARSAYILAN_TASIYICI = 2
    VARSAYILAN_YUK = 1
    """Bakteriosin — kimyasal savaş.

    ALAN etkilidir, temas gerekmez, kaçana da işler; ama yavaştır ve
    nişan alınamaz. Doğadaki gibi üretici kendi toksinine BAĞIŞIKTIR ve
    aynı geni taşıyan herkes de bağışıktır (bağışıklık proteini).
    """
    KEY = "TOXIN"; CHANNEL = 'chemical'; CONTACT = False; CONTINUOUS = True


class LysinLogic(WeaponLogic):
    VARSAYILAN_TASIYICI = 2
    VARSAYILAN_YUK = 4
    """Ekstraselüler litik enzim.

    Kimyasal olduğu için hücre DUVARINI yok sayar — zırhlı hedefe karşı en
    iyi silah. Karşılığında yavaştır.
    """
    KEY = "LYSIN"; CHANNEL = 'chemical'; CONTACT = True


class PhagocytosisLogic(WeaponLogic):
    VARSAYILAN_TASIYICI = 2
    VARSAYILAN_YUK = 3
    """Fagositoz — yutma (amip).

    Hasar vermez: hedefi bütün alır. Yalnızca kendinden yeterince küçük
    hedefe işler ve yutarken avcı bir süre hareketsiz kalır.
    """
    KEY = "PHAGO"; CHANNEL = 'engulf'; CONTACT = True; REQUIRES_BIND = True

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

import math
from systems.protein_systems.enzymes.digestion_enzymes.digestion_enzymes import DigestionEnzymes
import game_settings

class CytoplasmLogic:
    # Baslangic boyutu 2.0: size 1.0'da govde alani 314 px^2 ve bu,
    # birkac organ takilinca `can_fit_food` icin yetmiyor - hucre
    # hicbir besin alamiyordu (bkz. Doluluk gostergesi).
    def __init__(self, size=2.0):
        self.size = size
        self.enzyme = DigestionEnzymes()
        self.food_queue = []
        self.FOOD_AREA = game_settings.FOOD_AREA 

    @property
    def radius(self):
        # Kuresel olcek burada UYGULANMAZ: organs/registry.olcekle zaten
        # `size` alanini carpiyor ve add_organ tek gecis noktasi. Ikisini
        # birden yapinca olcek KARESIYLE giriyordu - olcek 30'da yaricap
        # 300 yerine 9000 cikti.
        return self.size * 10

    @property
    def total_area(self):
        return math.pi * (self.radius ** 2)

    @property
    def current_food_load(self):
        count = len(self.food_queue)
        if self.enzyme.current_food:
            count += 1
        return count * self.FOOD_AREA

    @property
    def base_energy_cost(self):
        """Govde bakimi (alanla, yani boyutun karesiyle) + enzim uretimi.

        Enzim maliyeti sindirim HIZIYLA orantilidir: sure kisaldikca daha
        cok enzim tutmak gerekir, yani 1/sure.
        """
        body = (self.size ** 2) * game_settings.COST_CYTOPLASM
        enzyme = game_settings.COST_DIGESTION / max(0.001, self.enzyme.base_digestion_time)
        return body + enzyme

    def can_fit_food(self, total_organ_area):
        return (self.current_food_load + total_organ_area + self.FOOD_AREA) <= self.total_area

    def add_food(self, food, total_organ_area):
        if self.can_fit_food(total_organ_area):
            self.food_queue.append(food)
            return True
        return False

    def update(self, dt):
        return self.enzyme.process(dt, self.food_queue)

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
        n = max(0.0, (self.size - 2.0) / max(1e-6, g.GROW_BODY))
        sd = self.enzyme.base_digestion_time
        # Sindirim SURESI dusuyor: gelisim ters yonde okunur.
        so = (g.DIGESTION_TIME - sd) / max(1e-6, g.DIGESTION_TIME - 1.0)
        return [("Boyut", min(1.0, n / 20.0), "%.2f" % self.size),
                ("Sindirim", max(0.0, min(1.0, so)), "%.1f s" % sd)]

    def grow_enzyme(self):
        self.enzyme.grow()

    def update_stats(self, delta_size=0):
        self.size += delta_size

    def grow(self):
        self.size += game_settings.GROW_BODY
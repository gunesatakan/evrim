import game_settings

class VacuoleLogic:
    def __init__(self, size=1.0):
        self.size = size 
        self.area = game_settings.VACUOLE_AREA * self.size

    @property
    def capacity(self):
        return self.area * game_settings.VACUOLE_ENERGY_MULTI

    @property
    def base_energy_cost(self):
        """Depoyu dolu tutmanin (osmotik dengenin) bedeli."""
        return self.area * game_settings.COST_VACUOLE

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
        n = max(0.0, (self.size - 1.0)
                / max(1e-6, game_settings.GROW_MAX_ENERGY))
        return [("Hacim", min(1.0, n / 10.0), "alan %.0f" % self.area)]

    def grow(self):
        self.size += game_settings.GROW_MAX_ENERGY
        self.area = game_settings.VACUOLE_AREA * self.size
import game_settings

class RibosomeLogic:
    def __init__(self, production_speed=None):
        self.base_production_time = production_speed if production_speed else game_settings.RIBOSOME_TIME
        # GELISIM TABANI ORGANIN KENDISINDE DURUR.
        #
        # Once gelisim orani ayardan geri hesaplaniyordu: "simdiki sure,
        # RIBOSOME_TIME'a gore ne kadar dustu". Ama ayardaki deger
        # (1.0 sn) organin gercek baslangicindan (10.0 sn) bagimsiz
        # degisebiliyor - o an oran sifira sapitiyordu. Organ nereden
        # basladigini kendi bilirse ayar ne olursa olsun dogru olcer.
        self._taban_sure = self.base_production_time
        self.area = game_settings.RIBOSOME_AREA
        self.current_task = None
        self.production_timer = 0.0
        self.queue = []

    @property
    def base_energy_cost(self):
        """Uretim hizi = ribozom sayisi; maliyet 1/sure ile orantili."""
        return game_settings.COST_RIBOSOME / max(0.001, self.base_production_time)

    def add_task(self, resource):
        self.queue.append(resource)

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
        tab = getattr(self, '_taban_sure', self.base_production_time)
        # Uretim SURESI dusuyor; 1.0 saniyelik tabana ne kadar yaklastigi.
        oran = (tab - self.base_production_time) / max(1e-6, tab - 1.0)
        return [("Uretim hizi", max(0.0, min(1.0, oran)),
                 "%.1f s/protein" % self.base_production_time)]

    def grow(self):
        self.base_production_time = max(1.0, self.base_production_time - game_settings.GROW_RIBOSOME)

    def update(self, dt):
        if self.current_task is None and self.queue:
            self.current_task = self.queue.pop(0)
            self.production_timer = 0.0
        if self.current_task:
            self.production_timer += dt
            if self.production_timer >= self.base_production_time:
                finished_product = self.current_task
                self.current_task = None
                self.production_timer = 0.0
                return finished_product
        return None

    @property
    def is_busy(self):
        return self.current_task is not None
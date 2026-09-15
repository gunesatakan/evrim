import game_settings
import math
import random

class PhotoreceptorLogic:
    def __init__(self, range=None, angle=None):
        self.range = range if range is not None else game_settings.VISION_RANGE_BASE
        self.angle = angle if angle is not None else game_settings.VISION_ANGLE_BASE
        self._update_visual_levels()

    def _update_visual_levels(self):
        """Renk ve neon seviyelerini hesapla (scale'den etkilenmez)"""
        # Renk seviyesi: range'den (0.0=Kırmızı, 1.0=Mor)
        self.color_level = min(max(0, (self.range - 25) / 175.0), 1.0)
        # Neon seviyesi: angle'dan (0.0=Mat, 1.0=Neon)
        angle_deg = math.degrees(self.angle)
        self.neon_level = min(1.0, max(0.0, (angle_deg - 10) / 90.0))

    @property
    def base_energy_cost(self):
        """Taranan gorme alaniyla orantili."""
        return self.range * self.angle * game_settings.COST_PHOTORECEPTOR

    def update_stats(self, delta_range=0, delta_angle=0):
        self.range += delta_range
        self.angle += delta_angle
        self._update_visual_levels()

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
        nr = max(0.0, (self.range - g.VISION_RANGE_BASE)
                 / max(1e-6, g.GROW_VISION_RANGE))
        na = max(0.0, (self.angle - g.VISION_ANGLE_BASE)
                 / max(1e-6, g.GROW_VISION_ANGLE))
        return [("Menzil", min(1.0, nr / 10.0), "%.0f px" % self.range),
                ("Gorus acisi", min(1.0, na / 10.0),
                 "%.0f der" % math.degrees(self.angle))]

    def grow(self, type='range'):
        if type == 'range':
            self.range += game_settings.GROW_VISION_RANGE
        elif type == 'angle':
            self.angle += game_settings.GROW_VISION_ANGLE
        self._update_visual_levels()

    # ---------------- ISIK OLCUMU ----------------
    #
    # GOZ ISIGIN YONUNU BILMEZ, YALNIZCA UZERINE DUSENI SAYAR.
    #
    # Suda isik her yonden gelir ama esit degil: aydinlik bolgenin
    # tarafindan daha cok foton gelir (ISIK_YONLULUK). Goz yalnizca kendi
    # gorus konisinden gelen fotonlari toplar; arkasini hucrenin govdesi
    # golgeler. Yani isiga bakan goz daha parlak, arkasi donuk goz daha
    # donuk okur. Yonu bu farktan hucre kendisi cikarmak zorunda.
    #
    # Gorus acisi bir takas: genis koni daha cok foton toplar (az gurultu)
    # ama gelen isigi daha genis bir yondan ortaladigi icin yon farkini
    # bulandirir; dar koni yonu keskin gorur ama los isikta gurultuye bogulur.

    def isik_yakalama(self):
        """Toplanan foton, taban gorus acisina gore kac kat (koni genisligi)."""
        return max(1e-3, self.angle / max(1e-6, game_settings.VISION_ANGLE_BASE))

    def yon_keskinligi(self):
        """Koninin icinden gelen isigin yonsel payini ne kadar koruyabildigi.

        Koni boyunca ortalanan cos(aci): sin(a)/a, a = yarim gorus acisi.
        Dar gozde 1'e yakin, 360 derece goren gozde 0 (yon bilgisi yok).
        """
        yarim = min(math.pi, max(1e-6, self.angle * 0.5))
        return math.sin(yarim) / yarim

    def olc(self, siddet, cos_teta, dt=None):
        """Bu gozun uzerine dusen isigin olcumu.

        siddet   : gozun bulundugu noktadaki isik siddeti
        cos_teta : gozun ekseni ile isigin geldigi yon arasindaki acinin cos'u
        dt       : sayim suresi; verilirse foton sayim gurultusu eklenir
        """
        if siddet <= 0.0:
            return 0.0
        g = game_settings
        yonluluk = min(1.0, max(0.0, float(g.ISIK_YONLULUK)))
        beklenen = siddet * (1.0 + yonluluk * cos_teta * self.yon_keskinligi())
        if beklenen <= 0.0:
            return 0.0
        # FOTON SAYIM GURULTUSU: sayilan foton N ise goreli hata 1/sqrt(N).
        if dt and g.ISIK_GURULTU > 0.0:
            n = beklenen * self.isik_yakalama() * dt / g.ISIK_GURULTU
            if n < 400.0:
                n = max(0.05, n)
                beklenen *= random.gammavariate(n, 1.0 / n)
            else:
                beklenen *= max(0.0, random.gauss(1.0, 1.0 / math.sqrt(n)))
        return beklenen

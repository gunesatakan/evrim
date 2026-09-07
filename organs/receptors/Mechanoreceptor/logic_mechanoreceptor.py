import math
import game_settings
from .mechano_danger import MechanoDanger

class MechanoreceptorLogic:
    def __init__(self, size=1.0):
        self.size = size 
        self.danger_sense = MechanoDanger()
        # ESIK: algilanabilen en kucuk basinc bozulmasi (birim: gurultu/px^2).
        # Taban deger, baslangic kulaginin referans gurultuyu tam
        # SES_MENZIL_OLCEGI mesafesinden duymasini saglayacak sekilde
        # secilir - eski davranisla ayni kalibrasyon.
        self.esik = (game_settings.GURULTU_REF
                     / (game_settings.SES_MENZIL_OLCEGI ** 2))
        # KAPSAMA: yon cozunurlugu (0 = yonsuz, 1 = tam). Dusuk baslar ki
        # gelismeye yer olsun.
        self.kapsama = game_settings.MECHANO_KAPSAMA_TABAN

    # ------------------------------------------------------------------
    # MEKANORESEPSIYON: her sey, organa carpan bir BASINC DALGASIDIR.
    #
    # Kendi kendine yuzen bir cisim kuvvet-serbesttir; uzak alani bir
    # stresslet'tir ve mesafenin KARESIYLE soner:
    #
    #     sinyal(r) = (yaricap x hiz) / r^2
    #
    # Bu yuzden MENZIL bir gen OLAMAZ - menzil zaten esigin sonucudur:
    #
    #     r_max = sqrt(gurultu / esik)
    #
    # "Alan yaricapim 3, ucta 4 birim duyarim" demek ile "esigim 4 birim"
    # demek ayni cumledir. Ikisini ayri gen yapmak birini gereksiz kilar.
    #
    # Gercekten bagimsiz olan iki eksen sunlar:
    #
    #   ESIK      - kanalin acilmasi icin gereken en kucuk deformasyon.
    #               Dusurmek daha sessizini ve daha uzaktakini duymaktir.
    #   KAPSAMA   - kac noktadan dinlendigi. MENZILI ARTIRMAZ, YON verir.
    #               Kopepodun onlarca setasi tam bunun icindir: tek seta
    #               "bir sey oldu" der, cok seta "surdan geliyor" der.
    #
    # Kapsamasi dusuk bir hucre "yakinda iri bir sey hizli hareket ediyor"
    # bilir ama nereye kacacagini bilmez.
    # ------------------------------------------------------------------

    @property
    def sensitivity(self):
        """Referans gurultudeki bir hedefi kac px oteden duyarim.

        Menzil turetilmis bir buyukluktur: r = sqrt(gurultu_ref / esik).
        `sound_radius` disariya bunu bildirir.
        """
        return math.sqrt(game_settings.GURULTU_REF / max(1e-9, self.esik))

    def duyulan_sinyal(self, gurultu, mesafe):
        """Bu mesafede algilanan basinc sinyali (esik biriminde).

        1'in altinda kalirsa hic duyulmaz; 1 = tam esikte; buyuk degerler
        gurultunun esige gore kac kati oldugunu soyler.
        """
        if gurultu <= 0.0:
            return 0.0
        r = max(1.0, float(mesafe))
        return (gurultu / (r * r)) / max(1e-9, self.esik)

    def yon_hatasi(self):
        """Sesin geldigi yonu ne kadar sasirir (derece, gauss sigma).

        Kapsama 1'e yakinsa yon neredeyse kesin; 0'a yakinsa hucre
        yalnizca "bir sey var" bilir ve rastgele bir yone tepki verir.
        """
        return (1.0 - min(1.0, max(0.0, self.kapsama))) * 180.0

    def grow(self):
        """ESIK gelisimi: daha kucuk titresimleri duyar (menzil buyur)."""
        self.esik = max(game_settings.MECHANO_ESIK_MIN,
                        self.esik * (1.0 - game_settings.GROW_MECHANO_ESIK))

    def grow_kapsama(self):
        """KAPSAMA gelisimi: sesin YONUNU daha iyi cikarir."""
        self.kapsama = min(1.0, self.kapsama
                           + game_settings.GROW_MECHANO_KAPSAMA)

    @property
    def base_energy_cost(self):
        """Iki eksen de bedel goturur: dusuk esik daha cok kanal ve iletim
        makinesi, yuksek kapsama daha cok algilayici nokta demektir."""
        return (self.sensitivity * game_settings.COST_MECHANORECEPTOR
                * (1.0 + self.kapsama))

    def update_stats(self, delta_size=0):
        self.size += delta_size

    
    def is_hearing(self, self_pos, target_pos):
        """Bu kulak hedefi duyuyor mu?"""
        # Organın konumu self_pos değil, dışarıdaki attachment point olmalı.
        # Ancak Logic sınıfı konumu bilmez (konum View/Lego sınıfında).
        # Bu yüzden mesafeyi Organism (Lego) sınıfında hesaplayıp buraya 'dist' olarak atmak daha doğru olur.
        # Şimdilik basitçe menzil kontrolü yapıyoruz.
        return True # Asıl kontrol Organism içinde yapılacak

    @staticmethod
    def gurultu(hedef):
        """Hedefin urettigi hidrodinamik bozulma.

        Bozulma hem CISMIN BUYUKLUGUYLE hem HIZIYLA artar: iri ve hizli
        olan cok su iter. Duran ya da tutulmus bir hucre sessizdir.
        """
        hiz = float(getattr(hedef, 'speed', 0.0) or 0.0)
        if getattr(hedef, 'stun_timer', 0.0) > 0 or getattr(hedef, 'bound_by', None):
            hiz = 0.0
        return max(0.0, float(getattr(hedef, 'radius', 0.0)) * hiz)

    def duyma_menzili(self, gurultu):
        """Bu gurultudeki bir hedefi kac px oteden duyarim?

        Bozulmanin siddeti uzaklikla duser; menzil de gurultunun
        KAREKOKUYLE artar. Referans gurultudeki (orta boy, orta hizli)
        bir hedef tam hassasiyet mesafesinden duyulur.
        """
        if gurultu is None:                # bilinmiyorsa referans gurultu
            gurultu = game_settings.GURULTU_REF
        if gurultu <= 0.0:
            return 0.0
        return math.sqrt(gurultu / max(1e-9, self.esik))

    def check_urgency(self, nearby_threats, current_pos):
        return self.danger_sense.analyze_urgency(nearby_threats, current_pos)

import math
import random

import game_settings
from .chemo_danger import ChemoDanger

class ChemoreceptorLogic:
    def __init__(self, length=5.0):
        self.length = length
        self.danger_sense = ChemoDanger()
        # KAZANC: alicidan gelen kucuk bir fark, davranisa ne kadar buyuk
        # bir degisim olarak gecer. ESIKTEN TAMAMEN AYRI bir moleküler
        # ozellik - esik "ne kadar azini fark ederim", kazanc "fark
        # ettigimi ne kadar buyuturum" demek. E. coli'de bu, alicilarin
        # isbirlikci kumeler halinde dizilmesinden gelir ve sinyali ~35
        # kat yukseltir.
        #
        # Olculdu: ayni koku alaninda tirmanilabilir bolge kazanc 5'te
        # %1.9, kazanc 15'te %62, kazanc 40'ta %86. Yani hucrenin kokuyu
        # KULLANABILMESINI belirleyen asil sey buydu ve herkeste ayni
        # sabitti - evrimlesemiyordu.
        self.kazanc = game_settings.CHEMO_GAIN_TABAN
        # ORNEKLEME PENCERESI: algiyi ne kadar sure ortalar.
        # Uzun pencere gurultuyu bastirir (Berg-Purcell: hata ~
        # 1/sqrt(derisim x sure)) ama tepkiyi geciktirir. "Hizli ve
        # gurultulu" ile "yavas ve emin" arasindaki secim.
        self.pencere = game_settings.CHEMO_SAMPLE_INTERVAL

    @property
    def smell_threshold(self):
        """Tehdit izi algılama eşiği (yüksek = daha az hassas)"""
        return 500.0 / self.length if self.length > 0 else 9999.0

    @property
    def scent_sensitivity(self):
        """
        Besin kokusu algı eşiği. Manifesto: I_threshold ∝ 1 / organ uzunluğu.

        Ters orantı hiçbir zaman sıfıra ulaşmaz: burun uzadıkça eşik düşmeye
        devam eder, ama her adımın kazancı bir öncekinden küçüktür (azalan
        getiri). Bu yüzden yapay bir tavana gerek yoktur.

        Eskiden üstel azalma (0.2 * e^(-0.3*(L-1))) ve 0.01 alt sınırı vardı;
        eşik uzunluk 11'de tabana çarpıp tamamen duruyordu, sonraki her
        kemoreseptör yükseltmesi boşa gidiyordu.

        base=0.3 ile başlangıç uzunluğunda (5) eşik eski değerle aynı kalır:
        length=1  → 0.300      length=11 → 0.027
        length=5  → 0.060      length=20 → 0.015
        length=8  → 0.038      length=50 → 0.006
        """
        base = game_settings.SCENT_SENSITIVITY_BASE
        if self.length <= 0:
            return base
        return base / self.length

    @property
    def base_energy_cost(self):
        """Uzunluk boyunca dizili reseptor proteinlerinin bakimi.

        Kazanc da bedel goturur: yuksek kazanc daha buyuk ve daha siki
        alici kumeleri demektir. Taban kazancta eski degerle ayni kalir.
        """
        return (self.length * game_settings.COST_CHEMORECEPTOR
                * (self.kazanc / max(1e-6, game_settings.CHEMO_GAIN_TABAN)))

    def grow_kazanc(self):
        """Alici kumelerini buyut: kucuk farklar daha guclu sinyal olur."""
        self.kazanc = min(game_settings.CHEMO_GAIN_MAX,
                          self.kazanc + game_settings.GROW_CHEMO_GAIN)

    def grow_pencere(self):
        """Uzun ortala: gurultu duser ama tepki gecikir."""
        self.pencere = min(game_settings.CHEMO_PENCERE_MAX,
                           self.pencere + game_settings.GROW_CHEMO_PENCERE)

    def grow(self):
        self.length += game_settings.GROW_SMELL

    def can_detect(self, intensity):
        """Tehdit izi yoğunluğunu algılayabilir mi?"""
        return intensity >= self.smell_threshold

    def perceive(self, raw_intensity, dt=None):
        """Weber-Fechner: perception = log(1 + intensity / threshold)

        BERG-PURCELL GURULTUSU. Alicilara molekul baglanmasi stokastiktir:
        hucre derisimi sayarak olcer ve sayim hatasi, sayilan molekul
        sayisinin karekokuyle azalir. Bagil hata

            ~ 1 / sqrt(derisim x sure)

        Yani DUSUK DERISIMDE OLCUM GURULTULUDUR. Bu, kazanc geninin
        bedelidir: yuksek kazanc gercek gradyani da gurultuyu de ayni
        oranda buyutur, hucre olmayan bir egimi takip etmeye baslar.
        Gurultu olmasaydi kazanci sonuna kadar buyutmek bedava bir
        yukseltme olurdu.

        Gurultu KARE BASINA eklenir; pencere boyunca biriktirme onu
        kendiliginden ortalar - yani uzun pencere gercekten gurultu
        bastirir. Zaman ortalamasinin fiziksel karsiligi tam olarak budur.
        """
        threshold = self.scent_sensitivity
        if raw_intensity < threshold * 0.1:
            return 0.0
        if dt and game_settings.CHEMO_GURULTU > 0.0:
            # SAYIM MODELI. Hucre derisimi, belli bir surede kac molekulun
            # aliciya carptigini SAYARAK olcer. Sayi Poisson dagilir; bagil
            # hata 1/sqrt(N) ile duser (Berg-Purcell).
            #
            # Once carpansal bir Gauss kullaniyordum ve dusuk derisimde
            # olcumu SIFIRA dusurebiliyordu - sifir da "koku yok" dalina
            # dusup butun ornekleme penceresini siliyordu. Tek bir
            # gurultulu kare biriken butun bilgiyi cope atiyordu.
            #
            # Gama dagilimi (ortalamasi 1, varyansi 1/N) hem dogru sekle
            # sahip hem de HER ZAMAN POZITIF: olcum bulaniklasir ama
            # "hicbir sey yok" demez.
            n = raw_intensity * dt / game_settings.CHEMO_GURULTU
            if n < 400.0:            # buyuk N'de gurultu zaten ihmal
                n = max(0.05, n)
                raw_intensity *= random.gammavariate(n, 1.0 / n)
        return math.log(1.0 + raw_intensity / threshold)

    def can_smell_food(self, scent_intensity):
        """Besin kokusunu algılayabilir mi?"""
        return self.perceive(scent_intensity) > 0.0

    def is_danger(self, trail_point):
        return self.danger_sense.assess_threat(trail_point)
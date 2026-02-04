from .chemo_danger import ChemoDanger

class ChemoreceptorLogic:
    def __init__(self, length=5.0):
        self.length = length
        self.danger_sense = ChemoDanger()

    @property
    def smell_threshold(self):
        """Tehdit izi algılama eşiği (yüksek = daha az hassas)"""
        return 500.0 / self.length if self.length > 0 else 9999.0

    @property
    def scent_sensitivity(self):
        """
        Besin kokusu hassasiyeti (0.0 - 1.0 arası minimum algılanabilir yoğunluk).
        Uzun kemoreseptör = daha hassas = daha düşük eşik.

        length=1 → sensitivity=0.20 (sadece güçlü kokuları algılar)
        length=5 → sensitivity=0.04 (zayıf kokuları da algılar)
        length=10 → sensitivity=0.02 (çok hassas)
        """
        # Uzunluk arttıkça hassasiyet artar (eşik düşer)
        # Üstel azalma: sensitivity = 0.2 * e^(-0.3 * (length-1))
        import math
        sensitivity = 0.2 * math.exp(-0.3 * (self.length - 1))
        return max(0.01, min(0.3, sensitivity))

    def grow(self):
        self.length += 1.0

    def can_detect(self, intensity):
        """Tehdit izi yoğunluğunu algılayabilir mi?"""
        return intensity >= self.smell_threshold

    def can_smell_food(self, scent_intensity):
        """Besin kokusunu algılayabilir mi?"""
        return scent_intensity >= self.scent_sensitivity

    def is_danger(self, trail_point):
        return self.danger_sense.assess_threat(trail_point)
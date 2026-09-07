import math

import game_settings
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
        """Uzunluk boyunca dizili reseptor proteinlerinin bakimi."""
        return self.length * game_settings.COST_CHEMORECEPTOR

    def grow(self):
        self.length += game_settings.GROW_SMELL

    def can_detect(self, intensity):
        """Tehdit izi yoğunluğunu algılayabilir mi?"""
        return intensity >= self.smell_threshold

    def perceive(self, raw_intensity):
        """Weber-Fechner: perception = log(1 + intensity / threshold)"""
        threshold = self.scent_sensitivity
        if raw_intensity < threshold * 0.1:
            return 0.0
        return math.log(1.0 + raw_intensity / threshold)

    def can_smell_food(self, scent_intensity):
        """Besin kokusunu algılayabilir mi?"""
        return self.perceive(scent_intensity) > 0.0

    def is_danger(self, trail_point):
        return self.danger_sense.assess_threat(trail_point)
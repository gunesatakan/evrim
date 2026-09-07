"""Saldiri organlarinin cepheleri (BaseOrgan uzerine).

Her silah ayni arayuze sahiptir; farklari logic sinifinda tanimlidir.
Launcher'dan oyun oncesi eklenebilir ve avlanma odulu cekilisinde de
havuzda bulunurlar (karar 1).
"""
import math

import pygame
from organs.base_organ import BaseOrgan
from .logic_weapons import (StyletLogic, HarpoonLogic, NematocystLogic,
                            ToxinLogic, LysinLogic, PhagocytosisLogic)
from .view_weapons import draw_weapon


class BaseWeapon(BaseOrgan):
    LOGIC = None
    DISPLAY_LENGTH = 10.0

    def __init__(self, attachment_angle=0, power=1.0):
        super().__init__(attachment_angle, offset_distance=1.0)
        self.logic = self.LOGIC(power)
        self.last_target_pos = None

    def aim_angle(self, parent):
        """Organın dünya üzerindeki bakış yönü (radyan)."""
        return (math.atan2(parent.direction.y, parent.direction.x)
                + self.attachment_angle)

    def can_hit(self, parent, target):
        """Menzil VE yön kontrolü.

        Organ konumu artık isabeti belirliyor: öndeki bir stilet arkadaki
        hedefi delemez. Eskiden yalnızca mesafeye bakılıyordu ve silahın
        nereye takıldığı savaşta hiçbir anlam taşımıyordu - oysa projenin
        geri kalanında (itme, tork, koku örnekleme, görüş konisi) organ
        konumu her zaman belirleyici.
        """
        lg = self.logic
        if not lg.in_range(parent, target):
            return False
        if lg.arc >= 180.0:
            return True                      # yönsüz (toksin)
        to_t = target.pos - parent.pos
        d = to_t.length()
        if d <= 1e-6:
            return True
        diff = abs(((math.atan2(to_t.y, to_t.x) - self.aim_angle(parent)
                     + math.pi) % (2 * math.pi)) - math.pi)
        # Hedefin açısal yarı genişliği sayılır: büyük hedefi vurmak kolaydır
        # (can_see de aynı yaklaşımı kullanıyor)
        half = math.atan2(target.radius, max(1.0, d))
        return diff <= math.radians(lg.arc) + half

    def update(self, dt, parent=None):
        self.logic.update(dt)
        self.last_target_pos = None

    def grow(self):
        self.logic.grow()

    RETRACTED_RATIO = 0.25    # boştayken görünen uzunluk oranı

    def is_deployed(self, parent):
        """Silah şu an çıkarılmış mı?

        Doğadaki delici yapıların çoğu (Pfiesteria pedunkülü, Vampyrella)
        sürekli dışarıda durmaz; besleneceği anda uzatılır. Bu yüzden
        tutunma gerektiren silahlar boştayken kısa bir çıkıntı olarak,
        yalnızca hedefe kenetlendiğinde tam boyda çizilir.
        Sürekli dışarıda olan tipler (suctoria dokunaçları) için bu ayrım
        yoktur; onlar zaten hep açık kabul edilir.
        """
        if not self.logic.REQUIRES_BIND:
            return True
        return getattr(parent, 'bound_target', None) is not None

    def draw(self, screen, parent):
        pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        delta = pos - parent.pos
        outward = delta.normalize() if delta.length() > 0 else parent.direction
        # DISPLAY_LENGTH bir SABIT: hucre kucultulup buyutulurken silahlar
        # ayni boyda kaliyordu (dunya gorunumunde hucreden buyuk, kesitte
        # kayip). Cizim olcegi konaktan okunur.
        k = float(getattr(parent, 'ciz_olcegi', 1.0))
        length = self.DISPLAY_LENGTH * self.logic.power * k
        if not self.is_deployed(parent):
            length *= self.RETRACTED_RATIO
        draw_weapon(screen, self.__class__.__name__, pos, outward, length,
                    self.logic.ready, self.last_target_pos, olcek=k)


class Stylet(BaseWeapon):
    LOGIC = StyletLogic
    DISPLAY_LENGTH = 12.0


class Harpoon(BaseWeapon):
    LOGIC = HarpoonLogic
    DISPLAY_LENGTH = 9.0


class Nematocyst(BaseWeapon):
    LOGIC = NematocystLogic
    DISPLAY_LENGTH = 8.0


class Toxin(BaseWeapon):
    LOGIC = ToxinLogic
    DISPLAY_LENGTH = 14.0     # halka yaricapi


class Lysin(BaseWeapon):
    LOGIC = LysinLogic
    DISPLAY_LENGTH = 7.0


class Phagocytosis(BaseWeapon):
    LOGIC = PhagocytosisLogic
    DISPLAY_LENGTH = 10.0


WEAPON_CLASSES = {
    "Stylet": Stylet, "Harpoon": Harpoon, "Nematocyst": Nematocyst,
    "Toxin": Toxin, "Lysin": Lysin, "Phagocytosis": Phagocytosis,
}

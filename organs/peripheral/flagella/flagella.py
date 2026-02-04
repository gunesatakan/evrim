import math
from organs.peripheral.base_motor import BaseMotorOrgan
from .logic_flagella import FlagellaLogic
from .view_flagella import draw_flagella


class Flagella(BaseMotorOrgan):
    def __init__(self, attachment_angle=math.pi, length=30.0, thrust_angle=None):
        """
        attachment_angle: Hücre zarında pozisyon (radyan)
        length: Flagella uzunluğu
        thrust_angle: İtme yönü (hücre lokal koordinatı, radyan)
                      None ise attachment_angle kullanılır (fiziksel olarak doğru)
        """
        super().__init__(attachment_angle, offset_distance=1.0)
        # Fizik: Flagella nereye takılıysa, o yönde iter
        # Örn: arkada (π) → geriye iter → hücre ileri gider
        # Örn: önde (0) → ileriye iter → hücre geri gider
        actual_thrust = thrust_angle if thrust_angle is not None else attachment_angle
        self.logic = FlagellaLogic(length, actual_thrust)

    def get_thrust_direction(self):
        """
        Flagella'nın itme yönünü döndür.

        Flagella, takılı olduğu noktadan dışa doğru iter.
        current_thrust_angle deflection dahil anlık yönü verir.
        """
        return self.logic.current_thrust_angle

    def update(self, dt, parent=None):
        """Her frame çağrılır - açı interpolasyonu için"""
        self.logic.update(dt)

    def sync_thrust_to_attachment(self):
        """Thrust açısını attachment açısına eşitler (sürükleme sonrası çağrılmalı)"""
        self.logic.base_thrust_angle = self.attachment_angle
        self.logic.current_thrust_angle = self.attachment_angle
        self.logic.target_thrust_angle = self.attachment_angle

    def draw(self, screen, parent):
        boost = parent.membrane.logic.calcium_boost if hasattr(parent, 'membrane') else 1.0
        # Güç seviyesine göre renk ayarla
        power = self.logic.power
        if power < 0.1:
            # Neredeyse kapalı - çok soluk
            color = tuple(max(30, int(c * 0.3)) for c in parent.color)
        elif power < 0.5:
            # Düşük güç - soluk
            color = tuple(max(50, int(c * 0.6)) for c in parent.color)
        else:
            # Normal/yüksek güç
            color = parent.color

        # attachment_angle: fiziksel tutunma noktası, thrust_angle: itme yönü (sapma dahil)
        draw_flagella(screen, parent.pos, parent.direction, parent.radius, color,
                     self.logic.length, parent.shutdown, boost * power,
                     attachment_angle=self.attachment_angle,
                     thrust_angle=self.logic.current_thrust_angle, show_thrust_vector=False)

    def grow(self):
        self.logic.grow()

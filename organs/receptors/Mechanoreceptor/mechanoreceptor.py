from organs.base_organ import BaseOrgan
from .logic_mechanoreceptor import MechanoreceptorLogic
from .view_mechanoreceptor import draw_mechanoreceptor_sausage

class Mechanoreceptor(BaseOrgan):
    def __init__(self, attachment_angle=0, size=1.0):
        super().__init__(attachment_angle, offset_distance=1.0)
        self.logic = MechanoreceptorLogic(size)

    def draw(self, screen, parent):
        # Sosis çizimi
        draw_mechanoreceptor_sausage(
            screen, 
            parent.pos, 
            parent.radius, 
            self.attachment_angle, 
            parent.direction,
            self.logic.size
        )

    def grow(self):
        self.logic.grow()

    def is_hearing(self, parent, target_pos, target_radius=0, gurultu=None):
        """Bu kulak hedefi duyuyor mu?

        SES, VARLIK DEGIL HAREKETTIR.

        Once yalnizca mesafeye bakiyordu: duran bir hucre de yuzen bir
        hucre kadar "duyuluyordu" ve sinif olarak da BOYUTU okunuyordu.
        Ama boyutu koku zaten veriyor ve menzili daha uzun - yani kulak,
        burnun daha kotu bir kopyasiydi. Islevsiz bir organ da evrimde
        atilir; nitekim atiliyordu.

        Gercekte mekanoresepsiyon SUYUN BOZULMASINI algilar: kopepod
        setalari, balik yan cizgisi. Hizli yuzen bir avci gurultuludur,
        suzulen bir hucre sessizdir. Bu, kokunun veremedigi bir bilgidir -
        anliktir (koku difuzyonla gecikir) ve YAKLASMAKTA OLANI haber
        verir.

        Yan sonucu da onemli: DONMAK artik bir strateji. Motor eforunu
        kesen hucre akustik olarak gorunmez olur. Davranis spektrumunun
        uclarinda (tam kacis / tam saldiri) efor 1.0'a ciktigi icin
        kararli bir hamle ayni zamanda kendini ELE VERIR.
        """
        my_pos = self.get_absolute_position(parent.pos, parent.direction, parent.radius)
        dist = my_pos.distance_to(target_pos) - target_radius
        if dist <= 0.0:
            return True
        return dist <= self.logic.duyma_menzili(gurultu)
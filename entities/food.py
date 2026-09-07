import pygame
import random
import math
import game_settings
from entities.entity import Entity, WIDTH, HEIGHT, GREEN

class Food(Entity):
    #: Besinin hücreye çekilme süresi (sn).
    #
    #  Önceden besin, temas anında listeden silinip doğrudan sindirim
    #  kuyruğuna giriyordu - ekranda "içeri ışınlanıyor" gibi görünen şey
    #  buydu. Artık zarfa değdiği anda YUTULMA başlar: besin küçülerek
    #  merkeze çekilir ve ancak oraya varınca kuyruğa girer.
    YUTULMA_SURESI = 0.9
    #: Sarmalama bu orana kadar surer; gerisi iceri cekme.
    KAVRAMA = 0.6

    def __init__(self, x, y, from_corpse=False):
        radius = math.sqrt(game_settings.FOOD_AREA / math.pi)
        super().__init__(x, y, radius, 0, GREEN)
        # Bu besin bir LEŞTEN mi geldi? Kairomon diyet kaynaklıdır: av
        # dokusunu sindirmek metabolik artık sızdırır, avı kendin mi
        # öldürdün yoksa leşini mi buldun fark etmez.
        self.from_corpse = from_corpse
        # --- yutulma durumu ---
        self.yutan = None          # onu çeken hücre
        self.yutma_t = 0.0         # 0..1 ilerleme
        self.taban_r = radius

    # ---------------- yutulma ----------------

    def yutulmaya_basla(self, hucre):
        """Hücre besine değdi: SARMALAMA başlasın. Zaten çekiliyorsa hayır."""
        if self.yutan is not None:
            return False
        self.yutan = hucre
        self.yutma_t = 0.0
        # Hücre de bunu bilmeli: yalancı ayakları ona doğru uzatacak.
        try:
            hucre.yutulan_besin = self
        except Exception:
            pass
        return True

    def yutma_guncelle(self, dt):
        """Çekmeyi ilerlet. Tamamlandıysa True (artık hücrenin içinde)."""
        if self.yutan is None:
            return False
        if getattr(self.yutan, 'dead', False):
            # Avcı öldü: besin serbest kalır ve eski boyuna döner.
            try:
                if getattr(self.yutan, 'yutulan_besin', None) is self:
                    self.yutan.yutulan_besin = None
            except Exception:
                pass
            self.yutan = None
            self.yutma_t = 0.0
            self.radius = self.taban_r
            return False
        self.yutma_t = min(1.0, self.yutma_t + dt / self.YUTULMA_SURESI)
        t = self.yutma_t
        # FAGOSITOZUN GERCEK SIRASI:
        #   1) SARMALAMA (t < KAVRAMA): yalancı ayaklar besinin etrafında
        #      kapanır. Besin bu sırada YERINDE durur - önce sarılır,
        #      sonra alınır. Eskiden ilk kareden itibaren merkeze doğru
        #      kayıyordu, bu da "içeri çekiliyor" değil "emiliyor" gibi
        #      görünüyordu.
        #   2) İÇERİ ALMA (t > KAVRAMA): kapanan kese sitoplazmaya çekilir.
        hedef = self.yutan.pos
        if t <= self.KAVRAMA:
            self.radius = self.taban_r          # sarılırken küçülmez
            return False
        u = (t - self.KAVRAMA) / max(1e-6, 1.0 - self.KAVRAMA)
        egri = u * u * (3 - 2 * u)
        self.pos = self.pos + (hedef - self.pos) * min(1.0, egri * 0.5 + dt * 5)
        # Kese içine girerken hafifçe sıkışır, ama YOK OLMAZ - sitoplazmada
        # görünmeye devam edecek.
        self.radius = max(1.5, self.taban_r * (1.0 - 0.35 * egri))
        return t >= 1.0

    @property
    def yutuluyor(self):
        return self.yutan is not None

    def draw(self, screen):
        pygame.draw.circle(screen, self.color,
                           (int(self.pos.x), int(self.pos.y)),
                           max(1, int(self.radius)))

    @staticmethod
    def spawn(count):
        return [Food(random.randint(30, WIDTH - 30), random.randint(30, HEIGHT - 30)) for _ in range(count)]

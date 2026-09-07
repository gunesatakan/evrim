import math
import pygame

# Her silahin kendi rengi - ekranda ayirt edilebilsin
COLORS = {
    "Stylet":       (255, 210, 120),
    "Harpoon":      (150, 220, 255),
    "Nematocyst":   (255, 120, 220),
    "Toxin":        (170, 255, 120),
    "Lysin":        (255, 150, 90),
    "Phagocytosis": (200, 200, 255),
}


def draw_weapon(screen, name, pos, outward, length, ready, firing_at=None,
                olcek=1.0):
    """Silahi govde uzerinde ciz. Bekleme suresindeyse soluk gorunur."""
    def _p(n):
        """Sabit piksel olcusunu cizim olcegine tasi (en az 1 px)."""
        return max(1, int(round(n * olcek)))

    col = COLORS.get(name, (255, 255, 255))
    if not ready:
        col = tuple(int(c * 0.35) for c in col)
    tip = pos + outward * length

    if name == "Toxin":
        # Alan silahi: govdenin cevresine halka
        pygame.draw.circle(screen, col, (int(pos.x), int(pos.y)), max(2, int(length)), _p(1))
    elif name == "Nematocyst":
        pygame.draw.line(screen, col, pos, tip, _p(2))
        pygame.draw.circle(screen, col, (int(tip.x), int(tip.y)), _p(3))
    elif name == "Phagocytosis":
        # SITOSTOM (hucre agzi). Once yalnizca bir yalanci ayak yayi
        # ciziliyordu; oysa yerellesmis fagositozun yapisi KALICIDIR -
        # Paramecium'un oral olugu, vestibulumu ve sitofarinksi hep oradadir
        # ve hucrenin en goze carpan yapisidir. Yalanci ayak amipteki
        # GENELLESMIS surumun gorunusudur, bizimki agizli surum.
        perp = pygame.math.Vector2(-outward.y, outward.x)
        agiz = length * 0.85
        bogaz = length * 0.28
        ic = pos - outward * length * 0.5
        pygame.draw.polygon(screen, tuple(int(c * 0.30) for c in col),
                            [pos + perp * agiz, tip + perp * agiz * 0.55,
                             tip - perp * agiz * 0.55, pos - perp * agiz])
        pygame.draw.lines(screen, col, False,
                          [tip + perp * agiz * 0.55, pos + perp * agiz,
                           ic + perp * bogaz, ic - perp * bogaz,
                           pos - perp * agiz, tip - perp * agiz * 0.55], 2)
    else:
        pygame.draw.line(screen, col, pos, tip, _p(2))

    if firing_at is not None:
        pygame.draw.line(screen, col, tip, firing_at, _p(1))

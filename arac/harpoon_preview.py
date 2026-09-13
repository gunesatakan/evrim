"""T6SS durumlarini deterministik olarak ciz (gorsel inceleme icin).

  python arac/harpoon_preview.py cikti.png

Dort karo: kilif kurulmus (atisa hazir), kilif kasildi (hemen atistan
sonra), kilif yeniden kuruluyor, firlatilan tup hedefin icinde cozunuyor.
"""
import math
import os
import random
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame


def render(path):
    pygame.init()
    pygame.display.set_mode((64, 64))
    import lab
    from systems.world import Dunya
    from organs.registry import organ_class

    screen = pygame.Surface((1000, 650))
    screen.fill((14, 22, 30))
    font = pygame.font.Font(None, 26)
    basliklar = ['Kilif kurulmus / atisa hazir', 'Kilif kasildi (atistan hemen sonra)',
                 'Kilif yeniden kuruluyor (%60)', 'Firlatilan tup hedefte cozunuyor']
    for i, baslik in enumerate(basliklar):
        random.seed(3)
        dunya = Dunya()
        saldirgan, hedef = dunya.hucreler[:2]
        organ = organ_class('Harpoon')()
        organ.attachment_angle = 0.0
        saldirgan.add_organ(organ)
        uretici = organ_class('Toxin')()
        uretici.logic.payload = 6
        uretici.logic.stok = float(lab.STOCK_MAX)
        uretici.attachment_angle = math.pi
        saldirgan.add_organ(uretici)
        saldirgan.recalculate_physics()
        saldirgan.direction.update(1, 0)
        saldirgan.pos.update(600, 400)
        hedef.pos.update(600 + saldirgan.radius + hedef.radius + 2.0, 400)
        for hucre in (saldirgan, hedef):
            hucre.onceki_pos = pygame.Vector2(hucre.pos)
            hucre.energy = 900.0
            hucre.molekuller = []
        saldirgan.attack_targets = {id(hedef)}
        if i >= 1:
            saldirgan.fire_weapons(1 / 30.0, [hedef])
        if i == 2:
            organ.logic.cooldown_timer = organ.logic.cooldown * 0.4
        if i == 3:
            for _ in range(8):
                saldirgan.mermileri_guncelle(1 / 30.0)
        ox, oy = (i % 2) * 500 + 150, (i // 2) * 325 + 175
        olcek = 9.0
        kamera = pygame.Vector2(600 + saldirgan.radius, 400)

        def don(v):
            return ((v.x - kamera.x) * olcek + ox + 100, (v.y - kamera.y) * olcek + oy)
        screen.set_clip(pygame.Rect((i % 2) * 500, (i // 2) * 325, 500, 325))
        for hucre in (hedef, saldirgan):
            lab.hucreyi_ciz(screen, hucre, don(hucre.pos), olcek)
            hucre.molekulleri_ciz(screen, olcek=olcek, donustur=don)
        saldirgan.atislari_ciz(screen, olcek=olcek, donustur=don)
        screen.set_clip(None)
        screen.fill((14, 22, 30), pygame.Rect((i % 2) * 500 + 5, (i // 2) * 325 + 5, 420, 26))
        screen.blit(font.render(baslik, True, (210, 225, 235)), ((i % 2) * 500 + 10, (i // 2) * 325 + 8))
    pygame.image.save(screen, str(path))
    pygame.quit()


if __name__ == '__main__':
    render(sys.argv[1])

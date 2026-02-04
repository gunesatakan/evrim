"""
Runtime debug - simulasyon sirasinda kemoreseptor ve hareket yonlerini loglar
"""
import pygame
import math
import sys
import time

pygame.init()
screen = pygame.display.set_mode((1200, 800))
pygame.display.set_caption("Kemoreseptor Debug")
clock = pygame.time.Clock()

# Modulleri import et
from entities.organism import Organism
from entities.food import Food
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor

# Debug log dosyasi
log_file = open("debug_runtime_log.txt", "w", encoding="utf-8")

def log(msg):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

def main():
    # Organizma olustur
    org = Organism(0, 400, 400, (255, 100, 100))
    org.direction = pygame.math.Vector2(1, 0)

    # Gerekli organlari ekle
    from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
    from organs.central.cytoplasm.cytoplasm import Cytoplasm
    from organs.peripheral.flagella.flagella import Flagella

    # Cytoskeleton (karar mekanizmasi)
    org.cytoskeleton = Cytoskeleton()
    org.add_organ(org.cytoskeleton)

    # Cytoplasm/Body (sindirim, enerji)
    org.body = Cytoplasm()
    org.add_organ(org.body)

    # Motor organ (hareket icin)
    flagella = Flagella(attachment_angle=math.pi, length=15.0)  # Arkada
    org.add_organ(flagella)

    # Kemoreseptorler (birden fazla - farkli yonlerde)
    chemo1 = Chemoreceptor(attachment_angle=0, length=20.0)  # Onde
    chemo2 = Chemoreceptor(attachment_angle=math.pi/2, length=15.0)  # Solda
    chemo3 = Chemoreceptor(attachment_angle=-math.pi/2, length=15.0)  # Sagda
    org.add_organ(chemo1)
    org.add_organ(chemo2)
    org.add_organ(chemo3)

    # Fizik hesapla
    org.recalculate_physics()

    # Besin olustur - organizmadan yakin saga (koku alaninda baslayacak sekilde)
    # Kemoreseptor uzunlugu 20, organizma radius 10, toplam 30 px one cikiyor
    # Besin scent_radius ~59, yani besin 89px uzakta olursa tip tam koku alaninda
    foods = [Food(460, 400)]  # 60px sagda - kemoreseptor koku alaninda

    log("="*60)
    log("RUNTIME DEBUG BASLATILDI")
    log("="*60)
    log(f"Organizma: {org.pos}")
    log(f"Besin: {foods[0].pos}")
    log(f"Besin scent_radius: {foods[0].scent_radius:.1f}")
    log("")

    frame = 0
    running = True

    while running:
        dt = clock.tick(30) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Koku ornekle
        intensity, scent_dir = org.sample_food_scent(foods)

        # Her 30 frame'de bir logla (1 saniye)
        if frame % 30 == 0:
            log(f"\n--- Frame {frame} ---")
            log(f"Organizma pos: ({org.pos.x:.1f}, {org.pos.y:.1f})")
            log(f"Organizma direction: ({org.direction.x:.3f}, {org.direction.y:.3f})")

            if scent_dir:
                scent_angle = math.degrees(math.atan2(scent_dir.y, scent_dir.x))
                log(f"Scent direction: ({scent_dir.x:.3f}, {scent_dir.y:.3f}) = {scent_angle:.1f} derece")
            else:
                log(f"Scent direction: None")

            if hasattr(org, 'target_movement') and org.target_movement:
                target_angle = math.degrees(math.atan2(org.target_movement.y, org.target_movement.x))
                log(f"Target movement: ({org.target_movement.x:.3f}, {org.target_movement.y:.3f}) = {target_angle:.1f} derece")
            else:
                log(f"Target movement: None")

            # Global koku kilidi
            if hasattr(org, '_scent_locked_intensity'):
                log(f"GLOBAL LOCK: intensity={org._scent_locked_intensity:.3f}")
                if org._scent_locked_direction:
                    lock_angle = math.degrees(math.atan2(org._scent_locked_direction.y, org._scent_locked_direction.x))
                    log(f"GLOBAL LOCK direction: {lock_angle:.1f} derece")

        # Organizma guncelle
        org.update(dt, [], foods)

        # Cizim
        screen.fill((20, 20, 30))

        # Besinleri ciz
        for food in foods:
            food.draw(screen)

        # Organizma ciz
        org.draw(screen)

        # Debug info ekranda
        font = pygame.font.Font(None, 24)
        y = 10
        texts = [
            f"Frame: {frame}",
            f"Org pos: ({org.pos.x:.1f}, {org.pos.y:.1f})",
            f"Intensity: {intensity:.3f}",
        ]
        if scent_dir:
            scent_angle = math.degrees(math.atan2(scent_dir.y, scent_dir.x))
            texts.append(f"Scent dir: {scent_angle:.1f} derece")
        if hasattr(org, 'target_movement') and org.target_movement:
            target_angle = math.degrees(math.atan2(org.target_movement.y, org.target_movement.x))
            texts.append(f"Target: {target_angle:.1f} derece")

        for txt in texts:
            surf = font.render(txt, True, (255, 255, 255))
            screen.blit(surf, (10, y))
            y += 25

        pygame.display.flip()
        frame += 1

        # 10 saniye sonra dur
        if frame > 300:
            running = False

    log("\n" + "="*60)
    log("DEBUG TAMAMLANDI")
    log("="*60)
    log_file.close()
    pygame.quit()

if __name__ == "__main__":
    main()

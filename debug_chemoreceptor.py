"""
Kemoreseptör debug scripti - yön hesaplamalarını test eder
"""
import pygame
import math
import sys

pygame.init()

# Modülleri import et
from entities.organism import Organism
from entities.food import Food
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor

def test_chemoreceptor_directions():
    """Kemoreseptör yön hesaplamalarını test et ve karşılaştır"""

    print("=" * 60)
    print("KEMORESEPTÖR DEBUG TESTİ")
    print("=" * 60)

    # Test organizması oluştur (merkez pozisyon)
    org = Organism(0, 400, 300, (255, 100, 100))  # index=0, x=400, y=300, color=red
    org.direction = pygame.math.Vector2(1, 0)  # Sağa bakıyor

    # Manuel olarak kemoreseptör ekle (önde, 0 derece)
    chemo = Chemoreceptor(attachment_angle=0, length=15.0)
    org.add_organ(chemo)

    # Kemoreseptörü bul
    chemoreceptors = [o for o in org.organs if isinstance(o, Chemoreceptor)]

    if not chemoreceptors:
        print("HATA: Organizmada kemoreseptör yok!")
        return

    print(f"\nOrganizma pozisyon: {org.pos}")
    print(f"Organizma yön: {org.direction}")
    print(f"Kemoreseptör sayısı: {len(chemoreceptors)}")

    for i, chemo in enumerate(chemoreceptors):
        print(f"\n  Kemoreseptör {i}:")
        print(f"    Attachment angle: {math.degrees(chemo.attachment_angle):.1f}°")
        print(f"    Length: {chemo.logic.length}")

    # Test besinleri oluştur - koku alanı içinde olacak şekilde yakın
    # Besin scent_radius yaklaşık 59 piksel
    test_cases = [
        ("Sagda (onde)", Food(440, 300)),      # Sagda, organizma saga bakiyor
        ("Solda (arkada)", Food(360, 300)),    # Solda
        ("Yukarida", Food(400, 260)),          # Yukarida
        ("Asagida", Food(400, 340)),           # Asagida
        ("Sag ust", Food(430, 270)),           # Sag ust kose
    ]

    for case_name, food in test_cases:
        print(f"\n{'='*60}")
        print(f"TEST: Besin {case_name}")
        print(f"{'='*60}")
        print(f"Besin pozisyon: {food.pos}")
        print(f"Besin radius: {food.radius:.1f}")
        print(f"Besin scent_radius: {food.scent_radius:.1f}")

        # Organizmadan besine mesafe
        dist_to_food = org.pos.distance_to(food.pos)
        print(f"Organizmadan besine mesafe: {dist_to_food:.1f}")
        print(f"Koku alanı içinde mi: {dist_to_food < food.scent_radius}")

        # Her kemoreseptör için test
        foods = [food]

        for i, chemo in enumerate(chemoreceptors):
            print(f"\n  --- Kemoreseptör {i} ---")

            # Tip pozisyonunu hesapla
            tip_pos = chemo.get_tip_position(org)
            print(f"  Tip pozisyon: ({tip_pos.x:.1f}, {tip_pos.y:.1f})")

            # Tip'ten besine mesafe
            tip_to_food = tip_pos.distance_to(food.pos)
            print(f"  Tip'ten besine mesafe: {tip_to_food:.1f}")
            print(f"  Tip koku alanında mı: {tip_to_food < food.scent_radius}")

            # Koku örnekle
            intensity, direction = chemo.sample_scent(org, foods)

            print(f"\n  SONUÇLAR:")
            print(f"    Algılanan yoğunluk: {intensity:.3f}")
            print(f"    Kilit aktif mi: {chemo.debug_is_locked}")
            print(f"    Kilitli yoğunluk: {chemo.locked_intensity:.3f}")

            if direction:
                angle = math.degrees(math.atan2(direction.y, direction.x))
                print(f"    Hesaplanan yon: ({direction.x:.3f}, {direction.y:.3f})")
                print(f"    Yon acisi: {angle:.1f} derece")

                # En yogun pixel'in pozisyonunu goster
                if chemo.debug_food_positions:
                    best_pos = None
                    best_int = 0
                    for pos, inten in chemo.debug_food_positions:
                        if inten > best_int:
                            best_int = inten
                            best_pos = pos
                    if best_pos:
                        print(f"    En yogun pixel: ({best_pos.x:.1f}, {best_pos.y:.1f})")
                        print(f"    En yogun pixel yogunluk: {best_int:.3f}")
            else:
                print(f"    Hesaplanan yon: None (algilama yok)")

            # Beklenen yön (organizma merkezinden besine)
            expected_dir = food.pos - org.pos
            if expected_dir.length() > 0:
                expected_dir = expected_dir.normalize()
                expected_angle = math.degrees(math.atan2(expected_dir.y, expected_dir.x))
                print(f"\n    BEKLENEN (merkez->besin): ({expected_dir.x:.3f}, {expected_dir.y:.3f})")
                print(f"    BEKLENEN açı: {expected_angle:.1f}°")

                if direction:
                    # Fark
                    angle_diff = abs(angle - expected_angle)
                    if angle_diff > 180:
                        angle_diff = 360 - angle_diff
                    print(f"\n    FARK: {angle_diff:.1f} derece")
                    if angle_diff > 10:
                        print(f"    !!! YON UYUMSUZLUGU !!!")

        # Birleşik sonuç (sample_food_scent)
        print(f"\n  --- BİRLEŞİK SONUÇ (sample_food_scent) ---")
        total_intensity, combined_dir = org.sample_food_scent(foods)
        print(f"  Toplam yoğunluk: {total_intensity:.3f}")
        if combined_dir:
            combined_angle = math.degrees(math.atan2(combined_dir.y, combined_dir.x))
            print(f"  Birleşik yön: ({combined_dir.x:.3f}, {combined_dir.y:.3f})")
            print(f"  Birleşik açı: {combined_angle:.1f}°")
        else:
            print(f"  Birleşik yön: None")

        # Kilidi sıfırla sonraki test için
        for chemo in chemoreceptors:
            chemo.locked_intensity = 0.0
            chemo.locked_direction = None

    print("\n" + "=" * 60)
    print("TEST TAMAMLANDI")
    print("=" * 60)

if __name__ == "__main__":
    test_chemoreceptor_directions()

import math
import pygame

class SmartFlagellaController:
    """
    Akıllı flagella kontrol sistemi.

    Organizmanın gitmek istediği yöne göre tüm flagellaları optimal şekilde kontrol eder:
    - Hedefe katkı sağlayan flagellalar aktif
    - Zıt yöndekiler pasif veya ters açıda
    - Dönüş için tüm flagellalar koordineli sapma yapar
    """

    def __init__(self):
        self.last_target_angle = 0
        self.turning_mode = False
        self.turn_direction = 0  # -1: sağa, +1: sola

    def calculate_flagella_contribution(self, flagella_angle, target_movement_angle):
        """
        Bir flagella'nın hedef harekete katkısını hesaplar.

        flagella_angle: Flagella'nın attachment açısı (radyan)
        target_movement_angle: Hedef hareket yönü (radyan, dünya koordinatı)

        Returns: -1.0 ile +1.0 arası
                 +1.0 = tam katkı (flagella hedef yönde itiyor)
                 -1.0 = tam karşı (flagella ters yönde itiyor)
        """
        # Flagella'nın itme yönü = attachment açısı (dışa doğru iter)
        # Tepki kuvveti = itme yönünün tersi (organizmayı hareket ettirir)
        reaction_angle = flagella_angle + math.pi

        # Hedef ile tepki açısı arasındaki fark
        angle_diff = target_movement_angle - reaction_angle

        # Normalize et (-π, π)
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Cosine similarity: 0° fark = 1.0, 90° fark = 0.0, 180° fark = -1.0
        contribution = math.cos(angle_diff)

        return contribution

    def calculate_turn_contribution(self, flagella_angle, turn_direction):
        """
        Bir flagella'nın dönüşe katkısını hesaplar - pozisyona göre farklı deflection.

        Fiziksel mantık (kürek çekme prensibi):
        - Sağa dönüş için: Sol flagella geriye yaslanır, sağ flagella da geriye yaslanır
          (ikisi de saat yönünde tork üretir)
        - Sola dönüş için: İkisi de ileriye yaslanır
          (ikisi de saat yönü tersi tork üretir)

        turn_direction: +1 = saat yönü tersi (sola), -1 = saat yönü (sağa)

        Returns: Optimal deflection açısı (pozisyona göre değişir)
        """
        # Flagella pozisyon faktörü:
        # sin(attachment_angle) → +1 = sol (π/2), -1 = sağ (-π/2), 0 = ön/arka
        position_factor = math.sin(flagella_angle)

        # "Geriye yaslanmak" = thrust'ı 180°'ye (π) yaklaştırmak
        # Sol flagella (base=90°): 90°→135° için deflection negatif
        # Sağ flagella (base=-90°): -90°→-135° için deflection pozitif
        #
        # Formül: deflection = turn_direction * position_factor
        # Sağa dönüş (turn=-1): Sol(-0.8), Sağ(+0.8) → ikisi de geriye yaslanır
        # Sola dönüş (turn=+1): Sol(+0.8), Sağ(-0.8) → ikisi de ileriye yaslanır

        deflection = turn_direction * position_factor * 0.8

        return deflection

    def update(self, organism, target_direction, dt):
        """
        Tüm flagellaları hedefe göre optimal kontrol et.

        organism: Kontrol edilecek organizma
        target_direction: Hedef yön vektörü (Vector2)
        dt: Delta time
        """
        from organs.peripheral.flagella.flagella import Flagella

        flagellas = [o for o in organism.organs if isinstance(o, Flagella)]
        if not flagellas:
            return

        # Organizma yönü
        org_angle = math.atan2(organism.direction.y, organism.direction.x)

        # Hedef hareket yönü (dünya koordinatı)
        target_angle = math.atan2(target_direction.y, target_direction.x)

        # Hedef ile mevcut yön arasındaki fark (dönüş gereksinimi)
        turn_needed = target_angle - org_angle
        while turn_needed > math.pi:
            turn_needed -= 2 * math.pi
        while turn_needed < -math.pi:
            turn_needed += 2 * math.pi

        # Dönüş modu mu, düz ilerleme mi?
        turn_threshold = math.radians(15)  # 15 dereceden fazla sapma = dönüş modu
        self.turning_mode = abs(turn_needed) > turn_threshold

        if self.turning_mode:
            self.turn_direction = 1 if turn_needed > 0 else -1

        # Her flagella için optimal kontrol hesapla
        for flagella in flagellas:
            # Flagella'nın dünya koordinatındaki açısı
            world_flagella_angle = org_angle + flagella.attachment_angle

            if self.turning_mode:
                # DÖNÜŞ MODU: Tüm flagellalar koordineli dönüş
                # Güç: Dönüşe katkı sağlayabilenler aktif

                # Flagella'nın dönüşe katkı potansiyeli
                # Yan flagellalar dönüşe en çok katkı sağlar
                side_factor = abs(math.sin(flagella.attachment_angle))

                # Ön/arka flagellalar da sapma ile katkı sağlayabilir
                base_power = 0.3 + side_factor * 0.7

                flagella.logic.set_power(base_power)

                # Tüm flagellalar aynı yöne sap (koordineli dönüş)
                deflection = self.calculate_turn_contribution(
                    flagella.attachment_angle, self.turn_direction
                )
                flagella.logic.set_deflection(deflection)

            else:
                # DÜZGÜN İLERLEME MODU: Hedefe katkı sağlayanlar aktif
                # Katkı sağlamayanlar saptırılarak katkı sağlamaya çalışır

                # Bu flagella'nın hedef harekete mevcut katkısı
                contribution = self.calculate_flagella_contribution(
                    world_flagella_angle, target_angle
                )

                # Optimal sapma açısını hesapla (flagella'yı hedefe yönlendirir)
                optimal_deflection = self._calculate_optimal_deflection(
                    flagella.attachment_angle, org_angle, target_angle
                )

                # Sapma ile elde edilecek potansiyel katkı
                # set_deflection: target = base - (deflection * max_deflection)
                max_def_rad = math.radians(45)
                deflected_thrust = world_flagella_angle - (optimal_deflection * max_def_rad)
                potential_contribution = self.calculate_flagella_contribution(
                    deflected_thrust, target_angle
                )

                if contribution > 0.3:
                    # Zaten iyi katkı sağlıyor: Tam güç, minimal sapma
                    flagella.logic.set_power(1.0)
                    flagella.logic.set_deflection(optimal_deflection * 0.3)

                elif potential_contribution > 0.3:
                    # Saptırılınca iyi katkı sağlayabilir: Tam güç + sapma
                    flagella.logic.set_power(1.0)
                    flagella.logic.set_deflection(optimal_deflection)

                elif contribution < -0.5 and potential_contribution < 0:
                    # Saptırılsa bile ters katkı: Kapat
                    flagella.logic.set_power(0.0)
                    flagella.logic.reset_deflection()

                else:
                    # Kısmen katkı sağlayabilir: Orta güç + sapma
                    power = max(0.3, min(0.8, potential_contribution + 0.5))
                    flagella.logic.set_power(power)
                    flagella.logic.set_deflection(optimal_deflection * 0.8)

    def _calculate_optimal_deflection(self, attachment_angle, org_angle, target_angle):
        """
        Flagella'nın hedefe maksimum katkı sağlaması için optimal sapma açısını hesaplar.

        attachment_angle: Flagella'nın organizma üzerindeki pozisyonu (lokal)
        org_angle: Organizmanın dünya koordinatındaki yönü
        target_angle: Hedef hareket yönü (dünya koordinatı)

        Returns: Normalize sapma (-1.0 ile +1.0 arası, max_deflection'a göre ölçekli)
        """
        # Flagella'nın mevcut itme yönü (dünya koordinatı)
        current_thrust = org_angle + attachment_angle

        # Tepki kuvveti (organizmayı hareket ettiren)
        current_reaction = current_thrust + math.pi

        # Hedef hareket yönü ile mevcut tepki arasındaki fark
        # Bu farkı kapatmak için flagella'yı saptırmalıyız
        angle_diff = target_angle - current_reaction

        # Normalize et (-π, π)
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Tepkiyi hedefe yaklaştırmak için thrust'ı aynı yönde saptır
        # angle_diff pozitif = tepki hedefin gerisinde = thrust'ı artır (pozitif sapma)
        # angle_diff negatif = tepki hedefin ilerisinde = thrust'ı azalt (negatif sapma)
        max_deflection = math.radians(45)

        # set_deflection içinde ters işaret var (target = base - deflection * max)
        # Bu yüzden sapma değerini tersine çevirmeliyiz
        optimal = -angle_diff

        # Normalize et ve sınırla
        normalized = optimal / max_deflection
        return max(-1.0, min(1.0, normalized))

    def _calculate_assist_deflection(self, attachment_angle, turn_needed):
        """
        Nötr bölgedeki flagella için yardımcı sapma hesapla. (Eski metot, geriye uyumluluk)
        """
        if abs(turn_needed) < 0.1:
            return 0
        return 1.0 if turn_needed > 0 else -1.0

    def get_debug_info(self, organism):
        """Debug bilgisi döndür"""
        from organs.peripheral.flagella.flagella import Flagella

        info = []
        for i, o in enumerate(organism.organs):
            if isinstance(o, Flagella):
                angle_deg = math.degrees(o.attachment_angle) % 360
                power = o.logic.power
                info.append(f"F{i}@{angle_deg:.0f}°: {power:.1%}")

        mode = "TURN" if self.turning_mode else "MOVE"
        return f"[{mode}] " + ", ".join(info)

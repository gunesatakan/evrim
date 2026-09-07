"""
SmartMotorBrain - Akıllı Motor Koordinasyon Sistemi

Cytoskeleton'un "beyni" gibi çalışır.
Hedefe ulaşmak için tüm organları optimal şekilde koordine eder.

Çalışma mantığı:
1. Hedef analizi: Açı farkını hesapla
2. Dönüş gerekiyorsa: Asimetrik güç + deflection → tork yarat
3. Düz gidiş: Eşit güç, deflection yok → maksimum hız

Bu yaklaşım fizik simülasyonuna güvenmek yerine,
organları bilinçli şekilde kontrol eder.
"""

import math
import pygame
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.cilia.cilia import Cilia


class SmartMotorBrain:
    """
    Akıllı motor koordinasyonu.

    Cytoskeleton bu sınıfı kullanarak tüm motorları yönetir.
    Hedef yöne göre en verimli hareket stratejisini uygular.
    """

    def __init__(self):
        self.target_direction = None  # Hedef hareket yönü (global, Vector2)

        # Kontrol parametreleri
        self.turn_threshold = math.radians(20)  # Bu açıdan büyükse dönüş modu
        self.alignment_threshold = math.radians(5)  # Bu açıdan küçükse tam hizalı

        # Dönüş parametreleri
        self.turn_power_high = 1.0   # Dönüş yönündeki motorlar
        self.turn_power_low = 0.2    # Ters yöndeki motorlar
        self.turn_deflection = 0.8   # Flagella eğim miktarı (-1 ile 1 arası)

        # Düz gidiş parametreleri
        self.straight_power = 1.0    # Tüm motorlar
        self.straight_deflection = 0.0

        # Dönüş yönü hafızası (oscillasyon önleme)
        self._last_turn_direction = 1  # +1=sol, -1=sağ
        self._hysteresis_threshold = math.radians(120)  # 120°+ açılarda eski yönü koru
        self._prev_target_angle = None  # Hedef değişimini takip et
        self._prev_angle_diff = None  # Açı değişimini takip et (overshoot tespiti)
        self._direction_lock_time = 0.0  # Yön değişikliği kilidi (saniye)
        self._direction_lock_duration = 0.5  # Minimum kilit süresi

        # Debug
        self.current_mode = "IDLE"
        self.angle_to_target = 0.0

    def set_target(self, direction):
        """
        Hedef hareket yönünü ayarla.

        Args:
            direction: pygame.math.Vector2 - gidilecek yön (global koordinat)
        """
        if direction is not None and direction.length() > 0:
            self.target_direction = direction.normalize()
        else:
            self.target_direction = None

    def update(self, organism, dt):
        """
        Her frame organları güncelle.

        Hedefe göre dönüş veya düz gidiş modunu seçer ve uygular.

        OPTIMAL ÖN SİSTEMİ:
        - Hücrenin "önü" = en hızlı gidebildiği yön
        - 360 derece taranarak hesaplanır (calculate_optimal_front)
        - Tüm motorların koordineli çalışmasıyla elde edilen maksimum hız yönü
        - Bu yön bakış yönünden farklı olabilir (kürek teknesi fiziği)
        """
        if self.target_direction is None:
            self._apply_idle_mode(organism)
            return

        # Hücrenin OPTIMAL ÖNÜ (360 derece taranarak hesaplanmış)
        # Bu değer organ eklendiğinde bir kere hesaplanır
        # En hızlı gidilebilecek yön = gerçek "ön"
        current_heading = math.atan2(organism.direction.y, organism.direction.x)
        optimal_front = getattr(organism, 'optimal_front_angle', 0.0)
        actual_movement_direction = current_heading + optimal_front

        # Hedef açı
        target_angle = math.atan2(self.target_direction.y, self.target_direction.x)

        # GERÇEK hareket yönü ile hedef arasındaki fark
        # (bakış yönü değil, hareket yönü!)
        angle_diff = target_angle - actual_movement_direction

        # Normalize: -π ile +π arası
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        self.angle_to_target = angle_diff

        # Hedef önemli ölçüde değiştiyse hysteresis'i sıfırla
        # (dolaşmadan ava geçiş gibi durumlarda eski dönüş yönü geçersiz)
        if self._prev_target_angle is not None:
            target_change = abs(self._normalize_angle(target_angle - self._prev_target_angle))
            if target_change > math.radians(45):
                # Hedef >45° değişti → eski dönüş yönünü unut
                self._last_turn_direction = 1 if angle_diff > 0 else -1
        self._prev_target_angle = target_angle

        # Mod seçimi
        if abs(angle_diff) > self.turn_threshold:
            # Dönüş gerekiyor

            # Zaman bazlı kilit güncelle
            self._direction_lock_time = max(0.0, self._direction_lock_time - dt)

            # Overshoot tespiti: Açı işareti değiştiyse VE 180° sınırını geçmemişse
            # (örn: -170° → +160° değil, -30° → +30° gibi)
            overshoot_detected = False
            if self._prev_angle_diff is not None:
                # İşaret değişti mi?
                sign_changed = (angle_diff > 0) != (self._prev_angle_diff > 0)
                # Her iki açı da 180°'den uzak mı? (gerçek overshoot, 180° bounce değil)
                both_far_from_180 = (abs(angle_diff) < math.radians(150) and
                                     abs(self._prev_angle_diff) < math.radians(150))
                if sign_changed and both_far_from_180:
                    overshoot_detected = True

            self._prev_angle_diff = angle_diff

            # Büyük açılarda oscillasyon önleme:
            # 1. Hysteresis: 120°+ açılarda eski yönü koru
            # 2. Zaman kilidi: Yön değişikliği sonrası 0.5s bekle
            use_hysteresis = abs(angle_diff) > self._hysteresis_threshold and not overshoot_detected
            direction_locked = self._direction_lock_time > 0

            if use_hysteresis or direction_locked:
                # Eski dönüş yönünü koru
                turn_direction = self._last_turn_direction
            else:
                # Normal durum: açı işaretine göre dön
                new_direction = 1 if angle_diff > 0 else -1  # +1: sola dön, -1: sağa dön

                # Yön değiştiyse kilidi başlat
                if new_direction != self._last_turn_direction:
                    self._direction_lock_time = self._direction_lock_duration

                turn_direction = new_direction

            self._last_turn_direction = turn_direction
            self._apply_turn_mode(organism, turn_direction, abs(angle_diff))
        elif abs(angle_diff) > self.alignment_threshold:
            # Hafif düzeltme gerekiyor
            turn_direction = 1 if angle_diff > 0 else -1
            self._last_turn_direction = turn_direction
            self._apply_correction_mode(organism, turn_direction, abs(angle_diff))
        else:
            # Hizalı - düz git
            self._apply_straight_mode(organism)

    def _apply_idle_mode(self, organism):
        """Hedef yok - tüm motorlar orta güçte, optimal_front yönünde ilerle."""
        self.current_mode = "IDLE"

        optimal_front = getattr(organism, 'optimal_front_angle', 0.0)

        for organ in organism.organs:
            if isinstance(organ, Flagella):
                organ.logic.set_power(0.5)
                organ.logic.reset_deflection()
            elif isinstance(organ, Cilia):
                # Cilia'yı optimal_front yönüne katkı sağlayacak teğet yöne ayarla
                self._set_cilia_for_direction(organ, optimal_front)
                organ.logic.power_boost = 1.0

    def _apply_turn_mode(self, organism, turn_direction, angle_magnitude):
        """
        Dönüş modu - hedefe doğru dön.

        turn_direction: +1 = sola dön (counterclockwise), -1 = sağa dön (clockwise)
        angle_magnitude: Dönülecek açı (radyan, mutlak değer)

        Strateji:
        - Flagella'lar: Asimetrik deflection → TORK üret (dönüşün ana kaynağı)
          Küçük açıda ileri+hafif tork, büyük açıda tam tork
        - Cilia'lar: SAF TORK - tüm cilia'lar koordineli teğet kuvvet
        - Güç proportional: büyük açıda hızlı dön, küçülünce yavaşla (overshoot önleme)
        """
        self.current_mode = f"TURN {'LEFT' if turn_direction > 0 else 'RIGHT'}"
        # Talep SAKLANIR: eskiden yerel degiskendi ve her kare atiliyordu,
        # bu yuzden cizim tarafi "ne kadar donmek istiyoruz" bilgisine
        # hic ulasamiyordu.
        self.turn_demand = turn_direction

        optimal_front = getattr(organism, 'optimal_front_angle', 0.0)

        # Tork vs ileri karışım oranı: açı büyüdükçe daha fazla tork
        # 20° (eşik) → 0.0,  90° → 1.0
        torque_blend = (angle_magnitude - self.turn_threshold) / \
                       (math.radians(90) - self.turn_threshold)
        torque_blend = max(0.0, min(1.0, torque_blend))

        for organ in organism.organs:
            if isinstance(organ, Flagella):
                # HER KAMCI KENDI HESABINI YAPAR, ISARET ORTAKTIR.
                #
                # Eski kod iki terimi karistiriyordu; ama tork terimi
                # cebirsel olarak her kamci icin AYNI +-1.0'a sadelesiyordu
                # (baglanma acisi sadelesir, 90/45 = 2 doyar). Yani buyuk
                # aci = herkese ayni sabit poz, kucuk aci = herkes kendi
                # yonune, torkler birbirini iptal.
                organ.logic.set_deflection(self._kamci_sapmasi(
                    organ, optimal_front, turn_direction * torque_blend))

                # Güç: tork üretmek için kuvvet lazım, düşürme
                organ.logic.set_power(max(0.4, 1.0 - torque_blend * 0.3))

            elif isinstance(organ, Cilia):
                # === YENİ YAKLAŞIM: base_dir HER ZAMAN optimal_front yönüne ===
                # Tork sadece GÜÇ ASİMETRİSİ ile üretilir (görsel tutarlılık için)
                #
                # Neden? Eski yaklaşımda büyük açılarda base_dir turn_direction'a bağlıydı.
                # turn_direction değişince (±180° sınırı) tüm cilia'lar 180° dönüyordu →
                # rastgele kol sallama görüntüsü.
                #
                # Yeni yaklaşım: base_dir sabit, güç asimetrisi ile dönüş.

                # Her zaman optimal_front yönüne katkı sağlayan teğet yöne ayarla
                self._set_cilia_for_direction(organ, optimal_front)

                # Güç asimetrisi ile tork üret
                # relative_angle: Cilia'nın optimal_front'a göre konumu
                # side > 0: Sağ tarafta, side < 0: Sol tarafta
                relative_angle = organ.attachment_angle - optimal_front
                side = math.sin(relative_angle)

                # alignment: Dönüş yönüne göre hizalama
                # turn_direction=+1 (LEFT): Sol taraf güçlü → sağ dönüş → CCW
                # turn_direction=-1 (RIGHT): Sağ taraf güçlü → sol dönüş → CW
                alignment = side * turn_direction

                # Büyük açılarda daha güçlü asimetri (daha hızlı dönüş)
                # Küçük açı: 0.15 fark (ilerlerken hafif dönüş)
                # Büyük açı: 0.50 fark (yerinde hızlı dönüş)
                power_diff = 0.15 + torque_blend * 0.35  # 0.15 → 0.50
                organ.logic.power_boost = max(0.3, min(1.7, 1.0 - alignment * power_diff))

    def _apply_correction_mode(self, organism, turn_direction, angle_magnitude):
        """
        Hafif düzeltme modu - küçük açı düzeltmesi.

        Düz giderken hafif dönüş için.
        Flagella'lar hedefe yönlendirilir.
        Cilia'lar: %70 optimal_front yönünde ileri + %30 dönüş tork.
        """
        self.current_mode = "CORRECT"

        optimal_front = getattr(organism, 'optimal_front_angle', 0.0)

        # Düzeltme şiddeti (açı küçük olduğu için düşük)
        correction = angle_magnitude / self.turn_threshold  # 0-1 arası

        # Hedef yönü lokal koordinata çevir (flagella için)
        if self.target_direction is not None:
            cell_heading = math.atan2(organism.direction.y, organism.direction.x)
            target_global = math.atan2(self.target_direction.y, self.target_direction.x)
            target_local = target_global - cell_heading
        else:
            target_local = optimal_front

        for organ in organism.organs:
            if isinstance(organ, Flagella):
                # Flagella'yı hedefe yönlendir (deflection yapabilir)
                organ.logic.set_deflection(self._kamci_sapmasi(
                    organ, target_local,
                    turn_direction * min(1.0, angle_magnitude /
                                         self.turn_threshold) * 0.45))
                organ.logic.set_power(0.9)  # Neredeyse tam güç
            elif isinstance(organ, Cilia):
                # Cilia: optimal_front yönüne katkı sağlayan teğet yön
                self._set_cilia_for_direction(organ, optimal_front)
                organ.logic.power_boost = 1.5

    def _apply_straight_mode(self, organism):
        """
        Düz gidiş modu - maksimum hız, optimal_front yönünde.

        Hücre zaten hedefe hizalanmış durumda.
        Tüm motorlar optimal_front yönünde maksimum itme yapar.
        """
        self.current_mode = "STRAIGHT"

        optimal_front = getattr(organism, 'optimal_front_angle', 0.0)

        # Hedef yönü al (global → lokal) - flagella için
        if self.target_direction is not None:
            cell_heading = math.atan2(organism.direction.y, organism.direction.x)
            target_global = math.atan2(self.target_direction.y, self.target_direction.x)
            target_local = target_global - cell_heading
        else:
            target_local = optimal_front

        for organ in organism.organs:
            if isinstance(organ, Flagella):
                organ.logic.set_power(self.straight_power)
                # Flagella'yı hedefe doğru yönlendir (deflection yapabilir)
                self._set_flagella_for_direction(organ, target_local)
            elif isinstance(organ, Cilia):
                # Cilia'yı optimal_front yönüne katkı sağlayacak teğet yöne ayarla
                self._set_cilia_for_direction(organ, optimal_front)
                organ.logic.power_boost = 2.0  # Tam güç

    def _set_cilia_for_direction(self, cilia, target_angle):
        """
        Cilia'yı hedef yöne maksimum katkı sağlayacak TEĞET yöne ayarla.

        Cilia teğet yönde iter: attachment ± π/2
        İki teğet yönden hedefe daha yakın olanı seçilir.

        Args:
            cilia: Cilia organı
            target_angle: Hedef hareket yönü (lokal koordinat, radyan)
        """
        attachment = cilia.attachment_angle

        # İki olası teğet yön
        tangent_plus = attachment + math.pi/2
        tangent_minus = attachment - math.pi/2

        # Her yönün tepki kuvveti (hareket yönü) = thrust + π
        reaction_plus = tangent_plus + math.pi
        reaction_minus = tangent_minus + math.pi

        # Hangisi hedef yöne daha yakın?
        diff_plus = abs(self._normalize_angle(target_angle - reaction_plus))
        diff_minus = abs(self._normalize_angle(target_angle - reaction_minus))

        if diff_plus <= diff_minus:
            best_direction = tangent_plus
        else:
            best_direction = tangent_minus

        cilia.logic.set_base_direction(best_direction)

    def _kamci_sapmasi(self, flagella, target_angle, donus_talebi=0.0):
        """Bir kamcinin KENDI sapmasi: hedefe it, ama torku bozma.

        Her kamci kendi baglanma acisindan yola cikarak hedefe en cok
        katki veren sapmayi bulur (bu zaten vardi). EKSIK OLAN sey su:
        tork = R * F * sin(sapma) - yani torkun ISARETI dogrudan sapmanin
        isaretidir ve baglanma acisi bu ifadede SADELESIR. Dolayisiyla
        farkli noktalardaki kamcilar "hedefe bak" dedigi icin zit isaretli
        sapmalar secebiliyor ve birbirlerinin torkunu iptal ediyorlardi.

        Olculdu: 180/90/300 derecede uc kamci, tam sapmada +63.6 / -63.6 /
        -5.6 tork uretiyordu - ikisi tam gucte birbirini kilitliyordu.

        Cozum: donus talebi varken sapma o isaretin YARI ARALIGINA
        kisitlanir. Kamci yine kendi hesabini yapar (hangi buyukluk
        hedefe en cok katki verir), ama hicbiri donusun tersine tork
        uretemez. Talep yoksa (duz gidis) eski davranis aynen kalir.
        """
        attachment = flagella.attachment_angle
        max_deflection = flagella.logic.max_deflection
        gerekli = self._normalize_angle(attachment + math.pi - target_angle)
        d = max(-1.0, min(1.0, gerekli / max_deflection))
        if donus_talebi:
            s = 1.0 if donus_talebi > 0 else -1.0
            # Kendi cozumunu koru ama yalnizca dogru yarim duzlemde;
            # talep buyudukce doyuma dogru cekilir.
            d = max(0.0, d * s) * s
            d = d * (1.0 - abs(donus_talebi)) + s * abs(donus_talebi)
            d = max(-1.0, min(1.0, d))
        return d

    def _set_flagella_for_direction(self, flagella, target_angle):
        """
        Flagella'yı hedef yöne maksimum katkı sağlayacak şekilde eğ.

        Args:
            flagella: Flagella organı
            target_angle: Hedef hareket yönü (lokal koordinat, radyan)
        """
        attachment = flagella.attachment_angle
        max_deflection = flagella.logic.max_deflection

        # Flagella attachment yönünde iter, tepki = attachment + π
        base_reaction = attachment + math.pi

        # Hedef yönüne ulaşmak için gereken deflection
        # set_deflection: thrust = base - (d * max_deflection)
        # reaction = thrust + π = attachment - (d * max) + π = target_angle
        # d = (attachment + π - target_angle) / max_deflection
        needed_deflection = attachment + math.pi - target_angle

        # Normalize et
        needed_deflection = self._normalize_angle(needed_deflection)

        # Max deflection sınırı içinde tut
        actual_deflection = max(-1.0, min(1.0, needed_deflection / max_deflection))

        flagella.logic.set_deflection(actual_deflection)

    def _normalize_angle(self, angle):
        """Açıyı -π ile +π arasına normalize et."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def _control_cilia_turn(self, cilia, organism, turn_direction, intensity):
        """
        Cilia dönüş kontrolü - DOĞRUDAN HEDEFE YÖNELİK.

        Strateji:
        1. Target movement yönüne (global) en iyi katkı sağlayan teğet yönü bul
        2. Güç asimetrisi ile hız/dönüş dengesi sağla

        Bu basit ve doğrudan yaklaşım: Hedefe git!
        """
        attachment = cilia.attachment_angle

        # Hedef yönü al (global → lokal dönüşüm)
        if self.target_direction is not None:
            cell_heading = math.atan2(organism.direction.y, organism.direction.x)
            target_global = math.atan2(self.target_direction.y, self.target_direction.x)
            target_local = target_global - cell_heading
        else:
            target_local = getattr(organism, 'optimal_front_angle', 0.0)

        # İki olası teğet yön
        tangent_plus = attachment + math.pi/2
        tangent_minus = attachment - math.pi/2

        # Her teğet yönün HEDEFE katkısını hesapla
        # Reaction (hareket yönü) = thrust + π
        reaction_plus = tangent_plus + math.pi
        reaction_minus = tangent_minus + math.pi

        # Hedef yönüne katkı (cosine similarity)
        contribution_plus = math.cos(self._normalize_angle(target_local - reaction_plus))
        contribution_minus = math.cos(self._normalize_angle(target_local - reaction_minus))

        # Hedefe en çok katkı sağlayan teğet yönü seç
        if contribution_plus >= contribution_minus:
            best_direction = tangent_plus
            best_contribution = contribution_plus
        else:
            best_direction = tangent_minus
            best_contribution = contribution_minus

        # Güç: Hedefe katkıya göre
        # Katkı yüksekse güçlü, düşükse zayıf
        if best_contribution > 0.3:
            power = 0.8 + 0.7 * best_contribution  # 0.8 - 1.5
        elif best_contribution > 0:
            power = 0.5 + 0.5 * best_contribution  # 0.5 - 0.8
        else:
            power = 0.3  # Minimum güç (hedefe karşı çalışıyor)

        cilia.logic.set_base_direction(best_direction)
        cilia.logic.power_boost = max(0.3, min(2.0, power * 1.5))

    def get_debug_info(self):
        """Debug bilgisi döndür."""
        return {
            'mode': self.current_mode,
            'angle_to_target': math.degrees(self.angle_to_target),
            'target': self.target_direction
        }

    def debug_motor_state(self, organism, label=""):
        """Motor durumunu debug için logla."""
        flagellas = [o for o in organism.organs if isinstance(o, Flagella)]
        cilias = [o for o in organism.organs if isinstance(o, Cilia)]

        print(f"\n=== MOTOR DEBUG {label} ===")
        print(f"Mode: {self.current_mode} | Angle to target: {math.degrees(self.angle_to_target):.1f}°")
        print(f"Target: {self.target_direction}")
        print(f"Optimal Front: {math.degrees(organism.optimal_front_angle):.1f}°")

        cell_heading = math.atan2(organism.direction.y, organism.direction.x)
        actual_move = cell_heading + organism.optimal_front_angle
        print(f"Cell Heading: {math.degrees(cell_heading):.1f}° | Actual Move Dir: {math.degrees(actual_move):.1f}°")

        print(f"\nFlagellas ({len(flagellas)}):")
        for i, f in enumerate(flagellas):
            base_thrust = f.logic.base_thrust_angle
            current_thrust = f.logic.current_thrust_angle
            deflection_deg = math.degrees(current_thrust - base_thrust)
            print(f"  [{i}] attach={math.degrees(f.attachment_angle):.1f}° "
                  f"base={math.degrees(base_thrust):.1f}° "
                  f"current={math.degrees(current_thrust):.1f}° "
                  f"deflection={deflection_deg:.1f}° "
                  f"power={f.logic.power:.2f}")

        print(f"\nCilias ({len(cilias)}):")
        optimal_front = getattr(organism, 'optimal_front_angle', 0.0)
        for i, c in enumerate(cilias):
            attach = c.attachment_angle
            base_dir = c.logic.base_direction
            reaction = base_dir + math.pi  # Hareket yönü

            # Tork hesabı
            r_x, r_y = math.cos(attach), math.sin(attach)
            f_x, f_y = math.cos(base_dir), math.sin(base_dir)
            torque = r_x * f_y - r_y * f_x  # Pozitif = CCW

            # Forward contribution
            fwd_contrib = math.cos(self._normalize_angle(optimal_front - reaction))

            print(f"  [{i}] attach={math.degrees(attach):.1f}° "
                  f"base_dir={math.degrees(base_dir):.1f}° "
                  f"reaction={math.degrees(reaction):.1f}° "
                  f"power={c.logic.power_boost:.2f} "
                  f"fwd={fwd_contrib:.2f} "
                  f"torque={torque:.2f}")

        # Net kuvvet hesabı
        net_x, net_y = 0.0, 0.0
        for f in flagellas:
            thrust_angle = f.logic.current_thrust_angle
            reaction = thrust_angle + math.pi
            mag = f.logic.thrust_magnitude
            net_x += math.cos(reaction) * mag
            net_y += math.sin(reaction) * mag

        for c in cilias:
            thrust_angle = c.logic.current_thrust_angle
            reaction = thrust_angle + math.pi
            mag = c.logic.current_thrust_magnitude
            net_x += math.cos(reaction) * mag
            net_y += math.sin(reaction) * mag

        net_mag = math.sqrt(net_x**2 + net_y**2)
        net_angle = math.atan2(net_y, net_x) if net_mag > 0.001 else 0
        print(f"\nNet Force: mag={net_mag:.2f} angle={math.degrees(net_angle):.1f}° (lokal)")
        print(f"========================\n")

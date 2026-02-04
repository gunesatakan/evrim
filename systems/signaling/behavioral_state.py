"""
Behavioral State System - Davranış Durumu Yönetimi

Tek hücrelilerde nöron yoktur. Davranışlar şu sistemlerle modellenir:
- Chemotaxis (kimyasal gradyan takibi)
- Signal Transduction (sinyal iletimi)
- Second Messenger Systems (cAMP, Ca2+, IP3)
- Metabolic Sensing (metabolik algılama)

Bu sistem hücrenin iç durumunu (interoception) algılar ve
uygun davranış durumunu belirler.
"""

class BehavioralState:
    # Durum sabitleri
    THREATENED = "THREATENED"  # Tehdit var, kaç
    HUNGRY = "HUNGRY"          # Aç, besin ara
    FULL = "FULL"              # Tok, besini bypass et
    IDLE = "IDLE"              # Boşta, rastgele dolaş

    def __init__(self):
        self.current_state = self.IDLE
        self.previous_state = self.IDLE

        # Eşik değerleri
        self.hunger_threshold = 0.7      # Enerji bu oranın altındaysa aç
        self.full_threshold = 0.95       # Enerji bu oranın üstündeyse tok

    def evaluate(self, organism, nearby_threats, scent_detected):
        """
        Hücrenin iç ve dış durumunu değerlendirip uygun state döndürür.

        Args:
            organism: Hücre
            nearby_threats: Yakındaki tehditler
            scent_detected: Koku algılandı mı? (direction veya None)

        Öncelik sırası:
        1. THREATENED - Tehdit varsa her şeyi bırak, kaç
        2. HUNGRY - Aç ve koku varsa, kokuyu takip et
        3. FULL - Tok veya sindirim doluysa, besini bypass et
        4. IDLE - Hiçbiri yoksa rastgele dolaş
        """
        self.previous_state = self.current_state

        # 1. TEHDİT KONTROLÜ (en yüksek öncelik)
        if nearby_threats and len(nearby_threats) > 0:
            self.current_state = self.THREATENED
            return self.current_state

        # 2. İÇ DURUM ALGILA (Interoception)
        energy_ratio = organism.energy / organism.max_energy if organism.max_energy > 0 else 1.0

        # Cytoplasm doluluk kontrolü
        cytoplasm_full = False
        if hasattr(organism, 'body') and hasattr(organism.body, 'logic'):
            cytoplasm = organism.body.logic
            # Sindirilecek besin var mı veya kapasite dolu mu?
            if hasattr(cytoplasm, 'food_queue'):
                cytoplasm_full = len(cytoplasm.food_queue) >= getattr(cytoplasm, 'max_queue_size', 3)
            elif hasattr(cytoplasm, 'digesting_food') and cytoplasm.digesting_food is not None:
                # Şu an sindirim yapılıyorsa da "meşgul" say
                cytoplasm_full = True

        # 3. DURUM BELİRLE
        # Öncelik: Koku algılandıysa ve sitoplazm müsaitse, enerji yüksek olsa bile koku takibi yap
        if scent_detected and not cytoplasm_full:
            # Koku var ve alabiliriz - kokuyu takip et
            self.current_state = self.HUNGRY
        elif cytoplasm_full:
            # Sindirim meşgul - besin aramaya gerek yok
            self.current_state = self.FULL
        elif energy_ratio >= self.full_threshold:
            # Tok ve koku yok - rastgele dolaş
            self.current_state = self.IDLE
        elif energy_ratio < self.hunger_threshold:
            # Aç ama koku yok - rastgele dolaş (koku arıyor)
            self.current_state = self.IDLE
        else:
            # Normal durum
            self.current_state = self.IDLE

        return self.current_state

    def should_seek_food(self):
        """Besin aramalı mı?"""
        return self.current_state == self.HUNGRY

    def should_flee(self):
        """Kaçmalı mı?"""
        return self.current_state == self.THREATENED

    def should_wander(self):
        """Rastgele dolaşmalı mı?"""
        return self.current_state in (self.IDLE, self.FULL)

    def state_changed(self):
        """Durum değişti mi?"""
        return self.current_state != self.previous_state

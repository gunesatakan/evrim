class MechanoDanger:
    def __init__(self):
        # Tehdit UID'si -> İlk Tespit Mesafesi
        self.detected_threats = {}

    def analyze_urgency(self, nearby_threats, current_pos):
        """
        Duyulan tehditlerin mesafelerini analiz eder ve 
        kalsiyum deşarjı için gerekli 'Aciliyet Çarpanını' (Boost) döner.
        """
        max_urgency = 1.0
        
        # O an duyulabilen tehditlerin UID'lerini topla
        active_uids = {k.uid for k in nearby_threats}
        
        # 1. TEMİZLİK: Artık duyulmayan tehditlerin takibini bırak
        uids_to_remove = [uid for uid in self.detected_threats if uid not in active_uids]
        for uid in uids_to_remove:
            del self.detected_threats[uid]

        # 2. HESAPLAMA
        for k in nearby_threats:
            dist = current_pos.distance_to(k.pos)
            
            # İlk tespit
            if k.uid not in self.detected_threats:
                self.detected_threats[k.uid] = dist
            
            initial_dist = self.detected_threats[k.uid]
            if initial_dist > 0:
                # Oran: Güncel / İlk
                # Yaklaştıkça oran 0'a gider -> Boost 3'e gider
                ratio = min(1.0, dist / initial_dist)
                urgency = 1.0 + (1.0 - ratio) * 2.0
                
                if urgency > max_urgency:
                    max_urgency = urgency
        
        return max_urgency

from .mechano_danger import MechanoDanger

class MechanoreceptorLogic:
    def __init__(self, size=1.0):
        self.size = size 
        self.danger_sense = MechanoDanger()

    @property
    def sensitivity(self):
        return self.size * 30

    def update_stats(self, delta_size=0):
        self.size += delta_size

    def grow(self):
        self.size += 0.2
        
    def is_hearing(self, self_pos, target_pos):
        """Bu kulak hedefi duyuyor mu?"""
        # Organın konumu self_pos değil, dışarıdaki attachment point olmalı.
        # Ancak Logic sınıfı konumu bilmez (konum View/Lego sınıfında).
        # Bu yüzden mesafeyi Organism (Lego) sınıfında hesaplayıp buraya 'dist' olarak atmak daha doğru olur.
        # Şimdilik basitçe menzil kontrolü yapıyoruz.
        return True # Asıl kontrol Organism içinde yapılacak

    def check_urgency(self, nearby_threats, current_pos):
        return self.danger_sense.analyze_urgency(nearby_threats, current_pos)

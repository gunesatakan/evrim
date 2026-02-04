import math

class PhotoreceptorAngle:
    def __init__(self, angle=0.75):
        # Radyan cinsinden görüş açısı
        self.value = angle 

    def grow(self, delta=0.05):
        """Görüş açısını genişletir."""
        self.value += delta
        # Maksimum 180 derece (math.pi radyan) ile sınırla
        if self.value > math.pi:
            self.value = math.pi

    def get_degrees(self):
        """Açıyı derece cinsinden döner."""
        return math.degrees(self.value)

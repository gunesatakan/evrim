from .logic_electrone_transport import ElectronTransportChain

class MembraneLogic:
    def __init__(self):
        # Kalsiyum Patlaması Sistemi
        self.calcium_boost = 1.0
        # Enerji Üretim Sistemi (ETC)
        self.etc = ElectronTransportChain(efficiency=1.0)

    @property
    def energy_regen(self):
        return self.etc.efficiency

    def set_calcium_signal(self, urgency_level):
        """Mekanoreseptörden gelen aciliyet sinyalini uygula."""
        self.calcium_boost = urgency_level
    
    def grow_etc(self):
        self.etc.grow()
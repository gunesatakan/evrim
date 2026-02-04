import game_settings

class ElectronTransportChain:
    def __init__(self, efficiency=None):
        # Enerji üretim verimliliği (birim/sn)
        self.efficiency = efficiency if efficiency is not None else game_settings.ENERGY_REGEN_BASE

    def grow(self):
        """Zincirdeki kompleks sayısını artırarak verimliliği yükselt."""
        self.efficiency += game_settings.GROW_ENERGY_REGEN
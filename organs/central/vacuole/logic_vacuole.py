import game_settings

class VacuoleLogic:
    def __init__(self, size=1.0):
        self.size = size 
        self.area = game_settings.VACUOLE_AREA * self.size

    @property
    def capacity(self):
        return self.area * game_settings.VACUOLE_ENERGY_MULTI

    @property
    def base_energy_cost(self):
        """Depoyu dolu tutmanin (osmotik dengenin) bedeli."""
        return self.area * game_settings.COST_VACUOLE

    def grow(self):
        self.size += game_settings.GROW_MAX_ENERGY
        self.area = game_settings.VACUOLE_AREA * self.size
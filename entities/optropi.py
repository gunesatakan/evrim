import math
import game_settings
from entities.organism import Organism
from organs.receptors.Photoreceptor.photoreceptor import Photoreceptor
from organs.receptors.Mechanoreceptor.mechanoreceptor import Mechanoreceptor
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.cilia.cilia import Cilia
from organs.central.cytoplasm.cytoplasm import Cytoplasm
from organs.peripheral.membrane.membrane import Membrane
from organs.central.vacuole.vacuole import Vacuole
from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
from organs.central.ribosome.ribosome import Ribosome

class Optropi(Organism):
    def __init__(self, index, x, y, color):
        super().__init__(index, x, y, color)

        # Load config from settings
        ent_id = f"optropi_{index}"
        cfg = game_settings.ENTITY_CONFIGS.get(ent_id, game_settings.ENTITY_CONFIGS["optropi_0"])

        # Özel organ konfigürasyonu var mı kontrol et
        organs_config = game_settings.get_entity_organs(ent_id)

        if organs_config:
            # Kaydedilmiş organ konfigürasyonunu kullan
            self._load_organs_from_config(organs_config, cfg)
        else:
            # Varsayılan organ yapılandırması
            self._load_default_organs(cfg)

        self.direction_memory.capacity = cfg["memory"]
        self.recalculate_physics()
        self.energy = self.max_energy  # Tam enerji ile başla

        # Optimal ön hesapla ve logla
        self._update_optimal_front()
        self._log_optimal_front()

        # DEBUG: Turuncu için motor debug aktif (index 3 = Orange)
        if self.index == 3:
            self.debug_motor = True
            print(f"[DEBUG] Orange (index={self.index}) debug modu aktif!")

    def _load_organs_from_config(self, organs_config, cfg):
        """Kaydedilmiş organ konfigürasyonundan organları yükle."""
        for organ_cfg in organs_config:
            organ_type = organ_cfg["type"]
            angle = organ_cfg.get("angle", 0)

            if organ_type == "Cytoplasm":
                self.add_organ(Cytoplasm(size=organ_cfg.get("size", cfg["cytoplasm"])))
            elif organ_type == "Ribosome":
                ribo = Ribosome()
                ribo.logic.area = cfg["ribosome_area"]
                self.add_organ(ribo)
            elif organ_type == "Cytoskeleton":
                self.add_organ(Cytoskeleton())
            elif organ_type == "Vacuole":
                vac = Vacuole(size=organ_cfg.get("size", 1.0))
                vac.logic.area = cfg["vacuole_area"]
                self.add_organ(vac)
            elif organ_type == "Photoreceptor":
                self.add_organ(Photoreceptor(
                    attachment_angle=angle,
                    range=organ_cfg.get("range", cfg["vision_range"]),
                    angle=organ_cfg.get("angle_val", math.radians(cfg["vision_angle"]))
                ))
            elif organ_type == "Mechanoreceptor":
                # sensitivity = size * 30, config'den sensitivity geliyor
                sensitivity = organ_cfg.get("sensitivity", cfg["sound"])
                self.add_organ(Mechanoreceptor(
                    attachment_angle=angle,
                    size=sensitivity / 30.0
                ))
            elif organ_type == "Chemoreceptor":
                self.add_organ(Chemoreceptor(
                    attachment_angle=angle,
                    length=organ_cfg.get("length", cfg["smell"])
                ))
            elif organ_type == "Flagella":
                self.add_organ(Flagella(
                    attachment_angle=angle,
                    length=organ_cfg.get("length", cfg["flagella"])
                ))
            elif organ_type == "Cilia":
                self.add_organ(Cilia(
                    attachment_angle=angle,
                    length=organ_cfg.get("length", cfg["cilia"])
                ))
            elif organ_type == "Membrane":
                self.add_organ(Membrane())

    def _load_default_organs(self, cfg):
        """Varsayılan organ yapılandırmasını yükle."""
        self.add_organ(Cytoplasm(size=cfg["cytoplasm"]))

        # Ribosome with specific area
        ribo = Ribosome()
        ribo.logic.area = cfg["ribosome_area"]
        self.add_organ(ribo)

        self.add_organ(Cytoskeleton())

        # Vacuole with specific area
        self.vacuole = Vacuole(size=1.0)
        self.vacuole.logic.area = cfg["vacuole_area"]
        self.add_organ(self.vacuole)

        self.eye_organ = Photoreceptor(
            attachment_angle=0,
            range=cfg["vision_range"],
            angle=math.radians(cfg["vision_angle"]),
            base_hue=0.0
        )
        self.add_organ(self.eye_organ)

        self.add_organ(Mechanoreceptor(attachment_angle=math.radians(45), size=cfg["sound"]/30.0))
        self.add_organ(Mechanoreceptor(attachment_angle=math.radians(-45), size=cfg["sound"]/30.0))

        self.add_organ(Flagella(attachment_angle=math.radians(180), length=cfg["flagella"]))

        # Çoklu Cilia - pozisyon bazlı dönüş kontrolü için
        self.add_organ(Cilia(attachment_angle=math.radians(60), length=cfg["cilia"]))
        self.add_organ(Cilia(attachment_angle=math.radians(120), length=cfg["cilia"]))
        self.add_organ(Cilia(attachment_angle=math.radians(-60), length=cfg["cilia"]))
        self.add_organ(Cilia(attachment_angle=math.radians(-120), length=cfg["cilia"]))

        self.add_organ(Chemoreceptor(attachment_angle=math.radians(135), length=cfg["smell"]))
        self.add_organ(Chemoreceptor(attachment_angle=math.radians(-135), length=cfg["smell"]))
        self.add_organ(Membrane())

    def _log_optimal_front(self):
        """Başlangıçta optimal ön bilgisini logla."""
        angle_deg = math.degrees(self.optimal_front_angle)
        # Motor organları say
        flagella_count = sum(1 for o in self.organs if isinstance(o, Flagella))
        cilia_count = sum(1 for o in self.organs if isinstance(o, Cilia))

        # Renk ismini config'den al
        ent_id = f"optropi_{self.index}"
        cfg = game_settings.ENTITY_CONFIGS.get(ent_id, game_settings.ENTITY_CONFIGS["optropi_0"])
        color_name = cfg.get("name", f"Optropi {self.index}")

        print(f"[{color_name}] Optimal Ön: {angle_deg:.1f}° | "
              f"Max Hız: {self.optimal_front_speed:.2f} | "
              f"Motorlar: {flagella_count} flagella, {cilia_count} cilia")
import math
import game_settings
from entities.entity import RED
from entities.organism import Organism, Genome, Morphology
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
from organs.peripheral.weapons.weapons import WEAPON_CLASSES, Stylet


class Kaotropi(Organism):
    """Tepe avcı — artık gerçek bir hücre.

    Eskiden `Entity` idi: düz çizgide gider, duvardan seker, dokunduğuna
    anında ölüm verirdi. Artık diğer hücreler gibi organları, enerjisi, zar
    bütünlüğü ve genomu var; besin yer, gelişir, bölünür ve ölebilir.

    Farkı büyüklüğü ve sağlamlığı: geniş gövde, güçlü motor, uzun görüş.
    Kimseden kaçmaz (tehdit listesi boş verilir), herkesi avlar.
    """

    def __init__(self, index, x, y):
        super().__init__(index, x, y, RED)

        cfg = game_settings.ENTITY_CONFIGS["kaotropi"]
        organs_config = game_settings.get_entity_organs("kaotropi")
        # KAYIT YOKLUGU ile KAYDEDILMIS BOSLUK ayri seylerdir.
        # Once `if organs_config:` yaziyordu; bos liste yanlis sayilip
        # varsayilan takim kuruluyordu. Yani launcher'da butun organlari
        # silmek de hicbir ise yaramiyordu - varlik yine 15 organla
        # doguyordu.
        if organs_config is not None:
            self._load_organs_from_config(organs_config, cfg)
        else:
            self._load_default_organs(cfg)

        self.direction_memory.capacity = cfg["memory"]
        self.davranisi_ayardan_kur(cfg)
        self.temel_yapiyi_tamamla()
        self.recalculate_physics()
        self.genome = Genome.from_organism(self)
        self.morphology = Morphology.from_organism(self)
        # Kurucu deposunun bir kismiyla dogar (BASLANGIC_ENERJI_ORANI).
        self.energy = self.max_energy * max(0.0, min(1.0, float(
            game_settings.BASLANGIC_ENERJI_ORANI)))
        self._update_optimal_front()

    # Trail renklendirmesi ve tehdit filtreleri "kaotropi" ön ekine bakar
    @property
    def uid(self):
        return f"kaotropi_{self.index}"

    def _load_default_organs(self, cfg):
        self.add_organ(Cytoplasm(size=cfg["cytoplasm"]))

        ribo = Ribosome()
        ribo.logic.area = cfg["ribosome_area"]
        self.add_organ(ribo)

        self.add_organ(Cytoskeleton())

        vac = Vacuole(size=1.0)
        vac.logic.area = cfg["vacuole_area"]
        self.add_organ(vac)
        self.vacuole = vac

        self.add_organ(Photoreceptor(
            attachment_angle=0,
            range=cfg["vision_range"],
            angle=math.radians(cfg["vision_angle"]),
            base_hue=0.0))

        self.add_organ(Mechanoreceptor(attachment_angle=math.radians(45),
                                       size=cfg["sound"] / 30.0))
        self.add_organ(Mechanoreceptor(attachment_angle=math.radians(-45),
                                       size=cfg["sound"] / 30.0))

        self.add_organ(Flagella(attachment_angle=math.radians(180),
                                length=cfg["flagella"]))
        self.add_organ(Cilia(attachment_angle=math.radians(70), length=cfg["cilia"]))
        self.add_organ(Cilia(attachment_angle=math.radians(-70), length=cfg["cilia"]))

        self.add_organ(Chemoreceptor(attachment_angle=math.radians(140),
                                     length=cfg["smell"]))
        self.add_organ(Chemoreceptor(attachment_angle=math.radians(-140),
                                     length=cfg["smell"]))
        # Tepe avcinin silahi: stilet (temas, mekanik). Eskiden kaotropi
        # silahsiz oldugu halde dokundugunu oldururdu - simdi herkes gibi
        # gercek bir organla saldiriyor ve davranis genomu "saldir" demezse
        # ates edemiyor.
        # Öne yakın ama GÖZDEN AYRI bir açı: ikisi de 0°'da olunca
        # stilet gözün üstünden çıkıyor gibi görünüyordu.
        self.add_organ(Stylet(attachment_angle=math.radians(25), power=2.0))
        self.add_organ(Membrane())

    def _load_organs_from_config(self, organs_config, cfg):
        """Launcher'da düzenlenmiş organ planından kur."""
        for oc in organs_config:
            t = oc["type"]
            angle = oc.get("angle", 0)
            if t == "Cytoplasm":
                self.add_organ(Cytoplasm(size=oc.get("size", cfg["cytoplasm"])))
            elif t == "Ribosome":
                ribo = Ribosome(); ribo.logic.area = cfg["ribosome_area"]
                self.add_organ(ribo)
            elif t == "Cytoskeleton":
                self.add_organ(Cytoskeleton())
            elif t == "Vacuole":
                vac = Vacuole(size=oc.get("size", 1.0))
                vac.logic.area = cfg["vacuole_area"]
                self.add_organ(vac)
            elif t == "Photoreceptor":
                self.add_organ(Photoreceptor(
                    attachment_angle=angle,
                    range=oc.get("range", cfg["vision_range"]),
                    angle=oc.get("angle_val", math.radians(cfg["vision_angle"]))))
            elif t == "Mechanoreceptor":
                self.add_organ(Mechanoreceptor(
                    attachment_angle=angle,
                    size=oc.get("sensitivity", cfg["sound"]) / 30.0))
            elif t == "Chemoreceptor":
                self.add_organ(Chemoreceptor(
                    attachment_angle=angle, length=oc.get("length", cfg["smell"])))
            elif t == "Flagella":
                self.add_organ(Flagella(
                    attachment_angle=angle, length=oc.get("length", cfg["flagella"])))
            elif t == "Cilia":
                self.add_organ(Cilia(
                    attachment_angle=angle, length=oc.get("length", cfg["cilia"])))
            elif t == "Membrane":
                mem = Membrane()
                lg = mem.logic
                if "integrity" in oc:
                    lg.max_integrity = oc["integrity"]
                    lg.integrity = lg.max_integrity
                for _d in ("wall", "outer", "capsule", "efflux", "repair",
                           "slip", "mucus", "slayer"):
                    if _d in oc:
                        setattr(lg, _d, oc[_d])
                # KATMAN VARLIGI: kaydedilmemisse VAR sayilir - eski
                # kayitlar bes katmanla dogsun.
                for _v in ("var_mucus", "var_capsule", "var_slayer", "var_wall"):
                    if _v in oc:
                        setattr(lg, _v, bool(oc[_v]))
                # KATMAN KALINLIKLARI: kaydedilmemisse varsayilan olgun
                # degerler kalir (eski kayitlar bozulmasin).
                _kal = oc.get("kalinlik")
                if isinstance(_kal, dict):
                    for _k, _v2 in _kal.items():
                        lg.katman_kalinligi_ayarla(_k, _v2)
                self.add_organ(mem)
            elif t in WEAPON_CLASSES:
                _w = WEAPON_CLASSES[t](
                    attachment_angle=angle, power=oc.get("power", 1.0))
                for _a in ("carrier", "payload", "marker"):
                    if _a in oc:
                        try:
                            setattr(_w.logic, _a, int(oc[_a]))
                        except Exception:
                            pass
                self.add_organ(_w)

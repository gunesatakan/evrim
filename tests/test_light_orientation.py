"""Fotoreseptor -> davranis -> hareket yonu regresyon testleri."""

import copy
import math
import os
import random
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import game_settings
from entities.optropi import Optropi
from entities.organism import Organism
from organs.central.cytoplasm.cytoplasm import Cytoplasm
from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
from organs.central.ribosome.ribosome import Ribosome
from organs.central.vacuole.vacuole import Vacuole
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.membrane.membrane import Membrane
from organs.receptors.Photoreceptor.logic_photoreceptor import PhotoreceptorLogic
from organs.receptors.Photoreceptor.photoreceptor import Photoreceptor
from systems import isik
from systems.protein_systems.short_protein_memory.direction_memory import (
    DirectionMemorySystem,
)
from organs.central.cytoskeleton.danger_transmission.danger_transmission import (
    DangerTransmission,
)

V = pygame.Vector2
DT = 1.0 / 30.0


def _gozlu_hucre(goz_acilari, bakis=V(1.0, 0.0)):
    """Kamcili, istenen acilarda gozleri olan ve her siddette isiga
    yaklasan hucre (400, 400) noktasinda."""
    o = Organism(1, 400, 400, (200, 200, 200))
    for organ in (Membrane(), Cytoplasm(size=2.0), Cytoskeleton(),
                  Vacuole(size=1.0), Ribosome(),
                  Flagella(attachment_angle=math.pi, length=10.0)):
        o.add_organ(organ)
    for aci in goz_acilari:
        o.add_organ(Photoreceptor(attachment_angle=math.radians(aci), range=30.0,
                                  angle=game_settings.VISION_ANGLE_BASE))
    o.pos = V(400.0, 400.0)
    o.direction = V(bakis).normalize()
    o.recalculate_physics()
    b = o.behavior
    b.scent_bands = [0.0] * len(b.scent_bands)
    b.ses_bands = [0.0] * len(b.ses_bands)
    b.kin_response = 0.0
    b.isik_bands = [1.0] * len(b.isik_bands)
    return o


class GozOlcumuTests(unittest.TestCase):
    """Goz yalnizca uzerine dusen isigi olcer; yonu hucre cikarir."""

    def test_isiga_bakan_goz_parlak_arkasi_donuk_okur(self):
        lg = PhotoreceptorLogic(range=30.0, angle=game_settings.VISION_ANGLE_BASE)
        yon = game_settings.ISIK_YONLULUK * lg.yon_keskinligi()
        self.assertAlmostEqual(lg.olc(0.4, 1.0), 0.4 * (1.0 + yon))
        self.assertAlmostEqual(lg.olc(0.4, 0.0), 0.4)
        self.assertAlmostEqual(lg.olc(0.4, -1.0), 0.4 * (1.0 - yon))
        self.assertEqual(lg.olc(0.0, 1.0), 0.0)

    def test_genis_goz_yonu_bulandirir_ama_az_gurultuyle_okur(self):
        dar = PhotoreceptorLogic(range=30.0, angle=math.radians(10.0))
        genis = PhotoreceptorLogic(range=30.0, angle=math.radians(120.0))
        self.assertGreater(dar.yon_keskinligi(), genis.yon_keskinligi())
        random.seed(4)

        def sapma(lg):
            x = [lg.olc(0.05, 0.0, DT) for _ in range(3000)]
            m = sum(x) / len(x)
            return math.sqrt(sum((v - m) ** 2 for v in x) / len(x)) / m

        self.assertGreater(sapma(dar), 2.0 * sapma(genis))


class GozleYonBulmaTests(unittest.TestCase):
    def setUp(self):
        self._yama = [patch.object(game_settings, k, v) for k, v in (
            ("BEHAVIOR_ENABLED", True), ("ISIK_GURULTU", 0.0),
            ("HARITA_ISIKLARI", [])) ]
        for p in self._yama:
            p.start()
        random.seed(2)

    def tearDown(self):
        for p in self._yama:
            p.stop()

    def _isik(self, x, y):
        game_settings.HARITA_ISIKLARI = [(x, y, 1.0, 800.0)]

    def test_tek_goz_isigin_yonunu_hazir_bilmez(self):
        # Isik arkada. Eskiden tek goz bile isigin tam yonunu aliyor ve
        # hucre ilk karede geri donuyordu.
        self._isik(100.0, 400.0)
        o = _gozlu_hucre((0.0,))
        surus, _ = o.perceive_and_decide([], DT)
        self.assertIsNotNone(surus)
        self.assertGreater(surus.normalize().dot(V(1.0, 0.0)), 0.99)

    def test_uc_goz_isigin_yonunu_gozlerin_farkindan_bulur(self):
        self._isik(400.0, 100.0)                   # isik yukarida
        for bakis_derece in (0.0, 70.0, 160.0, 250.0):
            o = _gozlu_hucre((0.0, 120.0, 240.0), V(1.0, 0.0).rotate(bakis_derece))
            surus, _ = o.perceive_and_decide([], DT)
            sapma = abs(surus.angle_to(V(0.0, -1.0)))
            sapma = min(sapma, 360.0 - sapma)
            self.assertLess(sapma, 15.0, bakis_derece)

    def test_iki_goz_isigin_hangi_yanda_oldugunu_bulur(self):
        self._isik(400.0, 100.0)                   # hucrenin solunda (ekranda yukari)
        o = _gozlu_hucre((60.0, -60.0))
        surus, _ = o.perceive_and_decide([], DT)
        self.assertGreater(surus.normalize().dot(V(0.0, -1.0)), 0.9)
        # Isik tam arkada: iki goz ayni okur, yon cikmaz; hucre yoluna devam.
        self._isik(100.0, 400.0)
        o = _gozlu_hucre((60.0, -60.0))
        surus, _ = o.perceive_and_decide([], DT)
        self.assertGreater(surus.normalize().dot(V(1.0, 0.0)), 0.99)

    def test_tek_goz_kararinca_doner_aydinlaninca_yoluna_devam_eder(self):
        o = _gozlu_hucre((0.0,))
        eksen = [(V(1.0, 0.0), 0.0)]
        pencere = int(round(game_settings.ISIK_PENCERE / DT))

        def pencere_gec(okuma):
            yon = None
            for _ in range(pencere):
                yon = o._isik_yonu([(eksen[0][0], okuma)], okuma, 1.0, DT)
            return V(yon)

        ilk = pencere_gec(0.30)
        aydinlanan = pencere_gec(0.40)
        self.assertAlmostEqual(aydinlanan.angle_to(ilk), 0.0)
        donen = pencere_gec(0.20)
        self.assertNotAlmostEqual(abs(donen.angle_to(aydinlanan)), 0.0, places=3)
        # Kacan hucre icin tersi: aydinlaninca doner.
        o2 = _gozlu_hucre((0.0,))
        for _ in range(pencere):
            ilk2 = V(o2._isik_yonu([(V(1.0, 0.0), 0.3)], 0.3, -1.0, DT))
        for _ in range(pencere):
            son2 = V(o2._isik_yonu([(V(1.0, 0.0), 0.5)], 0.5, -1.0, DT))
        self.assertNotAlmostEqual(abs(son2.angle_to(ilk2)), 0.0, places=3)


class LightFieldTests(unittest.TestCase):
    def test_direction_follows_local_intensity_gradient(self):
        # Dogudaki kaynak daha yakin; kaynak merkezlerini mesafeyle
        # carpip ortalamak kuzeydeki uzak kaynagi yanlislikla baskin
        # cikarirdi. Yerel gradyan doguyu gostermelidir.
        sources = [
            (100.0, 0.0, 1.0, 1000.0),
            (0.0, 200.0, 1.0, 1000.0),
        ]

        intensity, direction = isik.siddet_ve_yon(0.0, 0.0, sources)

        self.assertGreater(intensity, 0.0)
        self.assertGreater(direction.x, direction.y)
        self.assertAlmostEqual(direction.length(), 1.0, places=6)


class PhototaxisTests(unittest.TestCase):
    def test_behavior_direction_does_not_require_visible_prey(self):
        organism = SimpleNamespace(
            pos=pygame.Vector2(600.0, 400.0),
            organs=[],
            energy=1.0,
            max_energy=1.0,
            # Isik sosyal bir uyaran degildir. Besin kokusu cok guclu olsa
            # bile sosyal_oncelik kontrolu fototaksiyi kesmemeli.
            behavior=SimpleNamespace(sosyali_sec=lambda _scent: False),
        )
        transmission = DangerTransmission()

        with patch.object(game_settings, "BEHAVIOR_ENABLED", True):
            direction, kind, _vector = transmission.process_signals(
                1.0 / 60.0,
                organism,
                [],
                DirectionMemorySystem(),
                100.0,
                prey_dir=None,
                behavior_response=1.0,
                behavior_dir=pygame.Vector2(1.0, 0.0),
                behavior_is_social=False,
            )

        self.assertEqual(kind, "HUNT")
        self.assertAlmostEqual(direction.x, 1.0)
        self.assertAlmostEqual(direction.y, 0.0)

    def test_photoreceptor_light_reaches_behavior_direction(self):
        configs = copy.deepcopy(game_settings.DEFAULT_ENTITY_CONFIGS)
        with (
            patch.object(game_settings, "ENTITY_CONFIGS", configs),
            patch.object(game_settings, "WORLD_SCALE", 1.0),
            patch.object(game_settings, "BEHAVIOR_ENABLED", True),
            patch.object(game_settings, "SESSIZ", True),
            patch.object(game_settings, "HARITA_ISIKLARI",
                         [(800.0, 400.0, 1.0, 800.0)]),
        ):
            cell = Optropi(0, 400.0, 400.0, (255, 0, 255))
            cell.direction = pygame.Vector2(1.0, 0.0)
            cell._alici_noktalari = ()
            cell.behavior.isik_cuts = [0.0, 25.0, 50.0, 75.0]
            cell.behavior.isik_bands = [1.0] * 5

            drive, _strongest = cell.perceive_and_decide([])

            self.assertIsNotNone(drive)
            self.assertGreater(drive.x, 0.0)
            self.assertGreater(cell.current_response, 0.0)

            cell.cytoskeleton.update(
                1.0 / 60.0,
                cell,
                [],
                cell.direction_memory,
                0.0,
                prey_dir=None,
                behavior_response=cell.current_response,
                behavior_dir=drive.normalize(),
                behavior_is_social=False,
            )
            self.assertGreater(cell.target_movement.x, 0.0)


if __name__ == "__main__":
    unittest.main()

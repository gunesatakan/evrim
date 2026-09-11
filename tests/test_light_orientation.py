"""Fotoreseptor -> davranis -> hareket yonu regresyon testleri."""

import copy
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import game_settings
from entities.optropi import Optropi
from systems import isik
from systems.protein_systems.short_protein_memory.direction_memory import (
    DirectionMemorySystem,
)
from organs.central.cytoskeleton.danger_transmission.danger_transmission import (
    DangerTransmission,
)


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

"""Silah basligi, soketi ve kamera donusumu regresyon testleri."""

import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import lab
from entities.organism import Organism
from organs.peripheral.weapons.weapons import Stylet


class _Cell:
    center = pygame.Vector2(100, 100)
    outer_r = 12.0
    hiz_olcegi = 0.2

    @staticmethod
    def active():
        return []


class _WeaponOwner:
    def __init__(self):
        self.pos = pygame.Vector2(10, 20)
        self.direction = pygame.Vector2(1, 0)
        self.radius = 30.0

    def weapon_anchor(self):
        return self.pos + self.direction * self.radius


class WeaponRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 240))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_shot_scale_and_reach_belong_to_source(self):
        cell = _Cell()
        shot = lab.Shot(
            cell, pygame.Vector2(80, 100), pygame.Vector2(1, 0),
            lab.CARRIERS[5], lab.PAYLOADS[1], lab.MARKERS[0], 5,
            source_scale=0.8, reach=37.5)

        self.assertEqual(shot.vs, 0.8)
        self.assertEqual(shot.source_scale, 0.8)
        self.assertEqual(shot.reach, 37.5)
        self.assertEqual(shot.target_scale, 0.2)

    def test_shot_attachment_origin_follows_live_weapon(self):
        owner = _WeaponOwner()
        shot = lab.Shot(
            _Cell(), pygame.Vector2(80, 100), pygame.Vector2(1, 0),
            lab.CARRIERS[5], lab.PAYLOADS[1], lab.MARKERS[0], 5,
            source_scale=0.8)
        shot.sahip = owner
        shot.origin = pygame.Vector2(-100, -100)

        owner.pos = pygame.Vector2(40, 50)
        self.assertEqual(shot.attachment_origin(), pygame.Vector2(70, 50))
        shot.refresh_origin()
        self.assertEqual(shot.origin, pygame.Vector2(70, 50))

    def test_shot_draws_root_and_head_through_same_camera_transform(self):
        owner = _WeaponOwner()
        shot = lab.Shot(
            _Cell(), pygame.Vector2(90, 100), pygame.Vector2(1, 0),
            lab.CARRIERS[3], lab.PAYLOADS[0], lab.MARKERS[0], 3,
            source_scale=0.8)
        shot.sahip = owner
        transform = lambda v: (v.x * 4 + 11, v.y * 4 - 3)

        with patch("pygame.draw.line") as line:
            shot.draw(pygame.Surface((640, 480)), transform, 2.0)

        first = line.call_args_list[0].args
        self.assertEqual(first[2], (171, 77))
        self.assertEqual(first[3], (371, 397))

    def test_zoom_render_uses_one_global_transform_for_shots(self):
        spy = SimpleNamespace(draw=lambda *args: setattr(spy, "args", args))
        organism = object.__new__(Organism)
        organism.pos = pygame.Vector2(100, 80)
        organism.atislar = [spy]
        transform = lambda v: (v.x * 4 + 11, v.y * 4 - 3)

        organism.atislari_ciz(
            pygame.Surface((320, 240)), olcek=4.0, donustur=transform)

        self.assertIs(spy.args[1], transform)
        self.assertEqual(spy.args[2], 4.0)

    def test_active_weapon_draws_socket_instead_of_second_full_head(self):
        weapon = Stylet()
        weapon.mermi = SimpleNamespace(dead=False, bitti=False)
        parent = SimpleNamespace(
            pos=pygame.Vector2(80, 100), direction=pygame.Vector2(1, 0),
            radius=20.0, bound_target=object())
        surface = pygame.Surface((320, 240))

        with (
            patch("organs.peripheral.weapons.weapons.draw_weapon") as full,
            patch("organs.peripheral.weapons.weapons.draw_weapon_socket") as socket,
        ):
            weapon.draw(surface, parent)

        full.assert_not_called()
        socket.assert_called_once()


if __name__ == "__main__":
    unittest.main()

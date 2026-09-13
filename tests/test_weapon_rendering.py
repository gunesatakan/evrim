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
from organs.peripheral.weapons.weapons import Stylet, Harpoon
from organs.peripheral.weapons.geometry import carrier_scale


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

    def test_harpoon_growth_does_not_outgrow_cell(self):
        for radius in (5.0, 30.0, 300.0):
            sizes = [66 * carrier_scale(radius, power, 3) for power in (0.1, 1, 10, 1000)]
            self.assertEqual(sizes, sorted(sizes))
            self.assertLessEqual(max(sizes), radius * 0.6)
            self.assertAlmostEqual(carrier_scale(radius * 4, 1000, 3),
                                   4 * carrier_scale(radius, 1000, 3))

    def _t6ss_sahnesi(self, hedef_y=0.0):
        import math
        import random
        from systems.world import Dunya
        from organs.registry import organ_class
        random.seed(1)
        dunya = Dunya()
        saldirgan, hedef = dunya.hucreler[:2]
        organ = organ_class('Harpoon')()
        organ.attachment_angle = 0.0
        saldirgan.add_organ(organ)
        uretici = organ_class('Toxin')()
        uretici.logic.payload = 6
        uretici.logic.stok = float(lab.STOCK_MAX)
        uretici.attachment_angle = math.pi
        saldirgan.add_organ(uretici)
        saldirgan.recalculate_physics()
        saldirgan.direction.update(1, 0)
        saldirgan.pos.update(600, 400)
        hedef.pos.update(600 + saldirgan.radius + hedef.radius + 2.0, 400 + hedef_y)
        for hucre in (saldirgan, hedef):
            hucre.onceki_pos = pygame.Vector2(hucre.pos)
            hucre.energy = 900.0
            hucre.molekuller = []
        saldirgan.attack_targets = {id(hedef)}
        return saldirgan, hedef, organ

    def test_t6ss_contracts_in_one_frame_and_tube_is_not_retracted(self):
        saldirgan, hedef, organ = self._t6ss_sahnesi()
        saldirgan.fire_weapons(1 / 30.0, [hedef])
        # Kilif tek karede kasildi: tup organdan ayrildi, kilif yeniden kuruluyor.
        self.assertIsNone(organ.mermi)
        self.assertFalse(organ.logic.ready)
        self.assertGreaterEqual(organ.logic.cooldown, 1.0)
        birakilan = len(hedef.molekuller)
        enkaz = getattr(organ, 'enkaz', None)
        if birakilan:
            self.assertIsNotNone(enkaz)
            self.assertFalse(hasattr(enkaz, 't6_phase'))
        for _ in range(30):
            saldirgan.mermileri_guncelle(1 / 30.0)
        # Yuk bir kez birakilir; enkaz cozunur ve kaybolur.
        self.assertEqual(len(hedef.molekuller) - birakilan, 0)
        self.assertIsNone(getattr(organ, 'enkaz', None))

    def test_t6ss_fires_only_when_its_axis_reaches_the_target(self):
        saldirgan, hedef, organ = self._t6ss_sahnesi(hedef_y=46.0)
        for _ in range(3):
            saldirgan.fire_weapons(1 / 30.0, [hedef])
        self.assertTrue(organ.logic.ready)
        self.assertIsNone(getattr(organ, 'enkaz', None))

    def test_t6ss_sheath_drawing_follows_rebuild(self):
        from organs.peripheral.weapons.view_weapons import draw_weapon
        yuzey = pygame.Surface((320, 240))
        cagri = {}
        for kurulum in (0.1, 0.6, 1.0):
            with patch("pygame.draw.polygon") as poligon, patch("pygame.draw.line") as cizgi:
                draw_weapon(yuzey, "Harpoon", pygame.Vector2(160, 120), pygame.Vector2(1, 0),
                            20.0, True, olcek=1.0, carrier=3, kurulum=kurulum)
            cagri[kurulum] = (poligon.call_count, cizgi.call_count)
        # Mizrak ucu (ucgen) ve ic tup yalnizca kilif tamamlaninca cizilir.
        self.assertGreater(cagri[1.0][0], cagri[0.6][0])
        self.assertGreater(cagri[1.0][1], cagri[0.6][1])

if __name__ == "__main__":
    unittest.main()

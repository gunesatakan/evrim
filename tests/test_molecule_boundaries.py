"""Molekul konumu ile molekul ciziminin zar sinirlarini korudugunu test eder.

Molekul artik GERCEK boyunda cizilir; zardan gecmemis bir molekulun
sitoplazmada gorunmemesini kirpma degil KONUM saglar: baglanan molekul
dairesi karsi yuzu asmayacak yere oturur, durdurulan molekul zarin dis
yuzune degerek durur.
"""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import lab


class _MembraneCell:
    center = pygame.Vector2(0.0, 0.0)
    core_r = 110.0
    outer_r = 123.5
    generation = 0

    def __init__(self):
        self.bagli = []

    @staticmethod
    def active():
        return [lab.default_layers()[-1]]

    @staticmethod
    def boundaries():
        return [123.5]

    def receive(self, mol):
        self.bagli.append(mol)


class MoleculeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 240))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_membrane_bound_molecule_does_not_hang_into_cytoplasm(self):
        cell = _MembraneCell()
        molecule = lab.Molecule(
            cell, pygame.Vector2(cell.outer_r + 20.0, 0.0), pygame.Vector2(), 7)
        with patch.object(lab, "insertion_p", return_value=1.0):
            self.assertTrue(molecule._bind(0, pygame.Vector2(cell.outer_r, 0.0)))

        self.assertEqual(molecule.state, "arrived")
        visible = molecule.cizim_yaricapi()
        self.assertAlmostEqual(visible, molecule.rad * molecule.vs)
        d = molecule.pos.distance_to(cell.center)
        self.assertGreaterEqual(d - visible, cell.core_r - 1e-6)
        self.assertLessEqual(d, cell.outer_r)

    def test_injected_surface_payload_remains_visible_inside(self):
        cell = _MembraneCell()
        molecule = lab.Molecule(
            cell, pygame.Vector2(60.0, 0.0), pygame.Vector2(), 1)
        molecule.injected = True

        self.assertAlmostEqual(
            molecule.cizim_yaricapi(), molecule.rad * molecule.vs)

    def test_surface_binder_sits_on_the_outer_face(self):
        cell = _MembraneCell()
        molecule = lab.Molecule(
            cell, pygame.Vector2(cell.outer_r + 20.0, 0.0), pygame.Vector2(), 1)
        self.assertTrue(molecule._bind(0, pygame.Vector2(cell.outer_r, 0.0)))

        d = molecule.pos.distance_to(cell.center)
        self.assertGreaterEqual(d - molecule.cizim_yaricapi(), cell.outer_r - 1e-6)

    def test_external_surface_payload_is_stopped_if_it_reaches_cytoplasm(self):
        cell = _MembraneCell()
        molecule = lab.Molecule(
            cell, pygame.Vector2(0.0, 0.0), pygame.Vector2(), 1)
        before = lab.KORUMA_TETIK

        molecule.update(0.0)

        self.assertEqual(molecule.state, "stuck")
        self.assertEqual(lab.KORUMA_TETIK, before + 1)
        d = molecule.pos.distance_to(cell.center)
        self.assertGreaterEqual(d - molecule.cizim_yaricapi(), cell.outer_r - 1e-6)


if __name__ == "__main__":
    unittest.main()

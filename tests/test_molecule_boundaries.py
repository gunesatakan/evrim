"""Molekul konumu ile molekul ciziminin zar sinirlarini korudugunu test eder."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import lab


class _MembraneCell:
    center = pygame.Vector2(0.0, 0.0)
    core_r = 110.0
    outer_r = 123.5
    generation = 0

    @staticmethod
    def active():
        return [lab.default_layers()[-1]]

    @staticmethod
    def boundaries():
        return [123.5]


class MoleculeBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((320, 240))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_membrane_bound_molecule_is_clipped_to_membrane_band(self):
        cell = _MembraneCell()
        middle = (cell.core_r + cell.outer_r) * 0.5
        molecule = lab.Molecule(
            cell, pygame.Vector2(middle, 0.0), pygame.Vector2(), 7)
        molecule.state = "arrived"

        full = molecule.rad * molecule.vs
        visible = molecule.cizim_yaricapi()

        self.assertLess(visible, full)
        self.assertLessEqual(visible, middle - cell.core_r)
        self.assertLessEqual(visible, cell.outer_r - middle)

    def test_injected_surface_payload_remains_visible_inside(self):
        cell = _MembraneCell()
        molecule = lab.Molecule(
            cell, pygame.Vector2(60.0, 0.0), pygame.Vector2(), 1)
        molecule.injected = True

        self.assertAlmostEqual(
            molecule.cizim_yaricapi(), molecule.rad * molecule.vs)

    def test_cytoplasm_payload_stopped_in_membrane_is_clipped(self):
        cell = _MembraneCell()
        middle = (cell.core_r + cell.outer_r) * 0.5
        molecule = lab.Molecule(
            cell, pygame.Vector2(middle, 0.0), pygame.Vector2(), 6)
        molecule.state = "stuck"

        visible = molecule.cizim_yaricapi()

        self.assertLessEqual(visible, middle - cell.core_r)

    def test_external_surface_payload_is_stopped_if_it_reaches_cytoplasm(self):
        cell = _MembraneCell()
        molecule = lab.Molecule(
            cell, pygame.Vector2(0.0, 0.0), pygame.Vector2(), 1)

        molecule.update(0.0)

        self.assertEqual(molecule.state, "stuck")
        self.assertEqual(molecule.band(), 0)
        self.assertGreaterEqual(
            molecule.pos.distance_to(cell.center), cell.core_r)


if __name__ == "__main__":
    unittest.main()

"""Bolunme: iki yavru esittir. Ebeveyn diye bir sey yok; ilk yavru ayni
Python nesnesi olsa da payini ikinciden once ya da fazla almaz."""

import os
import random
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: F401  (organlar pygame vektoru kullanir)

import game_settings as g
from entities.organism import Organism
from organs.central.cytoplasm.cytoplasm import Cytoplasm
from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
from organs.central.ribosome.ribosome import Ribosome
from organs.central.vacuole.vacuole import Vacuole
from organs.peripheral.membrane.membrane import Membrane


def _hucre():
    o = Organism(1, 400, 400, (200, 200, 200))
    for organ in (Membrane(), Cytoplasm(size=2.0), Cytoskeleton(),
                  Vacuole(size=1.0), Ribosome()):
        o.add_organ(organ)
    o.genomu_kur()
    return o


class BolunmeTests(unittest.TestCase):
    def setUp(self):
        self._kayit = g.save_all
        g.save_all = lambda *a, **k: None
        random.seed(7)

    def tearDown(self):
        g.save_all = self._kayit

    def test_iki_yavru_kairomonu_ve_enerjiyi_esit_paylasir(self):
        o = _hucre()
        o.energy = o.max_energy
        enerji = o.energy
        o.kairomone = 8.0
        b = o.divide()
        self.assertAlmostEqual(o.kairomone, 4.0)
        self.assertAlmostEqual(b.kairomone, 4.0)
        self.assertAlmostEqual(o.energy, enerji * 0.5)
        self.assertAlmostEqual(b.energy, enerji * 0.5)

    def test_yavrular_ebeveyn_yaricapiyla_simetrik_ayrilir(self):
        o = _hucre()
        merkez = pygame.math.Vector2(o.pos)
        mesafe = o.radius + 2

        def irilesen(h):
            h.body.logic.size *= 2.0
            h.recalculate_physics()
            return 'buyume'

        # Ilk yavrunun bolunmede irilesmesi ikincinin yerini degistirmez.
        g_orj = g.ORGAN_GAIN_RATE
        try:
            g.ORGAN_GAIN_RATE = 1.0
            with mock.patch.object(Organism, 'yapi_kazan', irilesen):
                b = o.divide()
        finally:
            g.ORGAN_GAIN_RATE = g_orj
        self.assertGreater(o.radius + 2, mesafe + 1.0)
        self.assertAlmostEqual((o.pos - merkez).length(), mesafe)
        self.assertAlmostEqual((b.pos - merkez).length(), mesafe)


if __name__ == "__main__":
    unittest.main()

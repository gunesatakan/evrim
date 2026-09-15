"""Olum kaydi silahi, teslim yolunu ve molekulu tasir: panelde
"Zipkin ile Norotoksin enjeksiyonu" diye okunur."""

import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: F401  (organlar pygame vektoru kullanir)

import game_settings
import lab
from entities.organism import Organism
from organs.central.cytoplasm.cytoplasm import Cytoplasm
from organs.peripheral.membrane.membrane import Membrane
from organs.peripheral.weapons.weapons import Toxin
from systems.world import Dunya

PI = {p[0]: i for i, p in enumerate(lab.PAYLOADS)}


def _hucre(x=400):
    o = Organism(1, x, 400, (200, 200, 200))
    o.add_organ(Membrane())
    o.add_organ(Cytoplasm(size=2.0))
    return o


class OlumTanimiTests(unittest.TestCase):
    def test_silah_yol_ve_molekul_okunur(self):
        self.assertEqual(lab.olum_tanimi('harpoon', PI['Norotoksin'], 3),
                         'Zipkin ile Norotoksin enjeksiyonu')
        self.assertEqual(lab.olum_tanimi('toksin', PI['Amoebapor'], 2),
                         'Toksin ile Amoebapor fiskirtmasi (ozmotik lizis)')
        self.assertEqual(lab.olum_tanimi('lizin', PI['Lizozim'], 1),
                         'Lizin ile Lizozim salgisi (duvar coktu)')
        self.assertEqual(lab.olum_tanimi('patlama', PI['Perforin']),
                         'patlayan hucreden sacilan Perforin (ozmotik lizis)')
        self.assertEqual(lab.olum_tanimi('molekul', PI['T3SS efektoru']),
                         'T3SS efektoru zehirlenmesi (ic cokus)')
        self.assertIsNone(lab.olum_tanimi('harpoon', 0, 3))
        self.assertIsNone(lab.olum_tanimi('harpoon', None, 3))


class OlumKaydiTests(unittest.TestCase):
    def setUp(self):
        self._kayit = game_settings.save_all
        game_settings.save_all = lambda *a, **k: None
        random.seed(1)

    def tearDown(self):
        game_settings.save_all = self._kayit

    def test_olumcul_doz_ayrintiyla_kaydedilir(self):
        o = _hucre()
        zarf = o.zarf_arayuzu()
        zarf.neden, zarf.tasiyici = 'harpoon', 3
        zarf._etki(PI['Norotoksin'], lab.TIER_LETHAL)
        self.assertTrue(o.dead)
        self.assertEqual(o.death_cause, 'harpoon')
        self.assertEqual(o.olum_ayrinti, 'Zipkin ile Norotoksin enjeksiyonu')

        d = Dunya(kaotropi_count=0, optropi_count=0, notropi_count=0,
                  food_count=0, tohum=1)
        d._olum_kaydet(o)
        aclik = _hucre()
        aclik.die('aclik')
        d._olum_kaydet(aclik)
        self.assertEqual(d.olum_nedeni, {'harpoon': 1, 'aclik': 1})
        self.assertEqual(d.olum_ayrintisi,
                         {('harpoon', 'Zipkin ile Norotoksin enjeksiyonu'): 1,
                          ('aclik', None): 1})
        self.assertEqual(d.olum_gunlugu[0][4], 'Zipkin ile Norotoksin enjeksiyonu')

    def test_molekul_salan_silah_tasiyicisini_hedefe_yazar(self):
        saldirgan, hedef = _hucre(400), _hucre(460)
        toksin = Toxin(attachment_angle=0.0, power=1.0)
        saldirgan.add_organ(toksin)
        lg = toksin.logic
        lg.carrier, lg.payload, lg.stok = 1, PI['Amoebapor'], 0.0
        self.assertTrue(saldirgan._molekul_birak(hedef, lg, 1.0 / 30.0))
        zarf = hedef.zarf_arayuzu()
        self.assertEqual((zarf.neden, zarf.tasiyici), ('toksin', 1))


if __name__ == "__main__":
    unittest.main()

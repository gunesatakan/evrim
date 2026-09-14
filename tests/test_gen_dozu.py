"""Gen dozu: bir ozelligin degeri organin tasarim degeri + gen kopyasi sayisi
kadar gelisim adimidir. Gelisim kopya ekler, bolunmede kopyalar kaybolabilir
ve deger geri iner; tasarim degerinin altina inmez."""

import os
import random
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: F401  (organlar pygame vektoru kullanir)

import game_settings
from entities.organism import Organism
from organs.central.cytoplasm.cytoplasm import Cytoplasm
from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
from organs.central.ribosome.ribosome import Ribosome
from organs.central.vacuole.vacuole import Vacuole
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.membrane.membrane import Membrane
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor
from organs.receptors.Mechanoreceptor.mechanoreceptor import Mechanoreceptor

g = game_settings

# Bolunmedeki diger mutasyonlar kapatilir: test yalnizca gen dozunu olcer.
KAPALI = ('ORGAN_GAIN_RATE', 'ORGAN_LOSS_RATE', 'ORGAN_ANGLE_RATE',
          'RENK_MUTASYON', 'TOXIN_ALLELE_MUTATION', 'MARKER_MUTATION',
          'TASIYICI_VARYANT_MUTATION', 'URETICI_YUK_MUTATION')


def _hucre():
    """Iki kamci, bir burun, bir kulak ve duvari olan kurucu hucre."""
    o = Organism(1, 400, 400, (200, 200, 200))
    zar = Membrane()
    for alan in list(zar.logic.KATMANLAR):
        zar.logic.katman_cikar(alan)
    zar.logic.katman_ekle('wall')
    o.add_organ(zar)
    o.add_organ(Cytoplasm(size=2.0))
    o.add_organ(Cytoskeleton())
    o.add_organ(Vacuole(size=1.0))
    o.add_organ(Ribosome())
    o.add_organ(Flagella(attachment_angle=0.0, length=10.0))
    o.add_organ(Flagella(attachment_angle=3.0, length=10.0))
    o.add_organ(Chemoreceptor(attachment_angle=1.0, length=5.0))
    o.add_organ(Mechanoreceptor(attachment_angle=2.0, size=1.0))
    o.energy = o.max_energy
    o.genomu_kur()
    return o


def _organlar(o, sinif):
    return [x for x in o.organs if isinstance(x, sinif)]


class GenDozuTests(unittest.TestCase):
    def setUp(self):
        self._eski = {a: getattr(g, a) for a in KAPALI + ('GEN_KOPYA_KAYBI', 'save_all')}
        g.save_all = lambda *a, **k: None
        for a in KAPALI:
            setattr(g, a, 0.0)
        random.seed(5)

    def tearDown(self):
        for a, v in self._eski.items():
            setattr(g, a, v)

    def _ortalama(self, kopya):
        return g.CHEMO_ORTALAMA_TABAN + kopya * g.GROW_CHEMO_ORTALAMA

    def test_kemoreseptor_yon_ortalamasi_kopyalariyla_dogar(self):
        o = _hucre()
        burun = _organlar(o, Chemoreceptor)[0]
        k = g.CHEMO_ORTALAMA_KOPYA
        self.assertEqual(o.genome.kopya_sayisi('chemo_ortalama', 0), k)
        self.assertAlmostEqual(burun.logic.uzamsal_ortalama, self._ortalama(k))
        self.assertAlmostEqual(g.get_default('CHEMO_ORTALAMA_KOPYA')
                               * g.get_default('GROW_CHEMO_ORTALAMA'), 0.5)
        # Sonradan kazanilan burun da ayni kopyalarla gelir.
        gercek = random.choice
        with mock.patch('entities.organism.random.choice',
                        side_effect=lambda s: 'Chemoreceptor'
                        if 'Chemoreceptor' in s else gercek(s)):
            yeni = o.gain_random_organ()
        self.assertIsInstance(yeni, Chemoreceptor)
        self.assertEqual(o.genome.kopya_sayisi('chemo_ortalama', 1), k)
        self.assertAlmostEqual(yeni.logic.uzamsal_ortalama, self._ortalama(k))

    def test_gelisim_kopya_ekler_kayip_geri_indirir(self):
        o = _hucre()
        kamci = _organlar(o, Flagella)[1]
        boy0, itki0 = kamci.logic.length, kamci.logic.base_thrust
        for _ in range(4):
            o._apply_upgrade(('flagella', 1))
        self.assertEqual(o.genome.kopya_sayisi('flagella', 1), 4)
        self.assertAlmostEqual(kamci.logic.length, boy0 + 4 * g.GROW_FLAGELLA)
        o.genome.kopya_ekle('flagella', 1, -3)
        o.gen_dozlarini_uygula()
        self.assertAlmostEqual(kamci.logic.length, boy0 + g.GROW_FLAGELLA)
        o.genome.kopya_ekle('flagella', 1, -5)
        o.gen_dozlarini_uygula()
        # Tasarim degerinin altina inmez; turetilen itki de geri gelir.
        self.assertAlmostEqual(kamci.logic.length, boy0)
        self.assertAlmostEqual(kamci.logic.base_thrust, itki0)
        self.assertAlmostEqual(_organlar(o, Flagella)[0].logic.length, boy0)

    def test_sistem_genleri_ve_organin_kendi_siniri(self):
        o = _hucre()
        sure0 = o.body.logic.enzyme.base_digestion_time
        hafiza0 = o.direction_memory.capacity
        # Torbadaki nokta mutasyonu sistem genine eski sirayi tasiyabilir.
        o._apply_upgrade(('digestion_speed', 3))
        o._apply_upgrade(('memory_length', 0))
        self.assertEqual(o.genome.kopya_sayisi('digestion_speed', 0), 1)
        self.assertAlmostEqual(o.body.logic.enzyme.base_digestion_time,
                               max(1.0, sure0 - g.GROW_DIGESTION))
        self.assertEqual(o.direction_memory.capacity, hafiza0 + g.GROW_MEMORY)

        kulak = _organlar(o, Mechanoreceptor)[0]
        esik0 = kulak.logic.esik
        for _ in range(3):
            o._apply_upgrade(('sound_radius', 0))
        beklenen = esik0
        for _ in range(3):
            beklenen = max(g.MECHANO_ESIK_MIN, beklenen * (1.0 - g.GROW_MECHANO_ESIK))
        self.assertAlmostEqual(kulak.logic.esik, beklenen)

        burun = _organlar(o, Chemoreceptor)[0]
        for _ in range(200):
            o._apply_upgrade(('chemo_gain', 0))
        self.assertAlmostEqual(burun.logic.kazanc, g.CHEMO_GAIN_MAX)
        o.genome.kopya_ekle('chemo_gain', 0, -199)
        o.gen_dozlarini_uygula()
        self.assertAlmostEqual(burun.logic.kazanc, min(
            g.CHEMO_GAIN_MAX, burun.logic._gen_dozu['kazanc'][0] + g.GROW_CHEMO_GAIN))

        o.genome.kopya = {}
        o.gen_dozlarini_uygula()
        self.assertAlmostEqual(o.body.logic.enzyme.base_digestion_time, sure0)
        self.assertEqual(o.direction_memory.capacity, hafiza0)
        self.assertAlmostEqual(kulak.logic.esik, esik0)
        self.assertAlmostEqual(burun.logic.uzamsal_ortalama, g.CHEMO_ORTALAMA_TABAN)

    def test_bolunmede_kopyalar_kaybolur(self):
        for oran in (1.0, 0.0):
            g.GEN_KOPYA_KAYBI = oran
            o = _hucre()
            boy0 = _organlar(o, Flagella)[0].logic.length
            govde0 = o.body.logic.size
            for _ in range(6):
                o._apply_upgrade(('flagella', 0))
            o._apply_upgrade(('body_size', 0))
            once = sum(o.genome.kopya.values())
            o.pending_organ_rolls = 0
            o.energy = o.max_energy
            b = o.divide()
            for h in (o, b):
                toplam = sum(h.genome.kopya.values())
                if oran == 1.0:
                    # Hepsi gitti; kalan en fazla bu bolunmenin gelisimi.
                    self.assertLessEqual(toplam, 1)
                else:
                    self.assertIn(toplam, (once, once + 1))
                self.assertAlmostEqual(
                    _organlar(h, Flagella)[0].logic.length,
                    boy0 + h.genome.kopya_sayisi('flagella', 0) * g.GROW_FLAGELLA)
                self.assertAlmostEqual(
                    h.body.logic.size,
                    govde0 + h.genome.kopya_sayisi('body_size', 0) * g.GROW_BODY)
                self.assertAlmostEqual(
                    _organlar(h, Chemoreceptor)[0].logic.uzamsal_ortalama,
                    self._ortalama(h.genome.kopya_sayisi('chemo_ortalama', 0)))

    def test_hasar_korunur_katmansiz_gen_ifade_edilmez(self):
        o = _hucre()
        zar = o.membrane.logic
        for _ in range(3):
            o._apply_upgrade(('wall', 0))
        duvar = zar.wall
        zar.wall = duvar * 0.35                  # toksinle incelmis duvar
        o.genome.kopya_ekle('wall', 0, -1)
        o.gen_dozlarini_uygula()
        self.assertAlmostEqual(zar.wall, max(0.0, duvar * 0.35 - g.GROW_WALL))

        kapsul = zar.capsule
        o._apply_upgrade(('capsule', 0))
        self.assertEqual(o.genome.kopya_sayisi('capsule', 0), 0)
        self.assertEqual(zar.capsule, kapsul)

        for _ in range(2):
            o._apply_upgrade(('membrane_integrity', 0))
        tavan = zar.max_integrity
        self.assertAlmostEqual(zar.integrity, tavan)     # kopya dolu gelir
        zar.integrity = tavan - 5.0                      # hasar
        o.genome.kopya_ekle('membrane_integrity', 0, -1)
        o.gen_dozlarini_uygula()
        self.assertAlmostEqual(zar.max_integrity, tavan - g.GROW_MEMBRANE_INTEGRITY)
        self.assertAlmostEqual(zar.integrity,
                               min(tavan - 5.0, tavan - g.GROW_MEMBRANE_INTEGRITY))

    def test_organ_kaybinda_kopyalar_organla_gider(self):
        o = _hucre()
        kamcilar = _organlar(o, Flagella)
        for _ in range(2):
            o._apply_upgrade(('flagella', 0))
        for _ in range(4):
            o._apply_upgrade(('flagella', 1))
        boy1 = kamcilar[1].logic.length
        gercek = random.choice
        with mock.patch('entities.organism.random.choice',
                        side_effect=lambda s: kamcilar[0]
                        if kamcilar[0] in s else gercek(s)):
            self.assertEqual(o.organ_kaybet(), 'Flagella')
        self.assertEqual(o.genome.kopya_sayisi('flagella', 0), 4)
        self.assertEqual(o.genome.kopya_sayisi('flagella', 1), 0)
        self.assertEqual(o.gen_dozlarini_uygula(), 0)
        self.assertAlmostEqual(kamcilar[1].logic.length, boy1)


if __name__ == "__main__":
    unittest.main()

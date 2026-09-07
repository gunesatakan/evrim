"""Dunya: simulasyonun CIZIMDEN BAGIMSIZ cekirdegi.

Neden ayri bir dosya: evrim yavas bir surectir. Uc basari olcutunun
(silahli avlanma, ogrenilmis kac/saldir, savunma tipleri) gerceklesip
gerceklesmedigini gormek icin yuz binlerce kare kosturmak gerekir -
saniyede 60 kare cizen bir pencerede bu saatler alir ve olculemez.

Burasi ayni mantigi ekransiz ve hizli kosturur. simulation.py de ayni
sinifi kullanir; boylece "olctugum dunya" ile "oynadigim dunya" ayni kod
olur. Ikisini ayri yazsaydim olcum kisa surede gercekle iliskisini
yitirirdi.
"""
import random

import game_settings
from entities.entity import WIDTH, HEIGHT
from entities.food import Food
from entities.kaotropi import Kaotropi
from entities.notropi import Notropi
from entities.optropi import Optropi
from entities.organism import Organism, resolve_overlaps
from entities.trail import TrailManager
from organs.peripheral.weapons.weapons import BaseWeapon
from systems.environment import ScentEnvironment

OPTROPI_COLORS = [(255, 0, 255), (255, 255, 0), (0, 255, 0), (255, 165, 0)]


class BesinIzgarasi:
    """Besinleri kare kare kutulara boler.

    Hucre basina butun besin listesini taramak (400 besin x 40 hucre x 60
    kare = saniyede bir milyon mesafe testi) karenin en pahali islemiydi
    ve besin sayisi arttikca kotulesiyordu. Besinler cogunlukla
    KIMILDAMAZ; yalnizca yutulanlar hareket eder, onlar da zaten taramanin
    disinda tutuluyor.
    """

    KUTU = 64

    def __init__(self):
        self._kutular = {}
        self._damga = None

    def kur(self, foods):
        k = self.KUTU
        d = {}
        for f in foods:
            if f.yutan is not None:
                continue            # cekilenler zaten sahiplenilmis
            d.setdefault((int(f.pos.x // k), int(f.pos.y // k)), []).append(f)
        self._kutular = d

    def yakin(self, pos, r):
        k = self.KUTU
        x0, x1 = int((pos.x - r) // k), int((pos.x + r) // k)
        y0, y1 = int((pos.y - r) // k), int((pos.y + r) // k)
        d = self._kutular
        out = []
        for cy in range(y0, y1 + 1):
            for cx in range(x0, x1 + 1):
                b = d.get((cx, cy))
                if b:
                    out.extend(b)
        return out


class HucreIzgarasi:
    """Hucreleri kutulara boler; komsu aramasi O(N^2) olmaktan cikar.

    Roller sinifa gore dagitilmayi biraktiginda her hucrenin "digerleri"
    listesi butun populasyon oldu. 200 hucrede bu kare basina 40.000
    mesafe hesabi demek. Oysa bir hucrenin ilgilendigi yaricap en uzun
    duyusuyla sinirli - uzaktakini zaten algilayamiyor.
    """

    KUTU = 128

    def __init__(self, hucreler):
        k = self.KUTU
        d = {}
        for o in hucreler:
            d.setdefault((int(o.pos.x // k), int(o.pos.y // k)), []).append(o)
        self._kutular = d

    def yakin(self, hucre, r):
        k = self.KUTU
        p = hucre.pos
        x0, x1 = int((p.x - r) // k), int((p.x + r) // k)
        y0, y1 = int((p.y - r) // k), int((p.y + r) // k)
        d = self._kutular
        out = []
        for cy in range(y0, y1 + 1):
            for cx in range(x0, x1 + 1):
                b = d.get((cx, cy))
                if b:
                    for o in b:
                        if o is not hucre:
                            out.append(o)
        return out


def algi_menzili(o):
    """Bu hucrenin bir baskasini fark edebilecegi en uzak mesafe."""
    return max(o.smell_range, o.sound_radius, o.vision_range,
               game_settings.TOXIN_RANGE, game_settings.NEMATOCYST_RANGE)


def drop_corpse(organism, foods):
    """Olen hucre yerine besin birakir. Oldurenin onceligi yoktur."""
    n = organism.corpse_food_count()
    for _ in range(n):
        fx = organism.pos.x + random.uniform(-organism.radius, organism.radius)
        fy = organism.pos.y + random.uniform(-organism.radius, organism.radius)
        foods.append(Food(max(15, min(WIDTH - 15, fx)),
                          max(15, min(HEIGHT - 15, fy)),
                          from_corpse=True))
    return n


class Dunya:
    """Bir ekosistem ornegi. adim(dt) bir kare ilerletir."""

    def __init__(self, food_count=None, kaotropi_count=None,
                 optropi_count=4, notropi_count=None, tohum=None):
        if tohum is not None:
            random.seed(tohum)
        self.tohum = tohum
        if food_count is None:
            food_count = game_settings.FOOD_COUNT
        if kaotropi_count is None:
            kaotropi_count = game_settings.KAOTROPI_COUNT
        if notropi_count is None:
            notropi_count = int(game_settings.NOTROPI_COUNT)

        self.trail_manager = TrailManager()
        self.scent_env = ScentEnvironment(WIDTH, HEIGHT)

        self.kaotropis = [Kaotropi(i, random.randint(50, WIDTH - 50),
                                   random.randint(50, HEIGHT - 50))
                          for i in range(kaotropi_count)]
        self.optropis = []
        for i in range(optropi_count):
            self.optropis.append(Optropi(i, random.randint(50, WIDTH - 50),
                                         random.randint(50, HEIGHT - 50),
                                         OPTROPI_COLORS[i % len(OPTROPI_COLORS)]))
        for _ in range(notropi_count):
            self.optropis.append(Notropi(len(self.optropis),
                                         random.randint(50, WIDTH - 50),
                                         random.randint(50, HEIGHT - 50)))
        self.foods = Food.spawn(food_count)
        self._besin_izgara = BesinIzgarasi()
        self._food_accum = 0.0
        self.gecen_sure = 0.0
        self.kare = 0

        # --- olcum ---
        self.olum_nedeni = {}
        self.silah_olumu = {}      # silah adi -> oldurdugu hucre sayisi
        self.dogum = 0
        self.av_yeme = 0           # hucre yeme olayi (les dahil)

    # ------------------------------------------------------------------
    @property
    def hucreler(self):
        return list(self.optropis) + list(self.kaotropis)

    def _olum_kaydet(self, o):
        c = getattr(o, 'death_cause', '?')
        self.olum_nedeni[c] = self.olum_nedeni.get(c, 0) + 1

    # ------------------------------------------------------------------
    def adim(self, dt):
        self.gecen_sure += dt
        self.kare += 1
        foods = self.foods
        trail_manager = self.trail_manager
        scent_env = self.scent_env

        trail_manager.update(dt)

        # Besin yeniden dogusu
        if game_settings.FOOD_SPAWN_RATE > 0:
            if len(foods) < game_settings.FOOD_MAX:
                self._food_accum += game_settings.FOOD_SPAWN_RATE * dt
                while self._food_accum >= 1.0 and len(foods) < game_settings.FOOD_MAX:
                    self._food_accum -= 1.0
                    foods.append(Food(random.randint(30, WIDTH - 30),
                                      random.randint(30, HEIGHT - 30)))
            else:
                self._food_accum = 0.0

        # Yutulmakta olan besinler
        for f in list(foods):
            if not f.yutuluyor:
                continue
            if f.yutma_guncelle(dt):
                yiyen = f.yutan
                f.yutan = None
                if yiyen is not None and not yiyen.dead and yiyen.consume_food(f):
                    foods.remove(f)
                else:
                    f.radius = f.taban_r

        self._besin_izgara.kur(foods)

        # Koku alani
        for f in foods:
            scent_env.add_scent(f.pos.x, f.pos.y,
                                f.radius * game_settings.FOOD_SCENT_EMISSION * dt)
        if game_settings.PREY_SCENT_EMISSION > 0:
            for pobj in self.optropis:
                if isinstance(pobj, Notropi):
                    scent_env.add_scent(pobj.pos.x, pobj.pos.y,
                                        pobj.radius * game_settings.PREY_SCENT_EMISSION * dt)
        scent_env.update(dt)

        # --- HERKES ---
        #
        # ROL SINIFTAN GELMEZ.
        #
        # Once kim avci kim av oldugu tur adiyla belliydi: Kaotropi'nin av
        # listesi butun Optropiler, Notropi'nin av listesi ise BOSTU - yani
        # populasyonun ucte ikisi avlanmayi denemesi bile imkansiz
        # doguyordu. Avlanmanin "kendiliginden baslamasi" boyle bir dunyada
        # olamaz: baslamis olurdu, kodda yazili oldugu icin.
        #
        # Artik tek bir kural var: herkes herkesin komsusudur. Kime
        # saldirilacagi, kimden kacilacagi yalnizca davranis tablosundan ve
        # tasinan organlardan cikar.
        hepsi = self.optropis + self.kaotropis
        Organism.population_count = len(hepsi)
        izgara = HucreIzgarasi(hepsi)
        eaten_prey = set()
        oldu = []
        for o in hepsi:
            if random.random() < game_settings.TRAIL_RATE * dt:
                trail_manager.add_point(o.pos.x, o.pos.y, o.uid, o.direction, o.radius)
            if game_settings.PREY_SCENT_EMISSION > 0:
                scent_env.add_scent(o.pos.x, o.pos.y,
                                    o.radius * game_settings.PREY_SCENT_EMISSION * dt)

            menzil = algi_menzili(o) + o.radius + 40.0
            komsu = izgara.yakin(o, menzil)

            # Ayni liste hem "tehdit" hem "av" olarak gider: ikisini
            # ayirmak zaten rolu onceden dagitmak olurdu.
            o.update(dt, komsu, foods, trail_manager, None, scent_env, komsu)

            for victim in o.fire_weapons(dt, komsu):
                self.silah_olumu[victim.death_cause] = \
                    self.silah_olumu.get(victim.death_cause, 0) + 1

            for pobj in komsu:
                if pobj in eaten_prey:
                    continue
                if o.pos.distance_to(pobj.pos) < o.radius + pobj.radius:
                    if o.consume_prey(pobj):
                        eaten_prey.add(pobj)
                        self.av_yeme += 1
                        if not pobj.dead:
                            pobj.die('yutuldu')
                    break

            for f in self._besin_izgara.yakin(o.pos, o.radius + 12.0):
                if f.yutuluyor:
                    continue
                if o.pos.distance_to(f.pos) < o.radius + f.radius:
                    if hasattr(o, 'body') and \
                            o.body.logic.can_fit_food(o.calculate_organ_area()):
                        f.yutulmaya_basla(o)
                    break

            if o in eaten_prey and not o.dead:
                o.die('avlandi')

        for o in hepsi:
            if o.dead:
                oldu.append(o)
                self._olum_kaydet(o)
                if not getattr(o, 'consumed', False):
                    drop_corpse(o, foods)
        olu = set(map(id, oldu))

        # YAVRULAR. Olenler de taranir: mitoz tamamlandiysa yavrular ayri
        # birer hucredir, ebeveynin ayni karede olmesi onlari yok etmemeli.
        yavru_opt, yavru_kao = [], []
        for o in hepsi:
            if not o.pending_children:
                continue
            (yavru_kao if o in self.kaotropis else yavru_opt).extend(o.pending_children)
            o.pending_children = []
        self.dogum += len(yavru_opt) + len(yavru_kao)

        self.optropis = [o for o in self.optropis if id(o) not in olu] + yavru_opt
        self.kaotropis = [o for o in self.kaotropis if id(o) not in olu] + yavru_kao

        # NUFUS TAVANI = ELEME (duvar degil).
        # Tavan asildiginda bolunme engellenmez; en dusuk enerjili hucre
        # elenir. Boylece hizli beslenen gercekten yavasin yerini alir.
        # Tavan artik BUTUN populasyona uygulanir; eskiden yalnizca
        # optropiler sayiliyordu ve kaotropiler sinirsiz uruyordu.
        cap = int(game_settings.DIVISION_MAX_POPULATION)
        tum = self.optropis + self.kaotropis
        if cap > 0 and len(tum) > cap:
            tum.sort(key=lambda x: x.energy)
            for victim in tum[:len(tum) - cap]:
                victim.die('elendi')
                self._olum_kaydet(victim)
                drop_corpse(victim, foods)
            self.optropis = [o for o in self.optropis if not o.dead]
            self.kaotropis = [o for o in self.kaotropis if not o.dead]

        resolve_overlaps(self.optropis + self.kaotropis)

    # ------------------------------------------------------------------
    def organ_sayimi(self):
        """Tum populasyonda organ tipi -> tasiyan hucre sayisi."""
        out = {}
        for o in self.hucreler:
            for tip in {x.__class__.__name__ for x in o.organs}:
                out[tip] = out.get(tip, 0) + 1
        return out

    def silahli_oran(self):
        h = self.hucreler
        if not h:
            return 0.0
        n = sum(1 for o in h
                if any(isinstance(x, BaseWeapon) for x in o.organs))
        return n / len(h)

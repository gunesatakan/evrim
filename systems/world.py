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
from systems import isik
from entities.entity import WIDTH, HEIGHT
from entities.food import Food
from entities.kaotropi import Kaotropi
from entities.notropi import Notropi
from entities.optropi import Optropi
from entities.organism import (Organism, resolve_overlaps, ipleri_coz, ip_kisitlari,
                               ip_gerilmesi_denetle, ip_capalarini_tazele)
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

    def dolu(self, x, y):
        """Bu noktanin uzerinde bir hucre var mi?"""
        k = self.KUTU
        cx, cy = int(x // k), int(y // k)
        d = self._kutular
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for o in d.get((cx + dx, cy + dy), ()):  # noqa
                    ddx = o.pos.x - x
                    ddy = o.pos.y - y
                    r = o.radius
                    if ddx * ddx + ddy * ddy < r * r:
                        return True
        return False

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
    """Bu hucrenin bir baskasini fark edebilecegi en uzak mesafe.

    Koku menzili artik sabit degil, HEDEFE de bagli. Burada hedef henuz
    bilinmedigi icin en iyimser durum alinir (bkz. koku_menzili). Liste
    biraz genis kalir; dar kalsaydi hucre gercekten duyabilecegi bir
    kokuyu izgara elemesi yuzunden hic gormezdi - sessizce yanlis olurdu.
    """
    return max(o.koku_menzili(), o.sound_radius, o.vision_range,
               game_settings.TOXIN_RANGE, game_settings.NEMATOCYST_RANGE)


def drop_corpse(organism, foods):
    """Olen hucre yerine besin birakir. Oldurenin onceligi yoktur.

    TAVAN LESE DE UYGULANIR. Eskiden yalnizca DOGAN besin FOOD_MAX ile
    sinirlaniyordu; lesler siniri gormeden ekleniyordu. Hizli devrilen bir
    populasyonda bu, haritayi besinle bogar (olculdu: 450 -> 20.589) ve
    kitligi tamamen ortadan kaldirir. Harita doluyken cozunen bir les
    ortama yayilmis sayilir - kimse toplamaya yetismez.
    """
    # EN AZ CORPSE_FOOD_MIN: govdenin kendisi biyokutledir. Enerji
    # hesabi ac olen hucrede 0'a yuvarlaniyordu (0.5 x 166 / 270 = 0.3);
    # hucre kaybolup arkasinda hicbir sey birakmiyordu.
    taban_adet = max(0, int(getattr(game_settings, 'CORPSE_FOOD_MIN', 1)))
    n = max(taban_adet, organism.corpse_food_count())
    # LESIN KENDI TAVANI VAR. FOOD_MAX = FOOD_COUNT (80 = 80) oldugu
    # icin harita neredeyse hep doluydu ve les HIC dusmuyordu: olen
    # hucre arkasinda hicbir sey birakmiyordu. Tasma korumasi kaliyor
    # ama LESE ayri sayiliyor - dogal besin doluyken bile olum gorunur.
    tavan = int(getattr(game_settings, 'CORPSE_TOTAL_MAX',
                        game_settings.FOOD_MAX))
    les_sayisi = sum(1 for f in foods if getattr(f, 'from_corpse', False))
    for i in range(n):
        # Garanti edilen ilk besin(ler) tavani gormez: olum hep iz birakir.
        if i >= taban_adet and les_sayisi >= tavan:
            break
        les_sayisi += 1
        fx = organism.pos.x + random.uniform(-organism.radius, organism.radius)
        fy = organism.pos.y + random.uniform(-organism.radius, organism.radius)
        foods.append(Food(max(15, min(WIDTH - 15, fx)),
                          max(15, min(HEIGHT - 15, fy)),
                          from_corpse=True))
    return n


class Dunya:
    """Bir ekosistem ornegi. adim(dt) bir kare ilerletir."""

    #: Bir SILAHIN eseri olan olum nedenleri (silah sayacina yazilir).
    SILAH_NEDENLERI = frozenset((
        'toksin', 'lizin', 'molekul', 'nematocyst', 'harpoon', 'stylet',
        'phagocytosis', 'yutuldu', 'patlama', 'hasar'))

    def __init__(self, food_count=None, kaotropi_count=None,
                 optropi_count=None, notropi_count=None, tohum=None):
        if tohum is not None:
            random.seed(tohum)
        self.tohum = tohum
        if food_count is None:
            food_count = game_settings.FOOD_COUNT
        if kaotropi_count is None:
            kaotropi_count = game_settings.KAOTROPI_COUNT
        if notropi_count is None:
            notropi_count = int(game_settings.NOTROPI_COUNT)
        if optropi_count is None:
            optropi_count = int(getattr(game_settings, 'OPTROPI_COUNT', 1))

        self.trail_manager = TrailManager()
        self.scent_env = ScentEnvironment(WIDTH, HEIGHT)

        # ONCE BESIN, SONRA HUCRELER.
        #
        # Baslangic besini de yamali: dunyanin ilk hali ile sonraki hali
        # arasinda yapisal fark olmasin.
        self.foods = []
        self._yama_merkezleri = []
        _elde = getattr(game_settings, 'HARITA_YAMALARI', None)
        if _elde:
            # Cizilen duzen aynen kurulur; FOOD_COUNT'a bakilmaz cunku
            # kullanici besinin KAC TANE ve NEREDE olacagini zaten soyledi.
            for _y in _elde:
                self.besin_yamasi_konumda(
                    float(_y[0]), float(_y[1]),
                    int(_y[2]) if len(_y) > 2 else int(game_settings.FOOD_PATCH_SIZE),
                    float(_y[3]) if len(_y) > 3 else game_settings.FOOD_PATCH_SIGMA)
        else:
            _yama = max(1, int(game_settings.FOOD_PATCH_SIZE))
            while len(self.foods) < food_count:
                self.besin_yamasi(min(_yama, food_count - len(self.foods)))

        # KURUCULAR BOSLUGA DEGIL, BIR YAMANIN YANINA DOGAR.
        #
        # Besin seyreklestiginde populasyon bir KURULUS ESIGINE carpiyor:
        # uc kurucu hucre, yamalari bulamadan tukeniyor. Olculdu - 120
        # besinle 240 saniyede nufus tavana (120) cikiyor ve 1642 lokma
        # aliniyor; 80 besinle nufus 4'te kaliyor ve topu topu 3 lokma
        # aliniyor. Kademeli degil, keskin bir esik. Yani sonucu ekoloji
        # degil kuruculari sansi belirliyor.
        #
        # Bir populasyon zaten kaynagin oldugu yerde kurulur. Kurucular
        # rastgele bir yamanin cevresine birakilir; oradan sonrasi
        # tamamen secilime kalir.
        # ELDE SECILMIS BASLANGIC NOKTALARI. Kurucularin NEREDE dogdugu
        # sonucu belirleyen bir kosul (bkz. asagidaki kurulus esigi);
        # bunu da yamalar gibi elle koyabilmek gerekiyordu. Noktalar
        # sirayla kullanilir, kurucular noktadan cok ise basa donulur.
        _baslangic = [(float(b[0]), float(b[1]))
                      for b in (getattr(game_settings, 'HARITA_BASLANGIC', None) or ())
                      if len(b) >= 2]
        self._baslangic_noktalari = _baslangic
        _sira = [0]

        def _dogum_yeri():
            if _baslangic:
                bx, by = _baslangic[_sira[0] % len(_baslangic)]
                _sira[0] += 1
                # Ayni noktaya konan kurucular ust uste binmesin: bir
                # hucre capi kadar dagilim yeter.
                yari = game_settings.SPAWN_DAGILIM
                return (min(WIDTH - 50, max(50, random.gauss(bx, yari))),
                        min(HEIGHT - 50, max(50, random.gauss(by, yari))))
            if not self._yama_merkezleri:
                return (random.randint(50, WIDTH - 50),
                        random.randint(50, HEIGHT - 50))
            cx, cy = random.choice(self._yama_merkezleri)
            yari = game_settings.FOOD_PATCH_SIGMA * 2.5
            return (min(WIDTH - 50, max(50, random.gauss(cx, yari))),
                    min(HEIGHT - 50, max(50, random.gauss(cy, yari))))

        self.kaotropis = [Kaotropi(i, *_dogum_yeri())
                          for i in range(kaotropi_count)]
        self.optropis = []
        for i in range(optropi_count):
            self.optropis.append(Optropi(i, *_dogum_yeri(),
                                         color=OPTROPI_COLORS[i % len(OPTROPI_COLORS)]))
        for _ in range(notropi_count):
            self.optropis.append(Notropi(len(self.optropis), *_dogum_yeri()))
        self._besin_izgara = BesinIzgarasi()
        self._hucre_izgara = None
        self._food_accum = 0.0
        self.gecen_sure = 0.0
        self.kare = 0

        # --- olcum ---
        self.olum_nedeni = {}
        # OLUM GUNLUGU: son olumler (zaman, neden, hucre no, tur). Toplam
        # sayac tek basina "ne oluyor"u soylemez; kimin ne zaman neden
        # oldugu ekranda okunabilmeli.
        self.olum_gunlugu = []
        # Bu karede olenler - cizim katmani olum efektini buradan kurar.
        self.son_olenler = []
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
        self.olum_gunlugu.append((self.gecen_sure, c,
                                  int(getattr(o, 'index', -1)),
                                  type(o).__name__))
        if len(self.olum_gunlugu) > 40:
            del self.olum_gunlugu[0]

    # ------------------------------------------------------------------
    def adim(self, dt):
        self.gecen_sure += dt
        self.kare += 1
        foods = self.foods
        trail_manager = self.trail_manager
        scent_env = self.scent_env

        trail_manager.update(dt)

        # Besin yeniden dogusu - YAMA YAMA.
        if game_settings.FOOD_SPAWN_RATE > 0:
            # Les ayri tavana sayilir (bkz. drop_corpse); dogal dogus
            # yalnizca DOGAL besine bakar, yoksa lesler onu bastirirdi.
            dogal = sum(1 for f in foods if not getattr(f, 'from_corpse', False))
            if dogal < game_settings.FOOD_MAX:
                self._food_accum += game_settings.FOOD_SPAWN_RATE * dt
                yama = max(1, int(game_settings.FOOD_PATCH_SIZE))
                while (self._food_accum >= yama
                        and dogal < game_settings.FOOD_MAX):
                    dogal += yama
                    self._food_accum -= yama
                    # Onceki karenin hucre izgarasi: hucreler bir karede
                    # kendi yaricaplarinin yuzde biri kadar yer degistirir,
                    # bu yuzden bir kare eski olmasi onemsiz.
                    self.besin_yamasi(yama, self._hucre_izgara)
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

        # KOKU ALANI YALNIZCA BESINDIR.
        #
        # Once hucreler de ayni alana salgi birakiyordu ("avci kemotaksiyle
        # avi bulsun" diye). Ama kemoreseptor de AYNI alandan okuyor: hucre
        # kendi salgisini kokluyordu. Kendi sinyali kendi konumunda en
        # yuksek oldugu icin - ve Weber-Fechner algiyi logaritmik
        # sikistirdigi icin - besinin gradyani bunun altinda kayboluyordu.
        #
        # Olculdu: 120 besinlik yigina 700 px uzaktaki bir hucre yigindan
        # gelen kokuyu degil kendi kokusunu okuyordu (algi 3.5-4.3 sabit,
        # delta +-0.1 gurultu). Kemoreseptor tasimanin hicbir faydasi
        # yoktu: burunlu hucre 3.37, ciplak hucre 3.50 besin aliyordu.
        #
        # Hucrelerin birbirini kokla bulmasi zaten IKI ayri yoldan var:
        # iz sistemi (kendi izini disliyor) ve perceive_and_decide'in koku
        # menzili. Difuzyon alanina ihtiyaci yok.
        for f in foods:
            scent_env.add_scent(f.pos.x, f.pos.y,
                                f.radius * game_settings.FOOD_SCENT_EMISSION * dt)
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
        # Koku menzili hedefe de bagli oldugu icin izgara elemesi en
        # iyimser durumu bilmeli (bkz. Organism.koku_menzili).
        if hepsi:
            Organism.en_guclu_koku = max(o.scent_value for o in hepsi)
            Organism.en_iri_yaricap = max(o.radius for o in hepsi)
        izgara = HucreIzgarasi(hepsi)
        self._hucre_izgara = izgara
        eaten_prey = set()
        oldu = []
        for o in hepsi:
            if random.random() < game_settings.TRAIL_RATE * dt:
                trail_manager.add_point(o.pos.x, o.pos.y, o.uid, o.direction,
                                        o.radius, getattr(o, 'scent_value', 0.0))

            menzil = algi_menzili(o) + o.radius + 40.0
            komsu = izgara.yakin(o, menzil)

            # Ayni liste hem "tehdit" hem "av" olarak gider: ikisini
            # ayirmak zaten rolu onceden dagitmak olurdu.
            o.update(dt, komsu, foods, trail_manager, None, scent_env, komsu)

            # Silah olumleri OLUM DONGUSUNDE sayilir (asagida): igne
            # anindaki olumle molekulun saniyeler sonra getirdigi olum
            # ayni sayaca girsin, hicbiri iki kez sayilmasin.
            o.fire_weapons(dt, komsu)

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

        # IPLER: herkes hareket ettikten sonra gerilen ipler iki ucu da ceker.
        ipleri_coz(hepsi, dt, izgara)

        for o in hepsi:
            if o.dead:
                oldu.append(o)
                # Lizisle patlayan hucre stogunu komsulara sacar: toksin
                # dolu bir hucreyi patlatmak onu kimyasal bombaya cevirir.
                if getattr(o, 'olum_sekli', None) == 'patlama':
                    o.stok_sac(izgara.yakin(
                        o, o.radius + game_settings.SACILMA_MENZILI))
                self._olum_kaydet(o)
                # SILAHLA GELEN HER OLUM silah sayacina - igne aninda da,
                # molekul saniyeler sonra vardiginda da. Eskiden yalnizca
                # fire_weapons'in dondurdugu anlik olumler sayiliyordu;
                # toksinle olen hucre panelde "toksin" yaziyor ama silah
                # sayacinda gorunmuyordu.
                _c = getattr(o, 'death_cause', None)
                if _c in self.SILAH_NEDENLERI:
                    self.silah_olumu[_c] = self.silah_olumu.get(_c, 0) + 1
                if not getattr(o, 'consumed', False):
                    drop_corpse(o, foods)
        self.son_olenler = list(oldu)
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

        # NUFUS TAVANI = KEMOSTAT SEYRELMESI (rastgele yikanma).
        #
        # Once "en dusuk enerjili hucreyi ele" kurali vardi ve kulaga makul
        # geliyordu. Oysa SECILIMI TERSINE CEVIRIYORDU: bolunen hucrenin
        # enerjisi once bolunme bedeli kadar duser, sonra ikiye bolunur -
        # yani her uremis hucre bir anda listenin en dibine iner ve ilk
        # elenen o olur. Hic bolunmeyip enerjisini deposunda tutan bir
        # hucre ise hep tepede kalir ve hic elenmez.
        #
        # Olculdu: populasyon 400 saniyede kamcisini ve kemoreseptorunu
        # TAMAMEN yitirdi (1.00 -> 0.00), organ sayisi 7.0'dan 5.0'a dustu.
        # Yani hucreler hareketsizlesip korlesti - cunku dunya, ureyeni
        # cezalandirip istifleyeni odullendiriyordu. "Kompleks hucreler
        # gelismesi" beklenirken tam tersi seciliyordu.
        #
        # Kemostatta seyrelme RASTGELEDIR: kim oldugundan bagimsiz olarak
        # herkes ayni oranda disari yikanir. Boyle bir dunyada tek bir sey
        # kazandirir - KENDINI DAHA HIZLI YERINE KOYMAK. Mikrobiyal evrim
        # deneylerinin standart duzeni de tam olarak budur.
        #
        # Yikanan hucre les de birakmaz: sistemden CIKMISTIR, olmemistir.
        cap = int(game_settings.DIVISION_MAX_POPULATION)
        tum = self.optropis + self.kaotropis
        fazla = len(tum) - cap
        if cap > 0 and fazla > 0:
            # ONCE HAREKETSIZLER YIKANIR. Kemostatta akinti herkesi ayni
            # oranda tasir ama yuzebilen hucre akintiya karsi tutunur;
            # motorunu (kamci/sil) yitirmis hucre tutunamaz ve ilk o gider.
            # Kalan fazla yine RASTGELE secilir - "en zayifi ele" kurali
            # secilimi tersine cevirmisti (bkz. yukarisi), o yuzden burada
            # enerjiye bakilmaz; yalnizca yuzup yuzemedigine bakilir.
            def _motorsuz(o):
                return not any(x.__class__.__name__ in ('Flagella', 'Cilia')
                               for x in o.organs)
            hareketsiz = [o for o in tum if _motorsuz(o)]
            random.shuffle(hareketsiz)
            kurbanlar = hareketsiz[:fazla]
            if len(kurbanlar) < fazla:
                _sec = set(map(id, kurbanlar))
                kalan = [o for o in tum if id(o) not in _sec]
                kurbanlar += random.sample(kalan, fazla - len(kurbanlar))
            for victim in kurbanlar:
                victim.die('yikandi')
                self._olum_kaydet(victim)
                victim.consumed = True      # les birakmaz
                self.son_olenler.append(victim)
            self.optropis = [o for o in self.optropis if not o.dead]
            self.kaotropis = [o for o in self.kaotropis if not o.dead]

        # TEMASLAR VE IPLER BIRLIKTE. Hucreler ic ice giremez, ipler de
        # boylarindan uzun olamaz; iki kural ayni karede birkac turda
        # uzlastirilir. Uzlasamayan ip ya kopar ya kayar.
        _hucreler = self.optropis + self.kaotropis
        resolve_overlaps(_hucreler)
        for _tur in range(2):
            ip_kisitlari(_hucreler)
            resolve_overlaps(_hucreler)
        ip_gerilmesi_denetle(_hucreler, dt)
        ip_capalarini_tazele(_hucreler)

    def besin_yamasi_konumda(self, cx, cy, adet, sigma, izgara=None):
        """Belirtilen noktaya besin obegi birak.

        BESIN OLUSTURAN TEK YER burasi: hem elde cizilen duzen hem de
        yeniden dogus buradan gecer. Isik carpani da bu yuzden burada -
        iki ayri yerde uygulanınca biri unutuluyordu.
        """
        # ISIK FOTOSENTEZI SURER. Aydinlik sudaki bir yama, ayni yamanin
        # karanliktaki halinden daha cok uretir; carpan siddetle
        # dogrusaldir (tam isikta ISIK_BESIN_CARPANI, karanlikta 1).
        _kat = isik.besin_carpani(cx, cy)
        if _kat != 1.0:
            adet = max(1, int(round(adet * _kat)))
        self._yama_merkezleri.append((cx, cy))
        if len(self._yama_merkezleri) > 64:
            del self._yama_merkezleri[0]
        for _ in range(int(adet)):
            if sum(1 for f in self.foods
                   if not getattr(f, 'from_corpse', False)) >= game_settings.FOOD_MAX:
                return
            for _deneme in range(6):
                x = min(WIDTH - 15, max(15, random.gauss(cx, sigma)))
                y = min(HEIGHT - 15, max(15, random.gauss(cy, sigma)))
                if izgara is None or not izgara.dolu(x, y):
                    self.foods.append(Food(x, y))
                    break

    def besin_yamasi(self, adet=None, izgara=None):
        """Rastgele bir noktaya besin OBEGI birak.

        Tek tek dagitmak haritayi duzgun bir besin sisiyle kapliyordu ve
        koku alaninin gradyanini duzlestiriyordu; koklamanin bir anlami
        kalmiyordu. Obek, hem gercekci (deniz kari, cokelti, les) hem de
        duyu organlarinin bedelini odetip karsiligini veren tek duzen.

        BESIN HUCRENIN ICINDE BELIREMEZ.
        #
        Yaricapi 22 olan 200 hucre, 1200x800'luk dunyanin ucte birini
        kapliyor - yani rastgele dogan besinin ucte biri dogrudan bir
        hucrenin uzerine dusuyordu. Kimildamayan bir hucre bile boylece
        besleniyor, hatta yalnizca daha ucuz oldugu icin KAZANIYORDU.
        Olculdu: uzun kosularin sonunda populasyon kamcisini ve
        kemoreseptorunu tamamen birakip zirh yigan, hareketsiz ve kor
        bloklara donusuyordu (organ 5.7, kamci 0.06, burun 0.04,
        katman 1.6, atis 0).

        Besin ortamda belirir, bir hucrenin sitoplazmasinda degil. Uygun
        yer bulunamazsa o lokma o an olusmaz.
        """
        # ELDE CIZILMIS HARITA VARSA ONA UYULUR.
        # Kullanicinin koydugu yamalar kalici olmali; rastgele yer secmek
        # o duzeni bir dakika icinde yikayip gotururdu.
        elde = getattr(game_settings, 'HARITA_YAMALARI', None)
        if elde:
            y = random.choice(elde)
            cx, cy = float(y[0]), float(y[1])
            if len(y) > 2 and adet is None:
                adet = int(y[2])
            sigma = float(y[3]) if len(y) > 3 else game_settings.FOOD_PATCH_SIGMA
        else:
            sigma = game_settings.FOOD_PATCH_SIGMA
            cx = random.uniform(60, WIDTH - 60)
            cy = random.uniform(60, HEIGHT - 60)
        if adet is None:
            adet = int(game_settings.FOOD_PATCH_SIZE)
        self.besin_yamasi_konumda(cx, cy, adet, sigma, izgara)

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

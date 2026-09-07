import pygame
import random
import math
from .move_direction import MoveDirection
import game_settings
from systems.signaling.behavioral_state import BehavioralState
from entities.entity import WIDTH, HEIGHT
from organs.receptors.Photoreceptor.photoreceptor import Photoreceptor

class DangerTransmission:
    def __init__(self):
        self.area = game_settings.CYTOSKELETON_AREA # Kapladığı alan
        self.target_direction = pygame.math.Vector2(1, 0)
        self.wander_timer = 0

        # Kaçış yönü kilidi - oscillasyonu önlemek için
        self.escape_lock_timer = 0
        self.locked_escape_dir = None

        # Davranış durumu sistemi (interoception)
        self.behavioral_state = BehavioralState()

        # Temporal chemotaxis
        # last_perception: bir ÖNCEKİ algı penceresinin ortalaması.
        # None = henüz karşılaştırılacak pencere yok (ilk delta 0 olmalı).
        self.last_perception = None
        self.last_delta = 0.0
        self.base_tumble_rate = getattr(game_settings, 'BASE_TUMBLE_RATE', 1.0)
        self.tumble_rate = self.base_tumble_rate

        # Algı penceresi: kare başına (1/60 sn) ölçülen fark, canlı o sürede
        # neredeyse hiç yer değiştirmediği için sıfıra yakın çıkar ve
        # tumble_rate hiç modüle olmaz. Bu yüzden algı bir pencere boyunca
        # biriktirilip pencere ortalamaları karşılaştırılır.
        self.sample_interval = getattr(game_settings, 'CHEMO_SAMPLE_INTERVAL', 0.5)
        self._sample_accum = 0.0
        self._sample_time = 0.0

        # Levy flight (IDLE)
        self.levy_run_duration = 0.0
        self.levy_timer = 0.0

    def process_signals(self, dt, organism, nearby_threats, memory_system,
                        scent_intensity, prey_dir=None,
                        behavior_response=0.0, koku_gradyani=None):
        """
        Sinyalleri işler ve hareket yönünü belirler.
        BehavioralState sistemini kullanarak iç duruma göre karar verir.

        Args:
            scent_intensity: Skalar koku yoğunluğu (float)

        Geriye (new_direction, vector_type, vector_value) döner.
        vector_type: 'ESCAPE', 'TRAIL', 'HUNT' veya None
        """
        self_pos = organism.pos

        # Escape lock timer'ı güncelle
        if self.escape_lock_timer > 0:
            self.escape_lock_timer -= dt

        # Davranış durumunu değerlendir (interoception). Donen deger
        # dogrudan kullanilmaz; ic durum should_flee() uzerinden okunur.
        self.behavioral_state.evaluate(organism, nearby_threats,
                                       scent_intensity > 0)

        # KARAR SIRASI
        #
        # Once "tehdit gordun, KAC" refleksi en usteydi ve davranis
        # tablosunun onune geciyordu. Bu, kacma davranisini DOGUSTAN
        # yapiyordu: mekanoreseptor kazanan bir hucre butun komsularini
        # duyar, hepsini tehdit sayar ve genomu 'yoksay' dese bile
        # kacardi. Roller sinifa gore dagitilmayi biraktiginda bu daha da
        # kotulesti - artik herkesin komsu listesi butun populasyon.
        #
        # Kacmanin, saldirmanin ve yaklasmanin EVRIMLESMESI isteniyorsa
        # kararin sahibi tablo olmali. 'yoksay' da bir karardir, susmak
        # degil. Bu yuzden sira su:
        #
        #   1) DUVAR  - fiziksel kisit, davranis degil
        #   2) TABLO  - hucrenin evrimlesmis karari (kac/yaklas/saldir)
        #   3) IZ     - tablo susuyorsa baskasinin izinden kacin
        #   4) ARAMA  - kimse yoksa besin ara
        #
        # Sabit tehdit refleksi yalnizca davranis genomu KAPALIYKEN
        # (BEHAVIOR_ENABLED = False) devreye girer; o zaman zaten
        # evrimlesecek bir tablo yoktur.

        # 1. DUVAR - gorunuyorsa kacin (fiziksel kisit)
        wall_data = self._detect_wall_in_vision(organism)
        if wall_data:
            avoid_dir = MoveDirection.calculate_wall_avoidance(self_pos, wall_data)
            if avoid_dir and avoid_dir.length() > 0:
                self.target_direction = avoid_dir
                self._reset_chemotaxis_sampling()
                return (self.target_direction, 'WALL_AVOID', avoid_dir * 25)

        # 2. TABLO - hucrenin kendi karari
        #
        # KACMAK her zaman oncelikli: yenmek her seyi bitirir.
        # YAKLASMAK / SALDIRMAK ise beslenmeyle YARISIR ve bu yarisin
        # sonucunu da bir gen belirler (sosyal_oncelik). Aksi halde koku
        # menzilindeki her komsu kemotaksiyi bastirir; hucre hic
        # beslenmeden omur boyu birilerinin pesinde kosar.
        # Tepki SUREKLI bir sayi: isaret yon, buyukluk kararlilik.
        # Cok zayif bir tepki (mutlak deger kucuk) beslenmenin onune
        # gecmez - hucre umursamiyor demektir.
        kararlilik = abs(float(behavior_response))
        genome_drives = (getattr(game_settings, 'BEHAVIOR_ENABLED', False)
                         and kararlilik > 0.05
                         and prey_dir is not None)
        # KACIS her zaman onceliklidir - yenmek her seyi bitirir. Ama
        # "kacis" bir emir degil, yeterince guclu bir NEGATIF tepkidir.
        kaciyor = float(behavior_response) <= -game_settings.KACIS_ESIGI
        if genome_drives and not kaciyor:
            b = getattr(organism, 'behavior', None)
            if b is not None and not b.sosyali_sec(scent_intensity):
                genome_drives = False
        if genome_drives:
            self.target_direction = prey_dir
            self._reset_chemotaxis_sampling()
            vec_type = 'ESCAPE' if float(behavior_response) < 0 else 'HUNT'
            return (self.target_direction, vec_type, prey_dir * 45)

        # 2b. Davranis genomu kapaliysa eski sabit refleks
        if not getattr(game_settings, 'BEHAVIOR_ENABLED', False)                 and self.behavioral_state.should_flee():
            closest_threat = min(nearby_threats,
                                 key=lambda k: self_pos.distance_to(k.pos))
            if self.escape_lock_timer > 0 and self.locked_escape_dir:
                self.target_direction = self.locked_escape_dir
            else:
                mem_data = memory_system.retrieve(closest_threat.uid)
                escape_dir = MoveDirection.calculate_threat_escape(
                    self_pos, closest_threat, mem_data)
                self.target_direction = escape_dir
                self.locked_escape_dir = escape_dir
                self.escape_lock_timer = 0.5
            self._reset_chemotaxis_sampling()
            return (self.target_direction, 'ESCAPE', self.target_direction * 40)

        self.locked_escape_dir = None
        self.escape_lock_timer = 0

        # 3. KOKU IZI - tablo susuyorsa baskasinin gectigi yerden kacin
        trail_mem = memory_system.retrieve("trail_prediction")
        if trail_mem:
            avoid_dir = MoveDirection.calculate_trail_avoid(self_pos, trail_mem)
            if avoid_dir and avoid_dir.length() > 0:
                self.target_direction = avoid_dir
                self._reset_chemotaxis_sampling()
                return (self.target_direction, 'TRAIL', avoid_dir * 50)

        # 3.5 Tablo susuyor ama gorulen bir av var: eski sabit takip
        if prey_dir is not None and getattr(game_settings,
                                            'PREY_VISION_PRIORITY', 1):
            self.target_direction = prey_dir
            self._reset_chemotaxis_sampling()
            return (self.target_direction, 'HUNT', prey_dir * 45)

        # 4. ARAMA: Levy tabanli kesif + kemotaksi egilimi
        #
        # Once IKI AYRI MOD vardi: koku varsa run-and-tumble, yoksa Levy
        # ucusu. Bu kurgu burnu olan hucreyi cezalandiriyordu. Levy ucusu
        # superdifuzyondur - kosular 10 saniyeye kadar uzar, hucre genis
        # bir alani tarar. Run-and-tumble ise saniyede bir yon degistiren
        # bir rastgele yuruyustur ve ayni surede cok daha az yol alir.
        # Yani KOKU ALMAK, iyi bir arama stratejisini kotusuyle
        # degistiriyordu; kemotaksinin kazandirdigi egilim bu kaybi
        # kapatmiyordu.
        #
        # Olculdu (6 tohum x 120 sn, yamali besin): yalnizca kamci tasiyan
        # hucre 14.68 besin, kamci+burun tasiyan 14.04. Yani burun tasimak
        # NET ZARARDI - bakim enerjisi ve surtunme goturuyor, karsiliginda
        # hicbir sey vermiyordu. Boyle bir dunyada kemoreseptor
        # evrimlesemez; olcut 2 icin gereken duyu-davranis baglantisi hic
        # kurulamaz.
        #
        # Dogru kurgu TEK bir aramadir: taban kesif her hucrede aynidir
        # (Levy), koku yalnizca KOSUNUN NE KADAR SURECEGINI degistirir.
        #   gradyan yukseliyorsa -> kosu uzar  (iyi yondeyim, devam)
        #   gradyan dusuyorsa    -> kosu kisalir (yanlis yon, hemen don)
        # Boylece burun hicbir zaman zarar vermez: bilgi yoksa davranis
        # burunsuzunkiyle birebir aynidir, bilgi varsa ustune egilim ekler.
        # E. coli'nin yaptigi da tam olarak budur - tumble sikligini
        # degistirir, yuzme bicimini degil.
        # UZAMSAL GRADYAN: iki ya da daha fazla kemoreseptoru olan hucre
        # kokunun YONUNU dogrudan okur; deneme yanilmayla aramasi gerekmez.
        # Zamansal kemotaksinin ustune degil YERINE gecer - eldeki bilgi
        # zaten yon, kosu uzunlugu ayarlamaya gerek yok.
        if koku_gradyani is not None:
            self.target_direction = koku_gradyani
            self.levy_timer = 0.0
            return (self.target_direction, None, None)

        self.levy_timer += dt
        uzatma = 1.0
        if scent_intensity > 0:
            # Algiyi pencere boyunca biriktir: kare basina (1/30 sn) olculen
            # fark, hucre o surede neredeyse hic yer degistirmedigi icin
            # sifira yakin cikar ve hicbir egilim uretmez.
            self._sample_accum += scent_intensity * dt
            self._sample_time += dt
            if self._sample_time >= self.sample_interval:
                window_mean = self._sample_accum / self._sample_time
                if self.last_perception is None:
                    delta = 0.0      # ilk pencere: karsilastiracak sey yok
                else:
                    delta = window_mean - self.last_perception
                self.last_perception = window_mean
                self.last_delta = delta
                self._sample_accum = 0.0
                self._sample_time = 0.0

            d = self.last_delta
            kazanc = (game_settings.TUMBLE_GAIN_POSITIVE if d > 0
                      else game_settings.TUMBLE_GAIN_NEGATIVE)
            tavan = game_settings.CHEMO_RUN_CLAMP
            uzatma = math.exp(kazanc * d)
            uzatma = max(1.0 / tavan, min(tavan, uzatma))
            # Gozlem icin: etkin tumble sikligi
            self.tumble_rate = 1.0 / max(1e-6, self.levy_run_duration * uzatma)
        else:
            self._reset_chemotaxis_sampling()

        if self.levy_timer >= self.levy_run_duration * uzatma:
            alpha = game_settings.LEVY_ALPHA
            min_step = game_settings.LEVY_MIN_STEP
            max_dur = game_settings.LEVY_MAX_DURATION
            u = max(0.001, random.random())
            self.levy_run_duration = min(min_step / (u ** (1.0 / (alpha - 1))),
                                         max_dur)
            self.levy_timer = 0.0
            # TUMBLE ACISI DUZGUN DAGILIMLI DEGIL.
            #
            # Her donuste tamamen rastgele bir yone bakmak, bir onceki
            # kosudan ogrenilen her seyi siler; gradyan yuruyusu ancak
            # yonde bir SUREKLILIK kalirsa ise yarar. E. coli'nin tumble
            # acisi ~68 derece ortalamalidir ve ileriye yanlidir.
            aci = random.gauss(0.0, game_settings.TUMBLE_ANGLE_SIGMA)
            if random.random() < 0.5:
                aci = -aci
            aci = max(-180.0, min(180.0, aci))
            self.target_direction = self.target_direction.rotate(aci)
            if self.target_direction.length() > 0:
                self.target_direction = self.target_direction.normalize()

        return (self.target_direction, None, None)

    def _reset_chemotaxis_sampling(self):
        """Algı penceresini sıfırla.

        Kaçış / iz / duvar dallarına sapıldığında pencere yarıda kalır.
        Eski ortalamayı saklamak, kemotaksiye dönüşte saniyeler öncesine
        göre sahte bir sıçrama üretip yanlış bir RUN/TUMBLE kararı verdirir.
        """
        self.last_perception = None
        self.last_delta = 0.0
        self._sample_accum = 0.0
        self._sample_time = 0.0
        self.tumble_rate = self.base_tumble_rate

    def _detect_wall_in_vision(self, organism):
        """
        Organizmanın görme alanında duvar olup olmadığını kontrol eder.
        Photoreceptor'ün görme mesafesini kullanır.

        Returns:
            dict: {'walls': [...], 'distances': {...}} veya None
        """
        # Görme mesafesini bul (en uzun menzilli Photoreceptor)
        vision_range = 0
        for organ in organism.organs:
            if isinstance(organ, Photoreceptor):
                if organ.logic.range > vision_range:
                    vision_range = organ.logic.range

        if vision_range == 0:
            return None

        pos = organism.pos
        walls = []
        distances = {}

        # Sol duvar kontrolü
        if pos.x < vision_range:
            walls.append('left')
            distances['left'] = pos.x

        # Sağ duvar kontrolü
        if pos.x > WIDTH - vision_range:
            walls.append('right')
            distances['right'] = WIDTH - pos.x

        # Üst duvar kontrolü
        if pos.y < vision_range:
            walls.append('top')
            distances['top'] = pos.y

        # Alt duvar kontrolü
        if pos.y > HEIGHT - vision_range:
            walls.append('bottom')
            distances['bottom'] = HEIGHT - pos.y

        if walls:
            return {'walls': walls, 'distances': distances}

        return None
import copy
import pygame
import random
import math
import game_settings
from entities.entity import Entity, SCALE
import interactions.reflexes
from organs.receptors.Photoreceptor.photoreceptor import Photoreceptor
from organs.receptors.Mechanoreceptor.mechanoreceptor import Mechanoreceptor
from organs.receptors.Mechanoreceptor.logic_mechanoreceptor import (
    MechanoreceptorLogic)
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.cilia.cilia import Cilia
from organs.central.cytoplasm.cytoplasm import Cytoplasm
from organs.peripheral.membrane.membrane import Membrane
from organs.central.vacuole.vacuole import Vacuole
from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
from organs.peripheral.weapons.weapons import (BaseWeapon, Toxin, Phagocytosis,
                                               WEAPON_CLASSES)
from systems.protein_systems.short_protein_memory.direction_memory import DirectionMemorySystem
from systems.motor_control.motor_calibration import MotorCalibration
from systems.motor_control.smart_flagella_controller import SmartFlagellaController
from systems.motor_control.smart_motor_brain import SmartMotorBrain
from systems.signaling.behavior_genome import BehaviorGenome
from systems.signaling.lineage import LineageSignature
from systems.signaling.scent_profile import scent_value

class Genome:
    """Sequential genetics - deterministic upgrade order with mutations."""

    def __init__(self, sequence=None):
        self.sequence = sequence or []
        self.current_index = 0
        self.cycle_count = 0

    def next_instruction(self):
        if not self.sequence:
            return None
        instruction = self.sequence[self.current_index]
        self.current_index += 1
        if self.current_index >= len(self.sequence):
            self.current_index = 0
            self.cycle_count += 1
            self._maybe_mutate()
        return instruction

    def mutate(self):
        """Genom dizisine mutasyon uygula; KAÇ değişiklik olduğunu döndür.

        Sayı, koku kimliğinin ıraksama birikimini besler: kokuyu bir zamanlayıcı
        değil, gerçekten biriken kalıtsal değişim değiştirir.
        """
        return self._maybe_mutate()

    def _maybe_mutate(self):
        if len(self.sequence) < 2:
            return 0
        changes = 0
        new_seq = list(self.sequence)

        # Point mutation: %10 per gene (upgrade_type changes)
        all_types = [
            'flagella', 'cilia', 'chemoreceptor', 'vision_angle', 'vision_range',
            'sound_radius', 'body_size', 'digestion_speed', 'ribosome_speed',
            'max_energy', 'move_regen', 'memory_length',
            'sound_focus',
            'membrane_integrity', 'wall', 'outer', 'capsule', 'efflux', 'repair', 'slip',
            'mucus', 'slayer',
            'stylet', 'harpoon', 'nematocyst', 'toxin', 'lysin', 'phagocytosis'
        ]
        for i in range(len(new_seq)):
            if random.random() < 0.10:
                old_type, old_idx = new_seq[i]
                new_type = random.choice(all_types)
                new_seq[i] = (new_type, old_idx)
                if new_type != old_type:
                    changes += 1

        # Swap: %10 (iki gen yer degistirir)
        if len(new_seq) >= 2 and random.random() < 0.10:
            i, j = random.sample(range(len(new_seq)), 2)
            new_seq[i], new_seq[j] = new_seq[j], new_seq[i]
            changes += 1

        # Insertion: %5 (rastgele gen kopyalanip eklenir)
        if random.random() < 0.05:
            gene = random.choice(new_seq)
            pos = random.randint(0, len(new_seq))
            new_seq.insert(pos, gene)
            changes += 1

        # Deletion: %5, min 3 gen
        if len(new_seq) > 3 and random.random() < 0.05:
            del new_seq[random.randint(0, len(new_seq) - 1)]
            changes += 1

        self.sequence = new_seq
        return changes

    @staticmethod
    def from_organism(organism):
        """Build genome from organism's current organs, shuffled."""
        genes = []
        organ_counts = {}

        for organ in organism.organs:
            if isinstance(organ, Flagella):
                key = 'flagella'
                idx = organ_counts.get(key, 0)
                organ_counts[key] = idx + 1
                genes.append(('flagella', idx))
            elif isinstance(organ, Cilia):
                key = 'cilia'
                idx = organ_counts.get(key, 0)
                organ_counts[key] = idx + 1
                genes.append(('cilia', idx))
            elif isinstance(organ, Photoreceptor):
                key = 'photoreceptor'
                idx = organ_counts.get(key, 0)
                organ_counts[key] = idx + 1
                genes.append(('vision_angle', idx))
                genes.append(('vision_range', idx))
            elif isinstance(organ, Mechanoreceptor):
                key = 'mechanoreceptor'
                idx = organ_counts.get(key, 0)
                organ_counts[key] = idx + 1
                # Kulagin IKI ayri gelisim ekseni var ve ikisi de ayri
                # cekilir: esik (ne kadar kucugunu duyar) ve kapsama
                # (nereden geldigini bilir).
                genes.append(('sound_radius', idx))
                genes.append(('sound_focus', idx))
            elif isinstance(organ, Chemoreceptor):
                key = 'chemoreceptor'
                idx = organ_counts.get(key, 0)
                organ_counts[key] = idx + 1
                genes.append(('chemoreceptor', idx))
            elif isinstance(organ, BaseWeapon):
                key = organ.__class__.__name__.lower()
                idx = organ_counts.get(key, 0)
                organ_counts[key] = idx + 1
                genes.append((key, idx))

        # System upgrades (index 0)
        if hasattr(organism, 'body'):
            genes.append(('body_size', 0))
            genes.append(('digestion_speed', 0))
        if hasattr(organism, 'ribosome'):
            genes.append(('ribosome_speed', 0))
        if hasattr(organism, 'vacuole'):
            genes.append(('max_energy', 0))
        if hasattr(organism, 'membrane'):
            genes.append(('move_regen', 0))
            # Savunma zar özelliğidir; genleri de zarla birlikte gelir
            for d in ('membrane_integrity', 'wall', 'outer',
                      'capsule', 'efflux', 'repair', 'slip',
                      'mucus', 'slayer'):
                genes.append((d, 0))
        genes.append(('memory_length', 0))

        random.shuffle(genes)
        return Genome(genes)


class Morphology:
    """İSKELET GENİ: hücrenin hangi organı, hangi açıda taşıdığı.

    Genome ile karıştırılmamalı:
      - Genome     : hangi organın GELİŞECEĞİ (yükseltme torbası)
      - Morphology : hangi organın VAR OLDUĞU ve NEREDE durduğu (vücut planı)

    Bölünmede yavrulara aktarılır. Bu sayede avlanma ödülü olarak kazanılan
    bir organ - konumuyla birlikte - kalıcı olarak soya geçer; alakasız bir
    yerden çıkan flagella nesiller boyu orada kalır.
    """

    # Avlanma ödülü olarak çıkabilecek organlar (iç organlar hariç)
    # Avlanma ödülü çekilişinin havuzu. Karar 1: saldırı organları hem
    # launcher'dan baştan eklenebilir hem de burada bulunur.
    SPAWNABLE = ("Flagella", "Cilia", "Chemoreceptor", "Photoreceptor",
                 "Mechanoreceptor",
                 "Stylet", "Harpoon", "Nematocyst", "Toxin", "Lysin",
                 "Phagocytosis")

    def __init__(self, parts=None):
        # [{"type": str, "angle": float(radyan), "params": {...}}, ...]
        self.parts = parts or []

    def add(self, otype, angle, params=None):
        self.parts.append({"type": otype, "angle": float(angle),
                           "params": dict(params or {})})

    def counts(self):
        out = {}
        for p in self.parts:
            out[p["type"]] = out.get(p["type"], 0) + 1
        return out

    def describe(self):
        return ", ".join(f"{k}x{v}" for k, v in sorted(self.counts().items()))

    @staticmethod
    def from_organism(organism):
        """Mevcut organlardan vücut planını çıkar."""
        m = Morphology()
        for organ in organism.organs:
            name = organ.__class__.__name__
            params = {}
            lg = organ.logic
            for attr in ("length", "size", "range", "angle", "power"):
                if hasattr(lg, attr):
                    try:
                        params[attr] = float(getattr(lg, attr))
                    except (TypeError, ValueError):
                        pass
            m.add(name, getattr(organ, "attachment_angle", 0.0), params)
        return m

    @staticmethod
    def build_organ(otype, angle, params=None):
        """Plandaki bir parçadan gerçek organ nesnesi üret."""
        params = params or {}
        if otype == "Flagella":
            return Flagella(attachment_angle=angle,
                            length=params.get("length", 10.0))
        if otype == "Cilia":
            return Cilia(attachment_angle=angle,
                         length=params.get("length", 3.0))
        if otype == "Chemoreceptor":
            return Chemoreceptor(attachment_angle=angle,
                                 length=params.get("length", 5.0))
        if otype == "Photoreceptor":
            return Photoreceptor(attachment_angle=angle,
                                 range=params.get("range", 25.0),
                                 angle=params.get("angle", math.radians(10.0)))
        if otype == "Mechanoreceptor":
            return Mechanoreceptor(attachment_angle=angle,
                                   size=params.get("size", 1.0))
        wcls = WEAPON_CLASSES.get(otype)
        if wcls is not None:
            return wcls(attachment_angle=angle, power=params.get("power", 1.0))
        return None


class Organism(Entity):
    #: Uzamsal koku gradyani (>=2 kemoreseptor varsa). Guvenli varsayilan.
    koku_gradyani = None
    #: Motor eforu (0..1). Davranis spektrumunun buyuklugu belirler.
    motor_efor = 1.0
    #: Sesin yonunu ne kadar sasirdigimiz (derece). Kapsama belirler.
    hedef_yon_hatasi = 0.0
    #: Gercek hareket yonu (koku bulutunun surüklenme yonu icin).
    hareket_yonu = None

    #: Gorme organi onbellegi icin guvenli varsayilan. recalculate_physics
    #  tazeler; ondan once can_see cagrilirsa gozsuz sayilir.
    _gozler = ()

    # --- Bölünme modu için sınıf düzeyi durum ---
    # Yavrulara benzersiz index vermek için sayaç. uid ("organism_{index}")
    # iz filtrelemesinde kullanıldığından çakışma olmamalı.
    _next_index = 1000
    # simulation.py her kare günceller; nüfus tavanı kontrolü için.
    population_count = 0

    def __init__(self, index, x, y, color):
        super().__init__(x, y, 10, 0, color)
        self.index = index
        self.organs = []

        self.radius = 10
        self.speed = 0
        self.max_turn_rate = 0
        self.max_energy = 50
        self.energy = 50

        # Fizik tabanlı hareket değişkenleri
        self.thrust_direction = 0  # Net itme yönü (lokal koordinat)
        self.torque_turn_rate = 0  # Torktan kaynaklanan dönme hızı
        
        self.direction_memory = DirectionMemorySystem(capacity=10)
        self.motor_calibration = MotorCalibration()
        self.flagella_controller = SmartFlagellaController()
        self.motor_brain = SmartMotorBrain()  # Akıllı motor koordinasyonu

        # Optimal ön hesaplama sistemi
        # 360 derece taranarak en hızlı gidilebilecek yön bulunur
        self.optimal_front_angle = 0.0  # Lokal koordinatta (radyan)
        self.optimal_front_speed = 0.0  # Bu yönde elde edilebilecek maksimum hız
        self.natural_thrust_offset = 0.0  # Geriye uyumluluk için (optimal_front_angle ile aynı)
        self.wander_timer = 0
        self.target_direction = pygame.math.Vector2(self.direction)
        self.target_movement = None  # Hedef hareket yönü (fizik tabanlı)
        self.max_memory_length = 100 
        
        self.reflex_timer = 0
        self.reflex_direction = pygame.math.Vector2(0, 0)
        self.reflex_speed = 0

        self.shutdown = False
        self.log_enabled, self.log_timer = False, 0
        self.stuck_timer, self.stuck_check_interval = 0, 2.0
        self.last_stuck_pos = pygame.math.Vector2(x, y)
        self.current_trail_escape_vector, self.current_calm_escape_vector = None, None
        self.current_wall_avoid_vector = None  # Duvar kaçınma vektörü (turuncu)
        self.current_hunt_vector = None        # Av takip vektörü (kırmızı)
        self.current_scent_intensity = 0.0  # Anlık koku yoğunluğu
        self.genome = None  # Sequential genetics - initialized after organs are added
        self.pending_children = []  # bölünmede doğan, simulation'a katılacak yavrular
        self.morphology = None      # iskelet geni; organlar eklendikten sonra kurulur
        self.prey_eaten = 0          # kac hucre yendi (istatistik)
        # Omur boyu alinan besin. Sagkalimin degil BASARININ olcusu:
        # iki hucre de hayattaysa hangisinin daha iyi beslendigini baska
        # turlu gormek mumkun degil.
        self.toplam_besin = 0
        # Kac kez silah kullanildi. "Silah tasimak" ile "silah KULLANMAK"
        # ayri seyler: ucuz tasinan bir silah populasyonda suruklenmeyle
        # de yayilabilir. Avlanmanin gercekten basladigini soyleyebilmek
        # icin atisin da sayilmasi gerekir.
        self.atis_sayisi = 0
        self.pending_organ_rolls = 0  # avlanmadan kazanılan, mitozda çekilecek gelişim hakları
        self.dead = False           # simulation.py listeden düşürür
        self.death_cause = None     # 'aclik' | 'avlandi' | 'elendi' | 'kaotropi'
        self.starve_timer = 0.0     # enerjisiz geçen süre
        self.stun_timer = 0.0       # fagositoz sırasında hareketsizlik
        # Davranış genomu: uyaran -> tepki. Herkes RASTGELE başlar.
        self.behavior = BehaviorGenome.random()
        self.lineage = LineageSignature()
        # Av yedikce biriken, zamanla temizlenen metabolik sizinti
        self.kairomone = 0.0
        self.attack_targets = set()   # tablonun 'saldır' dediği hedefler
        self.current_response = 'ignore'
        # --- BAGLANMA ---
        self.bound_target = None    # tuttugum hucre (saldirgan tarafi)
        # Molekul fizigi hucrenin GORELI cercevesinde calisir: hucre
        # kaydiginda molekul duvara carpar, konumu kendiliginden degisir.
        self.onceki_pos = pygame.math.Vector2(self.pos)
        self.zarf_nesli = 0          # zarf geometrisi degisince artar
        self.molekuller = []
        # Su an sarmalanan besin (fagositoz gorseli icin)
        self.yutulan_besin = None
        self.bound_by = None        # beni tutan hucre (hedef tarafi)
        self.bind_timer = 0.0       # ne kadar suredir tutuyorum
        self.tether_timer = 0.0     # nematosist ipiyle tutuluyorum
        self.consumed = False       # leşi biri aldı mı (çift ödülü önler)

    def add_organ(self, organ):
        # KURESEL OLCEK tek gecis noktasi. Organlar bircok dosyada
        # (kaotropi/optropi/notropi/launcher) ayri ayri kuruluyor;
        # olcegi her birinde tekrarlamak yerine burada uygulanir.
        try:
            import game_settings as _gs
            from organs.registry import olcekle
            olcekle(organ, float(getattr(_gs, 'WORLD_SCALE', 1.0)))
        except Exception:
            pass
        self.organs.append(organ)
        if isinstance(organ, Membrane): self.membrane = organ
        if isinstance(organ, Cytoplasm): self.body = organ
        if isinstance(organ, Vacuole): self.vacuole = organ
        if isinstance(organ, Cytoskeleton): self.cytoskeleton = organ
        if organ.__class__.__name__ == "Ribosome": self.ribosome = organ

        # Cilia eklendiyse, tüm cilia yönlerini güncelle (koordineli teğet model)
        if isinstance(organ, Cilia):
            self._update_cilia_directions()

        # Motor organ eklendiyse, optimal önü yeniden hesapla
        if isinstance(organ, (Flagella, Cilia)):
            self._update_optimal_front()

        if hasattr(self, 'body'): self.recalculate_physics()

    @property
    def drag_factor(self):
        """Stokes sürüklenmesi: v = F / (6πμr) -> bölen (yarıçap/referans)^üs.

        Tek yerde tanımlı ki gerçek hız ile optimal-ön tahmini aynı fiziği
        kullansın.
        """
        ref = max(1e-6, game_settings.DRAG_REF_RADIUS)
        return max(1e-6, (self.suruklenme_yaricapi / ref)
                   ** game_settings.DRAG_EXPONENT)

    @property
    def suruklenme_yaricapi(self):
        """Suruklenmeyi belirleyen ETKIN yaricap: govde + organlar.

        Organlarin hicbir suruklenme bedeli yoktu - olculdu, otuz
        fotoreseptor takmak hizi 10.00'dan 10.00'a getiriyordu. Oysa
        alicilar, kamcilar ve silahlar akisin icinde durur. Organ alani
        govde alanina orani kadar etkin yaricapi buyutur.
        """
        r = max(0.1, self.radius)
        try:
            govde = getattr(getattr(self, 'body', None), 'logic', None)
            alan = getattr(govde, 'total_area', 0.0)
            if alan > 0:
                oran = self.calculate_organ_area() / alan
                r *= 1.0 + game_settings.ORGAN_DRAG_GAIN * oran
        except Exception:
            pass
        return r

    def calculate_optimal_thrust_direction(self):
        """
        Cilia dağılım eksenine dik olan optimal itme yönünü hesaplar.
        Kürek teknesi mantığı: kürekler teknın yanlarında, itme ileri/geri.

        Returns:
            float: Optimal itme yönü (radyan)
        """
        cilia_organs = [o for o in self.organs if isinstance(o, Cilia)]
        if not cilia_organs:
            return math.pi  # Varsayılan: geri

        # Cilia pozisyonlarının vektörel toplamı
        sum_x, sum_y = 0.0, 0.0
        for cilia in cilia_organs:
            sum_x += math.cos(cilia.attachment_angle)
            sum_y += math.sin(cilia.attachment_angle)

        # Dağılım ekseni (cilia'ların ortalama yönü)
        if abs(sum_x) < 0.01 and abs(sum_y) < 0.01:
            # Simetrik dağılım - varsayılan eksen kullan
            axis_angle = 0
        else:
            axis_angle = math.atan2(sum_y, sum_x)

        # Optimal itme = eksene dik (saat yönünde 90°)
        optimal_direction = axis_angle + math.pi/2
        return optimal_direction

    def calculate_optimal_front(self):
        """
        360 dereceyi tarayarak en hızlı gidilebilecek yönü (optimal ön) hesapla.

        Her açı için:
        1. Flagella'ları o açıya max katkı sağlayacak şekilde deflection ayarla
        2. Cilia'ları o açı için optimal power distribution ayarla
        3. Net itme vektörünü hesapla
        4. Target açıya olan projeksiyonu bul

        Returns:
            tuple: (optimal_angle, max_speed) - Lokal koordinatta radyan ve hız birimi
        """
        best_angle = 0.0
        best_speed = 0.0

        # Motor organları topla
        flagellas = [o for o in self.organs if isinstance(o, Flagella)]
        cilias = [o for o in self.organs if isinstance(o, Cilia)]

        if not flagellas and not cilias:
            return 0.0, 0.0  # Motor organ yok

        # Kaba tarama (STEP derece) + tepe civarinda 1 derecelik ince tarama.
        # Duz 360 tarama, organ sayisiyla dogru orantili maliyetliydi ve
        # add_organ her cagrildiginda calistigi icin organ biriktikce
        # karesel bir yavaslamaya yol aciyordu (200 organda ~200 ms donma).
        STEP = 8

        def probe(deg):
            return self._simulate_thrust_for_angle(math.radians(deg), flagellas, cilias)

        best_deg = 0
        for degree in range(0, 360, STEP):
            speed = probe(degree)
            if speed > best_speed:
                best_speed = speed
                best_deg = degree

        # Kaba taramanin bulduğu tepenin iki yanini 1 derecelik adimlarla tara
        for degree in range(best_deg - STEP, best_deg + STEP + 1):
            speed = probe(degree % 360)
            if speed > best_speed:
                best_speed = speed
                best_deg = degree % 360

        # Sürüklenme yönden bağımsız bir skaler olduğu için EN İYİ AÇIYI
        # değiştirmez; ama bildirilen hız gerçek hızla uyuşmalı.
        return math.radians(best_deg % 360), best_speed / self.drag_factor

    def _simulate_thrust_for_angle(self, target_angle, flagellas, cilias):
        """
        Verilen açıya gitmek için tüm motorları optimal kullandığımızda
        elde edilecek hızı hesapla.

        Args:
            target_angle: Hedef hareket yönü (lokal koordinat, radyan)
            flagellas: Flagella organlarının listesi
            cilias: Cilia organlarının listesi

        Returns:
            float: Target yönünde elde edilecek hız (projeksiyon)
        """
        net_x, net_y = 0.0, 0.0

        # --- FLAGELLA HESABI ---
        for flagella in flagellas:
            # Flagella'nın temel özellikleri
            base_thrust_angle = flagella.attachment_angle  # Takılı olduğu noktadan dışa iter
            max_deflection = flagella.logic.max_deflection
            thrust_magnitude = flagella.logic.base_thrust  # Tam güçte

            # Hedef: Tepki kuvveti target_angle yönünde olmalı
            # Tepki = thrust + π, yani thrust = target_angle + π - π = target_angle
            # Ama aslında: reaction = thrust + π → thrust = reaction - π
            # Biz target_angle'a gitmek istiyoruz, yani reaction = target_angle olmalı
            # Bu durumda: thrust = target_angle - π (veya target_angle + π, aynı şey)
            desired_thrust = target_angle + math.pi

            # Base thrust'tan desired thrust'a gitmek için gereken deflection
            needed_deflection = desired_thrust - base_thrust_angle

            # Normalize et (-π, π) arasına
            while needed_deflection > math.pi:
                needed_deflection -= 2 * math.pi
            while needed_deflection < -math.pi:
                needed_deflection += 2 * math.pi

            # Max deflection sınırı içinde tut
            actual_deflection = max(-max_deflection, min(max_deflection, needed_deflection))
            actual_thrust = base_thrust_angle + actual_deflection

            # Tepki yönü (hareket yönü) = thrust + π
            reaction_angle = actual_thrust + math.pi

            # Net kuvvete katkı
            net_x += math.cos(reaction_angle) * thrust_magnitude
            net_y += math.sin(reaction_angle) * thrust_magnitude

        # --- CILIA HESABI ---
        # Cilia'lar için: Her cilia'nın target_angle'a katkısını hesapla
        # Koordineli çalışma: Dönüş yönündekiler güçlü, ters yöndekiler zayıf
        for cilia in cilias:
            # Cilia teğet yönde iter: attachment_angle + π/2 veya - π/2
            # Hangi teğet yönün target'a daha yakın olduğunu bul
            attachment = cilia.attachment_angle

            # İki olası teğet yön
            tangent_cw = attachment - math.pi/2   # Saat yönünde teğet
            tangent_ccw = attachment + math.pi/2  # Saat yönü tersine teğet

            # Her iki yönün reaction'ı (hareket yönü)
            reaction_cw = tangent_cw + math.pi
            reaction_ccw = tangent_ccw + math.pi

            # Hangisi target'a daha yakın?
            diff_cw = abs(self._normalize_angle(target_angle - reaction_cw))
            diff_ccw = abs(self._normalize_angle(target_angle - reaction_ccw))

            if diff_cw < diff_ccw:
                best_reaction = reaction_cw
                best_thrust = tangent_cw
            else:
                best_reaction = reaction_ccw
                best_thrust = tangent_ccw

            # Target yönüne katkı (cosine similarity)
            contribution = math.cos(self._normalize_angle(target_angle - best_reaction))

            # Katkıya göre güç ayarla (0.2 - 1.0 arası)
            if contribution > 0:
                power = 0.2 + 0.8 * contribution  # Pozitif katkı → güçlü
            else:
                power = 0.2  # Negatif katkı → minimum güç

            thrust_magnitude = cilia.logic.base_thrust_magnitude * power

            # Net kuvvete katkı
            net_x += math.cos(best_reaction) * thrust_magnitude
            net_y += math.sin(best_reaction) * thrust_magnitude

        # Net kuvvet vektörü
        net_magnitude = math.sqrt(net_x**2 + net_y**2)

        if net_magnitude < 0.001:
            return 0.0

        net_angle = math.atan2(net_y, net_x)

        # Target yönündeki projeksiyon (bu yönde elde edilecek hız)
        angle_diff = self._normalize_angle(target_angle - net_angle)
        projection = net_magnitude * math.cos(angle_diff)

        return max(0.0, projection)

    def _normalize_angle(self, angle):
        """Açıyı -π ile +π arasına normalize et."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def _update_optimal_front(self):
        """
        Optimal önü yeniden hesapla.
        Motor organlar değiştiğinde çağrılmalı.
        """
        self.optimal_front_angle, self.optimal_front_speed = self.calculate_optimal_front()
        # Geriye uyumluluk için natural_thrust_offset'i de güncelle
        self.natural_thrust_offset = self.optimal_front_angle

    def _update_cilia_directions(self):
        """
        Tüm cilia'ların optimal itme yönünü hesapla ve ayarla.
        Koordineli teğet model: Tüm cilia'lar aynı yöne iter.

        NOT: Fizik sistemi LOKAL koordinat kullanıyor (hücre yönüne göre).
        Bu yüzden global optimal yönü lokal koordinata çeviriyoruz.
        """
        optimal_dir_global = self.calculate_optimal_thrust_direction()

        # Global -> Lokal dönüşüm: hücre yönünü çıkar
        cell_heading = math.atan2(self.direction.y, self.direction.x)
        optimal_dir_local = optimal_dir_global - cell_heading

        for organ in self.organs:
            if isinstance(organ, Cilia):
                organ.set_optimal_direction(optimal_dir_local)

    def set_cilia_reverse(self, reverse=True):
        """
        Geri hareket için cilia yönlerini tersine çevir.

        Args:
            reverse: True ise geri git, False ise normal yön
        """
        optimal_dir_global = self.calculate_optimal_thrust_direction()
        if reverse:
            optimal_dir_global += math.pi  # 180° döndür

        # Global -> Lokal dönüşüm
        cell_heading = math.atan2(self.direction.y, self.direction.x)
        optimal_dir_local = optimal_dir_global - cell_heading

        for organ in self.organs:
            if isinstance(organ, Cilia):
                organ.set_optimal_direction(optimal_dir_local)

    def update_motor_deflection(self, deflection):
        """
        Tüm motor organların thrust açılarını ayarlar (eski metot, geriye uyumluluk).
        """
        self.update_cilia_deflection(deflection)

    def update_cilia_deflection(self, deflection):
        """
        Koordineli teğet modelde cilia kontrolü.
        Optimal yönün bir tarafındaki cilia'lar güçlü, diğer taraftakiler zayıf.
        Flagella'lar SmartFlagellaController tarafından yönetiliyor.
        """
        optimal_dir = self.calculate_optimal_thrust_direction()

        for organ in self.organs:
            # Sadece Cilia için (set_turn_control olan organlar)
            if hasattr(organ.logic, 'set_turn_control'):
                # Cilia'nın optimal yöne göre pozisyonu
                relative_angle = organ.attachment_angle - optimal_dir
                position_factor = math.sin(relative_angle)

                power_boost = 1.0 - (position_factor * deflection * 0.8)
                power_boost = max(0.2, min(1.8, power_boost))

                organ.logic.set_turn_control(power_boost)
                organ.logic.set_deflection(deflection * 0.3)

    def reset_motor_deflection(self):
        """Tüm motor organları temel konuma döndür"""
        self.reset_cilia_deflection()

    def reset_cilia_deflection(self):
        """Sadece Cilia'ları temel konuma döndür"""
        for organ in self.organs:
            if hasattr(organ.logic, 'set_turn_control'):
                if hasattr(organ.logic, 'reset_deflection'):
                    organ.logic.reset_deflection()
                if hasattr(organ.logic, 'set_turn_control'):
                    organ.logic.set_turn_control(1.0)

    def recalculate_physics(self):
        """
        Fizik tabanlı hareket hesabı.
        Her motor organın pozisyonu ve itme yönü dikkate alınır.
        Asimetrik yerleşim → tork → dönme
        """
        # Yarıçapı ÖNCE güncelle: tork kolları, sürüklenme ve atalet bu
        # değeri kullanıyor. Eskiden en sonda güncelleniyordu ve tüm hesap
        # bir önceki yarıçapla yapılıyordu (gövde büyütüldüğünde hız bir
        # kare boyunca eski değerde kalıyordu).
        if hasattr(self, 'body'):
            # YARICAP = SITOPLAZMA + ZARF.
            #
            # Onceden `radius` yalnizca sitoplazmanin yaricapiydi, ama hucre
            # ekranda zarfla birlikte cizilir. Ikisini ayirmak iki yanlisin
            # arasinda sikisip kaliyordu:
            #   - zarfi disari cizince temas cekirdekte oluyordu, besin
            #     dokundugu anda gorsel olarak hucrenin ICINDE kaliyordu;
            #   - zarfi yaricapin icine oturtunca katman eklemek
            #     SITOPLAZMAYI eziyordu.
            # Dogrusu: hucrenin yaricapi zarfiyla birlikte olcuulen sey.
            # Sitoplazma kendi boyunu korur, zarf DISARI dogru eklenir ve
            # temas/ortusme/organ tutunmasi hep bu dis sinirda olur.
            cek = self.body.logic.radius
            try:
                import lab as _l
                zar = getattr(getattr(self, 'membrane', None), 'logic', None)
                self.radius = cek * _l.zarf_orani(zar)
            except Exception:
                self.radius = cek

        # Gorme organlari onbellegi - organ listesi her degistiginde
        # buradan gecilir, ayrica aranmasi gerekmez.
        self._gozler = [o for o in self.organs if isinstance(o, Photoreceptor)]

        boost = self.membrane.logic.calcium_boost if hasattr(self, 'membrane') else 1.0
        # Davranis spektrumunun belirledigi motor eforu ITKIYE dogrusal girer.
        boost *= float(getattr(self, 'motor_efor', 1.0))

        # Net kuvvet ve tork hesabı
        net_force_x = 0.0
        net_force_y = 0.0
        net_torque = 0.0

        for organ in self.organs:
            if hasattr(organ.logic, 'thrust_magnitude'):
                # current_thrust_angle kullan (dinamik)
                thrust_angle = getattr(organ.logic, 'current_thrust_angle',
                                      getattr(organ.logic, 'thrust_angle', math.pi))

                # Organın pozisyonu (hücre merkezine göre, lokal koordinat)
                r_x = math.cos(organ.attachment_angle) * self.radius
                r_y = math.sin(organ.attachment_angle) * self.radius

                # İtme kuvveti vektörü (lokal koordinat)
                thrust_mag = organ.logic.thrust_magnitude * boost
                f_x = math.cos(thrust_angle) * thrust_mag
                f_y = math.sin(thrust_angle) * thrust_mag

                # Net kuvvete ekle
                net_force_x += f_x
                net_force_y += f_y

                # Tork hesabı: τ = r × F_tepki (2D cross product)
                # Tepki kuvveti = -F (thrust'ın tersi)
                # Pozitif tork = saat yönünün tersine (counterclockwise)
                # Negatif tork = saat yönünde (clockwise)
                torque = -(r_x * f_y - r_y * f_x)  # Negatif çünkü tepki kuvveti
                net_torque += torque

        # Hız: Net kuvvetin büyüklüğü.
        #
        # Motor organi OLMAYAN hucre YUZEMEZ. Onceden sabit `thrust = 5.0`
        # veriliyordu - hem fizige aykiriydi (kamcisiz bakteri kendini
        # itemez) hem de zayif motoru olan bir hucreninkinden (min 1.0)
        # DAHA FAZLAYDI. Olculdu: hicbir organi olmayan hucre 200 px/sn ile
        # yuzuyordu, yani dunyayi 6 saniyede geciyordu.
        # ITME TABANI YOK.
        #
        # Burada `max(1.0, net_force_mag)` vardi ve motor fizigini fiilen
        # devre disi birakiyordu: olculdu, silialarin urettigi net kuvvet
        # 0.06-0.17 arasinda: yani HER motorlu hucre, silialari nerede
        # olursa olsun, tabandan gelen 1.0 ile ayni hizda (2.00 px/sn)
        # yuzuyordu. Bir yanina uc silia takilmis hucrenin duz gitmesinin
        # sebebi buydu - onu silialari degil taban itiyordu.
        #
        # Dusuk Reynolds rejiminde atalet yoktur: hiz ANLIK kuvvetle
        # dogru orantilidir. Kuvvet yoksa hareket de yoktur.
        net_force_mag = math.sqrt(net_force_x**2 + net_force_y**2)
        thrust = net_force_mag

        # SÜRÜKLENME: Stokes rejiminde v = F / (6πμr), yani hız yarıçapla
        # ters orantılı. Flagella ve cilia'nın katkısı zaten net_force_mag
        # içinde (uzunluk x çarpan x güç, yönleriyle vektörel toplanmış);
        # eksik olan tek şey gövdenin sürüklenmesiydi.
        #     hız = net itme * (referans yarıçap / yarıçap) ^ üs
        self.speed = thrust * game_settings.THRUST_SCALE / self.drag_factor

        # Hareket yönü = kuvvet yönünün tersi (Newton'un 3. yasası: tepki kuvveti)
        # Flagella geriye iter → Hücre ileriye gider
        if net_force_mag > 0.01:
            force_angle = math.atan2(net_force_y, net_force_x)
            self.thrust_direction = force_angle + math.pi  # Tepki = ters yön
        else:
            self.thrust_direction = 0  # İleri

        # DONME SURTUNMESI (atalet degil).
        #
        # Dusuk Reynolds rejiminde atalet yoktur: acisal hiz = tork /
        # surtunme. Bicim zaten boyleydi ama bolen `0.2 * r^2` idi; Stokes
        # donme surtunmesi a^3 ile buyur, oteleme a ile. Ayni dosyada
        # oteleme dogru olcekleniyordu, donme degil - buyuk hucre olmasi
        # gerekenden kolay doniyordu (yaricap 40'ta 35.8 yerine 9.0 d/s).
        #
        # Katsayi GOVDE yaricapi DRAG_REF_RADIUS iken eski bolenle ayni
        # degeri verir; bolende artik organlari da iceren etkin yaricap
        # kullanildigi icin gercek donme buna gore ayrica yavaslar.
        ref = max(1e-6, game_settings.DRAG_REF_RADIUS)
        us = game_settings.ROT_DRAG_EXPONENT
        k = 0.2 / (ref ** (us - 2.0))
        rr = max(0.1, self.suruklenme_yaricapi)
        rot_drag = max(1.0, k * (rr ** us))
        self.torque_turn_rate = net_torque / rot_drag

        # Duvar/kapsül ağırlığı hücreyi yavaşlatır
        if hasattr(self, 'membrane'):
            self.speed *= self.membrane.logic.speed_multiplier

        # Maksimum dönüş hızı
        self.max_turn_rate = max(0.05, abs(self.torque_turn_rate) * 2)

        # Diğer fiziksel özellikler (yarıçap yukarıda güncellendi)
        if hasattr(self, 'vacuole'):
            self.max_energy = self.vacuole.logic.capacity

    @property
    def uid(self): return f"organism_{self.index}"
    @property
    def current_path_end(self): return self.pos + self.direction * self.speed * 2.0
    @property
    def etc_efficiency(self):
        """Membranın sindirilen besinden enerji çıkarma verimliliği.

        'move_regen' geniyle yükseltilir. Eskiden saniyede eklenen bedava
        enerji miktarıydı; artık besin başına kazancın çarpanı.

        YUZEY/HACIM YASASI. Enerji uretimi (ETC) ZARDA olur, bakim ise
        SITOPLAZMANIN tamaminda. Zar cevreyle, sitoplazma alanla buyur;
        yani hucre irilestikce birim hacim basina dusen zar azalir ve
        besinden cikarabildigi enerji duser. Hucrelerin neden sinirsiz
        buyumedigini aciklayan sey budur ve modelde YOKTU.

        Yoklugunun sonucu olculdu: govde 2.0'dan 4.18'e cikti, uzerine
        3.92 katman zirh bindi, yaricap ~100 px oldu ve 200 hucre 2400x1600
        haritanin tamamini kaplayip besini SIFIRA indirdi (hiz 1.2 px/sn,
        kemoreseptor 0.00). Irilesmek her seyi cozuyordu: buyuk hucre
        koklamadan da besine carpiyor, zirhi sayesinde de yenmiyordu.
        Duyu ve davranis boyle bir dunyada gereksizdir.

        Carpan referans boyutta 1.0'dir; iki kat iri hucre besinden yarisi
        kadar enerji cikarir.
        """
        taban = self.membrane.logic.energy_regen if hasattr(self, 'membrane') else 1.0
        govde = getattr(getattr(self, 'body', None), 'logic', None)
        if govde is None:
            return taban
        ref = max(0.1, game_settings.YUZEY_HACIM_REF)
        return taban * min(1.0, ref / max(0.1, float(govde.size)))

    @property
    def move_regen(self):
        """Geriye uyumluluk: etc_efficiency ile aynı değer."""
        return self.etc_efficiency
    @property
    def memory(self):
        self.direction_memory.update()
        return self.direction_memory.memory_map

    # ORGAN YOKSA DUYU DA YOK.
    #
    # Bu uc ozellik organ bulunamayinca bir VARSAYILAN donduruyordu: kulagi
    # olmayan hucre 30 px duyuyor, burnu olmayan hucre koku aliyor, gozu
    # olmayan hucre 25 px goruyordu. Bedava duyu iki seyi birden bozar:
    #   - "ozellesmemis baslangic" yalan olur; hucre zaten her seyi algilar,
    #   - reseptor gelistirmenin bir getirisi kalmaz, cunku ONU TASIMAYAN
    #     da ayni bilgiye sahiptir. Yani duyu organlarinin evrimlesmesini
    #     saglayacak secilim baskisi hic dogmaz.
    # Artik algi organa baglidir: yoksa menzil sifirdir ve o kanal susar.

    @property
    def sound_radius(self):
        m = next((o for o in self.organs if isinstance(o, Mechanoreceptor)), None)
        return m.logic.sensitivity if m else 0.0

    @property
    def vision_range(self):
        p = next((o for o in self.organs if isinstance(o, Photoreceptor)), None)
        return p.logic.range if p else 0.0

    @property
    def smell_range(self):
        """Koku menzili: kemoreseptor uzadikca uzar. Koni YOK."""
        c = next((o for o in self.organs if isinstance(o, Chemoreceptor)), None)
        if c is None:
            return 0.0
        return game_settings.SMELL_RANGE_BASE * c.logic.length

    @property
    def scent_value(self):
        """Bu hücre NE KADAR kokuyor: organlarının ağırlıklı toplamı.

        Sürekli bir büyüklüktür ve geliştikçe büyür. Bu sorun değildir,
        çünkü mutlak okunmaz: algılayan hücre kendi puanına oranla okur.

        ONBELLEKLI: her hucre komsularinin koku puanini her karede tek tek
        okuyor; 200 hucrede bu, ayni toplamin saniyede yuz binlerce kez
        bastan hesaplanmasi demekti. Puan yalnizca organ ya da katman
        degistiginde degisir, o da bolunme ve gelisim anlarinda olur -
        kare basina bir kez tazelemek fazlasiyla yeterli (update icinde).
        """
        v = self._koku_onbellek
        if v is None:
            v = self._koku_onbellek = scent_value(self)
        return v

    _koku_onbellek = None

    def koku_kaynagi(self):
        """Bu hucrenin kokusunun ETKIN kaynagi (konumu degil).

        Hizli yuzen bir cisim kendi bulutunu geride birakir; kaynak
        gittigi yonun tersine `hiz x KOKU_SURUKLENME` kadar otelenir.
        """
        yon = getattr(self, 'hareket_yonu', None)
        if yon is None or self.speed <= 0.0:
            return self.pos
        return self.pos - yon * (self.speed
                                 * game_settings.KOKU_SURUKLENME)

    def koku_tazele(self):
        self._koku_onbellek = scent_value(self)
        return self._koku_onbellek

    def is_kin(self, other):
        """Karsidakini akraba olarak TANIYOR muyum?

        Tek yonludur: benim reseptorum onun molekulunu okuyor mu. Bu yuzden
        kulak misafiri olmak ve taklit mumkundur.
        """
        a = getattr(self, 'lineage', None)
        b = getattr(other, 'lineage', None)
        if a is None or b is None:
            return False
        return a.matches(b)

    @property
    def vision_angle(self):
        p = next((o for o in self.organs if isinstance(o, Photoreceptor)), None)
        return p.logic.angle if p else 0.75
    @property
    def propulsion_power(self):
        boost = self.membrane.logic.calcium_boost if hasattr(self, 'membrane') else 1.0
        return (sum(o.logic.thrust_magnitude * 100 for o in self.organs if isinstance(o, Cilia)) or 10) * boost

    def draw(self, screen): 
        self.direction_memory.draw(screen, self.color)
        # GOVDE HER ZAMAN CIZILIR.
        #
        # Govdeyi Cytoplasm organi ciziyordu; sitoplazmasi olmayan hucre
        # tamamen GORUNMEZ oluyordu - organ listesi bosaltilinca oyunda ve
        # editorde yalnizca koku izleri goruluyordu, hucrenin kendisi degil.
        # Oysa konum ve yaricap organlardan bagimsiz vardir; hucre hicbir
        # kosulda gorunmez olmamali, yoksa tiklanip secilemez de.
        if not any(o.__class__.__name__ == 'Cytoplasm' for o in self.organs):
            r = max(3, int(getattr(self, 'radius', 10)))
            p = (int(self.pos.x), int(self.pos.y))
            govde = pygame.Surface((r * 2 + 4,) * 2, pygame.SRCALPHA)
            pygame.draw.circle(govde, (*self.color, 70), (r + 2, r + 2), r)
            screen.blit(govde, (p[0] - r - 2, p[1] - r - 2))
            pygame.draw.circle(screen, self.color, p, r, 1)

        # ZAR KATMANLARI + GOZENEKLER. Cizimin tamami lab.hucreyi_ciz'de:
        # oyun, kamera yakinlastirmasi ve editor onizlemesi ayni yoldan
        # gecsin diye. Cizim sirasi hucrenin yapisini izler: ic organlar
        # cekirdekte -> zarf disarida (gercek delikleriyle) -> dis organlar
        # zarfin dis yuzeyinde.
        try:
            import lab as _lab
        except Exception:
            _lab = None
        if _lab is not None and hasattr(self, 'membrane'):
            _g = getattr(game_settings, 'GORUNUM_OLCEGI', 1.0)
            _lab.hucreyi_ciz(screen, self, self.pos, _g)
            self.molekulleri_ciz(screen, olcek=_g)
        else:
            for organ in self.organs:
                organ.draw(screen, self)

        if self.current_trail_escape_vector:
            end = self.pos + self.current_trail_escape_vector
            pygame.draw.line(screen, (0, 255, 255), self.pos, end, 3)
            pygame.draw.circle(screen, (0, 255, 255), (int(end.x), int(end.y)), 4)
        if self.current_calm_escape_vector:
            end = self.pos + self.current_calm_escape_vector
            pygame.draw.line(screen, (255, 255, 255), self.pos, end, 3)
            pygame.draw.circle(screen, (255, 255, 255), (int(end.x), int(end.y)), 4)
        if self.current_hunt_vector:
            end = self.pos + self.current_hunt_vector
            pygame.draw.line(screen, (255, 60, 60), self.pos, end, 2)   # kırmızı - av takibi
            pygame.draw.circle(screen, (255, 60, 60), (int(end.x), int(end.y)), 4)
        if self.current_wall_avoid_vector:
            end = self.pos + self.current_wall_avoid_vector
            pygame.draw.line(screen, (255, 140, 0), self.pos, end, 2)  # Turuncu - duvar kaçınma
            pygame.draw.circle(screen, (255, 140, 0), (int(end.x), int(end.y)), 3)

        # Koku yoğunluğu yazısı
        if self.current_scent_intensity > 0:
            font = pygame.font.Font(None, 18)
            text = f"{self.current_scent_intensity:.2f}"
            text_surface = font.render(text, True, (200, 255, 200))
            text_pos = (int(self.pos.x + self.radius + 5), int(self.pos.y - 8))
            screen.blit(text_surface, text_pos)

    def can_see(self, target):
        # GOZ YOKSA HIC HESAPLAMA.
        #
        # Eskiden fark vektoru, uzunlugu ve iki atan2 gorme organi olup
        # olmadigina BAKILMADAN hesaplaniyordu. Gozsuz bir populasyonda
        # bu, kare basina N^2 kez yapilip her seferinde False donuyordu -
        # olcumde karenin en pahali tek fonksiyonuydu. Basit bir hucrenin
        # gormeye calismasi bedava olmali, cunku denemiyor bile.
        gozler = self._gozler
        if not gozler:
            return False
        to_t = target.pos - self.pos; dist = to_t.length()
        target_radius_angle = math.degrees(math.atan2(target.radius, dist)) if dist > 0 else 0
        for o in gozler:
            if True:
                organ_pos = o.get_absolute_position(self.pos, self.direction, self.radius)
                outward_dir = (organ_pos - self.pos).normalize() if (organ_pos - self.pos).length() > 0 else self.direction
                base_angle = math.degrees(math.atan2(outward_dir.y, outward_dir.x))
                target_angle = math.degrees(math.atan2(to_t.y, to_t.x))
                diff = abs(target_angle - base_angle)
                if diff > 180: diff = 360 - diff
                if dist <= o.logic.range + target.radius:
                    if diff <= (math.degrees(o.logic.angle)/2) + target_radius_angle: return True
        return False

    def can_hear(self, target): return self.pos.distance_to(target.pos) <= self.sound_radius + target.radius

    def calculate_organ_area(self):
        total = 0
        for o in self.organs:
            # Cytoplasm'ın kendi alanını (body) hesaplamaya dahil etmiyoruz çünkü o kabuk.
            if o == self.body: continue
            if hasattr(o.logic, 'area'): total += o.logic.area
            # Diğer organlar için şimdilik 5px varsayılan alan kabul edelim (Lego parçaları yer kaplar)
            else: total += 5.0 
        return total

    def consume_food(self, food):
        if hasattr(self, 'body'):
            organ_area = self.calculate_organ_area()
            taken = self.body.logic.add_food(food, organ_area)
            if taken:
                self.toplam_besin += 1
            if taken and getattr(food, 'from_corpse', False):
                # LEŞ yemek de kairomon sızdırır. Avcıların çoğu avını
                # doğrudan yutmaz: stiletle öldürür, leş besine dönüşür,
                # sonra onu yer. Sızıntının asıl yolu budur.
                self.kairomone = min(game_settings.KAIROMONE_MAX,
                                     self.kairomone + game_settings.KAIROMONE_PER_KILL)
            return taken
        return False

    # ---------------- DAVRANIŞ ----------------

    def perceive_and_decide(self, others):
        """Görülen hücreler için davranış tablosuna danış.

        Işık uyaranı: hedefin RENK TONU sınıfı, yakınlığı da seviyesi olur
        (yakın/büyük = güçlü uyaran). Tablo her (renk, seviye) ikilisi için
        -1..+1 arasi bir sayi verir: isaret yonu (uzerine / uzaga),
        buyukluk ise harcanacak motor eforunu belirler.

        EN GUCLU TEPKIYI uyandiran hedefe gore karar doner:
            (tepki, hedef) veya (None, None)
        """
        self.attack_targets = set()
        if not others or not game_settings.BEHAVIOR_ENABLED:
            self.current_response = 0.0
            return None, None

        # Menzil 0 ise o kanal KAPALIDIR. `max(1.0, ...)` yazmak, organsiz
        # bir hucreye 1 px'lik bir duyu birakiyordu; temas halindeki iki
        # hucre birbirini "duyuyor" sayiliyordu.
        vrange = self.vision_range
        hrange = self.sound_radius
        srange = self.smell_range
        if vrange <= 0.0 and hrange <= 0.0 and srange <= 0.0:
            self.current_response = 0.0
            return None, None
        my_scent = self.scent_value      # döngü içinde değişmez, bir kez
        kulak = next((o.logic for o in self.organs
                      if isinstance(o, Mechanoreceptor)), None)
        best = None          # (seviye, -mesafe) -> hedef, tepki
        for t in others:
            if t is self or t.dead:
                continue
            d = self.pos.distance_to(t.pos)

            # Bir hedef hem GÖRÜLEBİLİR hem DUYULABİLİR. İkisi ayrı uyaran
            # tipidir ve tabloda ayrı satırları vardır; en güçlü olan kazanır.
            atak = game_settings.ATAK_ESIGI
            stimuli = []
            if vrange > 0.0 and d <= vrange + t.radius and self.can_see(t):
                stimuli.append(('light',
                                BehaviorGenome.hue_bin(t.color),
                                BehaviorGenome.level_bin(max(0.0, vrange - d), vrange)))
            if kulak is not None:
                # SES = ORGANA CARPAN BASINC DALGASI.
                #
                # Kendi kendine yuzen bir cisim kuvvet-serbesttir; uzak
                # alani stresslet'tir ve mesafenin KARESIYLE soner:
                #     sinyal(r) = (yaricap x hiz) / r^2
                # Duran hucre hic sinyal uretmez. Duyulmasi, sinyalin
                # organin ESIGINI asmasina baglidir.
                #
                # TEPKI DE SUREKLI BIR SPEKTRUMDAN OKUNUR - koku gibi.
                # Once boyut alti ayrik kutuya, siddet uc seviyeye
                # bolunuyordu; kucuk bir genetik degisim hucreyi bir anda
                # bambaska davranan biri yapiyordu ve mutasyon kutudan
                # kutuya SICRADIGI icin secilim kucuk iyilestirmeleri
                # biriktiremiyordu.
                #
                # Eksen GORELI BOYUT: ayni bozulma, kucuk bir hucre icin
                # devasa bir tehdit, iri bir hucre icin onemsiz bir
                # kipirdanmadir. Sinyalin siddeti ise tepkinin YONUNU
                # degil BUYUKLUGUNU olcekler - yani "ne" bilgisi
                # spektrumdan, "ne kadar" bilgisi dalganin siddetinden.
                _gur = MechanoreceptorLogic.gurultu(t)
                _sinyal = kulak.duyulan_sinyal(_gur, max(1.0, d - t.radius))
                if _sinyal >= 1.0:
                    _x = BehaviorGenome.relative_position(t.radius, self.radius)
                    _r = (self.behavior.ses_tepkisi(_x)
                          * BehaviorGenome.aciliyet(_sinyal))
                    if _r >= atak:
                        self.attack_targets.add(id(t))
                    key = (abs(_r), -d)
                    if best is None or key > best[0]:
                        best = (key, t, _r, 'sound')
            # KOKU KAYNAGI HEDEFIN KONUMUNDA DEGIL, ARKASINDADIR.
            #
            # Hizli yuzen bir cisim kendi koku bulutunu geride birakir
            # (Peclet: tasinim difuzyonu asar). Sonucu su: uzerine gelen
            # hizli bir hucreyi burunla GEC fark edersin, arkandan gideni
            # cok daha UZAKTAN koklarsin.
            #
            # Mekanoreseptoru gerekli kilan sey tam olarak budur - hizla
            # yaklasan cisim buruna SESSIZ, kulaga GURULTULUDUR. Iki duyu
            # boylece birbirinin kopyasi olmaktan cikar.
            _kaynak = t.koku_kaynagi()
            d_koku = self.pos.distance_to(_kaynak)

            scent_x = None
            if srange > 0.0 and d_koku <= srange + t.radius:
                # KOKU: koni yok, menzil en uzun. Ayrık sınıf DEĞİL, sürekli
                # eksen - ve hedefin puanı BENİM puanıma oranla okunur.
                # Böylece küçük genetik değişim küçük konum kayması yapar,
                # davranış ancak bir sınıra yakınsa döner: ani yabancı yok.
                scent_x = BehaviorGenome.relative_position(t.scent_value,
                                                           my_scent)

            if srange > 0.0 and t.kairomone > 0.0 and d_koku <= srange + t.radius:
                # KAIROMON: sınıf, hedefin ne kadar YAKINDA avlandığı.
                # Yüzey kimyası zırhı ele verir, kairomon ise davranışı:
                # "bu hücre az önce birini yedi" bilgisini taşıyan tek kanal.
                stimuli.append(('kairomone',
                                BehaviorGenome.kairomone_bin(t.kairomone),
                                BehaviorGenome.level_bin(
                                    max(0.0, srange - d_koku), srange)))

            kin = self.is_kin(t)
            if scent_x is not None:
                # Akrabanın özel sinyali, spektrumdan okunan genel
                # izlenimin önüne geçer: "iri biri" değil, "benden biri".
                resp = (self.behavior.kin_response if kin
                        else self.behavior.spectrum_response(scent_x))
                if resp >= atak:
                    self.attack_targets.add(id(t))
                # KAZANAN, EN GUCLU TEPKIYI UYANDIRAN HEDEFTIR.
                #
                # Once "uyaran siddeti" siralaniyordu: hangi hedef daha
                # yakinsa o kazaniyordu, tepkinin ne oldugundan bagimsiz.
                # Oysa artik tepkinin kendisi bir buyukluk - hucre neye
                # daha cok tepki veriyorsa onunla ilgilenir. Yakinlik
                # yalnizca esitlik bozar.
                key = (abs(resp), -d)
                if best is None or key > best[0]:
                    best = (key, t, resp, 'scent')

            for stim, cls_idx, level in stimuli:
                resp = self.behavior.respond(stim, cls_idx, level)
                if resp >= atak:
                    self.attack_targets.add(id(t))
                key = (abs(resp), -d)
                if best is None or key > best[0]:
                    best = (key, t, resp, stim)

        if best is None:
            self.current_response = 0.0
            return None, None
        _k, target, resp, kanal = best
        self.current_response = resp
        # SESIN YONU KAPSAMAYA BAGLI.
        #
        # Kazanan uyaran ses ise hucre "bir sey var" bilir ama nereden
        # geldigini ancak kapsamasi kadar bilir. Kapsamasi dusuk olan ters
        # yone kacabilir; yuksek olan dogrudan uzaklasir. Kulagin ikinci
        # gelisim ekseninin karsiligi budur.
        self.hedef_yon_hatasi = (kulak.yon_hatasi()
                                 if (kanal == 'sound' and kulak is not None)
                                 else 0.0)
        return resp, target

    # ---------------- BAĞLANMA ----------------

    @property
    def binding_resistance(self):
        """Tutulmaya direnç: kayganlık + kapsül."""
        if hasattr(self, 'membrane'):
            return self.membrane.logic.binding_resistance
        return 0.0

    @property
    def is_restrained(self):
        """Tutuluyor ya da ipe takılı - hareket edemez."""
        return self.bound_by is not None or self.tether_timer > 0

    def try_bind(self, target, grip):
        """Hedefe tutunmayı dene. Kaygan/kapsüllü hedefi yakalamak zordur."""
        if target.bound_by is not None or self.bound_target is not None:
            return False
        res = target.binding_resistance
        if random.random() > grip / (grip + res + 1e-6):
            return False
        self.bound_target = target
        target.bound_by = self
        self.bind_timer = 0.0
        return True

    def release_binding(self):
        """Bağı çöz (iki taraftan da)."""
        if self.bound_target is not None:
            self.bound_target.bound_by = None
            self.bound_target = None
        if self.bound_by is not None:
            self.bound_by.bound_target = None
            self.bound_by = None
        self.bind_timer = 0.0

    def update_binding(self, dt):
        """Bağı ilerlet: mesafe koptu mu, av kurtuldu mu, ip bitti mi."""
        if self.tether_timer > 0:
            self.tether_timer -= dt

        t = self.bound_target
        if t is None:
            return
        if t.dead or self.dead:
            self.release_binding()
            return
        # Menzil koparsa bağ çözülür
        if self.pos.distance_to(t.pos) > self.radius + t.radius + 6.0:
            self.release_binding()
            return
        self.bind_timer += dt
        # Av kurtulmaya çalışır: direnci yüksekse daha çabuk sıyrılır
        res = t.binding_resistance
        rate = game_settings.BIND_BREAK_RATE * res / (1.0 + res)
        if rate > 0 and random.random() < 1.0 - math.exp(-rate * dt):
            self.release_binding()

    # ---------------- SALDIRI ----------------

    def has_weapon(self, cls):
        return any(isinstance(o, cls) for o in self.organs)

    def is_immune_to_toxin(self, silah=None):
        """Bu BELIRLI bakteriosine bagisik miyim?

        Bagisiklik proteini toksin geniyle ayni operonda kodlanir; yani
        hucre yalnizca KENDI urettigi varyanta bagisiktir. Ayni alleli
        tasiyan akrabalari da bagisiktir - acik bir akraba tanima kodu
        olmadan soy-ici isbirligi buradan dogar. Alleli mutasyonla
        degisen yavru ise kendi soyunun toksininden olebilir.
        """
        if silah is None:                 # eski cagri bicimi: herhangi biri
            return self.has_weapon(Toxin)
        allel = getattr(silah, 'allel', None)
        if allel is None:
            return self.has_weapon(Toxin)
        for o in self.organs:
            if isinstance(o, Toxin) and getattr(o.logic, 'allel', None) == allel:
                return True
        return False

    def fire_weapons(self, dt, candidates):
        """Menzildeki hedeflere ateş et. Ölen hedeflerin listesini döndürür.

        NOT: Şimdilik menzile giren herkese ateş edilir. Aşama 4'te bu karar
        davranış genomuna devredilecek (kaç / yaklaş / saldır / yoksay).
        """
        killed = []
        if self.dead or self.stun_timer > 0:
            return killed
        # Davranış tablosu "saldır" demediyse silah kullanılmaz.
        # Bu olmadan hücreler menzildeki HERKESE ateş edip kendi türünü
        # yok ediyordu (ölçüldü: nematosistli optropiler birbirini kırdı).
        if game_settings.BEHAVIOR_ENABLED:
            candidates = [t for t in candidates if id(t) in self.attack_targets]
            if not candidates:
                return killed

        for organ in self.organs:
            if not isinstance(organ, BaseWeapon):
                continue
            lg = organ.logic

            # --- FAGOSİTOZ: hasar değil, yutma ---
            if isinstance(organ, Phagocytosis):
                # Amip önce ADEZYON kurar, sonra sarar. Tutma süresi
                # dolmadan yutamaz; av bu sırada sıyrılabilir.
                if self.bound_target is not None and lg.can_engulf(self, self.bound_target):
                    if self.bind_timer >= game_settings.PHAGO_BIND_TIME:
                        t = self.bound_target
                        self.release_binding()
                        self.energy -= lg.energy_cost
                        lg.trigger()
                        self.atis_sayisi += 1
                        self.stun_timer = game_settings.PHAGO_STUN
                        organ.last_target_pos = t.pos
                        t.die('yutuldu')
                        self.consume_prey(t)
                        killed.append(t)
                    continue
                if not lg.ready or self.energy < lg.energy_cost or self.bound_target is not None:
                    continue
                for t in candidates:
                    if t is self or t.dead:
                        continue
                    if not organ.can_hit(self, t) or not lg.can_engulf(self, t):
                        continue
                    # Deneme de bir atıştır: başarısız olsa bile bekleme ve
                    # enerji harcar. Yoksa saniyede 60 deneme yapılır ve
                    # kayganlık/kapsül hiçbir işe yaramaz.
                    self.energy -= lg.energy_cost
                    lg.trigger()
                    self.atis_sayisi += 1
                    self.try_bind(t, lg.power)
                    break
                continue

            # --- TOKSİN / LIZIN: sürekli, alan etkili ---
            if lg.CONTINUOUS:
                if self.energy < lg.energy_cost * dt:
                    continue
                hedefler = [t for t in candidates
                            if t is not self and not t.dead
                            and not t.is_immune_to_toxin(lg)
                            and organ.can_hit(self, t)]
                if not hedefler:
                    continue

                # MADDE KORUNUMU: hucre saniyede belli miktarda molekul
                # sentezler. Menzilde bes hedef varsa her birine besde biri
                # duser - hepsine birden tam doz DUSMEZ.
                #
                # Once her hedef kendi tam salimini aliyordu ve bedel yine
                # saniyede bir kez odeniyordu: kalabaliga rastgele sacmak
                # bedavaydi. Toksin bu yuzden butun silahlari eziyordu -
                # nisan almanin, yaklasmanin, secmenin hicbir karsiligi
                # yoktu.
                pay = 1.0 / len(hedefler)

                for t in hedefler:
                    # MESAFEYLE SEYRELME: radyal salinan bir maddenin
                    # derisimi uzaklikla duser. Menzilin ucundaki hucre ile
                    # dibindeki hucre ayni dozu alamaz; toksin boylece
                    # YAKIN mesafe silahi olur ve kullanmak icin
                    # yaklasmak - yani kendini gostermek - gerekir.
                    d = max(0.0, self.pos.distance_to(t.pos)
                            - self.radius - t.radius)
                    r0 = max(1.0, self.radius)
                    seyrelme = (r0 / (r0 + d)) ** 2
                    olcek = pay * seyrelme
                    # MOLEKUL SALIMI: hasari dogrudan yazmak yerine
                    # gercek molekuller birakilir. Hedefe varip varmadigina
                    # KATMANLARIN DELIKLERI karar verir - lab.py'deki ayni
                    # fizik, ayni geometri. Hasar molekul varinca dogar
                    # (HedefZarf.receive). Molekul yolu mesafeyi zaten
                    # fiziksel olarak yasar; ona yalnizca PAY uygulanir.
                    if not self._molekul_birak(t, lg, dt * pay):
                        t.take_damage(lg.damage * dt * olcek,
                                      lg.CHANNEL, lg.CONTACT, 'toksin', lg)
                    if t.dead:
                        killed.append(t)
                self.energy -= lg.energy_cost * dt
                self.atis_sayisi += 1
                continue

            # --- TEK ATIŞLIK SİLAHLAR ---
            if not lg.ready or self.energy < lg.energy_cost:
                continue

            # Tutunma gerektiren silahlar (stilet): önce bağ kurulmalı.
            # Bağlıysa hedef sabittir ve her bekleme dolduğunda vurulur.
            if lg.REQUIRES_BIND:
                if self.bound_target is None:
                    for t in candidates:
                        if t is self or t.dead or not organ.can_hit(self, t):
                            continue
                        self.energy -= lg.energy_cost
                        lg.trigger()
                        self.atis_sayisi += 1
                        self.try_bind(t, lg.power)
                        break
                    continue
                t = self.bound_target
                if t not in candidates:
                    continue
                self.energy -= lg.energy_cost
                lg.trigger()
                self.atis_sayisi += 1
                organ.last_target_pos = t.pos
                t.take_damage(lg.damage, lg.CHANNEL, lg.CONTACT,
                              organ.__class__.__name__.lower(), lg)
                if t.dead:
                    self.release_binding()
                    killed.append(t)
                continue

            for t in candidates:
                if t is self or t.dead or not organ.can_hit(self, t):
                    continue
                self.energy -= lg.energy_cost
                lg.trigger()
                self.atis_sayisi += 1
                organ.last_target_pos = t.pos
                t.take_damage(lg.damage, lg.CHANNEL, lg.CONTACT,
                              organ.__class__.__name__.lower(), lg)
                # Nematosist ipi: isabet edince avı bağlar. Saldırgan
                # serbest kalır - önceden tutunmaz, sonradan tutar.
                if lg.CREATES_TETHER and not t.dead:
                    res = t.binding_resistance
                    if random.random() < lg.power / (lg.power + res + 1e-6):
                        t.tether_timer = game_settings.NEMATOCYST_TETHER_TIME
                if t.dead:
                    killed.append(t)
                break
        return killed

    # ---------------- ZAR VE HASAR ----------------

    @property
    def integrity(self):
        return self.membrane.logic.integrity if hasattr(self, 'membrane') else 0.0

    @property
    def max_integrity(self):
        return self.membrane.logic.max_integrity if hasattr(self, 'membrane') else 0.0

    #: Hucre olmanin sartı. Bunlar organ DEGIL, hucrenin kendisidir.
    TEMEL_YAPILAR = ('Membrane', 'Cytoplasm')

    #: molekuler tasiyicilar (difuzyon / yonlu bosaltma / fiskirtma).
    #  Igneli tasiyicilar mermi yollar; onlar bu yoldan gecmez.
    MOLEKULER_TASIYICI = (0, 1, 2)

    def _molekul_birak(self, hedef, lg, dt):
        """Hedefin zarfina molekul sal. Birakildiysa True.

        Salim hizi silahin atis temposuna baglidir; her karede bir avuc
        molekul cikar ve gerisini fizik halleder. Molekuller HEDEFIN
        zarfina kaydedilir - orada dolasir, deliklerden gecmeye calisir,
        takilir ya da varir.
        """
        ci = int(getattr(lg, 'carrier', 2))
        if ci not in self.MOLEKULER_TASIYICI:
            return False
        pi = int(getattr(lg, 'payload', 0))
        try:
            import lab as _lab
        except Exception:
            return False
        if pi <= 0 or pi >= len(_lab.PAYLOADS) or _lab.PAYLOADS[pi][1] is None:
            return False
        zarf = hedef.zarf_arayuzu()
        birikim = getattr(lg, '_mol_birikim', 0.0) + dt * (4.0 + 3.0 * ci)
        n = int(birikim)
        lg._mol_birikim = birikim - n
        if n <= 0:
            return True          # tasiyici molekuler; bu karede sira gelmedi
        yon = hedef.pos - self.pos
        if yon.length() < 1e-6:
            yon = pygame.math.Vector2(1, 0)
        yon = yon.normalize()
        taban = math.atan2(yon.y, yon.x)
        yari = math.radians(_lab.CARRIER_SPREAD[ci])
        v0 = _lab.CARRIER_REACH[ci] * _lab._DRAG_K * (hedef.radius / 110.0)
        for _ in range(min(n, 6)):
            a = taban + random.uniform(-yari, yari)
            hiz = v0 * random.uniform(0.8, 1.2)
            v = pygame.math.Vector2(math.cos(a), math.sin(a)) * hiz
            m = _lab.Molecule(zarf, pygame.math.Vector2(self.pos), v, pi)
            hedef.molekul_ekle(m)
        return True

    def sindirim_keseleri(self):
        """Sitoplazmadaki BESIN KESELERI: [(oran, ilerleme)].

        Alinan besin sindirilene kadar hucrenin icinde durur - gercekte
        fagozom/lizozom kaynasmasi saniyeler surer. Ekranda hicbir izi
        yoktu: besin yutuluyor ve yok oluyordu. Kuyruktaki her besin bir
        kese, enzimin isledigi besin ise ilerlemesiyle birlikte gosterilir.

        `oran` kese icin sabit bir yerlesim tohumu (0..1), `ilerleme`
        sindirim orani (0 = yeni, 1 = bitmek uzere).
        """
        govde = getattr(getattr(self, 'body', None), 'logic', None)
        if govde is None:
            return []
        out = []
        enz = govde.enzyme
        if enz.current_food is not None:
            sure = max(1e-6, enz.base_digestion_time)
            out.append((0.0, max(0.0, min(1.0, enz.progress / sure))))
        for i, _f in enumerate(govde.food_queue):
            out.append(((i + 1) * 0.37 % 1.0, 0.0))
        return out

    def zarf_arayuzu(self):
        """lab.Molecule'un uzerinde calisacagi zarf adaptoru (tembel)."""
        z = getattr(self, '_zarf_arayuz', None)
        if z is None:
            import lab as _lab
            z = _lab.HedefZarf(self)
            self._zarf_arayuz = z
        return z

    def molekul_ekle(self, mol):
        """Bu hucrenin zarfinda dolasan bir molekul."""
        if not hasattr(self, 'molekuller'):
            self.molekuller = []
        if len(self.molekuller) < 240:      # ekran ve CPU icin ust sinir
            self.molekuller.append(mol)

    def molekulleri_guncelle(self, dt):
        """Molekul fizigi: lab.Molecule'un KENDI update'i calisir.

        Fizik burada yeniden yazilmaz - ayni kod, ayni delikler. Olen
        molekuller listeden dusurulur.
        """
        mols = getattr(self, 'molekuller', None)
        if not mols:
            return
        for m in mols:
            m.update(dt)
        self.molekuller = [m for m in mols if m.state != 'lost' and m.age < 12.0]

    def molekulleri_ciz(self, screen, merkez=None, olcek=1.0):
        """Molekulleri ciz. Kamera olcegi verilirse buyutulur."""
        mols = getattr(self, 'molekuller', None)
        if not mols:
            return
        mx, my = (merkez if merkez is not None else self.pos)
        # Molekul yaricapi da GEOMETRIYLE ayni oranda kuculur: m.rad
        # laboratuvar olceginde (cekirdek 110) verilmis bir sayidir, oldugu
        # gibi cizilince oyundaki hucreden buyuk gorunuyordu.
        vs = max(0.05, self.radius / 110.0)
        for m in mols:
            d = m.pos - self.pos
            x = mx + d.x * olcek
            y = my + d.y * olcek
            r = max(1, int(round(m.rad * vs * olcek)))
            pygame.draw.circle(screen, m.col, (int(x), int(y)), r)

    def temel_yapiyi_tamamla(self):
        """Zar ve sitoplazma yoksa ekle.

        Zarsiz hucre diye bir sey yok - ustelik kodda zarsiz varlik
        OLUMSUZ oluyordu: `take_damage` "zar yoksa 0.0 don" diyor, yani
        hicbir saldiri islemiyor. Sitoplazmasiz hucrenin de govdesi,
        dolayisiyla boyutu ve carpisma yaricapi yok. Ikisi de editorde
        "eklenebilir organ" olarak duruyordu; artik dogustan var.
        """
        from organs.registry import make_organ
        # FAZLASINI AT: eski editorde zar ve sitoplazma da "eklenebilir
        # organ" oldugu icin ust uste eklenebiliyordu. Iki zarli hucrede
        # `self.membrane` sonuncuya baglanip otekinin bakim gideri bosa
        # odeniyor, iki sitoplazmada govde yaricapi belirsizlesiyordu.
        gorulen = set()
        tekil = []
        for o in self.organs:
            ad = o.__class__.__name__
            if ad in self.TEMEL_YAPILAR:
                if ad in gorulen:
                    continue
                gorulen.add(ad)
            tekil.append(o)
        if len(tekil) != len(self.organs):
            self.organs = tekil
            # add_organ'in kurdugu kisayollar silinen kopyayi gosteriyor
            # olabilir; hayatta kalan ornege yeniden bagla.
            for o in tekil:
                ad = o.__class__.__name__
                if ad == 'Membrane':
                    self.membrane = o
                elif ad == 'Cytoplasm':
                    self.body = o
        for ad in self.TEMEL_YAPILAR:
            if ad not in gorulen:
                try:
                    self.add_organ(make_organ(ad))
                except Exception:
                    pass

    def take_damage(self, amount, channel='mechanical', contact=True, cause='hasar',
                    silah=None):
        """Zara hasar uygula. Bütünlük biterse hücre ölür.

        Hasar ENERJİ yakmaz (karar 6) - yalnızca zar bütünlüğünü düşürür.
        """
        if not hasattr(self, 'membrane') or self.dead:
            return 0.0
        # LABORATUVAR TESLIMAT MODELI
        #
        # Eskiden tek soru "hasar / (1 + direnc)" idi: her silah her zirha
        # karsi ayni sekilde zayifliyordu. Oysa laboratuvarda olculen sey
        # bambaska: yuk hedef bolgesine FIZIKSEL olarak variyor mu.
        # Olcum, silahlarin zirha karsi bambaska egriler cizdigini gosterdi -
        # T6SS herhangi bir duvarda tamamen duruyor, nematosist zirh 10'a
        # kadar deliyor, kimyasal silahlar daha az duyarli ama hic tam
        # etkili degil. Kurallar lab.py'de, tek kaynakta.
        amount = amount * self._teslimat_carpani(cause, silah)
        if amount <= 0.0:
            return 0.0
        applied = self.membrane.logic.take_damage(amount, channel, contact)
        if self.membrane.logic.is_ruptured:
            self.die(cause)
        return applied

    def _teslimat_carpani(self, silah_adi, silah=None):
        """Bu silah, BU hucrenin zirhina karsi yukunun ne kadarini ulastirir?

        `silah` verilirse onun SECILEN tasiyici/yuku kullanilir - editorde
        yapilan secim boylece dogrudan fizige giriyor. Verilmezse silah
        adina gore varsayilan esleme.
        """
        try:
            import lab
        except Exception:
            return 1.0
        zar = getattr(getattr(self, 'membrane', None), 'logic', None)
        if zar is None:
            return 1.0
        # Katman YOKSA yatirimi da zirh sayilmaz. Ham alan okumak,
        # kaldirilan duvarin depodaki puaniyla zirh uretiyordu.
        _puan = getattr(zar, 'katman_puani', None)
        _al = (lambda a: _puan(a)) if callable(_puan) else               (lambda a: getattr(zar, a, 0.0))
        return lab.silah_teslimat(
            silah_adi,
            duvar=_al('wall'),
            kapsul=_al('capsule'),
            dis_zar=getattr(zar, 'outer', 0.0),   # plazma zari: hep var
            carrier=getattr(silah, 'carrier', None),
            payload=getattr(silah, 'payload', None))

    def division_energy_cost(self):
        """Bölünme bedeli hücrenin BÜYÜKLÜĞÜYLE ölçeklenir.

        Bölünmek tüm hücreyi kopyalamaktır: gövde + organlar. Sabit bedel
        büyük hücreleri haksız yere ödüllendiriyordu; kaotropi 9 kat
        gövdesiyle optropiyle aynı bedeli ödüyordu. Organ alanının da
        sayılması, organ yığan soyların üremesini kendiliğinden pahalılaştırır.
        """
        base = game_settings.DIVISION_ENERGY_COST
        if not hasattr(self, 'body'):
            return base
        total = self.body.logic.total_area + self.calculate_organ_area()
        ref = max(1.0, game_settings.DIVISION_COST_REF_AREA)
        return base * (total / ref)

    def die(self, cause):
        """Hücreyi ölü işaretle. simulation.py listeden düşürür ve leş bırakır."""
        self.dead = True
        self.death_cause = cause
        self.release_binding()

    def biyokutle_besin(self):
        """Bu hucreyi yiyen kac besin kazanir?

        ENERJI KORUNUMU. Once deger hucrenin ALANINDAN hesaplaniyordu:
        sitoplazma alani 1256 / besin alani 100 x 0.5 = 6 besin. Ama alan
        bir kutle olcusu degil; o hucreyi INSA ETMEK 166 enerjiye, yani
        iki besine mal olmustu. Yani her olum, sisteme yoktan 4 besinlik
        enerji ekliyordu.

        Sonucu olculdu: nufus 300 saniyede 14 kez devrildi ve haritadaki
        besin 450'den 20.589'a cikti. Boyle bir dunyada kitlik yoktur;
        kitlik yoksa da ne kemotaksinin ne de avlanmanin bir anlami kalir.
        Hucreler organlarini dokup en ucuz hale geliyordu (organ sayisi
        7.0 -> 5.0).

        Dogrusu: bir hucrenin tasidigi enerji, INSA BEDELI + DEPOSUNDAKI
        artiktir. Trofik verim (< 1) ile carpilir, cunku yenen her sey
        kullanilamaz - ve bu carpan sistemin enerji SIZDIRMASINI saglar.
        Ac olen bir hucre neredeyse hicbir sey birakmaz; tok olen birakir.
        """
        enerji = (self.division_energy_cost() + max(0.0, self.energy))             * game_settings.PREY_BIOMASS_YIELD
        n = int(round(enerji / max(1.0, game_settings.FOOD_ENERGY)))
        return max(0, min(int(game_settings.CORPSE_FOOD_MAX), n))

    def corpse_food_count(self):
        """Lesten kac besin cikar. Yenmesiyle ayni deger - yalnizca
        dagilmis halde: kim once varirsa o alir."""
        return self.biyokutle_besin()

    # ---------------- AVLANMA ----------------

    def ensure_morphology(self):
        """İskelet geni yoksa mevcut organlardan türet."""
        if self.morphology is None:
            self.morphology = Morphology.from_organism(self)
        return self.morphology

    def gain_random_organ(self):
        """Rastgele bir organı RASTGELE bir açıya ekle (avlanma ödülü).

        Konum tamamen rastgeledir - hücrenin alakasız bir yerinden flagella
        çıkabilir. Organ iskelet genine yazıldığı için bölünmede yavrulara
        aktarılır ve o tuhaf yerleşim soyda kalıcı olur.
        """
        self.ensure_morphology()
        otype = random.choice(Morphology.SPAWNABLE)
        angle = random.uniform(-math.pi, math.pi)
        organ = Morphology.build_organ(otype, angle)
        if organ is None:
            return None
        self.add_organ(organ)                       # fizik + optimal ön yeniden hesaplanır
        params = {a: float(getattr(organ.logic, a))
                  for a in ("length", "size", "range", "angle")
                  if hasattr(organ.logic, a)}
        self.morphology.add(otype, angle, params)
        # Yeni organ yükseltme torbasına da girsin ki gelişebilsin
        if self.genome is not None:
            gene = self._GEN_ADI[otype]
            idx = sum(1 for o in self.organs if o.__class__.__name__ == otype) - 1
            self.genome.sequence.append((gene, idx))
        return organ

    def renk_mutasyonu(self, rng=random):
        """Rengi biraz kaydir.

        RENK BIR SINIF ETIKETI DEGIL, KALITSAL BIR OZELLIK OLMALI.

        Fotoreseptor hedefin RENK TONUNU okuyor (`hue_bin`) - ama renk
        dogumda sinifa gore atanip bir daha hic degismiyordu. Dunyada
        toplam alti sabit deger vardi ve hicbiri tasiyani hakkinda bir sey
        soylemiyordu. Renge tepki evrimlestirmenin bir anlami yoktu;
        islevsiz organ da atiliyordu.

        Renk kalitsal ve mutasyona acik olunca bir SINYALE donusur. Ustelik
        silahlarla ve zirhla birlikte kalitildigi icin onlarla ILISKILENIR:
        zehirli bir soy rengini korur, o tondan kacinan avci hayatta kalir -
        uyarici renklenme (aposematizm) boyle dogar. Savunmasiz bir soy
        ayni tona surukleniyorsa taklit (mimikri) dogar. Ikisi de
        kodlanmaz, cikabilir.

        Ton kayar, doygunluk ve parlaklik dar bir bantta tutulur - hucre
        ekranda gorunur kalmali.
        """
        import colorsys
        r, g, b = (max(0, min(255, int(c))) for c in self.color[:3])
        h, sat, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        h = (h + rng.gauss(0.0, game_settings.RENK_SIGMA)) % 1.0
        sat = min(1.0, max(0.45, sat + rng.gauss(0.0, 0.05)))
        v = min(1.0, max(0.55, v + rng.gauss(0.0, 0.05)))
        nr, ng, nb = colorsys.hsv_to_rgb(h, sat, v)
        self.color = (int(nr * 255), int(ng * 255), int(nb * 255))
        return self.color

    def organ_acisi_mutasyonu(self):
        """Bir organin TAKILDIGI ACIYI biraz kaydir.

        Organ konumu bu projede her yerde belirleyici: itme yonu, tork,
        koku ornekleme noktasi, gorus konisi ve silahin isabet yayi hep
        ondan cikiyor. Ama aci bir kez rastgele atandiktan sonra bir daha
        HIC degismiyordu - iskelet genine yazilip oldugu gibi kalitiliyordu.
        Sonucu su: mutasyonla stilet kazanan bir hucrenin stileti gerisine
        bakiyorsa o soy sonsuza kadar gerisine bakan bir stiletle yasar.
        Vucut plani evrimlesemez, yalnizca zar atisiyla belirlenir.

        Kucuk kaymalar, secilimin tirmanabilecegi bir egim birakir: one
        bakan silah isabet eder, arkaya bakan etmez; ise yarayan yerlesim
        nesiller icinde keskinlesir.
        """
        aday = [o for o in self.organs
                if o.__class__.__name__ in Morphology.SPAWNABLE]
        if not aday:
            return None
        organ = random.choice(aday)
        ad = organ.__class__.__name__
        eski = organ.attachment_angle
        yeni = eski + math.radians(random.gauss(
            0.0, game_settings.ORGAN_ANGLE_SIGMA))
        yeni = (yeni + math.pi) % (2 * math.pi) - math.pi
        organ.attachment_angle = yeni
        if self.morphology is not None:
            for parca in self.morphology.parts:
                if parca["type"] == ad and abs(parca["angle"] - eski) < 1e-9:
                    parca["angle"] = yeni
                    break
        self._update_optimal_front()
        self.recalculate_physics()
        return ad

    def yapi_kazan(self):
        """Yeni bir YAPI kazan: organ ya da zar katmani.

        Katmanlar da organ kadar birer yeniliktir - hucre duvari, kapsul,
        S-tabakasi ve mukus gercekte de sonradan kazanilan yapilardir. Ama
        oyunda kazanmanin bir yolu YOKTU: `grow_defense` olmayan katmani
        buyutmeyi reddediyor, `katman_ekle` ise yalnizca editorden
        cagriliyordu. Yani savunma tipi bir hucrenin evrimlesmesi
        imkansizdi; duvar geni genomda duruyor ama hicbir zaman ifade
        edilmiyordu.

        Kazanilan yapinin adini dondurur.
        """
        zar = getattr(getattr(self, 'membrane', None), 'logic', None)
        yok = []
        if zar is not None:
            yok = [a for a in zar.KATMANLAR if not zar.katman_var(a)]
        # Katman ve organ ayni cekilise girer: hucrenin bir sonraki adimi
        # zirh mi silah mi olacagi onceden belirlenmez.
        if yok and random.random() < len(yok) / (len(yok) + len(Morphology.SPAWNABLE)):
            alan = random.choice(yok)
            if zar.katman_ekle(alan):
                self.recalculate_physics()
                return alan
            return None
        organ = self.gain_random_organ()
        return organ.__class__.__name__ if organ is not None else None

    def yapi_kaybet(self):
        """Bir yapiyi yitir: organ ya da katman.

        Katmani birakmak bedavaya kurtulmak degil - o katmanin verdigi
        korumayi da birakmak demek. Ama tasimak da bedava degildi: bakim
        enerjisi ve yaricap artisi. Hangisinin agir bastigina ortam karar
        verir.
        """
        zar = getattr(getattr(self, 'membrane', None), 'logic', None)
        var = []
        if zar is not None:
            var = [a for a in zar.KATMANLAR if zar.katman_var(a)]
        if var and random.random() < len(var) / (len(var) + len(Morphology.SPAWNABLE)):
            alan = random.choice(var)
            if zar.katman_cikar(alan):
                self.recalculate_physics()
                return alan
            return None
        return self.organ_kaybet()

    def organ_kaybet(self):
        """Rastgele bir CEVRESEL organi yitir (mutasyon).

        Zar, sitoplazma, iskelet, koful ve ribozom disari birakilir: bunlar
        organ degil, hucrenin kendisidir. Kalanlar - motorlar, alicilar,
        silahlar - kaybedilebilir.

        Kaybin bir islevi var: organ bedava degil. Bakim enerjisi yakar ve
        surtunmeyi artirir. Ise yaramayan bir organ tasiyan soy, onu
        birakan yavrusuna gore surekli geride kalir. Kazancin yaninda kayip
        olmasaydi populasyon yalnizca sismekle kalirdi.

        Kaybedilen organin adini dondurur (yoksa None).
        """
        aday = [o for o in self.organs
                if o.__class__.__name__ in Morphology.SPAWNABLE]
        if not aday:
            return None
        organ = random.choice(aday)
        ad = organ.__class__.__name__
        self.organs.remove(organ)
        # Iskelet geninden de silinmeli, yoksa bolunmede geri gelir.
        if self.morphology is not None:
            for i, parca in enumerate(self.morphology.parts):
                if parca["type"] == ad:
                    del self.morphology.parts[i]
                    break
        # Yukseltme torbasindan da: olmayan organin geni cekilirse bos gecer
        gen = self._GEN_ADI.get(ad)
        if gen and self.genome is not None:
            for i, (g, _idx) in enumerate(self.genome.sequence):
                if g == gen:
                    del self.genome.sequence[i]
                    break
        self._update_optimal_front()
        self.recalculate_physics()
        return ad

    #: organ sinifi -> yukseltme geni
    _GEN_ADI = {"Flagella": "flagella", "Cilia": "cilia",
                "Chemoreceptor": "chemoreceptor",
                "Photoreceptor": "vision_range",
                "Mechanoreceptor": "sound_radius",
                "Stylet": "stylet", "Harpoon": "harpoon",
                "Nematocyst": "nematocyst", "Toxin": "toxin",
                "Lysin": "lysin", "Phagocytosis": "phagocytosis"}

    def can_consume(self, target):
        """Bu hedefi yiyebilir miyim?

        Gerçekteki ayrım: ÖLÜ bir hücrenin içeriği ortama dağılır ve komşular
        onu zar taşıyıcılarıyla emer (saprotrofi/ozmotrofi) - özel bir makine
        gerekmez. SAĞLAM ve CANLI bir hücreyi yemek içinse ya onu delmek
        (silah) ya da bütün olarak yutmak (fagositoz) gerekir; dokunmak yetmez.

        Bu yüzden: ölüye herkes, canlıya yalnızca fagositoz.

        DIKKAT: "canliya fagositoz" demek, fagositoz ORGANINA sahip olmak
        demek DEGILDIR. Fagositozun kendi asamalari var (fire_weapons
        icinde): once adezyon (try_bind), sonra PHAGO_BIND_TIME kadar
        tutma, can_engulf ile boy orani ve SERT YUZEY kontrolu, enerji
        bedeli, ardindan sersemleme. Burasi yalnizca `has_weapon` sorunca
        butun bu asamalar atlaniyordu: fagositoz takan hucre saglam bir avi
        dokundugu anda, bedelsiz ve kuralsiz yutuyordu.

        Canli av bu yoldan YENMEZ. Yutma isini fagositoz akisi yapar; o
        akis avi once oldurur (`t.die('yutuldu')`), sonra buraya gelir ve
        `target.dead` dogru oldugu icin gecer.
        """
        return bool(target.dead)

    def consume_prey(self, prey):
        """Bir hucreyi ye: BIYOKUTLESI kadar besin + bir gelisim hakki.

        Besinler sindirim kuyruğuna doğrudan konur (kapasite kontrolü
        atlanır) ki avın değeri tam karşılansın; enerji, yükseltme ve
        bölünme zinciri normal besinle birebir aynı yoldan işler.

        Yeni organ garanti değildir: av, mitozda çekilişe girecek bir
        gelişim hakkı kazandırır.
        """
        if not hasattr(self, 'body'):
            return False
        if not self.can_consume(prey):
            return False
        if getattr(prey, 'consumed', False):
            return False        # başkası çoktan aldı
        # AYNI MIDE: besin `can_fit_food`tan geciyordu ama av gecmiyordu.
        # Sonuc, organlarina sigmadigi icin bir besin bile alamayan bir
        # hucrenin koca bir hucreyi yutabilmesiydi. Deger tam odenir
        # (avin biyokutlesi), ama en az bir lokmalik yer olmali.
        if not self.body.logic.can_fit_food(self.calculate_organ_area()):
            return False
        prey.consumed = True
        # KAIROMON: av dokusunu sindirmek metabolik artık sızdırır. Bu bir
        # sinyal değil, engellenemez bir kaçaktır - avcı bunu istemez ama
        # susturamaz. Avlanmanın bedeli budur.
        self.kairomone = min(game_settings.KAIROMONE_MAX,
                             self.kairomone + game_settings.KAIROMONE_PER_KILL)
        # Avin degeri BEDENINDEN gelir, sabit bir sayidan degil: kucuk
        # bir yavruyu yemek ile iri bir hucreyi yemek ayni sey olamaz.
        # KUYRUGA AVIN KENDISI DEGIL, BESIN NESNELERI KONUR.
        #
        # Once dogrudan `prey` (bir Organism) ekleniyordu. Bolunme
        # deepcopy ile calistigi icin bu, yavruya avin TAMAMINI da
        # kopyaliyordu: organlari, hafizasi, davranis tablosu ve KENDI
        # sindirim kuyrugu - yani onun yedigi hucreler de. Her nesilde
        # katlanan bir nesne agaci. Olculdu: 3000 saniyelik bir kosuda
        # tek bir isci 6.3 GB'a ciktı.
        #
        # Sindirim zaten yalnizca iki sey soruyor: kac lokma var ve
        # lestenmis mi (kairomon sizintisi icin). Ikisi de hafif bir
        # Food nesnesiyle tasinir.
        from entities.food import Food as _Besin
        n = prey.biyokutle_besin()
        for _ in range(n):
            self.body.logic.food_queue.append(
                _Besin(self.pos.x, self.pos.y, from_corpse=True))
        self.prey_eaten += 1
        # Organ ANINDA verilmez: bir "gelişim hakkı" birikir ve mitoz
        # sırasındaki çekilişte kullanılır (bkz. _apply_random_upgrade).
        self.pending_organ_rolls += 1
        return True

    def _production_completed(self, food):
        # Membran (ETC) sindirimi biten besini enerjiye çevirir. Enerjinin
        # TEK kaynağı budur; eskiden her karede bedava enerji ekleniyordu ve
        # besinin enerjiyle ilgisi yoktu (sabit +1).
        self.energy = min(self.max_energy,
                          self.energy + game_settings.FOOD_ENERGY * self.etc_efficiency)

        if self.genome is None:
            self.genome = Genome.from_organism(self)

        # BÖLÜNME MODU: besin sindirildiğinde ikiye bölün, gelişimi iki
        # yavru için ayrı ayrı çek. Yeni hücre inşa etmenin enerji bedeli
        # karşılanamıyorsa bölünme olmaz; hücre yalnızca gelişir.
        if game_settings.DIVISION_MODE:
            # NUFUS TAVANI BIR DUVAR DEGIL, ELEMEDIR.
            #
            # Burada bir `has_room` kontrolu vardi: nufus tavana ulasinca
            # bolunme DURUYORDU. Sonucu olculdu - populasyon tam 200'de
            # donuyor, dogum neredeyse sifira iniyor (ilk 100 saniyede 165
            # dogum, sonraki 100 saniyede 19) ve evrim duruyordu. Cunku
            # mutasyon yalnizca bolunmede olur: bolunme yoksa cesitlilik de
            # yok, secilim de yok.
            #
            # Tavan yine korunuyor ama BASKA bir yerden: dunya her karede
            # fazlayi en dusuk enerjili hucreleri eleyerek kirpar. Yani
            # tavan uremeyi engellemez, YERINI KIMIN ALACAGINI belirler -
            # hizli beslenen gercekten yavasin yerini alir. Secilim budur.
            cost = self.division_energy_cost()
            if self.energy >= cost:
                self.energy -= cost
                self.divide()
            else:
                # Bolunmeye enerji yetmiyor: gelisim yine torbadan cekilir.
                self._apply_random_upgrade()
            return

        instruction = self.genome.next_instruction()
        if instruction is None:
            return
        self._apply_upgrade(instruction)

    def divide(self):
        """Mitoz: hücre iki EŞ yavruya bölünür.

        Ebeveyn diye bir şey yoktur. Bölünmeden sonra ortada iki yavru
        vardır ve ikisi de tamamen eşit muamele görür:
          - ikisi de yeni kimlik (index/uid) alır,
          - ikisinin genomu AYRI AYRI mutasyona uğrar,
          - ikisi de besinin sağladığı gelişim için BAĞIMSIZ birer
            rastgele çekiliş yapar (aynı geni çekmeleri mümkündür),
          - enerji ve konum simetrik bölünür.

        Uygulama notu: bu Python nesnesi A yavrusu olarak devam eder,
        deepcopy ile B yavrusu üretilir. Bu yalnızca bir uygulama
        detayıdır; davranış olarak ikisi arasında hiçbir ayrıcalık yoktur.
        """
        # Bölünmeden ÖNCE bağı çöz: deepcopy bir referansı takip edip
        # karşı hücrenin tamamını kopyalardı.
        self.release_binding()
        self.tether_timer = 0.0

        other = copy.deepcopy(self)
        other.pending_children = []
        other.bound_target = None
        other.bound_by = None
        other.log_enabled = False
        other.debug_motor = False

        # Sayacı hemen artır: aynı karede birden fazla hücre bölünebilir ve
        # hepsi kare başında okunan aynı nüfus değerini görürse tavan aşılır.
        Organism.population_count += 1

        origin = pygame.math.Vector2(self.pos)
        ang = random.uniform(0, 2 * math.pi)
        axis = pygame.math.Vector2(math.cos(ang), math.sin(ang))
        half_energy = self.energy * 0.5

        # İki yavruya da birebir aynı işlem uygulanır
        for daughter, side in ((self, 1.0), (other, -1.0)):
            Organism._next_index += 1
            daughter.index = Organism._next_index
            daughter.energy = half_energy
            # Sızıntı fizyolojik bir durumdur, gen değil: sitoplazma ikiye
            # bölününce metabolik yük de bölünür.
            daughter.kairomone = self.kairomone * 0.5
            daughter.pos = origin + axis * side * (self.radius + 2)
            daughter.direction = pygame.math.Vector2(axis * side)
            changes = 0
            if daughter.genome is not None:
                changes += daughter.genome.mutate() or 0
            # Davranış tablosu da kalıtsaldır ve mutasyona uğrar
            if daughter.behavior is not None:
                changes += daughter.behavior.mutate() or 0
            # KOKU: zar atışıyla değil, biriken ıraksamayla değişir. Eşiği
            # aşana kadar yavru ebeveyniyle AYNI kokar - kardeşler, kuzenler
            # ve yakın soylar aynı sınıfta kalır ki davranış evrimleşebilsin.
            # Gelişim ıraksamadan ÖNCE uygulanır ki sayılabilsin. Aksi
            # halde stilet kazanıp avcıya dönüşen bir hücrenin kokusu hiç
            # değişmiyordu - oysa fenotipi asıl değiştiren buydu.
            changes += daughter._apply_random_upgrade() or 0.0
            # ORGAN MUTASYONU: avlanmaktan bagimsiz kazanc ve kayip.
            # Ilk silahli hucrenin ortaya cikabilmesi buna bagli - avlanma
            # oduluyle sinirli kalsaydi kimse ilk silahi edinemezdi.
            # Yeni bakteriosin varyanti: nadir ama sonuclari buyuk.
            # Alleli degisen soy akrabalarinin bagisikligini yitirir ve
            # onlari oldurebilir hale gelir; toksin kartellerinin
            # dagilmasi ve cesitliligin korunmasi buradan gelir.
            for _o in daughter.organs:
                if isinstance(_o, Toxin) and                         random.random() < game_settings.TOXIN_ALLELE_MUTATION:
                    _o.logic.allel_mutasyonu()
                    changes += 1
            if random.random() < game_settings.ORGAN_GAIN_RATE:
                if daughter.yapi_kazan() is not None:
                    changes += game_settings.DIVERGENCE_NEW_ORGAN
            if random.random() < game_settings.ORGAN_LOSS_RATE:
                if daughter.yapi_kaybet() is not None:
                    changes += game_settings.DIVERGENCE_NEW_ORGAN
            # Vucut plani da evrimlesir: organin acisi kayar.
            if random.random() < game_settings.ORGAN_ANGLE_RATE:
                if daughter.organ_acisi_mutasyonu() is not None:
                    changes += game_settings.DIVERGENCE_UPGRADE
            # Renk de kalitsal bir ozelliktir ve kayar.
            if random.random() < game_settings.RENK_MUTASYON:
                daughter.renk_mutasyonu()
                changes += game_settings.DIVERGENCE_UPGRADE
            # Bolunme deepcopy ile calisir: ebeveynde kalmis bir kopya zar
            # ya da sitoplazma butun soya gecerdi. Her yavru tekillenir.
            # HAFIZA CEVRIMI (protein donusumu).
            #
            # `memory_length` geni kapasiteyi yalnizca ARTIRABILIYORDU ve
            # torbadan herkes ayni sikilikta cekiyordu; yani her soy, ise
            # yarasin yaramasin, kapasitesini durmadan sisiriyordu. Olculdu:
            # 100 bin dogum sonunda kapasite 24'ten 173'e cikti ve tek
            # basina saniyede 8.65 enerji goturuyordu - gelirin buyuk bir
            # kismi. Bu, hucreleri bedelini karsilamak icin irilesmeye
            # itiyordu.
            #
            # Gercek hucre kullanmadigi proteini yikar. Kapasite her
            # bolunmede biraz erir; yuksek kalmasi icin genin YENIDEN
            # cekilmesi gerekir. Organ kazanci/kaybi dengesiyle ayni mantik.
            dm = daughter.direction_memory
            taban = game_settings.MEMORY_TABAN
            if dm.capacity > taban:
                dm.capacity = max(taban, dm.capacity
                                  * (1.0 - game_settings.MEMORY_CEVRIM))
            daughter.temel_yapiyi_tamamla()
            if getattr(daughter, 'lineage', None) is not None:
                daughter.lineage.accumulate(changes)

        self.pending_children.append(other)
        return other

    def _apply_random_upgrade(self):
        """Bu gelişim adımında ne olacağını çek ve uygula.

        İki olasılık vardır:
          - YENİ ORGAN : yalnızca avlanmayla kazanılmış bir gelişim hakkı
                         varsa mümkündür ve o hakkın PREY_NEW_ORGAN_CHANCE
                         kadarı yeni organa dönüşür.
          - GEN GELİŞİMİ: genom torbasından rastgele bir gen yükseltilir.
                         Genom sıralı bir plan değil, ağırlıklı bir torbadır;
                         bir gen dizide kaç kez geçiyorsa şansı o kadar yüksek.

        Hak, hangi sonuç çıkarsa çıksın harcanır - av yemek yeni organı
        garanti etmez, yalnızca ihtimali açar.

        Iraksama birikimine yazılacak DEĞİŞİM AĞIRLIĞINI döndürür: yeni bir
        organ kazanmak, tek bir genin bir kademe büyümesinden çok daha
        büyük bir fenotip değişimidir.
        """
        if self.pending_organ_rolls > 0:
            self.pending_organ_rolls -= 1
            if random.random() < game_settings.PREY_NEW_ORGAN_CHANCE:
                self.gain_random_organ()
                return game_settings.DIVERGENCE_NEW_ORGAN

        if self.genome is None:
            self.genome = Genome.from_organism(self)
        if not self.genome.sequence:
            return 0.0
        self._apply_upgrade(random.choice(self.genome.sequence))
        return game_settings.DIVERGENCE_UPGRADE

    def _apply_upgrade(self, instruction):
        upgrade_type, organ_index = instruction

        # Organ upgrade types need a valid organ reference
        organ_upgrade_types = {'flagella', 'cilia', 'chemoreceptor',
                               'vision_angle', 'vision_range',
                               'sound_radius', 'sound_focus'}
        organ_upgrade_types |= set(('stylet', 'harpoon', 'nematocyst', 'toxin', 'lysin', 'phagocytosis'))

        organ = None
        if upgrade_type in organ_upgrade_types:
            organ = self._get_organ_by_type_index(upgrade_type, organ_index)
            if organ is None:
                # Mutation produced invalid ref - skip
                self.recalculate_physics()
                return

        # Apply upgrade
        if upgrade_type == 'flagella' and organ: organ.grow()
        elif upgrade_type == 'cilia' and organ: organ.grow()
        elif upgrade_type == 'chemoreceptor' and organ: organ.grow()
        elif upgrade_type == 'vision_angle' and organ: organ.grow('angle')
        elif upgrade_type == 'vision_range' and organ: organ.grow('range')
        elif upgrade_type == 'sound_radius' and organ: organ.grow()
        elif upgrade_type == 'sound_focus' and organ: organ.logic.grow_kapsama()
        elif upgrade_type in ('stylet', 'harpoon', 'nematocyst', 'toxin', 'lysin', 'phagocytosis') and organ: organ.grow()
        elif upgrade_type == 'body_size' and hasattr(self, 'body'): self.body.grow()
        elif upgrade_type == 'digestion_speed' and hasattr(self, 'body'): self.body.logic.grow_enzyme(); self._log("[EVRIM] Sindirim hizi artti")
        elif upgrade_type == 'ribosome_speed' and hasattr(self, 'ribosome'): self.ribosome.grow(); self._log("[EVRIM] Ribozom üretim hızı arttı")
        elif upgrade_type == 'max_energy' and hasattr(self, 'vacuole'): self.vacuole.grow(); self._log("[EVRIM] Vakuol büyüdü")
        elif upgrade_type == 'move_regen' and hasattr(self, 'membrane'): self.membrane.grow(); self._log("[EVRIM] ETC verimliliği arttı")
        elif upgrade_type == 'memory_length': self.direction_memory.capacity += game_settings.GROW_MEMORY; self._log("[EVRIM] Hafıza kapasitesi arttı")
        elif upgrade_type == 'membrane_integrity' and hasattr(self, 'membrane'): self.membrane.logic.grow_integrity(); self._log("[EVRIM] Zar bütünlüğü arttı")
        elif upgrade_type in ('wall', 'outer', 'capsule', 'efflux', 'repair', 'slip', 'mucus', 'slayer') and hasattr(self, 'membrane'):
            # Olmayan katmanin geni IFADE EDILMEZ: grow_defense False
            # doner ve hicbir sey degismez. Aksi halde duvarsiz hucre
            # duvar yatirimini buyutup bedelini oder, karsiliginda
            # hicbir katman ortaya cikmazdi.
            if self.membrane.logic.grow_defense(upgrade_type):
                self._log(f"[EVRIM] Savunma gelişti: {upgrade_type}")
            else:
                self._log(f"[EVRIM] {upgrade_type} geni ifade edilmedi: katman yok")

        self.recalculate_physics()

    def _get_organ_by_type_index(self, upgrade_type, index):
        """Tip ve index'e göre n'inci organı bul."""
        type_map = {
            'flagella': Flagella,
            'cilia': Cilia,
            'chemoreceptor': Chemoreceptor,
            'vision_angle': Photoreceptor,
            'vision_range': Photoreceptor,
            'sound_radius': Mechanoreceptor,
            'sound_focus': Mechanoreceptor,
        }
        for _wname, _wcls in WEAPON_CLASSES.items():
            type_map[_wname.lower()] = _wcls
        target_type = type_map.get(upgrade_type)
        if target_type is None:
            return None
        count = 0
        for organ in self.organs:
            if isinstance(organ, target_type):
                if count == index:
                    return organ
                count += 1
        return None

    def get_organ_stats(self):
        stats = []
        for o in self.organs:
            name = o.__class__.__name__
            if hasattr(o.logic, 'size'): stats.append(f"{name}(size:{o.logic.size:.2f})")
            elif hasattr(o.logic, 'length'): stats.append(f"{name}(len:{o.logic.length:.1f})")
            elif hasattr(o.logic, 'range'): stats.append(f"{name}(range:{o.logic.range:.1f})")
            elif name == "DigestionEnzymes": stats.append(f"Enzyme(time:{o.base_digestion_time:.1f}s)")
            elif name == "Ribosome": stats.append(f"Ribosome(time:{o.logic.base_production_time:.1f}s)")
            else: stats.append(name)
        
        # Sitoplazma içindeki enzimi ayrıca ekleyelim (çünkü o bir organ değil sistem)
        if hasattr(self, 'body') and hasattr(self.body.logic, 'enzyme'):
            stats.append(f"DigestionSpeed({self.body.logic.enzyme.base_digestion_time:.1f}s)")
            
        return ", ".join(stats)

    def _log(self, msg):
        if self.log_enabled: print(msg)

    def update(self, dt, kaotropis, foods=None, trail_manager=None, threat_uids=None, scent_env=None, prey=None):
        # 0. SİNDİRİM (DIGESTION) & ÜRETİM (PRODUCTION)
        # Molekuller GORELI cercevede yasar: hucre kaydiginda molekul
        # duvara carpar ve konumu kendiliginden degisir. SIRA onemli -
        # once molekuller (onceki_pos ile su anki pos arasindaki farki
        # gorurler), sonra onceki_pos tazelenir. Ters sirada prev == center
        # olur ve hucrenin hareketi molekullere HIC yansimazdi.
        self.koku_tazele()
        self.molekulleri_guncelle(dt)
        self.onceki_pos = pygame.math.Vector2(self.pos)
        if hasattr(self, 'body'):
            digested_food = self.body.logic.update(dt)
            if digested_food:
                if hasattr(self, 'ribosome'):
                    self.ribosome.logic.add_task(digested_food)
                else:
                    self._production_completed(digested_food)
        
        if hasattr(self, 'ribosome'):
            finished_product = self.ribosome.logic.update(dt)
            if finished_product:
                self._production_completed(finished_product)

        # 1. DUYU VERİSİ TOPLAMA
        nearby_threats = []
        for o in self.organs:
            if isinstance(o, Mechanoreceptor):
                heard = [k for k in kaotropis
                         if o.is_hearing(self, k.pos, k.radius,
                                         MechanoreceptorLogic.gurultu(k))]
                nearby_threats.extend(heard)
        
        # Gözler de eklenmeli
        for k in kaotropis:
            if self.can_see(k):
                nearby_threats.append(k)

        unique_threats = list({k.uid: k for k in nearby_threats}.values())

        # KOKU ORNEKLEME - iki ayri yetenek
        #
        # TEK alici yalnizca ZAMANSAL kemotaksi yapabilir: "az once daha
        # mi iyiydi?" diye sorar ve buna gore kosusunu uzatir. Bakteri de
        # boyle yapar; govdesi bir gradyani uzunlugunca olcemeyecek kadar
        # kucuktur.
        #
        # IKI ya da daha fazla alici, farkli acilara takili olduklari icin
        # AYNI ANDA farkli yerlerden okur - yani UZAMSAL gradyan cikarabilir
        # ve dogrudan o yone donebilir. Buyuk okaryot hucrelerin (amip,
        # notrofil) yaptigi budur ve tam olarak bu yuzden yapabilirler:
        # yeterince buyuk ve yeterince cok aliciya sahipler.
        #
        # Bu ayrim, karmasiklasmanin karsiligini veren gercek bir kazanc:
        # ikinci burun tasimak sadece "biraz daha hassas" degil, NITELIK
        # OLARAK BASKA bir arama demek.
        best_perception = 0.0
        self.koku_gradyani = None
        if scent_env:
            okumalar = []
            for organ in self.organs:
                if isinstance(organ, Chemoreceptor):
                    perception = organ.sample_environment(self, scent_env)
                    if perception > best_perception:
                        best_perception = perception
                    okumalar.append((organ._taban_ve_boy(self)[1], perception))
            if len(okumalar) >= 2 and best_perception > 0.0:
                ort = sum(p for _y, p in okumalar) / len(okumalar)
                v = pygame.math.Vector2(0.0, 0.0)
                for yon, p in okumalar:
                    v += yon * (p - ort)
                # Zayif bir fark gurultudur: aliciler birbirine yakinsa ya
                # da bulut duzse yon bilgisi tasimaz. Esik, ortalamanin
                # kucuk bir orani - mutlak deger degil, cunku algi
                # logaritmik ve olcegi ortama gore degisir.
                if v.length() > max(0.02, ort * game_settings.SPATIAL_CHEMO_MIN):
                    self.koku_gradyani = v.normalize()
        scent_intensity = best_perception
        self.current_scent_intensity = scent_intensity

        # Kalsiyum Seviyesi
        max_urgency = 1.0
        for o in self.organs:
            if isinstance(o, Mechanoreceptor):
                urgency = o.logic.check_urgency(unique_threats, self.pos)
                if urgency > max_urgency: max_urgency = urgency
        
        if hasattr(self, 'membrane'):
            self.membrane.update(dt, self, max_urgency)
            self.recalculate_physics()
        
        # Hafıza Güncelleme — yaşlanma simülasyon zamanıyla ilerler
        self.direction_memory.update(dt)
        for k in kaotropis:
            if self.can_see(k):
                start = pygame.math.Vector2(k.pos); vec = pygame.math.Vector2(k.current_path_end) - start
                if vec.length() > 0:
                    trunc = vec.normalize() * min(vec.length(), self.max_memory_length)
                    self.direction_memory.encode(k.uid, (start, start + trunc))

        # threat_uids None ise: KENDIMDEN BASKA HERKESIN izi. Roller artik
        # sinifa gore dagitilmadigi icin "tehdit listesi" diye onceden
        # belirlenmis bir kume yok; hucre baskasinin izini gorur, ne
        # yapacagina davranis tablosu karar verir.
        if trail_manager and (threat_uids is None or threat_uids):
            chemos = [o for o in self.organs if isinstance(o, Chemoreceptor)]
            # Eskiden bu satır her kare TÜM iz noktalarını dolaşıp her
            # kemoreseptör için is_touching çağırıyordu (40 hücre x 20.000
            # nokta x 2 organ = kare başına 1.6M çağrı, karenin %86'sı).
            # Artık: (1) organ konumları kare başına bir kez, (2) uzamsal
            # ızgaradan yalnızca yakın noktalar, (3) kesin test sadece
            # onlara. Sonuç kümesi ve sırası birebir aynı kalır.
            detected_points = []
            if chemos:
                probes = []
                for c in chemos:
                    _b, _t = c.touch_probes(self)
                    probes.append((_b.x, _b.y, _t.x, _t.y, c.logic))
                reach = self.radius + max(c.logic.length for c in chemos)
                _kendi = self.uid
                _dokun = Chemoreceptor.probes_touch_xy
                for p in trail_manager.query(
                        self.pos, reach + trail_manager.max_point_radius):
                    if (p.owner_uid == _kendi if threat_uids is None
                            else p.owner_uid not in threat_uids):
                        continue
                    px, py, pr2 = p.x, p.y, p.r2
                    for bx, by, tx, ty, logic in probes:
                        if (_dokun(bx, by, tx, ty, px, py, pr2)
                                and logic.can_detect(p.current_intensity)):
                            detected_points.append(p)
                            break
                detected_points.sort(key=lambda q: q.seq)
            if detected_points:
                avg_dir, center_pos, total_int = pygame.math.Vector2(0,0), pygame.math.Vector2(0,0), 0
                for p in detected_points: avg_dir += p.direction * p.current_intensity; center_pos += p.pos * p.current_intensity; total_int += p.current_intensity
                if total_int > 0:
                    final_dir = avg_dir.normalize() if avg_dir.length() > 0 else pygame.math.Vector2(1,0)
                    self.direction_memory.encode("trail_prediction", (center_pos / total_int, (center_pos / total_int) + final_dir * 300))
            else: self.direction_memory.forget("trail_prediction")

        # DAVRANIŞ GENOMU - görülen hücrelere verilecek tepki
        behave_dir, behave_resp = None, 0.0
        # Roller sinifa gore dagitilmayi biraktiginda "tehdit listesi" ve
        # "av listesi" ayni komsu listesi oldu; ikisini toplamak her
        # komsuyu IKI KEZ degerlendirmek demekti. perceive_and_decide
        # karenin en sicak fonksiyonlarindan biri, bedeli iki katina
        # cikiyordu.
        if prey is kaotropis or not prey:
            seen_pool = list(kaotropis)
        elif not kaotropis:
            seen_pool = list(prey)
        else:
            _g = {id(x): x for x in kaotropis}
            _g.update({id(x): x for x in prey})
            seen_pool = list(_g.values())
        resp, target = self.perceive_and_decide(seen_pool)
        if target is not None and abs(resp) > 0.05:
            v = target.pos - self.pos
            if v.length() > 0:
                v = v.normalize()
                # ISARET YON, BUYUKLUK EFOR.
                # Pozitif = uzerine git, negatif = uzaklas. Ortadaki
                # degerler ilgisiz surukleniste: hafifce yaklasma ya da
                # hafifce uzaklasma, az motor enerjisiyle.
                behave_dir = v if resp > 0 else -v
                _hata = getattr(self, 'hedef_yon_hatasi', 0.0)
                if _hata > 0.0:
                    behave_dir = behave_dir.rotate(
                        max(-180.0, min(180.0, random.gauss(0.0, _hata))))
                behave_resp = resp

        # AV TESPİTİ - görüş alanındaki en yakın av
        prey_dir = None
        if prey:
            best, best_d = None, float('inf')
            for pobj in prey:
                if pobj is self:
                    continue
                d = self.pos.distance_squared_to(pobj.pos)
                if d < best_d and self.can_see(pobj):
                    best, best_d = pobj, d
            if best is not None:
                v = best.pos - self.pos
                if v.length() > 0:
                    prey_dir = v.normalize()

        # MOTOR EFORU: davranis spektrumunun BUYUKLUGU.
        #
        # Uclar (tam kacis / tam saldiri) motorlari sonuna kadar zorlar;
        # ortadaki ilgisiz degerler neredeyse hic enerji harcamaz. Komsu
        # yokken taban efor gecerli - besin aramak da hareket ister.
        # Itki eforla DOGRUSAL, bedeli ise KARESIYLE artar: hizi iki
        # katina cikarmak dorde katlar. Kacmak ve saldirmak boylece gercek
        # bir karar olur, bedava bir refleks degil.
        self.motor_efor = max(game_settings.MOTOR_TABAN_EFOR,
                              min(1.0, abs(behave_resp)))

        # 2. KARAR MEKANİZMASI (CYTOSKELETON)
        if hasattr(self, 'cytoskeleton'):
            # scent_intensity: Skalar koku yoğunluğu (float)
            # Davranış tablosu bir şey söylüyorsa o kazanır; sessizse
            # eski sabit av takibine düşülür.
            drive = behave_dir if behave_dir is not None else prey_dir
            self.cytoskeleton.update(dt, self, unique_threats,
                                     self.direction_memory, scent_intensity,
                                     drive, behave_resp, self.koku_gradyani)
        
        # Silah bekleme sayaçları ve yutma sersemliği
        for _o in self.organs:
            if isinstance(_o, BaseWeapon):
                _o.update(dt, self)
        if self.stun_timer > 0:
            self.stun_timer -= dt
        # Kairomon temizlenmesi: sızıntı kalıcı değil, metabolizma onu yavaşça
        # atar. Bu yüzden "yakında avlanmış" ile "aç" ayırt edilebilir kalır.
        if self.kairomone > 0.0:
            self.kairomone -= game_settings.KAIROMONE_DECAY * dt
            if self.kairomone < 0.0:
                self.kairomone = 0.0
        self.update_binding(dt)

        # Zar onarımı (hasarı önlemez, sonradan kapatır)
        if hasattr(self, 'membrane'):
            self.membrane.logic.update_repair(dt)

        # 3. ENERJİ YÖNETİMİ
        # Enerji girişi YOK: tek kaynak sindirilen besindir ve yukarıdaki
        # adım 0'da (_production_completed) verilir. Burada yalnızca gider var.
        if self.energy <= 0:
            self.energy, self.shutdown = 0.0, True
        if self.shutdown:
            # Kapalıyken de sindirim işler (adım 0 bu satırdan önce çalışır).
            # Depoda besin varsa hücre kendini toparlar; yoksa açlıktan ölür.
            if self.energy > 0:
                self.shutdown = False
                self.starve_timer = 0.0
            else:
                self.starve_timer += dt
                if self.starve_timer >= game_settings.STARVE_TIMEOUT:
                    self.die('aclik')
                return

        # Bakım gideri: her organ kendi base_energy_cost'unu bildirir.
        # Eskiden yalnızca motorlar organdan, işitme/görme sabit bir
        # formülden geliyordu; burun, gövde, depo, ribozom, sindirim, zar ve
        # hafıza hiçbir şeye mal olmuyordu (bazı genler saf kazançtı).
        # Ayrıca eski formül, organ hiç yokken bile varsayılan görme/işitme
        # değerleri üzerinden ücret kesiyordu; artık organ yoksa gider de yok.
        motor_cost = 0.0
        upkeep = 0.0
        for o in self.organs:
            c = getattr(o.logic, 'base_energy_cost', 0.0)
            if not c:
                continue
            if isinstance(o, (Flagella, Cilia)):
                motor_cost += c      # kalsiyum patlamasında motorlar zorlanır
            else:
                upkeep += c
        # Hafıza bir organ değil, sistem: kapasitesiyle orantılı.
        upkeep += self.direction_memory.capacity * game_settings.COST_MEMORY

        boost = self.membrane.logic.calcium_boost if hasattr(self, 'membrane') else 1.0
        # Motor gucu = kuvvet x hiz; ikisi de eforla dogrusal oldugu icin
        # bedel eforun KARESIYLE artar.
        efor = float(getattr(self, 'motor_efor', 1.0))
        boost *= efor ** game_settings.MOTOR_EFOR_USSU
        self.energy -= (upkeep + motor_cost * boost) * dt

        self.log_timer -= dt
        if self.log_timer <= 0 and self.log_enabled:
            self.log_timer = 2.0
            self._log(f"\n--- ENERJI: {self.energy:.1f}/{self.max_energy:.1f} | Boost: x{boost:.1f}")

        # 4. FİZİKSEL HAREKET

        # Hedef hareketi belirle (target_movement veya target_direction'dan)
        movement_target = self.target_movement if self.target_movement else self.target_direction

        # Akıllı motor beynini kullan - organları koordine eder
        self.motor_brain.set_target(movement_target)
        self.motor_brain.update(self, dt)

        # DEBUG: Orange (index 3) için motor durumunu logla
        if getattr(self, 'debug_motor', False) and self.index == 3:
            if not hasattr(self, '_debug_timer'):
                self._debug_timer = 0
            self._debug_timer += dt
            if self._debug_timer >= 2.0:  # Her 2 saniyede bir
                self._debug_timer = 0
                self.motor_brain.debug_motor_state(self, f"Orange #{self.index}")

        # Motor organların açı/güç interpolasyonunu güncelle
        # NOT: Cytoskeleton farklı parametreler alır, onu atla
        for organ in self.organs:
            if isinstance(organ, (Flagella, Cilia)) and hasattr(organ, 'update'):
                organ.update(dt, self)

        # Fizik hesabını güncelle (güncel thrust açılarıyla)
        self.recalculate_physics()

        # TORK HER ZAMAN UYGULANIR.
        #
        # Eskiden yalnizca "TURN"/"CORRECT" modunda uygulaniyordu; duz
        # giderken hucrenin KENDI motorlarinin urettigi tepki torku
        # atiliyordu. Bir yanina uc silia takilmis hucre bu yuzden hic
        # donmeden duz suzulebiliyordu - oysa ayni tarafta duran motorlarin
        # r x F torklari ayni isaretli toplanir, hucre donmek ZORUNDADIR.
        # Kendi torkunu gormezden gelmek bir mod secimi olamaz.
        if abs(self.torque_turn_rate) > 0.001:
            torque_rotation = math.degrees(self.torque_turn_rate * dt)
            self.direction = self.direction.rotate(torque_rotation)
            if self.direction.length() > 0:
                self.direction = self.direction.normalize()

        # Hareket yönü = FİZİKTEN hesaplanan thrust yönü
        # Kürek fiziği: Cilia ön-arkada ise hücre YANA gider
        # thrust_direction: lokal koordinatta net itme yönünün tersi (hareket yönü)
        current_heading = math.atan2(self.direction.y, self.direction.x)
        actual_move_angle = current_heading + self.thrust_direction
        move_dir = pygame.math.Vector2(math.cos(actual_move_angle), math.sin(actual_move_angle))

        # Hareketsizlik: yutma sersemliği, tutulmak (bound_by / ip) ya da
        # birini TUTMAK. Saldırmak artık taahhüt: tutan da kıpırdayamaz.
        immobile = (self.stun_timer > 0 or self.is_restrained
                    or self.bound_target is not None)
        move_dist = 0.0 if immobile else self.speed * dt
        # Koku bulutunun nereye surukelendigini bilmek icin GERCEK hareket
        # yonu saklanir (yon vektoru degil - kurek fiziginde ikisi ayrilir).
        self.hareket_yonu = pygame.math.Vector2(0, 0) if immobile else move_dir
        self.pos += move_dir * move_dist
        self.check_bounds()


def resolve_overlaps(cells):
    """Üst üste binen hücreleri birbirinden ayır.

    Kurallar:
      - KENETLİ çiftler ayrılmaz. Stilet takılı avcı ile avı zaten birbirine
        yapışıktır; itmek bağlanma mekaniğini bozardı.
      - Kütleyle ağırlıklandırılır (kütle ~ yarıçap²): küçük hücre daha çok
        itilir, yavru bir hücre kaotropiyi kenara itemez.
      - Küçük bir tolerans bırakılır: gerçek hücreler kısmen deforme olup
        birbirine yaslanabilir; amaç tam geçişmeyi engellemek.
    """
    tol = 1.0 - game_settings.OVERLAP_TOLERANCE
    strength = game_settings.SEPARATION_STRENGTH
    # IZGARA: her hucreyi her hucreyle karsilastirmak N^2 idi (200 hucrede
    # kare basina 20.000 cift). Ustuste binme YEREL bir olay - haritanin
    # obur ucundaki iki hucrenin cakismasi mumkun degil.
    canli = [c for c in cells if not c.dead]
    if not canli:
        return
    # Kutu, EN BUYUK hucrenin capindan kucuk olamaz; yoksa iri bir hucre
    # iki kutu oteden komsusuyla cakisir ve kimse fark etmez.
    kutu = max(96.0, 2.0 * max(c.radius for c in canli))
    izgara = {}
    for c in canli:
        izgara.setdefault((int(c.pos.x // kutu), int(c.pos.y // kutu)),
                          []).append(c)
    # Yarim komsuluk: her cift TAM BIR KEZ ele alinsin.
    YARIM = ((0, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
    for (cx, cy), kova in izgara.items():
        for dx, dy in YARIM:
            karsi = izgara.get((cx + dx, cy + dy))
            if not karsi:
                continue
            ayni = (dx == 0 and dy == 0)
            for i, a in enumerate(kova):
                ar = a.radius
                for b in (kova[i + 1:] if ayni else karsi):
                    if a.bound_target is b or b.bound_target is a:
                        continue            # kenetliler yapışık kalır
                    limit = (ar + b.radius) * tol
                    dx2 = b.pos.x - a.pos.x
                    dy2 = b.pos.y - a.pos.y
                    d2 = dx2 * dx2 + dy2 * dy2
                    if d2 >= limit * limit:
                        continue
                    d = math.sqrt(d2)
                    if d < 1e-6:        # tam üst üste: rastgele bir yöne aç
                        ang = random.uniform(0, 2 * math.pi)
                        dx2, dy2, d = math.cos(ang), math.sin(ang), 1.0
                    nx, ny = dx2 / d, dy2 / d
                    push = (limit - d) * strength
                    # Kütle ~ alan ~ yarıçap²; ağır olan az kıpırdar
                    ma, mb = ar * ar, b.radius * b.radius
                    total = ma + mb
                    fa, fb = mb / total, ma / total
                    a.pos.x -= nx * push * fa
                    a.pos.y -= ny * push * fa
                    b.pos.x += nx * push * fb
                    b.pos.y += ny * push * fb

import pygame
import math
import game_settings
from entities.entity import WIDTH, HEIGHT, FPS, BLACK
from entities.optropi import Optropi
from entities.notropi import Notropi
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.cilia.cilia import Cilia
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor
from systems.world import Dunya

# ─── DİAGNOSTİK LOGLAMA ───
DIAG_LOG_PATH = "motor_diagnostic.log"
DIAG_INTERVAL = 1.0  # saniye
COLOR_NAMES_DIAG = ["Magenta", "Yellow", "LimeGreen", "Orange"]

def _deg(rad):
    return math.degrees(rad)

def _vec_str(v):
    if v is None:
        return "None"
    return f"({v.x:.1f}, {v.y:.1f}) ang={_deg(math.atan2(v.y, v.x)):.1f}°"

def log_diagnostics(f, optropis, elapsed):
    """Sadece Yellow (index=1) optropinin motor/karar/organ durumunu dosyaya yaz."""
    f.write(f"\n{'='*90}\n")
    f.write(f"  t = {elapsed:.1f}s\n")
    f.write(f"{'='*90}\n")

    for o in optropis:
        if not isinstance(o, Optropi):
            continue
        # Sadece Yellow (index=1) loglansın
        if o.index != 1:
            continue
        name = COLOR_NAMES_DIAG[o.index] if o.index < len(COLOR_NAMES_DIAG) else f"#{o.index}"

        # --- 1. HAREKET ---
        heading_deg = _deg(math.atan2(o.direction.y, o.direction.x))
        opt_front_deg = _deg(o.optimal_front_angle)
        actual_move_deg = heading_deg + opt_front_deg
        f.write(f"\n┌─ [{name}] ──────────────────────────────────\n")
        f.write(f"│ Pos: ({o.pos.x:.0f}, {o.pos.y:.0f})  Speed: {o.speed:.2f}\n")
        f.write(f"│ Heading: {heading_deg:.1f}°  OptimalFront: {opt_front_deg:.1f}°  ActualMoveDir: {actual_move_deg:.1f}°\n")
        f.write(f"│ ThrustDir(local): {_deg(o.thrust_direction):.1f}°  TorqueTurnRate: {o.torque_turn_rate:.3f} rad/s\n")
        f.write(f"│ Shutdown: {o.shutdown}  Energy: {o.energy:.1f}/{o.max_energy:.1f}\n")

        # --- 2. KARAR SİSTEMİ ---
        bstate = "?"
        if hasattr(o, 'cytoskeleton') and hasattr(o.cytoskeleton, 'logic'):
            dt_logic = o.cytoskeleton.logic
            bstate = dt_logic.behavioral_state.current_state
        mb = o.motor_brain
        f.write(f"│\n")
        f.write(f"│ BehavioralState: {bstate}\n")
        f.write(f"│ MotorMode: {mb.current_mode}  AngleToTarget: {_deg(mb.angle_to_target):.1f}°\n")
        f.write(f"│ TargetMovement: {_vec_str(o.target_movement)}\n")
        f.write(f"│ TargetDirection: {_vec_str(o.target_direction)}\n")

        # Aktif vektörler
        vec_type = "None"
        if o.current_calm_escape_vector:
            vec_type = f"ESCAPE {_vec_str(o.current_calm_escape_vector)}"
        elif o.current_trail_escape_vector:
            vec_type = f"TRAIL {_vec_str(o.current_trail_escape_vector)}"
        f.write(f"│ ActiveVector: {vec_type}\n")

        # --- 3. FLAGELLA DETAY ---
        flagellas = [organ for organ in o.organs if isinstance(organ, Flagella)]
        f.write(f"│\n│ FLAGELLA ({len(flagellas)}):\n")
        for i, fl in enumerate(flagellas):
            lg = fl.logic
            attach_deg = _deg(fl.attachment_angle)
            base_deg = _deg(lg.base_thrust_angle)
            curr_deg = _deg(lg.current_thrust_angle)
            target_deg = _deg(lg.target_thrust_angle)
            defl_deg = curr_deg - base_deg
            # Tepki yönü (hareket) = thrust + 180
            reaction_deg = curr_deg + 180
            f.write(f"│   [{i}] attach={attach_deg:>7.1f}°  base_thrust={base_deg:>7.1f}°  "
                    f"curr_thrust={curr_deg:>7.1f}°  target={target_deg:>7.1f}°\n")
            f.write(f"│       deflection={defl_deg:>+6.1f}°  reaction(move)={reaction_deg:>7.1f}°  "
                    f"power={lg.power:.2f}  thrust_mag={lg.thrust_magnitude:.2f}\n")

        # --- 4. CİLİA DETAY ---
        cilias = [organ for organ in o.organs if isinstance(organ, Cilia)]
        f.write(f"│\n│ CILIA ({len(cilias)}):\n")
        for i, cl in enumerate(cilias):
            lg = cl.logic
            attach_deg = _deg(cl.attachment_angle)
            base_dir_deg = _deg(lg.base_direction)
            curr_deg = _deg(lg.current_thrust_angle)
            target_dir_deg = _deg(lg.target_direction)
            reaction_deg = curr_deg + 180
            stroke = "POWER" if lg.is_power_stroke else "RECOVERY"
            f.write(f"│   [{i}] attach={attach_deg:>7.1f}°  base_dir={base_dir_deg:>7.1f}°  "
                    f"curr_thrust={curr_deg:>7.1f}°  target_dir={target_dir_deg:>7.1f}°\n")
            f.write(f"│       reaction(move)={reaction_deg:>7.1f}°  pwr_boost={lg.power_boost:.2f}  "
                    f"thrust_mag={lg.current_thrust_magnitude:.3f}  ext={lg.extension:.2f}  {stroke}\n")

        # --- 5. NET KUVVET HESABI ---
        boost = o.membrane.logic.calcium_boost if hasattr(o, 'membrane') else 1.0
        net_fx, net_fy, net_torque = 0.0, 0.0, 0.0
        for organ in o.organs:
            if hasattr(organ.logic, 'thrust_magnitude'):
                ta = getattr(organ.logic, 'current_thrust_angle',
                             getattr(organ.logic, 'thrust_angle', math.pi))
                r_x = math.cos(organ.attachment_angle) * o.radius
                r_y = math.sin(organ.attachment_angle) * o.radius
                tmag = organ.logic.thrust_magnitude * boost
                fx = math.cos(ta) * tmag
                fy = math.sin(ta) * tmag
                net_fx += fx
                net_fy += fy
                net_torque += -(r_x * fy - r_y * fx)
        net_mag = math.sqrt(net_fx**2 + net_fy**2)
        net_ang = _deg(math.atan2(net_fy, net_fx)) if net_mag > 0.001 else 0
        reaction_ang = net_ang + 180
        moi = max(1.0, o.radius * o.radius * 0.2)
        calc_turn = net_torque / moi
        f.write(f"│\n│ NET: force_mag={net_mag:.2f}  force_ang={net_ang:.1f}°  "
                f"reaction(move)={reaction_ang:.1f}°\n")
        f.write(f"│     net_torque={net_torque:.3f}  MoI={moi:.1f}  "
                f"calc_turn_rate={calc_turn:.3f} rad/s  calcium={boost:.2f}\n")
        f.write(f"└──────────────────────────────────────────────\n")

# ─── RUNTIME INSPECTOR ───

class RuntimeInspector:
    """Right-side panel showing selected organism's brain/sensory state."""

    PANEL_W = 300
    BG_ALPHA = 200

    # Colour palette
    COL_BG        = (15, 15, 25)
    COL_HEADER    = (0, 220, 220)
    COL_LABEL     = (160, 160, 170)
    COL_VALUE     = (255, 255, 255)
    COL_BAR_BG    = (40, 40, 50)
    COL_BAR_OK    = (80, 220, 80)
    COL_BAR_LOW   = (220, 60, 60)
    COL_DIVIDER   = (60, 60, 80)
    COL_HIGHLIGHT = (255, 200, 50)

    # Gene type → colour for genome strip
    GENE_COLORS = {
        'flagella':         (100, 180, 255),
        'cilia':            (180, 100, 255),
        'chemoreceptor':    (100, 255, 100),
        'vision_angle':     (255, 255, 100),
        'vision_range':     (255, 200, 100),
        'sound_radius':     (255, 150, 150),
        'body_size':        (200, 200, 200),
        'digestion_speed':  (200, 150, 100),
        'ribosome_speed':   (150, 200, 255),
        'max_energy':       (255, 100, 255),
        'move_regen':       (100, 255, 200),
        'memory_length':    (200, 200, 150),
    }

    STATE_COLORS = {
        "THREATENED": (255, 60, 60),
        "HUNGRY":     (255, 200, 50),
        "FULL":       (80, 220, 80),
        "IDLE":       (160, 160, 170),
    }

    def __init__(self):
        self.selected = None
        # LABORATUVAR GORUNUMU: secili hucrenin buyutulmus kesiti.
        # Dunyayi 30 kat buyutmek yerine (cizim yuzeyi 3.46 GB'a cikiyordu)
        # yalnizca SECILEN hucre lab olceginde ayrica cizilir.
        self.lab_hucre = None
        self.lab_kaynak = None
        self.lab_acik = True
        self.show_heatmap = True   # koku alanı varsayılan olarak görünür (H ile kapanır)
        self.evrim_paneli = True   # populasyon ozeti (E ile kapanir)
        self._evrim_onbellek = None
        self._evrim_yas = 1e9
        self._evrim_gecmis = []    # [(t, silahli_oran, katmanli_oran)]
        self.panel_x = WIDTH - self.PANEL_W

        # Fonts (pygame must be init'd before this)
        # Zaman olcegi: simulasyon dt'si bununla carpilir. Cizim ve girdi
        # gercek zamanda kalir, yalnizca SIMULE EDILEN sure yavaslar/hizlanir.
        self.time_scale = 1.0
        self.paused = False
        self._fnt_h  = pygame.font.Font(None, 22)
        self._fnt_l  = pygame.font.Font(None, 18)
        self._fnt_v  = pygame.font.Font(None, 20)
        self._fnt_s  = pygame.font.Font(None, 16)

    # ── events ──────────────────────────────────────────────

    def handle_event(self, event, organisms):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Olcekli tam ekranda tiklama pencere koordinatinda gelir;
            # dunya koordinatina cevrilmezse secim goruntudeki yere denk
            # gelmez. Cevrimi main() olay dongusu yapip event'e yazar.
            mx, my = getattr(event, 'dunya_pos', event.pos)
            # Ignore clicks on panel area when panel is open
            if mx >= self.panel_x and self.selected is not None:
                return
            best, best_d = None, float('inf')
            for o in organisms:
                d = math.hypot(o.pos.x - mx, o.pos.y - my)
                if d < o.radius + 15 and d < best_d:
                    best, best_d = o, d
            self.selected = best
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                self.show_heatmap = not self.show_heatmap
            elif event.key == pygame.K_e:
                self.evrim_paneli = not self.evrim_paneli
            elif event.key == pygame.K_ESCAPE:
                self.selected = None
            elif event.key == pygame.K_SPACE:
                self.paused = not self.paused
            elif event.key == pygame.K_l:
                self.lab_acik = not self.lab_acik
            elif event.key in self.SPEED_KEYS:
                self.time_scale = self.SPEED_KEYS[event.key]
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self._step_speed(+1)
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self._step_speed(-1)

    # HIZLANDIRMA ALT-ADIMLA YAPILIR, dt BUYUTULEREK DEGIL.
    #
    # Once time_scale dogrudan dt ile carpiliyordu: 4x demek kare basina
    # 0.067 saniyelik bir adim demekti. O olcekte hucre bir karede kendi
    # yaricapi kadar yer degistirir, temas ve gozenek fizigi kacar.
    # 1'in ustundeki degerler artik kare basina KAC KEZ adim atilacagini
    # soyluyor; her adim yine gercek kare suresi kadar. Fizik bozulmaz,
    # yalnizca daha cok is yapilir.
    #
    # Bir kusak ~20 sim-saniye surdugu icin evrimi izlemek 1x'te uzun
    # surer; 16x'te dakikalar mertebesine iner.
    SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)
    SPEED_KEYS = {pygame.K_1: 0.25, pygame.K_2: 0.5, pygame.K_3: 1.0,
                  pygame.K_4: 2.0, pygame.K_5: 4.0, pygame.K_6: 8.0,
                  pygame.K_7: 16.0}

    def _step_speed(self, direction):
        """Bir kademe hizlandir/yavaslat."""
        try:
            i = self.SPEEDS.index(self.time_scale)
        except ValueError:
            i = 2
        self.time_scale = self.SPEEDS[max(0, min(len(self.SPEEDS) - 1, i + direction))]

    def _draw_speed(self, screen):
        """Sol ustte hiz durumu ve tus yardimi."""
        if self.paused:
            txt, col = "DURAKLADI", (255, 180, 80)
        else:
            txt = f"{self.time_scale:g}x".replace("0.25x", "0.25x")
            col = (120, 220, 160) if self.time_scale <= 1.0 else (240, 200, 120)
        lbl = self._fnt_h.render(txt, True, col)
        screen.blit(lbl, (12, 10))
        keys = self._fnt_s.render(
            "1..7 = 0.25x .. 16x   +/- kademe   BOSLUK = duraklat",
            True, (100, 100, 120))
        screen.blit(keys, (12, 34))

    def validate(self, alive_list):
        """Drop selection if organism died."""
        if self.selected and self.selected not in alive_list:
            self.selected = None

    # ── main draw entry ─────────────────────────────────────

    def _draw_lab(self, screen, o):
        """Seçili hücrenin laboratuvar ölçeğinde kesiti."""
        try:
            import lab as _lab
        except Exception:
            return
        # Organ dizilimi degistiyse yeniden kur (evrimle organ kazanabilir)
        # Onbellek imzasi KATMAN VARLIGINI da tasimali: katman
        # eklenip cikarilinca organ SAYISI degismiyor, dolayisiyla
        # buyutulmus kesit eski zarfi gostermeye devam ediyordu.
        _zar = getattr(getattr(o, 'membrane', None), 'logic', None)
        _kat = tuple(bool(getattr(_zar, v, True)) for v in
                     ('var_mucus', 'var_capsule', 'var_slayer', 'var_wall'))
        imza = (id(o), len(getattr(o, 'organs', [])), _kat)
        alan_w = self.panel_x
        merkez = (alan_w * 0.5, HEIGHT * 0.5)
        if self.lab_hucre is None or self.lab_kaynak != imza:
            self.lab_kaynak = imza
            # Cekirdek yaricapi gorunur alana sigacak sekilde secilir
            cek = max(40.0, min(110.0, (min(alan_w, HEIGHT) * 0.5 - 30) * 0.36))
            self.lab_hucre = _lab.LabCell.from_organism(o, merkez, cek)
        c = self.lab_hucre
        c.center = pygame.math.Vector2(merkez)
        c.home = pygame.math.Vector2(merkez)
        perde = pygame.Surface((alan_w, HEIGHT), pygame.SRCALPHA)
        perde.fill((8, 10, 18, 246))
        screen.blit(perde, (0, 0))
        c.draw(screen, self._fnt_v, self._fnt_s)
        kimlik = (getattr(o, 'display_name', None) or getattr(o, 'name', None)
                  or f'{o.__class__.__name__} #{getattr(o, "index", 0)}')
        b = self._fnt_h.render(f'{kimlik} - buyutulmus kesit', True, (200, 220, 245))
        screen.blit(b, (16, 12))
        alt = self._fnt_s.render(
            'L = kesiti kapat   |   BOSLUK = duraklat   |   ESC = secimi birak',
            True, (120, 130, 155))
        screen.blit(alt, (16, HEIGHT - 22))

    def draw(self, screen, scent_env, elapsed, dt, dunya=None):
        # 1) Selection ring
        if self.selected:
            self._draw_selection_ring(screen, elapsed)

        # Hiz gostergesi - secim olsun olmasin her zaman gorunur
        self._draw_speed(screen)

        # EVRIM PANELI: populasyonun BUTUNU.
        #
        # Tek hucreye bakarak evrim gorulmez - gorulen sey o hucrenin
        # sansidir. Ekranda kalici duran bu birkac sayi silahin
        # yayilmasini, katmanlarin birikmesini ve organ sayisinin artisini
        # dogrudan gosterir; yoksa "evrim oluyor" iddiasi ancak kosu
        # bittikten sonra bir dosyadan okunabilir.
        if dunya is not None and self.evrim_paneli:
            self._draw_evrim(screen, dunya)

        # 2) If nothing selected, just show a hint
        if not self.selected:
            hint = self._fnt_s.render(
                "Hucreye tikla  |  H = koku  |  E = evrim paneli",
                True, (100, 100, 120))
            screen.blit(hint, (WIDTH - hint.get_width() - 10, HEIGHT - 20))
            return

        o = self.selected

        # 2.5) BUYUTULMUS KESIT
        if self.lab_acik:
            self._draw_lab(screen, o)

        # 3) Semi-transparent panel background
        panel = pygame.Surface((self.PANEL_W, HEIGHT), pygame.SRCALPHA)
        panel.fill((*self.COL_BG, self.BG_ALPHA))
        screen.blit(panel, (self.panel_x, 0))
        pygame.draw.line(screen, self.COL_DIVIDER,
                         (self.panel_x, 0), (self.panel_x, HEIGHT), 1)

        px = self.panel_x + 12          # left padding
        pw = self.PANEL_W - 24          # usable width
        y = 10

        # ── IDENTITY & VITALS ──────────────────────────────
        y = self._header(screen, "IDENTITY & VITALS", y, px, pw)

        type_name = ("Optropi" if isinstance(o, Optropi)
                     else "Notropi" if isinstance(o, Notropi)
                     else "Organism")
        y = self._kv(screen, "ID", f"{type_name} #{o.index}", y, px,
                     vc=o.color)

        # Behavioral state
        bstate = self._safe_attr(o, 'cytoskeleton.logic.behavioral_state.current_state', '?')
        y = self._kv(screen, "State", bstate, y, px,
                     vc=self.STATE_COLORS.get(bstate, self.COL_VALUE))

        # Energy bar
        e_ratio = o.energy / o.max_energy if o.max_energy > 0 else 0
        bar_c = self.COL_BAR_OK if e_ratio > 0.3 else self.COL_BAR_LOW
        y = self._bar(screen, "Energy", e_ratio,
                      f"{o.energy:.1f} / {o.max_energy:.1f}",
                      y, px, pw, bar_c)

        y = self._kv(screen, "Speed", f"{o.speed:.1f} px/s", y, px)
        if o.shutdown:
            y = self._kv(screen, "Shutdown", "YES", y, px,
                         vc=(255, 60, 60))
        y += 6

        # ── SENSORY ECOLOGY ────────────────────────────────
        y = self._header(screen, "SENSORY ECOLOGY (Weber-Fechner)", y, px, pw)

        raw_I = scent_env.get_concentration(o.pos.x, o.pos.y)

        # Best (lowest) threshold across chemoreceptors
        threshold, chemo_n = 0.0, 0
        for organ in o.organs:
            if isinstance(organ, Chemoreceptor):
                chemo_n += 1
                s = organ.logic.scent_sensitivity
                if threshold == 0.0 or s < threshold:
                    threshold = s

        perception = o.current_scent_intensity

        y = self._kv(screen, "Raw Intensity (I)", f"{raw_I:.4f}", y, px)
        y = self._kv(screen, "Threshold (I_th)",
                     f"{threshold:.4f}" if chemo_n else "N/A", y, px)
        perc_c = (80, 255, 80) if perception > 0 else self.COL_LABEL
        y = self._kv(screen, "Perception (S)", f"{perception:.4f}", y, px,
                     vc=perc_c)
        y = self._kv(screen, "Receptors", str(chemo_n), y, px)
        y += 6

        # ── CHEMOTAXIS ─────────────────────────────────────
        y = self._header(screen, "CHEMOTAXIS (Run-and-Tumble)", y, px, pw)

        dt_logic = self._safe_obj(o, 'cytoskeleton.logic')

        if dt_logic:
            tumble_r   = dt_logic.tumble_rate
            delta      = dt_logic.last_delta
            base_tr    = dt_logic.base_tumble_rate

            # Derive display mode
            if bstate == "THREATENED":
                mode, mode_c = "ESCAPE", (255, 60, 60)
            elif perception > 0:
                if tumble_r < base_tr:
                    mode, mode_c = "RUN", (80, 255, 80)
                else:
                    mode, mode_c = "TUMBLE", (255, 200, 50)
            else:
                mode, mode_c = "LEVY FLIGHT", (140, 140, 200)

            y = self._kv(screen, "Mode", mode, y, px, vc=mode_c)

            # Delta colour: green if positive, red if negative
            d_c = ((80, 255, 80) if delta > 0.0001
                   else (255, 100, 100) if delta < -0.0001
                   else self.COL_LABEL)
            d_sign = "+" if delta > 0 else ""
            y = self._kv(screen, "Memory (Delta)",
                         f"{d_sign}{delta:.4f}", y, px, vc=d_c)

            # Tumble probability this frame
            frame_dt = max(dt, 1.0 / 60.0)
            t_prob = (1.0 - math.exp(-tumble_r * frame_dt)) * 100.0
            p_c = ((255, 100, 100) if t_prob > 50
                   else (255, 200, 50) if t_prob > 20
                   else (80, 255, 80))
            y = self._kv(screen, "Tumble Prob", f"{t_prob:.1f}%", y, px,
                         vc=p_c)
            y = self._kv(screen, "Tumble Rate", f"{tumble_r:.3f}", y, px)

            if mode == "LEVY FLIGHT":
                rem = max(0, dt_logic.levy_run_duration - dt_logic.levy_timer)
                y = self._kv(screen, "Levy Run",
                             f"{dt_logic.levy_timer:.1f} / "
                             f"{dt_logic.levy_run_duration:.1f}s", y, px)
        else:
            y = self._kv(screen, "Mode", "N/A", y, px)
        y += 6

        # ── GENETICS ───────────────────────────────────────
        # Bölünme modunda genom sıralı bir plan değil, ağırlıklı bir
        # torbadır; "Next Upgrade" diye bir kavram yoktur. Sıralı moda ait
        # alanları burada göstermek yanıltıcı olur (hepsi sequence[0]'ı
        # gösterip sabit kalır), o yüzden panel moda göre değişir.
        division = getattr(game_settings, 'DIVISION_MODE', False)
        y = self._header(
            screen,
            "GENETICS (Random Draw)" if division else "GENETICS (Build Order)",
            y, px, pw)

        genome = getattr(o, 'genome', None)
        if genome and genome.sequence:
            seq = genome.sequence
            seq_len = len(seq)
            cur_idx = genome.current_index
            cycle   = genome.cycle_count

            if division:
                y = self._kv(screen, "Genes", str(seq_len), y, px)
                y = self._kv(screen, "Draw", "random from pool", y, px,
                             vc=self.COL_HIGHLIGHT)
                # Torbadaki ağırlıklar: bir gen kaç kez geçiyorsa çekilme
                # şansı o kadar yüksek. Asıl bilgi bu.
                counts = {}
                for gtype, _gi in seq:
                    counts[gtype] = counts.get(gtype, 0) + 1
                top = sorted(counts.items(), key=lambda kv: -kv[1])[:3]
                for gtype, n in top:
                    y = self._kv(screen, f"  {gtype}",
                                 f"{n}  ({100.0 * n / seq_len:.0f}%)", y, px,
                                 vc=self.GENE_COLORS.get(gtype, self.COL_VALUE))
            else:
                y = self._kv(screen, "Genome Step",
                             f"{cur_idx} / {seq_len}", y, px)
                y = self._kv(screen, "Cycle Count", str(cycle), y, px)

                # Next upgrade
                if cur_idx < seq_len:
                    ntype, nidx = seq[cur_idx]
                    y = self._kv(screen, "Next Upgrade",
                                 f"{ntype} [{nidx}]", y, px,
                                 vc=self.COL_HIGHLIGHT)

            # Genome strip visualisation
            y += 4
            strip_h = 14
            gene_w = max(4, min(12, pw // max(seq_len, 1)))
            for i, (gtype, _gidx) in enumerate(seq):
                gx = px + i * gene_w
                if gx + gene_w > self.panel_x + self.PANEL_W - 12:
                    break
                color = self.GENE_COLORS.get(gtype, (80, 80, 80))
                # İmleç yalnızca sıralı modda anlamlı; bölünme modunda
                # sıradaki gen diye bir şey yok.
                if i == cur_idx and not division:
                    pygame.draw.rect(screen, (255, 255, 255),
                                     (gx, y, gene_w, strip_h), 1)
                pygame.draw.rect(screen, color,
                                 (gx + 1, y + 1, gene_w - 2, strip_h - 2))
            y += strip_h + 4

            # Compact legend (2-column)
            seen = []
            seen_set = set()
            for gtype, _ in seq:
                if gtype not in seen_set:
                    seen_set.add(gtype)
                    seen.append(gtype)
            col_w = pw // 2
            for li, ltype in enumerate(seen):
                lx = px + (li % 2) * col_w
                ly = y + (li // 2) * 14
                lcolor = self.GENE_COLORS.get(ltype, (80, 80, 80))
                pygame.draw.rect(screen, lcolor, (lx, ly + 2, 8, 8))
                lbl = self._fnt_s.render(ltype, True, self.COL_LABEL)
                screen.blit(lbl, (lx + 12, ly))
            if seen:
                y += ((len(seen) + 1) // 2) * 14
        else:
            y = self._kv(screen, "Genome", "Not initialized", y, px,
                         vc=self.COL_LABEL)

        # Bottom hint
        hint = self._fnt_s.render("ESC = Deselect   H = Heatmap",
                                  True, (80, 80, 100))
        screen.blit(hint, (self.panel_x + 12, HEIGHT - 22))

    # ── drawing helpers ─────────────────────────────────────

    #: Evrim paneli kac saniyede bir yeniden hesaplansin. Populasyonu
    #  bastan taramak ucuz degil ve bu sayilar kare kare degismez.
    EVRIM_ARALIK = 0.5

    def _evrim_olc(self, dunya):
        from organs.peripheral.weapons.weapons import BaseWeapon
        h = dunya.hucreler
        n = len(h)
        if not n:
            return None
        silahli = katmanli = savunmaci = 0
        organ = burun = kamci = 0
        silah_sayaci = {}
        for o in h:
            s_ = 0
            for x in o.organs:
                ad = x.__class__.__name__
                if isinstance(x, BaseWeapon):
                    s_ += 1
                    silah_sayaci[ad] = silah_sayaci.get(ad, 0) + 1
                elif ad == "Chemoreceptor":
                    burun += 1
                elif ad == "Flagella":
                    kamci += 1
            organ += len(o.organs)
            zar = getattr(getattr(o, "membrane", None), "logic", None)
            k = 0
            if zar is not None and hasattr(zar, "katman_var"):
                k = sum(1 for a in ("wall", "capsule", "mucus", "slayer")
                        if zar.katman_var(a))
            if s_:
                silahli += 1
            if k:
                katmanli += 1
                if not s_:
                    savunmaci += 1
        return {
            "n": n, "silahli": silahli / n, "katmanli": katmanli / n,
            "savunmaci": savunmaci / n, "organ": organ / n,
            "burun": burun / n, "kamci": kamci / n,
            "kusak": dunya.dogum / max(1, n), "silah": silah_sayaci,
        }

    def _draw_evrim(self, screen, dunya):
        self._evrim_yas += 1.0 / max(1.0, FPS)
        if self._evrim_onbellek is None or self._evrim_yas >= self.EVRIM_ARALIK:
            self._evrim_yas = 0.0
            self._evrim_onbellek = self._evrim_olc(dunya)
            v = self._evrim_onbellek
            if v is not None:
                self._evrim_gecmis.append(
                    (dunya.gecen_sure, v["silahli"], v["katmanli"]))
                if len(self._evrim_gecmis) > 300:
                    del self._evrim_gecmis[0]
        v = self._evrim_onbellek
        if v is None:
            return
        g, y0, w, yuk = 12, 62, 252, 152
        yuzey = pygame.Surface((w, yuk), pygame.SRCALPHA)
        yuzey.fill((14, 18, 26, 205))
        screen.blit(yuzey, (g, y0))
        pygame.draw.rect(screen, (60, 80, 110), (g, y0, w, yuk), 1)
        screen.blit(self._fnt_l.render("EVRIM", True, (140, 210, 180)),
                    (g + 10, y0 + 7))

        def sat(i, ad, deger, renk=(210, 220, 235)):
            yy = y0 + 26 + i * 16
            screen.blit(self._fnt_s.render(ad, True, (130, 145, 170)),
                        (g + 10, yy))
            t = self._fnt_s.render(deger, True, renk)
            screen.blit(t, (g + w - 10 - t.get_width(), yy))

        sat(0, "nufus / kusak", "%d / %.1f" % (v["n"], v["kusak"]))
        sat(1, "silahli hucre", "%.0f%%" % (100 * v["silahli"]),
            (240, 160, 140) if v["silahli"] > 0.05 else (150, 160, 175))
        sat(2, "katmanli hucre", "%.0f%%" % (100 * v["katmanli"]),
            (160, 200, 240) if v["katmanli"] > 0.05 else (150, 160, 175))
        sat(3, "savunmaci tip", "%.0f%%" % (100 * v["savunmaci"]),
            (150, 230, 190) if v["savunmaci"] > 0.02 else (150, 160, 175))
        sat(4, "organ/burun/kamci",
            "%.1f / %.1f / %.1f" % (v["organ"], v["burun"], v["kamci"]))
        if v["silah"]:
            ilk = sorted(v["silah"].items(), key=lambda x: -x[1])[:3]
            sat(5, "silahlar", " ".join("%s%d" % (a[:3], b) for a, b in ilk),
                (240, 190, 150))

        # Kucuk zaman serisi: silahli (kirmizi) ve katmanli (mavi) oran.
        if len(self._evrim_gecmis) > 2:
            gx, gy, gw, gh = g + 10, y0 + yuk - 24, w - 20, 16
            pygame.draw.rect(screen, (40, 50, 66), (gx, gy, gw, gh), 1)
            t0 = self._evrim_gecmis[0][0]
            t1 = max(t0 + 1e-6, self._evrim_gecmis[-1][0])
            for idx, renk in ((1, (240, 160, 140)), (2, (160, 200, 240))):
                nokta = [(gx + gw * (kayit[0] - t0) / (t1 - t0),
                          gy + gh * (1.0 - min(1.0, kayit[idx])))
                         for kayit in self._evrim_gecmis]
                if len(nokta) > 1:
                    pygame.draw.lines(screen, renk, False, nokta, 1)

    def _draw_selection_ring(self, screen, elapsed):
        o = self.selected
        pulse = math.sin(elapsed * 4.0) * 0.5 + 0.5      # 0..1
        ring_r = int(o.radius + 8 + pulse * 4)
        alpha  = int(140 + pulse * 115)
        size   = ring_r * 2 + 4
        surf   = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255, alpha),
                           (ring_r + 2, ring_r + 2), ring_r, 2)
        screen.blit(surf,
                    (int(o.pos.x) - ring_r - 2,
                     int(o.pos.y) - ring_r - 2))

    def _header(self, screen, text, y, px, pw):
        pygame.draw.line(screen, self.COL_DIVIDER,
                         (px, y), (px + pw, y), 1)
        y += 4
        surf = self._fnt_h.render(text, True, self.COL_HEADER)
        screen.blit(surf, (px, y))
        return y + surf.get_height() + 4

    def _kv(self, screen, key, value, y, px, vc=None):
        if vc is None:
            vc = self.COL_VALUE
        ks = self._fnt_l.render(f"{key}:", True, self.COL_LABEL)
        vs = self._fnt_v.render(str(value), True, vc)
        screen.blit(ks, (px, y))
        screen.blit(vs, (px + ks.get_width() + 6, y))
        return y + max(ks.get_height(), vs.get_height()) + 2

    def _bar(self, screen, label, ratio, text, y, px, pw, color):
        ls = self._fnt_l.render(f"{label}:", True, self.COL_LABEL)
        screen.blit(ls, (px, y))
        y += ls.get_height() + 2
        bar_h = 14
        pygame.draw.rect(screen, self.COL_BAR_BG, (px, y, pw, bar_h))
        fill_w = int(pw * max(0.0, min(1.0, ratio)))
        if fill_w > 0:
            pygame.draw.rect(screen, color, (px, y, fill_w, bar_h))
        pygame.draw.rect(screen, self.COL_DIVIDER, (px, y, pw, bar_h), 1)
        ts = self._fnt_s.render(text, True, self.COL_VALUE)
        screen.blit(ts, (px + (pw - ts.get_width()) // 2, y + 1))
        return y + bar_h + 4

    # ── safe attribute access ───────────────────────────────

    @staticmethod
    def _safe_attr(obj, dotpath, default='?'):
        """Safely traverse a.b.c style attribute chain."""
        try:
            cur = obj
            for part in dotpath.split('.'):
                cur = getattr(cur, part)
            return cur
        except AttributeError:
            return default

    @staticmethod
    def _safe_obj(obj, dotpath):
        """Like _safe_attr but returns None on failure (for object refs)."""
        try:
            cur = obj
            for part in dotpath.split('.'):
                cur = getattr(cur, part)
            return cur
        except AttributeError:
            return None


def main(food_count=None, kaotropi_count=None):
    # Ayarlardan al (parametre verilmemişse)
    if food_count is None:
        food_count = game_settings.FOOD_COUNT
    if kaotropi_count is None:
        kaotropi_count = game_settings.KAOTROPI_COUNT
    pygame.init()
    # TAM EKRAN: dunya WIDTH x HEIGHT olarak KALIR, yalnizca goruntu
    # ekrana olceklenir. Dunyayi buyutmek yogunlugu dusurup ekosistem
    # dengesini bozuyordu.
    tam_ekran = True
    window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen = pygame.Surface((WIDTH, HEIGHT))

    def _fit():
        w, h = window.get_size()
        k = min(w / WIDTH, h / HEIGHT)
        return k, ((w - WIDTH * k) * 0.5, (h - HEIGHT * k) * 0.5)

    olcek, kayma = _fit()

    # KAMERA: fare tekerlegi yakinlastirir. Yakinlastirma yeni bir temsil
    # URETMEZ - dunya zaten gercek gozenek geometrisiyle cizilmis durumda,
    # kamera yalnizca daha buyuk cizdirir (lab.hucreyi_ciz'e olcek gecer).
    # Tuvali buyutup ustunu olceklemek detay KAZANDIRMAZDI: 1200x800'e
    # cizilmis 1 px'lik delik buyutulunce bulaniklasir, acilmaz.
    kamera = {"z": 1.0, "cx": WIDTH * 0.5, "cy": HEIGHT * 0.5}
    # x1 = kucultulmus dunya gorunumu, x4 = zarfin gercek boyutu,
    # x64 = laboratuvar yakinligi (gozenekler tek tek okunur).
    ZOOM_MIN, ZOOM_MAX = 1.0, 64.0

    def dunya_konumu(p):
        """Ekran (tuval) noktasi -> dunya noktasi."""
        z = kamera["z"]
        return ((p[0] - WIDTH * 0.5) / z + kamera["cx"],
                (p[1] - HEIGHT * 0.5) / z + kamera["cy"])

    def tuval_konumu(p):
        """Dunya noktasi -> tuval noktasi."""
        z = kamera["z"]
        return ((p[0] - kamera["cx"]) * z + WIDTH * 0.5,
                (p[1] - kamera["cy"]) * z + HEIGHT * 0.5)

    def ekran_konumu(p):
        # Yuvarlanir: kesirli birakinca sinirlarda isabet kaciyor.
        return (round((p[0] - kayma[0]) / olcek),
                round((p[1] - kayma[1]) / olcek))
    pygame.display.set_caption("Evolution Simulation")
    clock = pygame.time.Clock()
    
    # DUNYA: butun ekosistem mantigi systems/world.py'de. Burasi yalnizca
    # onu cizer ve olaylari isler.
    dunya = Dunya(food_count=food_count, kaotropi_count=kaotropi_count)
    trail_manager = dunya.trail_manager
    scent_env = dunya.scent_env
    kaotropis = dunya.kaotropis
    optropis = dunya.optropis
    foods = dunya.foods
    if optropis:
        optropis[0].log_enabled = True
    inspector = RuntimeInspector()

    # Diagnostik loglama
    diag_file = open(DIAG_LOG_PATH, "w", encoding="utf-8")
    diag_timer = 0.0
    elapsed_time = 0.0
    diag_file.write("=== MOTOR DİAGNOSTİK LOG ===\n")
    diag_file.write(f"Optropi sayısı: 4, Interval: {DIAG_INTERVAL}s\n")

    running = True
    birikim = 0.0     # sabit adim icin biriken gercek sure
    while running:
        real_dt = clock.tick(FPS) / 1000.0    # gercek gecen sure (cizim icin)
        # Simulasyon zamani olceklenir. Duraklatildiginda dt=0: dunya donar
        # ama hicbir sey ilerlemez, yine de tiklayip inceleyebilirsin.
        # SABIT SIMULASYON ADIMI.
        #
        # Once adim suresi KARE SURESIYDI (real_dt). Iki sakincasi vardi:
        #
        #  1. Simulasyon kare hizina bagimliydi: ayni dunya 30 fps'te
        #     baska, 144 fps'te baska ilerliyordu. Fizik ve olcum
        #     tekrarlanabilir olmuyordu.
        #  2. Oyun 1/60'lik adimlarla, olcum kosulari 1/30'lik adimlarla
        #     ilerliyordu - yani oyun ayni SIMULASYON saniyesi icin iki kat
        #     is yapiyordu. Hizlandirma yarisi buraya gidiyordu.
        #
        # Artik adim sabit (SIM_DT) ve gecen gercek sure biriktirilerek
        # kac adim atilacagi hesaplanir. 1x gercek zaman, 16x on alti kat.
        SIM_DT = 1.0 / 30.0
        if inspector.paused:
            dt, adim_sayisi = 0.0, 0
        else:
            dt = SIM_DT
            birikim += real_dt * inspector.time_scale
            adim_sayisi = int(birikim / SIM_DT)
            birikim -= adim_sayisi * SIM_DT
            # Cok geride kalindiysa borcu silmek gerekir; yoksa yavaslama
            # bir daha asla kapanmayan bir kuyruk yaratir.
            if birikim > 0.5:
                birikim = 0.0
        # Kare butcesi: makine yetismezse adim sayisi kirpilir ki arayuz
        # donmasin. Hizlanma o zaman istenenden az olur - ama akici kalir.
        kare_butce = 0.12

        for event in pygame.event.get():
            if hasattr(event, 'pos'):
                event.dunya_pos = ekran_konumu(event.pos)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                tam_ekran = not tam_ekran
                window = pygame.display.set_mode(
                    (0, 0) if tam_ekran else (WIDTH, HEIGHT),
                    pygame.FULLSCREEN if tam_ekran else 0)
                olcek, kayma = _fit()
            elif event.type == pygame.MOUSEWHEEL:
                # Imlecin gosterdigi DUNYA noktasi sabit kalsin: once o
                # noktayi bul, zoom'u degistir, sonra merkezi geri hesapla.
                _m = ekran_konumu(pygame.mouse.get_pos())
                _hedef = dunya_konumu(_m)
                _z = kamera["z"] * (1.15 ** event.y)
                kamera["z"] = max(ZOOM_MIN, min(ZOOM_MAX, _z))
                if kamera["z"] <= ZOOM_MIN + 1e-6:
                    kamera["cx"], kamera["cy"] = WIDTH * 0.5, HEIGHT * 0.5
                else:
                    kamera["cx"] = _hedef[0] - (_m[0] - WIDTH * 0.5) / kamera["z"]
                    kamera["cy"] = _hedef[1] - (_m[1] - HEIGHT * 0.5) / kamera["z"]
                continue
            if event.type == pygame.QUIT:
                running = False
            inspector.handle_event(event, optropis)

        # ---------------- DUNYA BIR ADIM ----------------
        # Ekosistemin butunu systems/world.py'de. Buradaki tek is onu
        # ilerletmek; besin dogusu, koku, avlanma, bolunme, eleme - hepsi
        # olcum kosusuyla BIREBIR ayni koddan geciyor.
        _t0 = pygame.time.get_ticks()
        for _ in range(adim_sayisi):
            dunya.adim(dt)
            elapsed_time += dt
            if (pygame.time.get_ticks() - _t0) * 0.001 > kare_butce:
                break
        kaotropis = dunya.kaotropis
        optropis = dunya.optropis
        foods = dunya.foods

        # Draw
        screen.fill(BLACK)
        
        # 0. Trails + koku isi haritasi.
        #
        # Bunlar DUNYA koordinatlarinda ciziliyor; kamera yakinlasinca
        # besinler ve hucreler donusuyor ama bunlar yerinde kaliyordu -
        # koku bulutu besinden kopuyordu. Yakinlastirilmis karede ikisi de
        # once dunya olceginde bir tuvale cizilip kameraya gore
        # olceklenir: konumlari artik besinle AYNI donusumden geciyor.
        if kamera["z"] <= 1.0 + 1e-6:
            trail_manager.draw(screen)
            if inspector.show_heatmap:
                scent_env.draw_debug(screen)
        else:
            _dz = kamera["z"]
            _kat = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            trail_manager.draw(_kat)
            if inspector.show_heatmap:
                scent_env.draw_debug(_kat)
            _bk = pygame.transform.smoothscale(
                _kat, (int(WIDTH * _dz), int(HEIGHT * _dz)))
            screen.blit(_bk, (WIDTH * 0.5 - kamera["cx"] * _dz,
                              HEIGHT * 0.5 - kamera["cy"] * _dz))

        # 1. Memory lines (Background)
        # Memory is now drawn inside o.draw(), but since it's the bottom layer,
        # we don't need a separate loop here if o.draw() handles order correctly.
        # But wait, o.draw() handles EVERYTHING.
        # So we can remove this loop too? 
        # No, memory lines should be below EVERYTHING else.
        # Let's keep o.draw() as the single point of entry.
        
        _z = kamera["z"]
        if _z <= 1.0 + 1e-6:
            # Yakinlastirma yokken dunya kendi koordinatlarinda cizilir;
            # hucreler GORUNUM_OLCEGI ile kucultulur (Organism.draw).
            for f in foods:
                f.draw(screen)

            for k in kaotropis:
                k.draw(screen)

            for o in optropis:
                o.draw(screen)
        else:
            # KAMERA GORUNUMU: ayni geometri, buyuk olcekte cizilir.
            # Gorunmeyen sey cizilmez - yakinlasinca kare basina is artmaz.
            _gorunum = getattr(game_settings, 'GORUNUM_OLCEGI', 1.0)
            _yari = (WIDTH * 0.5 / _z, HEIGHT * 0.5 / _z)
            for f in foods:
                if (abs(f.pos.x - kamera["cx"]) > _yari[0] + f.radius or
                        abs(f.pos.y - kamera["cy"]) > _yari[1] + f.radius):
                    continue
                _p = tuval_konumu(f.pos)
                pygame.draw.circle(screen, getattr(f, 'color', (120, 220, 140)),
                                   (int(_p[0]), int(_p[1])),
                                   max(1, int(f.radius * _z * _gorunum)))
            import lab as _kam_lab
            for o in list(kaotropis) + list(optropis):
                _r = getattr(o, 'radius', 10) * 3.0
                if (abs(o.pos.x - kamera["cx"]) > _yari[0] + _r or
                        abs(o.pos.y - kamera["cy"]) > _yari[1] + _r):
                    continue
                # try/except YOK: hatayi yutmak, kamera yolunu sessizce
                # eski cizime dusurup "yakinlasinca gozenek gorunmuyor"
                # diye anlasilmaz bir sonuc uretirdi.
                # Kamera olcegi GORUNUM ile carpilir: x1'de dunyadaki
                # boyut, x4'te zarfin gercek (kucultulmemis) boyutu.
                _ok = _z * _gorunum
                _mrk = tuval_konumu(o.pos)
                _kam_lab.hucreyi_ciz(screen, o, _mrk, _ok)
                o.molekulleri_ciz(screen, _mrk, _ok)
            _f = pygame.font.SysFont("consolas", 16)
            screen.blit(_f.render("ZOOM x%.1f  (tekerlek)" % _z, True,
                                  (150, 170, 200)), (14, HEIGHT - 26))

        # 7. Inspector panel (topmost layer)
        inspector.validate(optropis)
        inspector.draw(screen, scent_env, elapsed_time, dt, dunya)

        window.fill((0, 0, 0))
        window.blit(pygame.transform.smoothscale(
            screen, (int(WIDTH * olcek), int(HEIGHT * olcek))), kayma)
        pygame.display.flip()

        # Diagnostik loglama (her DIAG_INTERVAL saniyede bir)
        diag_timer += dt
        if diag_timer >= DIAG_INTERVAL:
            diag_timer = 0.0
            log_diagnostics(diag_file, optropis, elapsed_time)
            diag_file.flush()

    # Diagnostik dosyasını kapat
    diag_file.close()
    print(f"\n[DIAG] Log dosyası kaydedildi: {DIAG_LOG_PATH}")

    # Sonlandırma — tüm optropilerin statlarını logla
    COLOR_NAMES = ["Cyan", "Magenta", "Yellow", "Lime Green", "Orange"]
    print("\n===== OPTROPI STATLARI =====")
    for o in optropis:
        name = COLOR_NAMES[o.index] if o.index < len(COLOR_NAMES) else f"#{o.index}"
        print(f"\n[{name}]")
        print(f"  Hayatta       : Evet")
        print(f"  Enerji        : {o.energy:.2f}/{o.max_energy:.2f}")
        print(f"  Hiz           : {o.speed:.1f} px/sn")
        print(f"  Gorus Acisi   : {o.vision_angle:.1f} derece")
        print(f"  Gorus Menzili : {o.vision_range:.1f} px")
        print(f"  Ses Yaricapi  : {o.sound_radius:.1f} px")
        print(f"  Hafiza Boyutu : {o.max_memory_length:.1f} px")
        print(f"  Donus Hizi    : {o.max_turn_rate:.2f} rad/sn")
        print(f"  Max Enerji    : {o.max_energy:.2f}")
        print(f"  ETC Verimi    : x{o.etc_efficiency:.2f} (besin basina enerji carpani)")
        print(f"  Shutdown      : {'Evet' if o.shutdown else 'Hayir'}")
        print(f"  Organeller    : {o.get_organ_stats()}")
    print("\n============================")

    pygame.quit()

if __name__ == "__main__":
    main()
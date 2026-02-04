import pygame
import random
import math
import game_settings
from entities.entity import WIDTH, HEIGHT, FPS, BLACK
from entities.kaotropi import Kaotropi
from entities.optropi import Optropi
from entities.notropi import Notropi
from entities.food import Food
from entities.trail import TrailManager
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.cilia.cilia import Cilia

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

def main(food_count=None, kaotropi_count=None):
    # Ayarlardan al (parametre verilmemişse)
    if food_count is None:
        food_count = game_settings.FOOD_COUNT
    if kaotropi_count is None:
        kaotropi_count = game_settings.KAOTROPI_COUNT
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Evolution Simulation")
    clock = pygame.time.Clock()
    
    trail_manager = TrailManager()

    # Colors for 5 Optropis
    # First one is removed Smart, shifting others
    OPTROPI_COLORS = [
        (255, 0, 255),    # Magenta
        (255, 255, 0),    # Yellow
        (0, 255, 0),      # Lime Green
        (255, 165, 0)     # Orange
    ]

    # Create Entities
    kaotropis = [Kaotropi(i, random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)) for i in range(kaotropi_count)]
    
    optropis = []
    
    # 2. Standard Optropis
    for i in range(4): # 4 Standart Optropi
        x = random.randint(50, WIDTH-50)
        y = random.randint(50, HEIGHT-50)
        optropis.append(Optropi(i, x, y, OPTROPI_COLORS[i]))

    optropis[0].log_enabled = True # İlk Standart Optropi loglansın

    # 3. Notropis (6 adet)
    for i in range(6):
        x = random.randint(50, WIDTH-50)
        y = random.randint(50, HEIGHT-50)
        # Indexi optropi sayısına ekleyerek verelim ki karışmasın
        notropi = Notropi(len(optropis), x, y)
        optropis.append(notropi)

    foods = Food.spawn(food_count)

    # Diagnostik loglama
    diag_file = open(DIAG_LOG_PATH, "w", encoding="utf-8")
    diag_timer = 0.0
    elapsed_time = 0.0
    diag_file.write("=== MOTOR DİAGNOSTİK LOG ===\n")
    diag_file.write(f"Optropi sayısı: 4, Interval: {DIAG_INTERVAL}s\n")

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0 # Delta time in seconds
        elapsed_time += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update Trails
        trail_manager.update(dt)

        # Update
        for k in kaotropis:
            k.move(dt)
            # Kaotropiler iz bırakır
            if random.random() < 0.3: # Her karede değil, bazen bırak ki performans düşmesin
                trail_manager.add_point(k.pos.x, k.pos.y, k.uid, k.direction, k.radius)
        
        # Update Optropis and check collisions
        active_optropis = []
        for o in optropis:
            # Optropiler iz bırakır
            if random.random() < 0.3:
                trail_manager.add_point(o.pos.x, o.pos.y, o.uid, o.direction, o.radius)

            # Tehdit listesini belirle
            threats = list(kaotropis)
            if isinstance(o, Notropi):
                # Notropiler için diğer tüm Optropiler (Smart, Notropi, Std) de tehdittir
                threats.extend([other for other in optropis if other != o])
            
            # Tehdit UID'lerini topla (Trail filtreleme için)
            threat_uids = {t.uid for t in threats}
            
            # Trail Manager ve Threat UID'leri update'e gönderiyoruz
            o.update(dt, threats, foods, trail_manager, threat_uids)

            # Check if Optropi eats a food
            eaten = None
            for f in foods:
                if o.pos.distance_to(f.pos) < o.radius + f.radius:
                    if o.consume_food(f):
                        eaten = f
                        break
            if eaten:
                foods.remove(eaten)
            
            # Check for collision with any Kaotropi
            collided = False
            for k in kaotropis:
                if o.check_collision(k):
                    collided = True
                    break
            
            if not collided:
                active_optropis.append(o)
        
        optropis = active_optropis

        # Draw
        screen.fill(BLACK)
        
        # 0. Trails (En arkada)
        trail_manager.draw(screen)
        
        # 1. Memory lines (Background)
        # Memory is now drawn inside o.draw(), but since it's the bottom layer,
        # we don't need a separate loop here if o.draw() handles order correctly.
        # But wait, o.draw() handles EVERYTHING.
        # So we can remove this loop too? 
        # No, memory lines should be below EVERYTHING else.
        # Let's keep o.draw() as the single point of entry.
        
        # 4. Foods
        for f in foods:
            f.draw(screen)

        # 5. Kaotropis (Mid-ground)
        for k in kaotropis:
            k.draw(screen)
            
        # 6. Optropis (Foreground)
        for o in optropis:
            o.draw(screen)

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
        print(f"  Hareket Dolum : {o.move_regen:.2f} birim/sn")
        print(f"  Shutdown      : {'Evet' if o.shutdown else 'Hayir'}")
        print(f"  Organeller    : {o.get_organ_stats()}")
    print("\n============================")

    pygame.quit()

if __name__ == "__main__":
    main()
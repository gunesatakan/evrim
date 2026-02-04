import pygame
import sys
import math
import game_settings
from simulation import main as run_simulation
from entities.entity import BLACK, WHITE
from entities.optropi import Optropi
from entities.notropi import Notropi
from organs.receptors.Photoreceptor.photoreceptor import Photoreceptor
from organs.receptors.Mechanoreceptor.mechanoreceptor import Mechanoreceptor
from organs.receptors.Chemoreceptor.chemoreceptor import Chemoreceptor
from organs.peripheral.flagella.flagella import Flagella
from organs.peripheral.cilia.cilia import Cilia
from organs.peripheral.membrane.membrane import Membrane
from organs.central.cytoplasm.cytoplasm import Cytoplasm
from organs.central.vacuole.vacuole import Vacuole
from organs.central.cytoskeleton.cytoskeleton import Cytoskeleton
from organs.central.ribosome.ribosome import Ribosome

# --- MODERN COLOR PALETTE ---
BG_COLOR = (15, 20, 28)
SIDEBAR_COLOR = (22, 28, 38)
CARD_COLOR = (30, 38, 50)
ACCENT_COLOR = (0, 230, 255)
TEXT_COLOR = (220, 230, 240)
GRAY = (120, 130, 140)
LIGHT_GRAY = (180, 190, 200)
HIGHLIGHT = (45, 55, 75)
SUCCESS = (50, 255, 150)
WARNING = (255, 180, 50)
DANGER = (255, 80, 80)

# Organ türleri ve özellikleri
ORGAN_TYPES = {
    "Photoreceptor": {"color": (255, 255, 0), "internal": False, "base_width": 15},
    "Mechanoreceptor": {"color": (255, 100, 100), "internal": False, "base_width": 20},
    "Chemoreceptor": {"color": (100, 255, 100), "internal": False, "base_width": 10},
    "Flagella": {"color": (100, 200, 255), "internal": False, "base_width": 12},
    "Cilia": {"color": (200, 150, 255), "internal": False, "base_width": 8},
    "Membrane": {"color": (150, 150, 150), "internal": True, "base_width": 0},
    "Cytoplasm": {"color": (200, 200, 200), "internal": True, "base_width": 0},
    "Vacuole": {"color": (100, 150, 200), "internal": True, "base_width": 0},
    "Cytoskeleton": {"color": (180, 180, 180), "internal": True, "base_width": 0},
    "Ribosome": {"color": (255, 200, 100), "internal": True, "base_width": 0},
}

class InputBox:
    def __init__(self, x, y, w, h, attr, font, ent_id=None, on_change=None):
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.attr = attr
        self.ent_id = ent_id
        self.font = font
        self.active = False
        self.on_change = on_change  # Callback fonksiyonu
        self.update_text()

    def handle_event(self, event, scroll_y=0):
        adjusted_rect = self.rect.move(0, int(scroll_y))
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = adjusted_rect.collidepoint(event.pos)
            if not self.active: self.submit()
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                self.submit()
            elif event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            else:
                if event.unicode in "0123456789.-": self.text += event.unicode

    def submit(self):
        try:
            if self.text == "": return
            if self.ent_id:
                old_val = game_settings.ENTITY_CONFIGS[self.ent_id][self.attr]
                new_val = int(float(self.text)) if isinstance(old_val, int) else float(self.text)
                # Sadece değer değiştiyse kaydet ve callback çağır
                if new_val != old_val:
                    game_settings.set_entity_value(self.ent_id, self.attr, new_val)
                    self.text = str(new_val)
                    if self.on_change:
                        self.on_change()
            else:
                old_val = getattr(game_settings, self.attr)
                new_val = int(float(self.text)) if isinstance(old_val, int) else float(self.text)
                if new_val != old_val:
                    game_settings.set_value(self.attr, new_val)
                    self.text = str(new_val)
                    if self.on_change:
                        self.on_change()
        except: self.update_text()

    def update_text(self):
        if not self.active:
            if self.ent_id:
                self.text = str(game_settings.ENTITY_CONFIGS[self.ent_id][self.attr])
            else:
                self.text = str(getattr(game_settings, self.attr))

    def draw(self, screen, scroll_y=0, screen_height=1080):
        draw_rect = self.rect.move(0, int(scroll_y))
        if draw_rect.bottom < 80 or draw_rect.top > screen_height: return
        color = ACCENT_COLOR if self.active else HIGHLIGHT
        pygame.draw.rect(screen, color, draw_rect, 1)
        if self.active:
            overlay = pygame.Surface((draw_rect.width-2, draw_rect.height-2), pygame.SRCALPHA)
            overlay.fill((0, 230, 255, 30))
            screen.blit(overlay, (draw_rect.x+1, draw_rect.y+1))
        txt = self.font.render(self.text, True, TEXT_COLOR)
        screen.blit(txt, (int(draw_rect.x + 8), int(draw_rect.y + 6)))

class ModernLauncher:
    def __init__(self):
        pygame.init()
        # Pencere boyutu
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Evolution Engine - Lab Edition")
        self.clock = pygame.time.Clock()
        self.font_main = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 22)
        self.font_title = pygame.font.Font(None, 48)

        self.state = "DASHBOARD"
        self.sidebar_width = 220
        self.tabs = ["DASHBOARD", "ENTITIES", "SETTINGS"]

        self.scroll_y = 0
        self.max_scroll = 0
        self.total_content_height = 0
        self.dragging_scroll = False
        self.entity_ui_elements = []

        # Preview panel ayarları
        self.preview_scale = 4.0
        self.preview_panel_width = 380
        self.preview_panel_height = 380

        # Organ editör ayarları
        self.selected_organ = None
        self.selected_organ_index = -1
        self.dragging_organ = False
        self.drag_start_angle = 0
        self.organ_editor_mode = False  # True = organ düzenleme modu aktif
        self.hover_organ_index = -1
        self.add_organ_menu_open = False
        self.organ_overlap_warning = False
        self.preview_center_x = 0
        self.preview_center_y = 0

        # Organ editör butonları
        self.remove_btn_rect = None
        self.add_organ_btns = []
        self.organ_param_inputs = {}  # Seçili organ için parametre input'ları

        # Entity editör pop-up
        self.entity_popup_open = False
        self.popup_close_btn = None
        self.popup_entity = None  # Popup'ta düzenlenen varlık

        # Entity editör için varsayılanlar
        self.selected_entity = None
        self.dummy_optropis = []
        self.dummy_notropi = None

        self.settings_categories = {
            "WORLD (DÜNYA)": ["FOOD_COUNT", "KAOTROPI_COUNT", "FOOD_AREA"],
            "CILIA (SİLLER)": ["CILIA_SPEED_MULTI", "GROW_CILIA"],
            "FLAGELLA (KAMÇI)": ["FLAGELLA_SPEED_MULTI", "GROW_FLAGELLA"],
            "PHOTORECEPTOR (GÖZ)": ["GROW_VISION_RANGE", "GROW_VISION_ANGLE"],
            "MECHANORECEPTOR (KULAK)": ["GROW_SOUND"],
            "CHEMORECEPTOR (BURUN)": ["GROW_SMELL"],
            "VACUOLE (KOFUL)": ["VACUOLE_ENERGY_MULTI", "GROW_MAX_ENERGY"],
            "RIBOSOME (RİBOZOM)": ["RIBOSOME_TIME", "GROW_RIBOSOME"],
            "MEMBRANE (ZAR)": ["GROW_ENERGY_REGEN"],
            "DIGESTION (SİNDİRİM)": ["DIGESTION_TIME", "GROW_DIGESTION"],
            "CYTOPLASM (SİTOPLAZMA)": ["GROW_BODY"],
            "CYTOSKELETON (İSKELET)": ["CYTOSKELETON_AREA"],
            "MEMORY (HAFIZA)": ["GROW_MEMORY"]
        }
        
        self.setup_ui()

    def setup_ui(self):
        self.ui_elements = []
        if self.state == "SETTINGS":
            self.scroll_y = 0
            y = 100
            for cat, attrs in self.settings_categories.items():
                y += 60
                for attr in attrs:
                    ibox = InputBox(self.screen_width - 160, y, 100, 32, attr, self.font_small)
                    self.ui_elements.append(ibox)
                    y += 45
                y += 20
            self.total_content_height = y - 100
            self.max_scroll = min(0, (self.screen_height - 100) - self.total_content_height)
        
        elif self.state == "ENTITIES":
            self.dummy_optropis = [Optropi(i, 0, 0, c) for i, c in enumerate([(255,0,255), (255,255,0), (0,255,0), (255,165,0)])]
            self.dummy_notropi = Notropi(0, 0, 0)
            self.selected_entity = self.dummy_optropis[0]
            self.create_entity_editor()

    def refresh_selected_entity(self):
        """Seçili entity'yi güncel config ile yeniden oluşturur."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return

        # Seçili entity'nin index ve rengini sakla
        if isinstance(entity, Notropi):
            ent_id = "notropi"
            # Gen değeri değiştiğinde organ config'i temizle (varsayılan organlarla yeniden oluştur)
            game_settings.clear_entity_organs(ent_id)
            # Notropi'yi yeniden oluştur
            self.dummy_notropi = Notropi(0, 0, 0)
            self.selected_entity = self.dummy_notropi
            if self.entity_popup_open:
                self.popup_entity = self.dummy_notropi
        else:
            idx = entity.index
            color = entity.color
            ent_id = f"optropi_{idx}"
            # Gen değeri değiştiğinde organ config'i temizle (varsayılan organlarla yeniden oluştur)
            game_settings.clear_entity_organs(ent_id)
            # Optropi'yi yeniden oluştur
            self.dummy_optropis[idx] = Optropi(idx, 0, 0, color)
            self.selected_entity = self.dummy_optropis[idx]
            if self.entity_popup_open:
                self.popup_entity = self.dummy_optropis[idx]

    def get_organ_angular_width(self, organ):
        """Organın zar üzerinde kapladığı açısal genişliği hesaplar (derece)."""
        organ_name = organ.__class__.__name__
        base_width = ORGAN_TYPES.get(organ_name, {}).get("base_width", 10)

        # Organa özel genişlik hesabı
        if isinstance(organ, Photoreceptor):
            # Görüş açısı ne kadar genişse o kadar yer kaplar
            return max(15, math.degrees(organ.logic.angle) * 0.5 + base_width)
        elif isinstance(organ, Mechanoreceptor):
            # Size'a göre genişlik
            return base_width + organ.logic.size * 5
        elif isinstance(organ, Chemoreceptor):
            return base_width + organ.logic.length * 0.5
        elif isinstance(organ, Flagella):
            return base_width + organ.logic.length * 0.3
        elif isinstance(organ, Cilia):
            return base_width + organ.logic.length * 0.2

        return base_width

    def check_organ_overlap(self, organ_index, new_angle):
        """
        Belirli bir açıda organ örtüşmesi olup olmadığını kontrol eder.
        Returns: (overlap_exists, overlapping_organ_index)
        """
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return False, -1

        organ = entity.organs[organ_index]
        organ_name = organ.__class__.__name__

        # İç organlar için örtüşme kontrolü yapma
        if ORGAN_TYPES.get(organ_name, {}).get("internal", True):
            return False, -1

        new_angle_deg = math.degrees(new_angle) % 360
        organ_width = self.get_organ_angular_width(organ)

        for i, other in enumerate(entity.organs):
            if i == organ_index:
                continue

            other_name = other.__class__.__name__
            if ORGAN_TYPES.get(other_name, {}).get("internal", True):
                continue

            other_angle_deg = math.degrees(other.attachment_angle) % 360
            other_width = self.get_organ_angular_width(other)

            # İki organın arasındaki açısal mesafe
            diff = abs(new_angle_deg - other_angle_deg)
            if diff > 180:
                diff = 360 - diff

            # Minimum mesafe = her iki organın yarı genişliklerinin toplamı
            min_distance = (organ_width + other_width) / 2

            if diff < min_distance:
                return True, i

        return False, -1

    def get_organ_at_position(self, screen_x, screen_y, preview_center_x, preview_center_y):
        """Ekran koordinatında bir organ var mı kontrol eder."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return -1

        # Preview merkezine göre offset
        dx = screen_x - preview_center_x
        dy = screen_y - preview_center_y

        # Tıklama noktasının açısı
        click_angle = math.atan2(dy, dx)
        click_dist = math.sqrt(dx*dx + dy*dy)

        # Büyütülmüş yarıçap
        scaled_radius = entity.radius * self.preview_scale

        # Zar yakınında mı? (±50 piksel tolerans)
        if abs(click_dist - scaled_radius) > 50:
            return -1

        # En yakın organı bul
        best_match = -1
        best_diff = float('inf')

        for i, organ in enumerate(entity.organs):
            organ_name = organ.__class__.__name__
            # İç organları atla
            if ORGAN_TYPES.get(organ_name, {}).get("internal", True):
                continue

            # Organın açısı (entity sağa baktığı için düzeltme yapmaya gerek yok)
            organ_angle = organ.attachment_angle

            # Açı farkı
            diff = abs(math.atan2(math.sin(click_angle - organ_angle),
                                  math.cos(click_angle - organ_angle)))
            diff_deg = math.degrees(diff)

            # Organın genişliği kadar tolerans
            organ_width = self.get_organ_angular_width(organ)

            if diff_deg < organ_width and diff < best_diff:
                best_diff = diff
                best_match = i

        return best_match

    def add_organ_to_entity(self, organ_type, angle=0):
        """Entity'ye yeni organ ekler."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return False

        # Organ türüne göre yeni organ oluştur
        if organ_type == "Photoreceptor":
            new_organ = Photoreceptor(attachment_angle=angle, range=15, angle=0.3)
        elif organ_type == "Mechanoreceptor":
            new_organ = Mechanoreceptor(attachment_angle=angle, size=1.0)
        elif organ_type == "Chemoreceptor":
            new_organ = Chemoreceptor(attachment_angle=angle, length=5.0)
        elif organ_type == "Flagella":
            new_organ = Flagella(attachment_angle=angle, length=10.0)
        elif organ_type == "Cilia":
            new_organ = Cilia(attachment_angle=angle, length=3.0)
        else:
            return False

        # Örtüşme kontrolü
        temp_index = len(entity.organs)
        entity.organs.append(new_organ)

        overlap, _ = self.check_organ_overlap(temp_index, angle)
        if overlap:
            # Örtüşme varsa eklenemez, geri al
            entity.organs.pop()
            return False

        entity.recalculate_physics()
        return True

    def remove_selected_organ(self):
        """Seçili organı entity'den kaldırır."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity or self.selected_organ_index < 0:
            return False

        organ = entity.organs[self.selected_organ_index]
        organ_name = organ.__class__.__name__

        # Kritik organları kaldırma
        if organ_name in ["Membrane", "Cytoplasm", "Cytoskeleton"]:
            return False

        entity.organs.pop(self.selected_organ_index)
        self.selected_organ = None
        self.selected_organ_index = -1
        entity.recalculate_physics()
        return True

    def extract_organ_config(self, entity):
        """Entity'den organ konfigürasyonunu çıkarır."""
        organs_config = []
        for organ in entity.organs:
            organ_name = organ.__class__.__name__
            config = {
                "type": organ_name,
                "angle": organ.attachment_angle
            }

            # Organa özel parametreler
            if organ_name == "Photoreceptor":
                config["range"] = organ.logic.range
                config["angle_val"] = organ.logic.angle
            elif organ_name == "Mechanoreceptor":
                config["sensitivity"] = organ.logic.sensitivity
            elif organ_name == "Chemoreceptor":
                config["length"] = organ.logic.length
            elif organ_name == "Flagella":
                config["length"] = organ.logic.length
            elif organ_name == "Cilia":
                config["length"] = organ.logic.length
            elif organ_name == "Cytoplasm":
                config["size"] = organ.logic.size
            elif organ_name == "Vacuole":
                config["size"] = organ.logic.size
            elif organ_name == "Ribosome":
                config["time"] = organ.logic.base_production_time

            organs_config.append(config)

        return organs_config

    def save_all_organ_configs(self):
        """Tüm entity'lerin organ konfigürasyonlarını kaydet."""
        for i, entity in enumerate(self.dummy_optropis):
            ent_id = f"optropi_{entity.index}"
            organs_config = self.extract_organ_config(entity)
            game_settings.set_entity_organs(ent_id, organs_config)

        if self.dummy_notropi:
            organs_config = self.extract_organ_config(self.dummy_notropi)
            game_settings.set_entity_organs("notropi", organs_config)

    def create_entity_editor(self):
        self.entity_ui_elements = []
        if not self.selected_entity:
            return
        ent_id = "notropi" if isinstance(self.selected_entity, Notropi) else f"optropi_{self.selected_entity.index}"
        cfg = game_settings.ENTITY_CONFIGS[ent_id]

        # InputBox'lar draw_entities'de pozisyonlanacak
        # Organ editöründe düzenlenen parametreleri atla
        skip_keys = [
            "name", "organs",
            # Organ parametreleri (artık organ editöründe düzenleniyor)
            "smell", "sound", "vision_range", "vision_angle", "flagella", "cilia"
        ]
        for key in cfg.keys():
            if key in skip_keys:
                continue
            ibox = InputBox(0, 0, 80, 28, key, self.font_small, ent_id=ent_id,
                           on_change=self.refresh_selected_entity)
            self.entity_ui_elements.append((key, ibox))

    def set_state(self, state):
        self.state = state
        self.setup_ui()

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, (0, 0, self.sidebar_width, self.screen_height))
        self.screen.blit(self.font_title.render("EVO", True, ACCENT_COLOR), (30, 40))
        self.screen.blit(self.font_small.render("DESIGNER v4.1", True, TEXT_COLOR), (30, 85))
        for i, tab in enumerate(self.tabs):
            y = 180 + i * 60
            rect = pygame.Rect(0, y, self.sidebar_width, 50)
            color = ACCENT_COLOR if tab == self.state else (WHITE if rect.collidepoint(pygame.mouse.get_pos()) else GRAY)
            if tab == self.state: pygame.draw.rect(self.screen, ACCENT_COLOR, (0, y, 5, 50))
            self.screen.blit(self.font_main.render(tab, True, color), (30, y + 12))

    def draw_dashboard(self):
        rect = pygame.Rect(self.sidebar_width + 100, self.screen_height//2 - 40, 400, 80)
        color = SUCCESS if rect.collidepoint(pygame.mouse.get_pos()) else ACCENT_COLOR
        pygame.draw.rect(self.screen, color, rect, 2)
        txt = self.font_title.render("START WORLD", True, color)
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_scrollbar(self):
        if self.max_scroll >= 0: return
        tx, ty, th = self.screen_width - 25, 100, self.screen_height - 120
        pygame.draw.rect(self.screen, SIDEBAR_COLOR, (tx, ty, 12, th))
        thumb_h = max(30, th * ((self.screen_height - 120) / self.total_content_height))
        thumb_y = ty + (th - thumb_h) * (self.scroll_y / self.max_scroll)
        pygame.draw.rect(self.screen, GRAY, (int(tx + 2), int(thumb_y), 8, int(thumb_h)))

    def draw_settings(self):
        cy = 100 + self.scroll_y
        box_idx = 0
        for cat, attrs in self.settings_categories.items():
            if cy + 20 > 80:
                pygame.draw.line(self.screen, HIGHLIGHT, (int(self.sidebar_width + 40), int(cy - 5)), (int(self.screen_width - 40), int(cy - 5)), 1)
                self.screen.blit(self.font_main.render(cat, True, ACCENT_COLOR), (int(self.sidebar_width + 40), int(cy - 35)))
            cy += 60
            for attr in attrs:
                if 80 < cy + 40 < self.screen_height + 40:
                    row_rect = pygame.Rect(int(self.sidebar_width + 30), int(cy - 4), int(self.screen_width - self.sidebar_width - 80), 38)
                    if row_rect.collidepoint(pygame.mouse.get_pos()): pygame.draw.rect(self.screen, (40, 50, 70), row_rect)
                    self.screen.blit(self.font_small.render(attr.replace("_", " "), True, TEXT_COLOR), (int(self.sidebar_width + 50), int(cy + 8)))
                if box_idx < len(self.ui_elements):
                    self.ui_elements[box_idx].update_text(); self.ui_elements[box_idx].draw(self.screen, self.scroll_y, self.screen_height); box_idx += 1
                cy += 45
            cy += 20
        pygame.draw.rect(self.screen, BG_COLOR, (self.sidebar_width, 0, self.screen_width, 80))
        self.screen.blit(self.font_main.render("WORLD & EVOLUTION PARAMETERS", True, WHITE), (self.sidebar_width + 40, 30))
        self.draw_scrollbar()

    def draw_organ_highlights(self, center_x, center_y):
        """Seçili ve hover organları vurgular. Membran üzerinde tüm organların pozisyonlarını gösterir."""
        entity = self.popup_entity if self.entity_popup_open else self.selected_entity
        if not entity:
            return

        scaled_radius = entity.radius * self.preview_scale

        # Önce membran çemberini çiz (organ editör modundayken)
        if self.organ_editor_mode:
            # Dış çember (membran)
            pygame.draw.circle(self.screen, HIGHLIGHT, (int(center_x), int(center_y)),
                             int(scaled_radius + 15), 1)

            # Açı göstergeleri (her 45 derecede)
            for angle_deg in range(0, 360, 45):
                angle_rad = math.radians(angle_deg)
                inner_x = center_x + math.cos(angle_rad) * (scaled_radius + 5)
                inner_y = center_y + math.sin(angle_rad) * (scaled_radius + 5)
                outer_x = center_x + math.cos(angle_rad) * (scaled_radius + 15)
                outer_y = center_y + math.sin(angle_rad) * (scaled_radius + 15)
                pygame.draw.line(self.screen, GRAY, (int(inner_x), int(inner_y)),
                               (int(outer_x), int(outer_y)), 1)

        for i, organ in enumerate(entity.organs):
            organ_name = organ.__class__.__name__
            if ORGAN_TYPES.get(organ_name, {}).get("internal", True):
                continue

            # Organın pozisyonu
            angle = organ.attachment_angle
            pos_x = center_x + math.cos(angle) * scaled_radius
            pos_y = center_y + math.sin(angle) * scaled_radius

            organ_color = ORGAN_TYPES.get(organ_name, {}).get("color", WHITE)

            # Editor modunda tüm organların pozisyonlarını göster
            if self.organ_editor_mode:
                # Açısal genişlik yayı
                width_deg = self.get_organ_angular_width(organ)
                width_rad = math.radians(width_deg)

                # Her organın kapladığı alanı göster (yarı saydam)
                if i != self.selected_organ_index:
                    # Yay çiz
                    arc_rect = pygame.Rect(
                        int(center_x - scaled_radius - 8),
                        int(center_y - scaled_radius - 8),
                        int((scaled_radius + 8) * 2),
                        int((scaled_radius + 8) * 2)
                    )
                    arc_color = tuple(c // 2 for c in organ_color)  # Daha koyu
                    pygame.draw.arc(self.screen, arc_color, arc_rect,
                                  -(angle + width_rad/2), -(angle - width_rad/2), 2)

            # Seçili organ için
            if i == self.selected_organ_index:
                # Parlak daire
                pygame.draw.circle(self.screen, SUCCESS, (int(pos_x), int(pos_y)), 14, 3)

                # Açısal genişlik göstergesi (parlak)
                width_deg = self.get_organ_angular_width(organ)
                width_rad = math.radians(width_deg)
                arc_rect = pygame.Rect(
                    int(center_x - scaled_radius - 10),
                    int(center_y - scaled_radius - 10),
                    int((scaled_radius + 10) * 2),
                    int((scaled_radius + 10) * 2)
                )
                pygame.draw.arc(self.screen, SUCCESS, arc_rect,
                              -(angle + width_rad/2), -(angle - width_rad/2), 4)

            # Hover organ için
            elif i == self.hover_organ_index:
                pygame.draw.circle(self.screen, ACCENT_COLOR, (int(pos_x), int(pos_y)), 12, 2)

    def get_organ_editable_params(self, organ):
        """Organın düzenlenebilir parametrelerini döndürür."""
        organ_name = organ.__class__.__name__
        params = {}

        if organ_name == "Photoreceptor":
            params["range"] = ("Range", organ.logic.range, 5, 100)
            params["angle"] = ("Angle", math.degrees(organ.logic.angle), 1, 180)
        elif organ_name == "Mechanoreceptor":
            # sensitivity = size * 30, kullanıcıya sensitivity göster
            params["sensitivity"] = ("Sensitivity", organ.logic.sensitivity, 3, 150)
        elif organ_name == "Chemoreceptor":
            params["length"] = ("Length", organ.logic.length, 1, 20)
        elif organ_name == "Flagella":
            params["length"] = ("Length", organ.logic.length, 1, 50)
        elif organ_name == "Cilia":
            params["length"] = ("Length", organ.logic.length, 1, 20)

        return params

    def update_organ_param(self, param_name, new_value):
        """Seçili organın parametresini günceller."""
        if not self.selected_organ:
            return

        organ_name = self.selected_organ.__class__.__name__

        try:
            if organ_name == "Photoreceptor":
                if param_name == "range":
                    self.selected_organ.logic.range = float(new_value)
                elif param_name == "angle":
                    self.selected_organ.logic.angle = math.radians(float(new_value))
            elif organ_name == "Mechanoreceptor":
                if param_name == "sensitivity":
                    # sensitivity = size * 30, yani size = sensitivity / 30
                    self.selected_organ.logic.size = float(new_value) / 30.0
            elif organ_name == "Chemoreceptor":
                if param_name == "length":
                    self.selected_organ.logic.length = float(new_value)
            elif organ_name == "Flagella":
                if param_name == "length":
                    self.selected_organ.logic.length = float(new_value)
                    self.selected_organ.logic.recalculate_boosts()
            elif organ_name == "Cilia":
                if param_name == "length":
                    self.selected_organ.logic.length = float(new_value)
                    self.selected_organ.logic.recalculate_boosts()

            # Fiziği yeniden hesapla
            entity = self.popup_entity if self.entity_popup_open else self.selected_entity
            if entity:
                entity.recalculate_physics()
        except:
            pass

    def draw_organ_editor_panel(self, card_x, card_y):
        """Organ editör panelini çizer."""
        panel_width = self.preview_panel_width
        panel_height = 380

        # Panel arka plan
        panel_rect = pygame.Rect(card_x, card_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, CARD_COLOR, panel_rect)
        pygame.draw.rect(self.screen, ACCENT_COLOR if self.organ_editor_mode else HIGHLIGHT, panel_rect, 2)

        # Başlık
        title = "ORGAN EDITOR" + (" [ACTIVE]" if self.organ_editor_mode else "")
        title_color = SUCCESS if self.organ_editor_mode else ACCENT_COLOR
        self.screen.blit(self.font_main.render(title, True, title_color),
                        (card_x + 20, card_y + 12))

        # Editor mode toggle butonu
        toggle_rect = pygame.Rect(card_x + panel_width - 85, card_y + 12, 70, 24)
        toggle_hover = toggle_rect.collidepoint(pygame.mouse.get_pos())
        toggle_color = SUCCESS if self.organ_editor_mode else GRAY
        pygame.draw.rect(self.screen, toggle_color, toggle_rect)
        toggle_text = "ON" if self.organ_editor_mode else "OFF"
        text = self.font_small.render(toggle_text, True, BLACK if self.organ_editor_mode else WHITE)
        self.screen.blit(text, text.get_rect(center=toggle_rect.center))

        if not self.organ_editor_mode:
            # Editor kapalıyken sadece talimat göster
            self.screen.blit(self.font_small.render("Enable editor to modify organs", True, GRAY),
                           (card_x + 20, card_y + 50))
            return

        # === SEÇİLİ ORGAN BİLGİSİ ===
        y = card_y + 45
        pygame.draw.line(self.screen, HIGHLIGHT, (card_x + 10, y), (card_x + panel_width - 10, y))
        y += 8

        if self.selected_organ:
            organ_name = self.selected_organ.__class__.__name__
            organ_color = ORGAN_TYPES.get(organ_name, {}).get("color", WHITE)
            pygame.draw.rect(self.screen, organ_color, (card_x + 15, y, 12, 12))
            self.screen.blit(self.font_small.render(f"Selected: {organ_name}", True, WHITE),
                           (card_x + 35, y - 2))
            y += 18

            # Organ pozisyonu (derece)
            angle_deg = math.degrees(self.selected_organ.attachment_angle) % 360
            self.screen.blit(self.font_small.render(f"Position: {angle_deg:.1f}°", True, TEXT_COLOR),
                           (card_x + 35, y))
            y += 22

            # === ORGAN PARAMETRELERİ ===
            params = self.get_organ_editable_params(self.selected_organ)
            if params:
                pygame.draw.line(self.screen, HIGHLIGHT, (card_x + 10, y), (card_x + panel_width - 10, y))
                y += 5
                self.screen.blit(self.font_small.render("PARAMETERS:", True, ACCENT_COLOR), (card_x + 15, y))
                y += 20

                for param_key, (param_label, param_value, min_val, max_val) in params.items():
                    # Parametre adı
                    self.screen.blit(self.font_small.render(param_label, True, TEXT_COLOR), (card_x + 20, y + 2))

                    # Input box
                    input_rect = pygame.Rect(card_x + 100, y, 70, 22)
                    input_key = f"{self.selected_organ_index}_{param_key}"

                    # Input box'ı sakla
                    if input_key not in self.organ_param_inputs:
                        self.organ_param_inputs[input_key] = {
                            "rect": input_rect,
                            "text": f"{param_value:.1f}",
                            "active": False,
                            "param": param_key
                        }
                    else:
                        self.organ_param_inputs[input_key]["rect"] = input_rect
                        # Aktif değilse değeri güncelle
                        if not self.organ_param_inputs[input_key]["active"]:
                            self.organ_param_inputs[input_key]["text"] = f"{param_value:.1f}"

                    inp = self.organ_param_inputs[input_key]
                    box_color = ACCENT_COLOR if inp["active"] else HIGHLIGHT
                    pygame.draw.rect(self.screen, box_color, input_rect, 1)
                    if inp["active"]:
                        pygame.draw.rect(self.screen, (0, 50, 60), input_rect.inflate(-2, -2))

                    text_surf = self.font_small.render(inp["text"], True, WHITE)
                    self.screen.blit(text_surf, (input_rect.x + 5, input_rect.y + 3))

                    # Min-max göster
                    range_text = f"({min_val}-{max_val})"
                    self.screen.blit(self.font_small.render(range_text, True, GRAY), (card_x + 180, y + 2))

                    y += 26

            y += 5
            # Kaldır butonu
            self.remove_btn_rect = pygame.Rect(card_x + 15, y, 130, 26)
            remove_hover = self.remove_btn_rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, DANGER if remove_hover else (120, 50, 50), self.remove_btn_rect)
            pygame.draw.rect(self.screen, WHITE if remove_hover else GRAY, self.remove_btn_rect, 1)
            self.screen.blit(self.font_small.render("REMOVE ORGAN", True, WHITE),
                           (self.remove_btn_rect.x + 12, self.remove_btn_rect.y + 5))
        else:
            self.screen.blit(self.font_small.render("Click an organ in preview", True, GRAY),
                           (card_x + 15, y))
            self.screen.blit(self.font_small.render("to select it", True, GRAY),
                           (card_x + 15, y + 18))
            self.remove_btn_rect = None

        # Örtüşme uyarısı
        if self.organ_overlap_warning:
            self.screen.blit(self.font_small.render("! Overlap!", True, WARNING),
                           (card_x + 160, card_y + 95))

        # === ORGAN EKLEME BUTONLARI ===
        y = card_y + 150
        pygame.draw.line(self.screen, HIGHLIGHT, (card_x + 10, y), (card_x + panel_width - 10, y))
        y += 8
        self.screen.blit(self.font_small.render("ADD NEW ORGAN:", True, ACCENT_COLOR), (card_x + 15, y))
        y += 22

        addable_organs = ["Photoreceptor", "Mechanoreceptor", "Chemoreceptor", "Flagella", "Cilia"]
        btn_x = card_x + 10
        btn_y = y
        btn_width = 58
        btn_height = 26

        # Buton rect'lerini sakla (event handler için)
        self.add_organ_btns = []

        for i, organ_type in enumerate(addable_organs):
            organ_color = ORGAN_TYPES.get(organ_type, {}).get("color", WHITE)
            btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
            self.add_organ_btns.append((organ_type, btn_rect))
            is_hover = btn_rect.collidepoint(pygame.mouse.get_pos())

            # Buton arka planı
            bg_color = tuple(min(255, c + 40) for c in organ_color) if is_hover else organ_color
            pygame.draw.rect(self.screen, bg_color, btn_rect)
            pygame.draw.rect(self.screen, WHITE if is_hover else GRAY, btn_rect, 1)

            # Kısa isim
            short_names = {
                "Photoreceptor": "Eye",
                "Mechanoreceptor": "Ear",
                "Chemoreceptor": "Nose",
                "Flagella": "Flag",
                "Cilia": "Cilia"
            }
            text = self.font_small.render(short_names.get(organ_type, organ_type[:4]), True, BLACK)
            text_rect = text.get_rect(center=btn_rect.center)
            self.screen.blit(text, text_rect)

            btn_x += btn_width + 4
            if i == 2:  # 3 butondan sonra alt satıra geç
                btn_y += btn_height + 4
                btn_x = card_x + 10

        # === TALİMATLAR ===
        y = card_y + 260
        pygame.draw.line(self.screen, HIGHLIGHT, (card_x + 10, y), (card_x + panel_width - 10, y))
        y += 8
        instructions = [
            "• Click organ in preview to select",
            "• Drag to reposition on membrane",
            "• Organs cannot overlap"
        ]
        for inst in instructions:
            self.screen.blit(self.font_small.render(inst, True, GRAY), (card_x + 10, y))
            y += 16

    def draw_entity_popup(self):
        """Varlık düzenleme için tam ekran popup çizer."""
        if not self.entity_popup_open or not self.popup_entity:
            return

        # Yarı saydam arka plan
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Popup ana panel (ekranın büyük kısmını kaplar)
        margin = 30
        popup_rect = pygame.Rect(margin, margin,
                                  self.screen_width - margin * 2,
                                  self.screen_height - margin * 2)
        pygame.draw.rect(self.screen, CARD_COLOR, popup_rect)
        pygame.draw.rect(self.screen, ACCENT_COLOR, popup_rect, 2)

        # Başlık
        entity_name = "Notropi" if isinstance(self.popup_entity, Notropi) else f"Optropi #{self.popup_entity.index + 1}"
        title = f"EDITING: {entity_name}"
        self.screen.blit(self.font_title.render(title, True, ACCENT_COLOR),
                        (popup_rect.x + 20, popup_rect.y + 15))

        # Kapatma butonu (sağ üst)
        close_size = 40
        self.popup_close_btn = pygame.Rect(popup_rect.right - close_size - 10,
                                            popup_rect.y + 10,
                                            close_size, close_size)
        close_hover = self.popup_close_btn.collidepoint(pygame.mouse.get_pos())
        close_color = DANGER if close_hover else GRAY
        pygame.draw.rect(self.screen, close_color, self.popup_close_btn)
        pygame.draw.rect(self.screen, WHITE, self.popup_close_btn, 1)
        # X işareti
        cx, cy = self.popup_close_btn.center
        pygame.draw.line(self.screen, WHITE, (cx - 10, cy - 10), (cx + 10, cy + 10), 3)
        pygame.draw.line(self.screen, WHITE, (cx - 10, cy + 10), (cx + 10, cy - 10), 3)

        # İçerik alanı
        content_y = popup_rect.y + 70
        content_height = popup_rect.height - 90

        # === SOL BÖLÜM: Preview ve Organ Editor ===
        left_section_x = popup_rect.x + 20
        left_section_width = 450

        # Preview Panel
        preview_height = 350
        preview_rect = pygame.Rect(left_section_x, content_y, left_section_width, preview_height)
        border_color = SUCCESS if self.organ_editor_mode else HIGHLIGHT
        pygame.draw.rect(self.screen, (20, 25, 35), preview_rect)
        pygame.draw.rect(self.screen, border_color, preview_rect, 2 if self.organ_editor_mode else 1)

        # Preview başlık
        preview_title = "ORGANISM PREVIEW" + (" [EDIT MODE]" if self.organ_editor_mode else "")
        self.screen.blit(self.font_small.render(preview_title, True, SUCCESS if self.organ_editor_mode else ACCENT_COLOR),
                         (preview_rect.x + 10, preview_rect.y + 8))

        # Preview merkezi
        self.preview_center_x = preview_rect.x + preview_rect.width // 2
        self.preview_center_y = preview_rect.y + preview_rect.height // 2 + 15

        # Varlığı çiz
        self.screen.set_clip(pygame.Rect(preview_rect.x + 2, preview_rect.y + 28,
                                          preview_rect.width - 4, preview_rect.height - 32))
        self.draw_entity_preview(self.popup_entity, self.preview_center_x, self.preview_center_y, self.preview_scale)
        if self.organ_editor_mode:
            self.draw_organ_highlights(self.preview_center_x, self.preview_center_y)
        self.screen.set_clip(None)

        # Scale bilgisi
        scale_text = f"Scale: {self.preview_scale:.1f}x"
        if self.organ_editor_mode:
            scale_text += " | Drag organs to reposition"
        self.screen.blit(self.font_small.render(scale_text, True, GRAY),
                         (preview_rect.x + 10, preview_rect.bottom - 22))

        # Organ Editor Panel (Preview'in altında)
        editor_y = preview_rect.bottom + 15
        editor_height = content_height - preview_height - 20
        self.draw_popup_organ_editor(left_section_x, editor_y, left_section_width, editor_height)

        # === ORTA BÖLÜM: İstatistikler ===
        middle_section_x = left_section_x + left_section_width + 20
        middle_section_width = 280

        stats_rect = pygame.Rect(middle_section_x, content_y, middle_section_width, 180)
        pygame.draw.rect(self.screen, (25, 30, 40), stats_rect)
        pygame.draw.rect(self.screen, HIGHLIGHT, stats_rect, 1)

        self.screen.blit(self.font_main.render("STATISTICS", True, ACCENT_COLOR),
                        (stats_rect.x + 15, stats_rect.y + 10))

        self.popup_entity.recalculate_physics()
        stats = [
            ("Max Energy", f"{self.popup_entity.max_energy:.1f}"),
            ("Speed", f"{self.popup_entity.speed:.1f}"),
            ("Turn Rate", f"{self.popup_entity.max_turn_rate:.2f}"),
            ("Vision Range", f"{self.popup_entity.vision_range}"),
            ("Total Organs", f"{len(self.popup_entity.organs)}")
        ]

        sy = stats_rect.y + 45
        for k, v in stats:
            self.screen.blit(self.font_small.render(k, True, GRAY), (stats_rect.x + 20, sy))
            self.screen.blit(self.font_small.render(v, True, WHITE), (stats_rect.x + 150, sy))
            sy += 26

        # === SAĞ BÖLÜM: Starting Genes ===
        right_section_x = middle_section_x + middle_section_width + 20
        right_section_width = popup_rect.right - right_section_x - 20

        genes_rect = pygame.Rect(right_section_x, content_y, right_section_width, content_height)
        pygame.draw.rect(self.screen, (25, 30, 40), genes_rect)
        pygame.draw.rect(self.screen, HIGHLIGHT, genes_rect, 1)

        self.screen.blit(self.font_main.render("STARTING GENES", True, SUCCESS),
                        (genes_rect.x + 15, genes_rect.y + 10))

        gy = genes_rect.y + 50
        for key, ibox in self.entity_ui_elements:
            if gy + 28 > genes_rect.bottom - 20:
                break
            # Label
            self.screen.blit(self.font_small.render(key.replace("_", " ").upper(), True, TEXT_COLOR),
                            (genes_rect.x + 15, gy + 3))
            # Input box
            ibox.rect.x = genes_rect.x + right_section_width - 100
            ibox.rect.y = gy
            ibox.rect.width = 80
            ibox.rect.height = 24
            ibox.update_text()
            ibox.draw(self.screen)
            gy += 30

        self.screen.blit(self.font_small.render("* Changes auto-save", True, GRAY),
                        (genes_rect.x + 15, genes_rect.bottom - 25))

    def draw_popup_organ_editor(self, x, y, width, height):
        """Popup içindeki organ editör panelini çizer."""
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (25, 30, 40), panel_rect)
        pygame.draw.rect(self.screen, ACCENT_COLOR if self.organ_editor_mode else HIGHLIGHT, panel_rect, 2)

        # Başlık ve Toggle
        title = "ORGAN EDITOR" + (" [ACTIVE]" if self.organ_editor_mode else "")
        title_color = SUCCESS if self.organ_editor_mode else ACCENT_COLOR
        self.screen.blit(self.font_main.render(title, True, title_color), (x + 15, y + 10))

        # Toggle butonu
        toggle_rect = pygame.Rect(x + width - 90, y + 10, 75, 28)
        toggle_hover = toggle_rect.collidepoint(pygame.mouse.get_pos())
        toggle_color = SUCCESS if self.organ_editor_mode else GRAY
        pygame.draw.rect(self.screen, toggle_color, toggle_rect)
        toggle_text = "ON" if self.organ_editor_mode else "OFF"
        text = self.font_small.render(toggle_text, True, BLACK if self.organ_editor_mode else WHITE)
        self.screen.blit(text, text.get_rect(center=toggle_rect.center))

        if not self.organ_editor_mode:
            self.screen.blit(self.font_small.render("Enable editor to modify organs", True, GRAY), (x + 15, y + 50))
            return

        # İki sütunlu layout
        col1_x = x + 10
        col2_x = x + width // 2 + 10
        col_width = width // 2 - 20

        # === SOL SÜTUN: Seçili Organ Bilgisi ===
        cy = y + 45

        if self.selected_organ:
            organ_name = self.selected_organ.__class__.__name__
            organ_color = ORGAN_TYPES.get(organ_name, {}).get("color", WHITE)
            pygame.draw.rect(self.screen, organ_color, (col1_x + 5, cy, 14, 14))
            self.screen.blit(self.font_small.render(f"Selected: {organ_name}", True, WHITE), (col1_x + 25, cy - 1))
            cy += 20

            angle_deg = math.degrees(self.selected_organ.attachment_angle) % 360
            self.screen.blit(self.font_small.render(f"Position: {angle_deg:.1f}°", True, TEXT_COLOR), (col1_x + 25, cy))
            cy += 25

            # Parametreler
            params = self.get_organ_editable_params(self.selected_organ)
            if params:
                self.screen.blit(self.font_small.render("PARAMETERS:", True, ACCENT_COLOR), (col1_x + 5, cy))
                cy += 20

                for param_key, (param_label, param_value, min_val, max_val) in params.items():
                    self.screen.blit(self.font_small.render(param_label, True, TEXT_COLOR), (col1_x + 10, cy + 2))

                    input_rect = pygame.Rect(col1_x + 80, cy, 60, 22)
                    input_key = f"{self.selected_organ_index}_{param_key}"

                    if input_key not in self.organ_param_inputs:
                        self.organ_param_inputs[input_key] = {
                            "rect": input_rect,
                            "text": f"{param_value:.1f}",
                            "active": False,
                            "param": param_key
                        }
                    else:
                        self.organ_param_inputs[input_key]["rect"] = input_rect
                        if not self.organ_param_inputs[input_key]["active"]:
                            self.organ_param_inputs[input_key]["text"] = f"{param_value:.1f}"

                    inp = self.organ_param_inputs[input_key]
                    box_color = ACCENT_COLOR if inp["active"] else HIGHLIGHT
                    pygame.draw.rect(self.screen, box_color, input_rect, 1)
                    if inp["active"]:
                        pygame.draw.rect(self.screen, (0, 50, 60), input_rect.inflate(-2, -2))
                    text_surf = self.font_small.render(inp["text"], True, WHITE)
                    self.screen.blit(text_surf, (input_rect.x + 5, input_rect.y + 3))

                    range_text = f"({min_val}-{max_val})"
                    self.screen.blit(self.font_small.render(range_text, True, GRAY), (col1_x + 150, cy + 2))
                    cy += 26

            cy += 5
            # Kaldır butonu
            self.remove_btn_rect = pygame.Rect(col1_x + 5, cy, 130, 26)
            remove_hover = self.remove_btn_rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, DANGER if remove_hover else (120, 50, 50), self.remove_btn_rect)
            pygame.draw.rect(self.screen, WHITE if remove_hover else GRAY, self.remove_btn_rect, 1)
            self.screen.blit(self.font_small.render("REMOVE ORGAN", True, WHITE),
                           (self.remove_btn_rect.x + 12, self.remove_btn_rect.y + 5))
        else:
            self.screen.blit(self.font_small.render("Click an organ in", True, GRAY), (col1_x + 5, cy))
            self.screen.blit(self.font_small.render("preview to select", True, GRAY), (col1_x + 5, cy + 18))
            self.remove_btn_rect = None

        if self.organ_overlap_warning:
            self.screen.blit(self.font_small.render("! Overlap detected!", True, WARNING), (col1_x + 5, y + height - 25))

        # === SAĞ SÜTUN: Organ Ekleme ===
        cy = y + 45
        self.screen.blit(self.font_small.render("ADD NEW ORGAN:", True, ACCENT_COLOR), (col2_x, cy))
        cy += 25

        addable_organs = ["Photoreceptor", "Mechanoreceptor", "Chemoreceptor", "Flagella", "Cilia"]
        short_names = {
            "Photoreceptor": "Eye",
            "Mechanoreceptor": "Ear",
            "Chemoreceptor": "Nose",
            "Flagella": "Flagella",
            "Cilia": "Cilia"
        }

        self.add_organ_btns = []
        btn_width = 85
        btn_height = 28

        for i, organ_type in enumerate(addable_organs):
            organ_color = ORGAN_TYPES.get(organ_type, {}).get("color", WHITE)
            btn_rect = pygame.Rect(col2_x + (i % 2) * (btn_width + 10), cy + (i // 2) * (btn_height + 8), btn_width, btn_height)
            self.add_organ_btns.append((organ_type, btn_rect))
            is_hover = btn_rect.collidepoint(pygame.mouse.get_pos())

            bg_color = tuple(min(255, c + 40) for c in organ_color) if is_hover else organ_color
            pygame.draw.rect(self.screen, bg_color, btn_rect)
            pygame.draw.rect(self.screen, WHITE if is_hover else GRAY, btn_rect, 1)

            text = self.font_small.render(short_names.get(organ_type, organ_type[:5]), True, BLACK)
            self.screen.blit(text, text.get_rect(center=btn_rect.center))

        # Talimatlar
        inst_y = y + height - 50
        pygame.draw.line(self.screen, HIGHLIGHT, (col2_x, inst_y - 5), (x + width - 15, inst_y - 5))
        instructions = ["• Click organ to select", "• Drag to reposition"]
        for inst in instructions:
            self.screen.blit(self.font_small.render(inst, True, GRAY), (col2_x, inst_y))
            inst_y += 18

    def draw_entity_preview(self, entity, center_x, center_y, scale):
        """Varlığı büyütülmüş olarak çizer - tüm organeller orantılı."""
        if not entity:
            return

        # Orijinal değerleri sakla
        original_radius = entity.radius
        original_pos = pygame.math.Vector2(entity.pos)
        original_direction = pygame.math.Vector2(entity.direction)

        # Organ orijinal değerlerini sakla
        organ_originals = []
        for organ in entity.organs:
            orig = {}
            if hasattr(organ.logic, 'length'):
                orig['length'] = organ.logic.length
                organ.logic.length *= scale
            if hasattr(organ.logic, 'size'):
                orig['size'] = organ.logic.size
                organ.logic.size *= scale
            # Vacuole area'sını scale et (alan = scale^2 ile büyür)
            if hasattr(organ.logic, 'area'):
                orig['area'] = organ.logic.area
                organ.logic.area *= (scale * scale)
            # Görüş menzilini scale et (clip region taşmayı önlüyor)
            if hasattr(organ.logic, 'range'):
                orig['range'] = organ.logic.range
                organ.logic.range *= scale
            # sensitivity bir property (size * 30), size zaten büyütüldü
            organ_originals.append(orig)

        # Büyütülmüş değerleri uygula
        entity.radius = original_radius * scale
        entity.pos = pygame.math.Vector2(center_x, center_y)

        # Yön vektörünü sağa doğru ayarla (güzel görünsün)
        entity.direction = pygame.math.Vector2(1, 0)

        # Varlığı çiz (hafıza çizimi hariç, sadece organlar)
        for organ in entity.organs:
            organ.draw(self.screen, entity)

        # Orijinal değerleri geri yükle
        entity.radius = original_radius
        entity.pos = original_pos
        entity.direction = original_direction

        for i, organ in enumerate(entity.organs):
            orig = organ_originals[i]
            if 'length' in orig:
                organ.logic.length = orig['length']
            if 'size' in orig:
                organ.logic.size = orig['size']
            if 'area' in orig:
                organ.logic.area = orig['area']
            if 'range' in orig:
                organ.logic.range = orig['range']

    def draw_entities(self):
        # Popup açıksa, popup'ı çiz
        if self.entity_popup_open:
            self.draw_entity_popup()
            return

        # Ana panel başlığı
        self.screen.blit(self.font_title.render("SPECIES EDITOR", True, ACCENT_COLOR),
                        (self.sidebar_width + 40, 30))
        self.screen.blit(self.font_small.render("Select a species to edit its organs and genes", True, GRAY),
                        (self.sidebar_width + 40, 75))

        # Varlık kartları - grid düzeni
        card_width = 280
        card_height = 200
        cards_per_row = 3
        start_x = self.sidebar_width + 40
        start_y = 120
        gap = 25

        all_entities = self.dummy_optropis + [self.dummy_notropi]

        for idx, ent in enumerate(all_entities):
            row = idx // cards_per_row
            col = idx % cards_per_row

            card_x = start_x + col * (card_width + gap)
            card_y = start_y + row * (card_height + gap)

            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            is_hover = card_rect.collidepoint(pygame.mouse.get_pos())

            # Kart arka planı
            bg_color = HIGHLIGHT if is_hover else CARD_COLOR
            pygame.draw.rect(self.screen, bg_color, card_rect)
            pygame.draw.rect(self.screen, ACCENT_COLOR if is_hover else GRAY, card_rect, 2 if is_hover else 1)

            # Varlık adı
            name = "Notropi" if isinstance(ent, Notropi) else f"Optropi #{idx + 1}"
            self.screen.blit(self.font_main.render(name, True, ent.color), (card_x + 15, card_y + 12))

            # Varlık preview (küçük)
            preview_center_x = card_x + card_width // 2
            preview_center_y = card_y + 95
            mini_scale = 2.0

            # Clip region
            self.screen.set_clip(pygame.Rect(card_x + 5, card_y + 40, card_width - 10, 100))
            self.draw_entity_preview(ent, preview_center_x, preview_center_y, mini_scale)
            self.screen.set_clip(None)

            # İstatistikler
            ent.recalculate_physics()
            stats_y = card_y + 150
            stats_text = f"Organs: {len(ent.organs)}  |  Energy: {ent.max_energy:.0f}  |  Speed: {ent.speed:.1f}"
            self.screen.blit(self.font_small.render(stats_text, True, GRAY), (card_x + 15, stats_y))

            # Edit butonu
            edit_btn = pygame.Rect(card_x + card_width - 80, card_y + card_height - 40, 65, 28)
            edit_hover = edit_btn.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, ACCENT_COLOR if edit_hover else HIGHLIGHT, edit_btn)
            pygame.draw.rect(self.screen, WHITE if edit_hover else GRAY, edit_btn, 1)
            edit_text = self.font_small.render("EDIT", True, BLACK if edit_hover else WHITE)
            self.screen.blit(edit_text, edit_text.get_rect(center=edit_btn.center))

    def handle_entity_list_events(self, event, m_pos):
        """Varlık listesi ve popup olaylarını işler."""
        if self.state != "ENTITIES":
            return

        # Popup kapatma
        if self.entity_popup_open:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.popup_close_btn and self.popup_close_btn.collidepoint(m_pos):
                    self.entity_popup_open = False
                    self.popup_entity = None
                    self.selected_organ = None
                    self.selected_organ_index = -1
                    self.organ_editor_mode = False
                    self.organ_param_inputs = {}
                    return
            return  # Popup açıkken diğer olayları organ editöre aktar

        # Varlık kartlarına tıklama
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            card_width = 280
            card_height = 200
            cards_per_row = 3
            start_x = self.sidebar_width + 40
            start_y = 120
            gap = 25

            all_entities = self.dummy_optropis + [self.dummy_notropi]

            for idx, ent in enumerate(all_entities):
                row = idx // cards_per_row
                col = idx % cards_per_row

                card_x = start_x + col * (card_width + gap)
                card_y = start_y + row * (card_height + gap)

                # Edit butonuna tıklama
                edit_btn = pygame.Rect(card_x + card_width - 80, card_y + card_height - 40, 65, 28)
                if edit_btn.collidepoint(m_pos):
                    self.popup_entity = ent
                    self.selected_entity = ent
                    self.entity_popup_open = True
                    self.selected_organ = None
                    self.selected_organ_index = -1
                    self.organ_param_inputs = {}
                    self.create_entity_editor()
                    return

                # Kart alanına tıklama (edit butonu dışında)
                card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
                if card_rect.collidepoint(m_pos):
                    self.popup_entity = ent
                    self.selected_entity = ent
                    self.entity_popup_open = True
                    self.selected_organ = None
                    self.selected_organ_index = -1
                    self.organ_param_inputs = {}
                    self.create_entity_editor()
                    return

    def handle_organ_editor_events(self, event, m_pos):
        """Organ editör olaylarını işler."""
        if self.state != "ENTITIES":
            return

        # Popup kapalıysa işleme
        if not self.entity_popup_open or not self.popup_entity:
            return

        # Popup içindeki preview ve editor alanı
        margin = 30
        popup_rect = pygame.Rect(margin, margin,
                                  self.screen_width - margin * 2,
                                  self.screen_height - margin * 2)
        content_y = popup_rect.y + 70
        left_section_x = popup_rect.x + 20
        left_section_width = 450
        preview_height = 350
        preview_rect = pygame.Rect(left_section_x, content_y, left_section_width, preview_height)

        # Editor panel pozisyonu
        editor_y = preview_rect.bottom + 15
        panel_width = left_section_width

        # Toggle butonu kontrolü
        toggle_rect = pygame.Rect(left_section_x + panel_width - 90, editor_y + 10, 75, 28)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Toggle butonu
            if toggle_rect.collidepoint(m_pos):
                self.organ_editor_mode = not self.organ_editor_mode
                self.selected_organ = None
                self.selected_organ_index = -1
                self.organ_param_inputs = {}  # Input'ları temizle
                return

            # Organ parametre input'ları
            if self.organ_editor_mode and self.organ_param_inputs:
                clicked_input = False
                for input_key, inp in self.organ_param_inputs.items():
                    if inp["rect"].collidepoint(m_pos):
                        inp["active"] = True
                        clicked_input = True
                    else:
                        # Başka yere tıklandıysa, aktif input'u kaydet
                        if inp["active"]:
                            inp["active"] = False
                            self.update_organ_param(inp["param"], inp["text"])
                if clicked_input:
                    return

            # Organ ekleme ve kaldırma butonları
            if self.organ_editor_mode:
                # Kaldır butonu - önce kontrol et
                if hasattr(self, 'remove_btn_rect') and self.remove_btn_rect and self.selected_organ:
                    if self.remove_btn_rect.collidepoint(m_pos):
                        self.remove_selected_organ()
                        self.organ_param_inputs = {}  # Input'ları temizle
                        return

                # Organ ekleme butonları
                if hasattr(self, 'add_organ_btns'):
                    for organ_type, btn_rect in self.add_organ_btns:
                        if btn_rect.collidepoint(m_pos):
                            # Organ türüne göre başlangıç açısı belirle
                            if organ_type == "Flagella":
                                start_angle = 180  # Arka
                            elif organ_type == "Photoreceptor":
                                start_angle = 0  # Ön
                            elif organ_type == "Chemoreceptor":
                                start_angle = 135  # Arka-yan
                            elif organ_type == "Mechanoreceptor":
                                start_angle = 45  # Ön-yan
                            elif organ_type == "Cilia":
                                start_angle = 90  # Yan
                            else:
                                start_angle = 0

                            # Başlangıç açısından başlayarak boş yer ara
                            added = False
                            for offset in range(0, 360, 10):
                                test_angle = (start_angle + offset) % 360
                                test_rad = math.radians(test_angle)
                                if self.add_organ_to_entity(organ_type, test_rad):
                                    added = True
                                    break
                            if not added:
                                # Daha ince adımlarla tekrar dene
                                for offset in range(0, 360, 5):
                                    test_angle = (start_angle + offset) % 360
                                    test_rad = math.radians(test_angle)
                                    if self.add_organ_to_entity(organ_type, test_rad):
                                        break
                            return

            # Preview alanında organ seçimi
            if self.organ_editor_mode and preview_rect.collidepoint(m_pos):
                organ_idx = self.get_organ_at_position(
                    m_pos[0], m_pos[1],
                    self.preview_center_x, self.preview_center_y
                )
                if organ_idx >= 0:
                    # Yeni organ seçildiğinde input'ları temizle
                    if organ_idx != self.selected_organ_index:
                        self.organ_param_inputs = {}
                    self.selected_organ_index = organ_idx
                    self.selected_organ = self.popup_entity.organs[organ_idx]
                    self.dragging_organ = True
                    self.drag_start_angle = self.selected_organ.attachment_angle
                else:
                    self.selected_organ = None
                    self.selected_organ_index = -1
                    self.organ_param_inputs = {}

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging_organ:
                self.dragging_organ = False
                self.organ_overlap_warning = False

        elif event.type == pygame.MOUSEMOTION:
            # Hover kontrolü
            if self.organ_editor_mode and preview_rect.collidepoint(m_pos) and not self.dragging_organ:
                self.hover_organ_index = self.get_organ_at_position(
                    m_pos[0], m_pos[1],
                    self.preview_center_x, self.preview_center_y
                )
            else:
                self.hover_organ_index = -1

            # Sürükleme
            if self.dragging_organ and self.selected_organ_index >= 0:
                # Yeni açıyı hesapla
                dx = m_pos[0] - self.preview_center_x
                dy = m_pos[1] - self.preview_center_y
                new_angle = math.atan2(dy, dx)

                # Örtüşme kontrolü
                overlap, _ = self.check_organ_overlap(self.selected_organ_index, new_angle)

                if not overlap:
                    # Pozisyonu güncelle
                    organ = self.popup_entity.organs[self.selected_organ_index]
                    organ.attachment_angle = new_angle
                    # Flagella ise thrust açısını da güncelle
                    if hasattr(organ, 'sync_thrust_to_attachment'):
                        organ.sync_thrust_to_attachment()
                    self.selected_organ = organ
                    self.organ_overlap_warning = False
                    self.popup_entity.recalculate_physics()
                else:
                    self.organ_overlap_warning = True

        # Klavye olayları (organ parametre input'ları için)
        elif event.type == pygame.KEYDOWN:
            if self.organ_editor_mode and self.organ_param_inputs:
                for input_key, inp in self.organ_param_inputs.items():
                    if inp["active"]:
                        if event.key == pygame.K_RETURN:
                            inp["active"] = False
                            self.update_organ_param(inp["param"], inp["text"])
                        elif event.key == pygame.K_BACKSPACE:
                            inp["text"] = inp["text"][:-1]
                        elif event.unicode in "0123456789.-":
                            inp["text"] += event.unicode
                        break

    def run(self):
        while True:
            self.screen.fill(BG_COLOR)
            m_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                if event.type == pygame.MOUSEWHEEL and self.state == "SETTINGS":
                    self.scroll_y = min(0, max(self.max_scroll, self.scroll_y + event.y * 30))
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "SETTINGS" and m_pos[0] > self.screen_width - 30: self.dragging_scroll = True
                    for i, tab in enumerate(self.tabs):
                        if pygame.Rect(0, 180 + i * 60, self.sidebar_width, 50).collidepoint(event.pos): self.set_state(tab)
                    if self.state == "DASHBOARD" and pygame.Rect(self.sidebar_width + 100, self.screen_height//2 - 40, 400, 80).collidepoint(event.pos):
                        # Organ konfigürasyonlarını kaydet
                        self.save_all_organ_configs()
                        pygame.quit(); run_simulation(); sys.exit()
                if event.type == pygame.MOUSEBUTTONUP: self.dragging_scroll = False
                if self.dragging_scroll and event.type == pygame.MOUSEMOTION:
                    self.scroll_y = ((max(0, min(self.screen_height-120, m_pos[1]-100))) / (self.screen_height-120)) * self.max_scroll
                
                if self.state == "SETTINGS":
                    for el in self.ui_elements: el.handle_event(event, self.scroll_y)
                elif self.state == "ENTITIES":
                    self.handle_entity_list_events(event, m_pos)
                    if self.entity_popup_open:
                        for _, ibox in self.entity_ui_elements: ibox.handle_event(event)
                        self.handle_organ_editor_events(event, m_pos)

            self.draw_sidebar()
            if self.state == "DASHBOARD": self.draw_dashboard()
            elif self.state == "SETTINGS": self.draw_settings()
            elif self.state == "ENTITIES": self.draw_entities()
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    ModernLauncher().run()
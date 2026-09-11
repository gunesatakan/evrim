"""Editor olaylari -> gecici settings.json -> yeni hucre: kayit regresyonlari.

Calistirma: python -m unittest discover -s tests -p test_editor_persistence.py
"""
import copy
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
import game_settings
from launcher import ModernLauncher
from entities.kaotropi import Kaotropi
from entities.notropi import Notropi
from entities.optropi import Optropi


class EditorPersistenceTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.enterContext(patch.object(game_settings, "SETTINGS_FILE",
                                      str(Path(folder.name) / "settings.json")))
        configs = copy.deepcopy(game_settings.DEFAULT_ENTITY_CONFIGS)
        for cfg in configs.values():
            cfg["organs"] = [
                {"type": "Membrane", "var_wall": False},
                {"type": "Cytoplasm", "size": cfg["cytoplasm"]},
                {"type": "Cytoskeleton"},
                {"type": "Ribosome"},
                {"type": "Vacuole", "size": 1.0},
                {"type": "Flagella", "angle": 3.141592653589793, "length": 10.0},
                {"type": "Chemoreceptor", "angle": 0.0, "length": 6.0},
            ]
        self.enterContext(patch.object(game_settings, "ENTITY_CONFIGS", configs))
        self.enterContext(patch.object(game_settings, "WORLD_SCALE", 1.0))
        game_settings.save_all()
        self.app = ModernLauncher()
        self.addCleanup(pygame.quit)
        self.app.set_state("ENTITIES")
        self.open_entity(self.app.dummy_optropis[0])

    def open_entity(self, entity):
        self.app.selected_entity = self.app.popup_entity = entity
        self.app.entity_popup_open = self.app.organ_editor_mode = True
        self.app.selected_organ = None
        self.app.selected_organ_index = -1
        self.app.selected_layer = None
        self.app.organ_param_inputs = {}
        self.app.create_entity_editor()
        self.app.draw_entity_popup()

    def select_organ(self, name):
        i, organ = next((i, o) for i, o in enumerate(self.app.popup_entity.organs)
                        if type(o).__name__ == name)
        self.app.selected_layer = None
        self.app.selected_organ_index = i
        self.app.selected_organ = organ
        self.app.organ_param_inputs = {}
        self.app.draw_entity_popup()
        return organ

    def type_param(self, param, text):
        inp = next(v for v in self.app.organ_param_inputs.values() if v["param"] == param)
        inp["active"] = True
        inp["text"] = text

    @staticmethod
    def click(pos):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)

    def close_popup(self):
        pos = self.app.popup_close_btn.center
        self.app.handle_entity_list_events(self.click(pos), pos)

    def reloaded(self, ent_id="optropi_0"):
        # Diskten oku; yalnizca editorun bellekte tuttugu nesneyi sinama.
        with patch.object(game_settings, "ENTITY_CONFIGS", game_settings.load()["entities"]):
            if ent_id == "kaotropi":
                return Kaotropi(0, 0, 0)
            if ent_id == "notropi":
                return Notropi(0, 0, 0)
            return Optropi(int(ent_id.rsplit("_", 1)[1]), 0, 0, (255, 0, 255))

    @staticmethod
    def organ(entity, name):
        return next(o for o in entity.organs if type(o).__name__ == name)

    def test_close_commits_last_typed_value_for_every_species(self):
        for entity in self.app.editable_entities():
            ent_id = self.app.entity_id(entity)
            with self.subTest(entity=ent_id):
                self.open_entity(entity)
                self.select_organ("Chemoreceptor")
                self.type_param("length", "12.5")
                self.close_popup()
                self.assertEqual(self.organ(self.reloaded(ent_id), "Chemoreceptor").logic.length, 12.5)

    def test_quit_commits_last_typed_value(self):
        self.select_organ("Flagella")
        self.type_param("length", "24")
        with patch("pygame.event.get", return_value=[pygame.event.Event(pygame.QUIT)]):
            with self.assertRaises(SystemExit):
                self.app.run()
        self.assertEqual(self.organ(self.reloaded(), "Flagella").logic.length, 24.0)

    def test_toggle_off_commits_last_typed_value(self):
        self.select_organ("Chemoreceptor")
        self.type_param("length", "14")
        pos = self.app.popup_toggle_rect.center
        self.app.handle_organ_editor_events(self.click(pos), pos)
        self.assertFalse(self.app.organ_editor_mode)
        self.assertEqual(self.organ(self.reloaded(), "Chemoreceptor").logic.length, 14.0)

    def test_enter_saves_without_closing_editor(self):
        self.select_organ("Chemoreceptor")
        self.type_param("length", "13")
        self.app.handle_organ_editor_events(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"), (0, 0))
        self.assertEqual(self.organ(self.reloaded(), "Chemoreceptor").logic.length, 13.0)

    def test_starting_gene_refresh_preserves_organs_and_selection(self):
        self.select_organ("Chemoreceptor")
        self.app.update_organ_param("length", "12")
        self.assertTrue(self.app.add_organ_to_entity("Toxin", angle=1.0))
        box = next(b for key, b in self.app.entity_ui_elements if key == "cytoplasm")
        box.text = "4.0"
        box.submit()
        self.assertEqual(self.app.popup_entity.body.logic.size, 4.0)
        self.assertTrue(any(type(o).__name__ == "Toxin" for o in self.app.popup_entity.organs))
        self.assertIs(self.app.selected_organ, self.organ(self.app.popup_entity, "Chemoreceptor"))
        self.app.update_organ_param("length", "15")
        self.close_popup()
        cell = self.reloaded()
        self.assertEqual(cell.body.logic.size, 4.0)
        self.assertEqual(self.organ(cell, "Chemoreceptor").logic.length, 15.0)

    def test_close_commits_starting_gene(self):
        box = next(b for key, b in self.app.entity_ui_elements if key == "cytoplasm")
        box.text, box.active = "4.5", True
        self.close_popup()
        self.assertEqual(self.reloaded().body.logic.size, 4.5)

    def test_layer_thickness_survives_close(self):
        self.app.popup_entity.membrane.logic.katman_ekle("wall")
        self.app.selected_layer = "wall"
        self.app.draw_entity_popup()
        self.type_param("kalinlik:wall", "8.5")
        self.close_popup()
        self.assertEqual(self.reloaded().membrane.logic.katman_kalinligi("wall"), 8.5)

    def test_added_and_removed_organs_are_saved_immediately(self):
        self.assertTrue(self.app.add_organ_to_entity("Toxin", angle=1.0))
        self.assertTrue(any(type(o).__name__ == "Toxin" for o in self.reloaded().organs))
        self.select_organ("Toxin")
        self.assertTrue(self.app.remove_selected_organ())
        self.assertFalse(any(type(o).__name__ == "Toxin" for o in self.reloaded().organs))

    def test_switching_tabs_commits_and_closes_popup(self):
        self.select_organ("Chemoreceptor")
        self.type_param("length", "16")
        self.app.set_state("SETTINGS")
        self.app.set_state("ENTITIES")
        self.assertFalse(self.app.entity_popup_open)
        self.assertEqual(self.organ(self.app.dummy_optropis[0], "Chemoreceptor").logic.length, 16.0)

    def test_same_tab_does_not_replace_edited_entity(self):
        entity = self.app.popup_entity
        self.app.set_state("ENTITIES")
        self.assertIs(self.app.dummy_optropis[0], entity)

    def test_drag_saves_position_on_mouse_release(self):
        self.select_organ("Chemoreceptor")
        self.app.dragging_organ = True
        pos = (self.app.preview_center_x + 100, self.app.preview_center_y + 60)
        self.app.handle_organ_editor_events(
            pygame.event.Event(pygame.MOUSEMOTION, pos=pos), pos)
        self.app.handle_organ_editor_events(
            pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos), pos)
        self.assertAlmostEqual(self.organ(self.reloaded(), "Chemoreceptor").attachment_angle,
                               math.atan2(60, 100))

    def test_weapon_settings_are_saved(self):
        self.assertTrue(self.app.add_organ_to_entity("Toxin", angle=1.0))
        self.select_organ("Toxin")
        values = {"power": 2.5, "carrier": 1, "payload": 2, "marker": 1}
        for param, value in values.items():
            self.app.update_organ_param(param, str(value))
        logic = self.organ(self.reloaded(), "Toxin").logic
        for param, value in values.items():
            self.assertEqual(getattr(logic, param), value)

    def test_layer_buttons_save_addition_and_removal(self):
        pos = next(r.center for kind, name, r in self.app.add_organ_btns
                   if kind == "katman" and name == "Duvar")
        self.app.handle_entity_editor_event(self.click(pos), pos)
        self.assertTrue(self.reloaded().membrane.logic.katman_var("wall"))
        self.app.draw_entity_popup()
        pos = self.app.katman_kaldir_rect.center
        self.app.handle_entity_editor_event(self.click(pos), pos)
        self.assertFalse(self.reloaded().membrane.logic.katman_var("wall"))

    def test_popup_click_does_not_activate_covered_sidebar(self):
        entity = self.app.popup_entity
        self.select_organ("Chemoreceptor")
        self.type_param("length", "11")
        # Bu nokta popup onizlemesinde, arkadaki HARITA sekmesinin ustunde.
        pos = (100, 320)
        with patch("pygame.mouse.get_pos", return_value=pos), patch(
                "pygame.event.get", side_effect=[[self.click(pos)],
                                                [pygame.event.Event(pygame.QUIT)]]):
            with self.assertRaises(SystemExit):
                self.app.run()
        self.assertEqual(self.app.state, "ENTITIES")
        self.assertIs(self.app.dummy_optropis[0], entity)
        self.assertEqual(self.organ(self.reloaded(), "Chemoreceptor").logic.length, 11.0)

    def test_switching_from_organ_input_to_gene_input_keeps_both(self):
        self.select_organ("Chemoreceptor")
        self.type_param("length", "18")
        box = next(b for key, b in self.app.entity_ui_elements if key == "cytoplasm")
        pos = box.rect.center
        self.app.handle_entity_editor_event(self.click(pos), pos)
        self.assertTrue(box.active)
        box.text = "4.0"
        self.app.handle_entity_editor_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"), pos)
        self.app.draw_entity_popup()
        cell = self.reloaded()
        self.assertEqual(cell.body.logic.size, 4.0)
        self.assertEqual(self.organ(cell, "Chemoreceptor").logic.length, 18.0)


if __name__ == "__main__":
    unittest.main()

import json
import os

# Default Global World/Evolution Settings
DEFAULT_SETTINGS = {
    "FOOD_COUNT": 1000,
    "KAOTROPI_COUNT": 8,
    "CILIA_SPEED_MULTI": 0.2,
    "FLAGELLA_SPEED_MULTI": 0.5,
    "DIGESTION_TIME": 10.0,
    "RIBOSOME_TIME": 10.0,
    "VACUOLE_ENERGY_MULTI": 1.5,
    "ENERGY_REGEN_BASE": 1.0,
    "CYTOSKELETON_AREA": 10.0,
    "FOOD_AREA": 50.0,

    "GROW_FLAGELLA": 3.0,
    "GROW_CILIA": 1.0,
    "GROW_DIGESTION": 0.5,
    "GROW_RIBOSOME": 0.5,
    "GROW_ENERGY_REGEN": 0.1,
    "GROW_MAX_ENERGY": 0.05,
    "GROW_VISION_RANGE": 5.0,
    "GROW_VISION_ANGLE": 2.0,
    "GROW_SMELL": 1.0,
    "GROW_SOUND": 2.0,
    "GROW_BODY": 0.01,
    "GROW_MEMORY": 5
}

# Added ribosome_area and vacuole_area to each entity
DEFAULT_ENTITY_CONFIGS = {
    "optropi_0": {"name": "Magenta", "cytoplasm": 1.0, "flagella": 10.0, "cilia": 3.0, "vision_range": 25.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 30.0, "ribosome_area": 20.0, "vacuole_area": 30.0},
    "optropi_1": {"name": "Yellow", "cytoplasm": 1.0, "flagella": 10.0, "cilia": 3.0, "vision_range": 25.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 30.0, "ribosome_area": 20.0, "vacuole_area": 30.0},
    "optropi_2": {"name": "Lime Green", "cytoplasm": 1.0, "flagella": 10.0, "cilia": 3.0, "vision_range": 25.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 30.0, "ribosome_area": 20.0, "vacuole_area": 30.0},
    "optropi_3": {"name": "Orange", "cytoplasm": 1.0, "flagella": 10.0, "cilia": 3.0, "vision_range": 25.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 30.0, "ribosome_area": 20.0, "vacuole_area": 30.0},
    "notropi":   {"name": "Hunter", "cytoplasm": 0.5, "flagella": 20.0, "cilia": 1.0, "vision_range": 15.0, "vision_angle": 10.0, "memory": 10, "smell": 5.0, "sound": 33.0, "ribosome_area": 15.0, "vacuole_area": 20.0}
}

SETTINGS_FILE = "settings.json"

def load():
    configs = {"settings": DEFAULT_SETTINGS, "entities": DEFAULT_ENTITY_CONFIGS}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                loaded = json.load(f)
                if "settings" in loaded: configs["settings"].update(loaded["settings"])
                if "entities" in loaded: 
                    for k, v in loaded["entities"].items():
                        if k in configs["entities"]: configs["entities"][k].update(v)
        except: pass
    return configs

def save_all():
    current_settings = {k: v for k, v in globals().items() if k.isupper() and k in DEFAULT_SETTINGS}
    to_save = {"settings": current_settings, "entities": ENTITY_CONFIGS}
    with open(SETTINGS_FILE, "w") as f:
        json.dump(to_save, f, indent=4)

def set_value(attr, val):
    globals()[attr] = val
    save_all()

def set_entity_value(ent_id, key, val):
    ENTITY_CONFIGS[ent_id][key] = val
    save_all()

def set_entity_organs(ent_id, organs_list):
    """
    Organ konfigürasyonunu kaydet.
    organs_list: [{"type": "Photoreceptor", "angle": 0.0, "params": {...}}, ...]
    """
    ENTITY_CONFIGS[ent_id]["organs"] = organs_list
    save_all()

def get_entity_organs(ent_id):
    """Organ konfigürasyonunu al. Yoksa None döner."""
    return ENTITY_CONFIGS.get(ent_id, {}).get("organs", None)

def clear_entity_organs(ent_id):
    """Organ konfigürasyonunu temizle (varsayılana dön)."""
    if ent_id in ENTITY_CONFIGS and "organs" in ENTITY_CONFIGS[ent_id]:
        del ENTITY_CONFIGS[ent_id]["organs"]
        save_all()

# Initialize
_data = load()
globals().update(_data["settings"])
ENTITY_CONFIGS = _data["entities"]

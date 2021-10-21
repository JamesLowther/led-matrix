import os
from dotenv import dotenv_values
import yaml

class Config:
    # Paths.
    SRC_BASE = os.path.dirname(__file__)
    FONTS = os.path.join(SRC_BASE, "assets", "fonts")
    STATE_PATH = os.path.join(SRC_BASE, "..", "state.yml")

    # Environment variables.
    ENV_VALUES = dotenv_values()

    VIRTUAL_MODE = False

    # Enable virtual mode even if running on Pi.
    VIRTUAL_MODE_OVERRIDE = False

    # Default state values.
    DEFAULTS = {
        "mode": "timed",
        "view": 0
    }

    def initialize_state():
        if not os.path.isfile(Config.STATE_PATH):
            open(Config.STATE_PATH, "a").close()
        
        os.chmod(Config.STATE_PATH, 0o664)

        yaml_s = Config.read_full()

        if yaml_s == None:
            yaml_s = dict()

        if not set(Config.DEFAULTS.keys()).issubset(set(yaml_s.keys())):
            for key in Config.DEFAULTS.keys():
                if not key in yaml_s.keys():
                    yaml_s[key] = Config.DEFAULTS[key]

            Config.update_full(yaml_s)

    def read_full():
        state = open(Config.STATE_PATH, "r")
        yaml_s = yaml.load(state, Loader=yaml.FullLoader)
        state.close()

        return yaml_s

    def read_key(key):
        yaml_s = Config.read_full()
        
        return yaml_s[key]

    def update_full(data):
        state = open(Config.STATE_PATH, "w")
        yaml.dump(data, state)
        state.close()

    def update_key(key, value):
        yaml_s = Config.read_full()
        yaml_s[key] = value
        Config.update_full(yaml_s)

        

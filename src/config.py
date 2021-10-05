import os
from dotenv import dotenv_values

# Paths.
SRC_BASE = os.path.dirname(__file__)
FONTS = os.path.join(SRC_BASE, "assets", "fonts")

# Environment variables.
ENV_VALUES = dotenv_values()
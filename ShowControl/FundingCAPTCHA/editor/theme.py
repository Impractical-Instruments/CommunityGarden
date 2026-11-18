"""The level editor's colours, window layout and fonts."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
DK_GREY    = ( 28,  28,  28)
MID_GREY   = ( 75,  75,  75)
LT_GREY    = (160, 160, 160)
GREEN      = (  0, 170,  60)
RED        = (180,  40,  40)
CYAN       = (  0, 200, 220)
YELLOW     = (220, 180,   0)
SIDEBAR_BG = ( 20,  20,  28)
FIELD_BG   = ( 38,  38,  52)
BTN_NRM    = ( 52,  52,  72)
BTN_HOV    = ( 78,  78, 108)
VALID_ON   = (  0, 200,  80)
VALID_HOV  = ( 60, 240, 120)
CELL_OFF   = ( 42,  42,  55)
CELL_HOV   = ( 62,  62,  80)
GRID_LINE  = ( 90,  90, 105)

W, H    = 1060, 700
SIDE_W  = 300
GRID_W  = W - SIDE_W


@dataclass
class Fonts:
    """The four fonts the editor draws with, named by point size."""
    f11: pygame.font.Font
    f12: pygame.font.Font
    f15: pygame.font.Font
    f20: pygame.font.Font

    @classmethod
    def load(cls) -> "Fonts":
        return cls(
            f11=pygame.font.SysFont("monospace", 11),
            f12=pygame.font.SysFont("monospace", 12),
            f15=pygame.font.SysFont("monospace", 15, bold=True),
            f20=pygame.font.SysFont("monospace", 20, bold=True),
        )

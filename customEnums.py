from enum import Enum

class TileState(Enum):
    NONE = 0,
    RED = 1,
    BLUE = 2,
    RED_PREVIEW = 3,
    BLUE_PREVIEW = 4,

class GameState(Enum):
    PLAYING = 0,
    REDWIN = 1,
    BLUEWIN = 2,
    DRAW = 3,
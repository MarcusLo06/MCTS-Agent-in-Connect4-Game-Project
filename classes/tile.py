import pygame
import random
from pygame.math import Vector2
from helpers.pixelTranslate import translateCoordinateToPixel
from helpers.assetsGetter import get_pixels_font, get_none_dot, get_blue_dot, get_red_dot, get_preview_blue_dot, get_preview_red_dot, get_winning_blue_dot, get_winning_red_dot
from helpers.customTextRender import render_text_with_outline
from customEnums import TileState

class Tile:
    def __init__(
            self, surface: pygame.Surface, coordinate: Vector2, 
            tileSize: Vector2 =  Vector2(50,50), outline: int = 0, color: TileState = TileState.NONE,
            topBarHeight: int = 0, footerHeight: int = 0
            ):
        self.surface = surface
        self.coordinate = coordinate
        self.tileSize = tileSize
        self.state = color
        self.hovering = False
        self.outline = outline
        self.isWinningTile = False
        self.topBarHeight = topBarHeight
        self.footerHeight = footerHeight
        self.ucb_score = None
        self.winrate = None

        self.ucbscoreFont = pygame.font.Font(get_pixels_font() , 16)

        self.rectStartPos = translateCoordinateToPixel(self.coordinate, tileSize)
        self.rectStartPos.y += self.topBarHeight
        self.rect = pygame.Rect(self.rectStartPos.x, self.rectStartPos.y, self.tileSize.x, self.tileSize.y)


        self.refresh_image()


    def clone(self) -> 'Tile':
        # 1. Create a new instance passing the shared surface and copied vectors
        new_tile = Tile(
            surface=self.surface,
            coordinate=Vector2(self.coordinate.x, self.coordinate.y),
            tileSize=Vector2(self.tileSize.x, self.tileSize.y),
            outline=self.outline,
            color=self.state,
            topBarHeight=self.topBarHeight,
            footerHeight=self.footerHeight
        )

        # 2. Copy dynamic boolean / state properties
        new_tile.hovering = self.hovering
        new_tile.isWinningTile = self.isWinningTile

        # 3. Explicitly copy the Pygame Rect and pixel position
        new_tile.rectStartPos = Vector2(self.rectStartPos.x, self.rectStartPos.y)
        new_tile.rect = self.rect.copy()

        return new_tile

    def update_preview(self, turn_color: TileState):
        if self.hovering:
            if turn_color == TileState.RED:
                self.set_image(get_preview_red_dot())
            elif turn_color == TileState.BLUE:
                self.set_image(get_preview_blue_dot())

    def refresh_image(self):
        if self.state == TileState.NONE:
            self.set_image(get_none_dot())
        elif self.state == TileState.BLUE:
            if self.isWinningTile:
                self.set_image(get_winning_blue_dot())
            else:
                self.set_image(get_blue_dot())

        elif self.state == TileState.RED:
            if self.isWinningTile:
                self.set_image(get_winning_red_dot())
            else:
                self.set_image(get_red_dot())

    def set_image(self, image_path: str):
        dot_image = pygame.image.load(image_path).convert_alpha()
        dot_image = pygame.transform.scale(dot_image, self.tileSize)
        self.image = dot_image


    def draw(self, debug: bool = False):
        self.surface.blit(self.image, self.rect)


    def draw_ucb_score(self, debug: bool = False):
        if not self.ucb_score: return
        if not self.winrate: return
        # if not self.isWinningTile: return
        if not debug: return

        ucb_label = render_text_with_outline(
            fontType=self.ucbscoreFont,
            text=f"{self.ucb_score:.2f}",
            color=(0,255,0)
        )

        ucbLabel_rect = ucb_label.get_rect(center = self.rectStartPos + (Vector2(self.tileSize) / 2) - Vector2(0,10))
        self.surface.blit(ucb_label, ucbLabel_rect)

        winrate_label = render_text_with_outline(
            fontType=self.ucbscoreFont,
            text=f"{self.winrate * 100:.1f}%",
            color=(0,255,0)
        )

        winrateLabel_rect = winrate_label.get_rect(center = self.rectStartPos + (Vector2(self.tileSize) / 2) + Vector2(0, 10))
        self.surface.blit(winrate_label, winrateLabel_rect)
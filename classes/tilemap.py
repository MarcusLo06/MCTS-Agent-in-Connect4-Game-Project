import pygame
from pygame import mixer
from pygame.math import Vector2
from .tile import Tile
from customEnums import TileState, GameState
from helpers.assetsGetter import get_click_sound

class TileMap:
    def __init__(self, surface: pygame.surface, rows: int = 10, columns: int = 10, topBarHeight: int = 0, footerHeight: int = 0, tileSize: Vector2 = Vector2(50, 50)):
        self.surface = surface
        self.tilesDictionary: dict[tuple[int,int], Tile] = {}
        self.rows = rows
        self.columns = columns
        self.topBarHeight = topBarHeight
        self.footerHeight = footerHeight
        self.tileSize = tileSize
        self.winningTiles = []
        self.selectedColumns = -1
        self.placed = 0
        self.turn = TileState.RED
        self.state = GameState.PLAYING


        self.click_sound = pygame.mixer.Sound(get_click_sound())
        self.click_sound.set_volume(0.7)


    def clone(self):
        # 1. Create a new instance sharing the surface and static dimensions
        new_map = TileMap(
            surface=self.surface,
            rows=self.rows,
            columns=self.columns,
            topBarHeight=self.topBarHeight,
            footerHeight=self.footerHeight,
            tileSize=Vector2(self.tileSize.x, self.tileSize.y)
        )

        # 2. Duplicate primitive attributes
        new_map.winningTiles = list(self.winningTiles)
        new_map.selectedColumns = self.selectedColumns
        new_map.placed = self.placed
        new_map.turn = self.turn
        new_map.state = self.state

        # 3. Deep-copy each Tile in the dictionary
        for pos, tile in self.tilesDictionary.items():
            # If your Tile class has a copy/clone method:
            new_map.tilesDictionary[pos] = tile.clone()
            
            # OR if Tile only holds simple data (like color/state):
            # new_map.tilesDictionary[pos] = Tile(pos, tile.color)

        return new_map

    def reset(self):
        """Resets the board state and tile grid to start a fresh game."""
        # 1. Reset game state and metrics
        self.winningTiles.clear()
        self.selectedColumns = -1
        self.placed = 0
        self.turn = TileState.BLUE
        self.state = GameState.PLAYING

        # 2. Reset every individual tile in the grid
        for tile in self.tilesDictionary.values():
            tile.state = TileState.NONE
            tile.hovering = False
            tile.isWinningTile = False
            if hasattr(tile, "refresh_image"):
                tile.refresh_image()

    

    def tileIsLegit(self, coordinate: Vector2) -> bool:
        coord = Vector2(coordinate)
        return (0 <= coord.x < self.columns and 0 <= coord.y < self.rows)


    def tileIsInMap(self, coordinate: Vector2) -> bool:
        return self.tileIsLegit(coordinate) and (tuple(coordinate) in self.tilesDictionary)

    def checkWinCondition(self, coordinate: Vector2) -> bool:
        coord_tuple = tuple(coordinate)
        
        # 1. Ensure the placed tile exists
        if not self.tileIsInMap(coordinate):
            return False
            
        target_color = self.tilesDictionary[tuple(coordinate)].state
        
        # Do not evaluate empty/unplaced spaces as wins
        if target_color == TileState.NONE:
            return False

        # 2. Define the 4 directions to check (dx, dy)
        directions = [
            (1, 0),   # Horizontal (-)
            (0, 1),   # Vertical (|)
            (1, 1),   # Diagonal Up-Right (/)
            (1, -1)   # Diagonal Down-Right (\)
        ]

        for dx, dy in directions:
            matching_tiles = [coord_tuple]

            # Check positive direction (+)
            for step in range(1, 4):
                neighbor = (coord_tuple[0] + dx * step, coord_tuple[1] + dy * step)
                if self.tileIsInMap(neighbor) and self.tilesDictionary[neighbor].state == target_color:
                    matching_tiles.append(neighbor)
                else:
                    break

            # Check negative direction (-)
            for step in range(1, 4):
                neighbor = (coord_tuple[0] - dx * step, coord_tuple[1] - dy * step)
                if neighbor in self.tilesDictionary and self.tilesDictionary[neighbor].state == target_color:
                    matching_tiles.append(neighbor)
                else:
                    break


            # 3. Check if 4 or more in a row exist in this line
            # print("debugg for", target_color.name, "matchs:", len(matching_tiles), "at", coordinate, matching_tiles)
            if len(matching_tiles) >= 4:
                self.winningTiles = matching_tiles  # Store the winning line coordinates
                return True

        return False

    def getLegalMove(self) -> list[tuple[int,int]]:
        moves = []
        for i in range(self.columns):
            placeable_row = self.columns_placeable_row(i)
            if placeable_row != -1:
                moves.append((i, placeable_row))

        return moves
    

    def initTile(self, 
            tileCoordinate: Vector2, tileColor: TileState = TileState.NONE, 
            outline: int = 0
        ) -> bool:
        if self.tileIsInMap(tileCoordinate):
            print("Tiles at", Vector2(tileCoordinate), "is in map")
            return False
        if not self.tileIsLegit(tileCoordinate):
            print("Tile out of bounds", Vector2(tileCoordinate))
            return False

        newTile = Tile(self.surface, Vector2(tileCoordinate), self.tileSize, outline, tileColor, self.topBarHeight, self.footerHeight)
        self.tilesDictionary[tuple(tileCoordinate)] = newTile
        return True


    def columns_placeable_row(self, col: int):
        for i in range(self.rows - 1, -1, -1):
            tile_state = self.tilesDictionary[(col, i)].state
            if (tile_state != TileState.RED) and (tile_state != TileState.BLUE):
                return i

        return -1

    def update_hovering(self, col: int, hovering: bool):
        col = int(col)
        
        # 1. Cleanup: turn off hovering on ALL tiles in this column
        if not hovering:
            for row in range(self.rows):
                tile = self.tilesDictionary.get((col, row))
                if tile and tile.hovering:
                    tile.hovering = False
                    tile.refresh_image()
            return

        # 2. Preview: calculate placeable row and apply hovering
        placeable_row = self.columns_placeable_row(col)
        
        # Check if column is full (columns_placeable_row returned -1 or invalid row)
        if placeable_row != -1 and (col, placeable_row) in self.tilesDictionary:
            preview_tile = self.tilesDictionary[(col, placeable_row)]
            preview_tile.hovering = True
            preview_tile.update_preview(self.turn)
            # print("tile", preview_tile.coordinate, preview_tile.hovering, preview_tile.color)


    def update_preview_column(self, coord: Vector2):
        # Clean up previous hovered column
        if self.selectedColumns != -1:
            self.update_hovering(self.selectedColumns, False)

        if not (0 <= coord[0] < self.columns):
            return

        col = int(coord[0])


        # Set new hovered column
        self.selectedColumns = col
        self.update_hovering(self.selectedColumns, True)




    def place_at_columns(self, coord: Vector2) -> bool:
        coord = tuple(coord)
        tileColor = self.turn

        if not self.tileIsLegit(coord): return

        col = int(coord[0])

        placable_row = self.columns_placeable_row(col)
        if placable_row != -1:
            self.tilesDictionary[(col, placable_row)].state = tileColor
            self.tilesDictionary[(col, placable_row)].refresh_image()
            self.placed += 1

            if self.checkWinCondition((col, placable_row)):
                if tileColor == TileState.BLUE:
                    self.state = GameState.BLUEWIN
                    # print("blue team win")
                elif tileColor == TileState.RED:
                    self.state = GameState.REDWIN
                    # print("red team win")
            else:
                if self.placed == self.rows * self.columns:
                    self.state = GameState.DRAW
                    # print("game draw")

            self.turn = TileState.RED if self.turn == TileState.BLUE else TileState.BLUE


            self.click_sound.play()
            return True

        return False



    def draw(self, debug: bool = False):
        for tile in self.tilesDictionary.values():
            if tile.coordinate in self.winningTiles:
                tile.isWinningTile = True
                tile.refresh_image()
            
            tile.draw(debug)
            tile.draw_ucb_score(debug)


        # if self.selectedColumns:
        #     self.selectedColumns.draw_highlight()

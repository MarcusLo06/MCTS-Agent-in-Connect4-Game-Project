import pygame
from pygame.math import Vector2

def translateCoordinateToPixel(coordinate: Vector2, tileSize: Vector2) -> Vector2:
    return Vector2(coordinate.x * tileSize.x, coordinate.y * tileSize.y)

def translatePixelToCoordinate(pos: Vector2, tileSize: Vector2) -> Vector2:
    vectorPos = Vector2(pos)
    return Vector2(vectorPos.x // tileSize.x, vectorPos.y // tileSize.y)
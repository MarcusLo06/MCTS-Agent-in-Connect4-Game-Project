import pygame

def render_text_with_outline(fontType, text: str, color: tuple, outline_color: tuple = (0,0,0), thickness: int = 1) -> pygame.Surface:
    """Helper method inside your Tile/Node class to draw text with an outline."""
    text_surface = fontType.render(text, True, color)
    
    # Create canvas large enough for text plus border offsets
    w = text_surface.get_width() + 2 * thickness
    h = text_surface.get_height() + 2 * thickness
    full_surface = pygame.Surface((w, h), pygame.SRCALPHA)
    
    # Render outline layer
    outline_surface = fontType.render(text, True, outline_color)
    
    # Stamp the outline around the center
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx != 0 or dy != 0:
                full_surface.blit(outline_surface, (dx + thickness, dy + thickness))
                
    # Stamp main text on top in the center
    full_surface.blit(text_surface, (thickness, thickness))
    
    return full_surface
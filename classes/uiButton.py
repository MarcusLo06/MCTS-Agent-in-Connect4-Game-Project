import pygame
from pygame.math import Vector2

class UIButton:
    def __init__(self, x, y, width, height, color, fontType: pygame.font, text="", text_color=(255, 255, 255), on_click=None, image_path: str = None):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.color = color
        self.text = text
        self.text_color = text_color
        self.on_click = on_click  # Store the function to run when clicked
        self.image_path = image_path
        
        # Setup basic font for the button text
        self.font = fontType

        self.refresh_image()

    def refresh_image(self):
        if self.image_path:
            profile_image = pygame.image.load(self.image_path).convert_alpha()
            profile_image = pygame.transform.scale(profile_image, self.rect.size)
            self.image = profile_image

    def draw(self, surface):


        if self.image_path:
            surface.blit(self.image, self.rect)

        else:
            # 1. Draw the button background rectangle
            pygame.draw.rect(surface, self.color, self.rect)
            
            # 2. Draw the text centered on the button
            if self.text:
                text_surf = self.font.render(self.text, True, self.text_color)
                text_rect = text_surf.get_rect(center=self.rect.center)
                surface.blit(text_surf, text_rect)

    async def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
            # Check if the mouse click was inside the button's rectangle
            if self.rect.collidepoint(event.pos):
                if self.on_click is not None:
                    await self.on_click()  # Trigger the callback function
        # elif (event.type == pygame.KEYDOWN and event.key == pygame.K_r):
        #       if self.on_click is not None:
        #             self.on_click()  # Trigger the callback function
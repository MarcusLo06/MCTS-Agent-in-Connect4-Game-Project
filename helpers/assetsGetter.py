import os, random
from customEnums import TileState

def get_random_image_in_folder(folder_path: str) -> str:
    # 1. Get a list of all files in the folder that end with .png
        png_files = [
            file for file in os.listdir(folder_path) if file.lower().endswith(".png")
        ]
    
        # 2. Check if any PNG files were found
        if not png_files:
            raise FileNotFoundError(f"No PNG files found in {folder_path}")
    
        # 3. Choose a random file name
        chosen_file = random.choice(png_files)
    
        # 4. Join the folder path and file name to create the full path
        return os.path.join(folder_path, chosen_file)


def get_pixels_font() -> str:
    return "assets/fonts/BoldPixels.ttf"

def get_none_dot() -> str:
    return "assets/connect4/empty_dot.png"

def get_blue_dot() -> str:
    return "assets/connect4/blue_dot.png"

def get_preview_blue_dot() -> str:
    return "assets/connect4/blur_blue_dot.png"

def get_red_dot() -> str:
    return "assets/connect4/red_dot.png"

def get_preview_red_dot() -> str:
    return "assets/connect4/blur_red_dot.png"

def get_winning_blue_dot() -> str:
    return "assets/connect4/winning_blue_dot.png"

def get_winning_red_dot() -> str:
    return "assets/connect4/winning_red_dot.png"


def get_profile_icon(color: TileState, isRobot: bool = False) -> str:
    if isRobot:
        if color == TileState.RED:
            return "assets/connect4/red_robot.png"
        elif color == TileState.BLUE:
            return "assets/connect4/blue_robot.png"
    else:
        if color == TileState.RED:
            return "assets/connect4/red_human.png"
        elif color == TileState.BLUE:
            return "assets/connect4/blue_human.png"

def get_click_sound() -> str:
    return "assets/connect4/click.ogg"
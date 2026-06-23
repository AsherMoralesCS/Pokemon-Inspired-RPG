import os

import pygame

from config import (
    ASSETS_SPRITES,
    ASSETS_UI,
    BASE_DIR,
    FIRE_COLOR,
    FONT_PATH,
    GRASS_COLOR,
    TILE_SIZE,
    WATER_COLOR,
)


def ensure_dirs():
    dirs = [
        os.path.join(BASE_DIR, "assets", "sprites", "player"),
        os.path.join(BASE_DIR, "assets", "sprites", "npcs"),
        os.path.join(BASE_DIR, "assets", "sprites", "pokemon"),
        os.path.join(BASE_DIR, "assets", "sprites", "tiles"),
        os.path.join(BASE_DIR, "assets", "ui"),
        os.path.join(BASE_DIR, "assets", "fonts"),
        os.path.join(BASE_DIR, "data"),
    ]
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)


def save_surface(surface, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(surface, path)


def generate_player_frames():
    directions = ["down", "up", "left", "right"]
    base_path = os.path.join(ASSETS_SPRITES, "player")
    for direction in directions:
        for frame in range(3):
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            body = (60, 120, 220)
            pygame.draw.rect(surface, body, (8, 8, 16, 20))
            pygame.draw.circle(surface, (255, 200, 160), (16, 10), 6)
            offset = frame - 1
            if direction == "down":
                pygame.draw.rect(surface, (40, 80, 180), (10 + offset, 26, 4, 6))
                pygame.draw.rect(surface, (40, 80, 180), (18 - offset, 26, 4, 6))
            elif direction == "up":
                pygame.draw.rect(surface, (40, 80, 180), (10, 26, 4, 6))
                pygame.draw.rect(surface, (40, 80, 180), (18, 26, 4, 6))
            elif direction == "left":
                pygame.draw.rect(surface, (40, 80, 180), (6, 22 + offset, 6, 4))
            else:
                pygame.draw.rect(surface, (40, 80, 180), (20, 22 + offset, 6, 4))
            save_surface(surface, os.path.join(base_path, direction + "_" + str(frame) + ".png"))


def generate_npcs():
    guide = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(guide, (100, 200, 100), (6, 6, 20, 24))
    pygame.draw.circle(guide, (255, 210, 170), (16, 10), 7)
    save_surface(guide, os.path.join(ASSETS_SPRITES, "npcs", "guide.png"))

    trainer = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(trainer, (200, 60, 60), (6, 6, 20, 24))
    pygame.draw.circle(trainer, (255, 210, 170), (16, 10), 7)
    save_surface(trainer, os.path.join(ASSETS_SPRITES, "npcs", "battle_trainer.png"))


def generate_pokemon_sprite(color, front=True):
    surface = pygame.Surface((96, 96), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, color, (10, 20, 76, 60))
    eye_x = 70 if front else 26
    pygame.draw.circle(surface, color, (eye_x, 30), 20)
    pygame.draw.circle(surface, (255, 255, 255), (eye_x + 4, 26), 6)
    pygame.draw.circle(surface, (0, 0, 0), (eye_x + 6, 26), 3)
    return surface


def generate_pokemon():
    types = [
        ("water", WATER_COLOR),
        ("grass", GRASS_COLOR),
        ("fire", FIRE_COLOR),
    ]
    for type_name, color in types:
        for stage in range(1, 4):
            shade = tuple(min(255, c + stage * 15) for c in color)
            front = generate_pokemon_sprite(shade, front=True)
            back = generate_pokemon_sprite(shade, front=False)
            save_surface(front, os.path.join(ASSETS_SPRITES, "pokemon", type_name + str(stage) + "_front.png"))
            save_surface(back, os.path.join(ASSETS_SPRITES, "pokemon", type_name + str(stage) + "_back.png"))


def generate_font():
    if os.path.exists(FONT_PATH):
        return
    pygame.font.init()
    font = pygame.font.SysFont("consolas", 16)
    surface = font.render("A", True, (255, 255, 255))
    os.makedirs(os.path.dirname(FONT_PATH), exist_ok=True)


def generate_all():
    pygame.init()
    ensure_dirs()
    generate_player_frames()
    generate_npcs()
    generate_pokemon()
    generate_font()
    print("Assets generated successfully.")


if __name__ == "__main__":
    generate_all()

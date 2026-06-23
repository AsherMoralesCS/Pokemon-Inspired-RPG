import os

import pygame

from config import (
    ASSETS_SPRITES,
    PLAYER_SPEED,
    TILE_SIZE,
)


class SpriteSheet:
    def __init__(self, surface):
        self.surface = surface


class AnimatedSprite:
    def __init__(self):
        self.frame_index = 0
        self.frame_timer = 0
        self.animation_speed = 10

    def update_animation(self, moving):
        if moving:
            self.frame_timer += 1
            if self.frame_timer >= self.animation_speed:
                self.frame_timer = 0
                self.frame_index = (self.frame_index + 1) % 3
        else:
            self.frame_index = 0
            self.frame_timer = 0


class PlayerSprite(AnimatedSprite):
    DIRECTIONS = ["down", "up", "left", "right"]

    def __init__(self, x, y):
        super().__init__()
        self.pixel_x = float(x)
        self.pixel_y = float(y)
        self.direction = 0
        self.moving = False
        self.frames = self.load_frames()
        self.rect = pygame.Rect(int(self.pixel_x), int(self.pixel_y), TILE_SIZE, TILE_SIZE)

    def load_frames(self):
        frames = {direction: [] for direction in self.DIRECTIONS}
        base_path = os.path.join(ASSETS_SPRITES, "player")
        for direction in self.DIRECTIONS:
            for frame_num in range(3):
                path = os.path.join(base_path, direction + "_" + str(frame_num) + ".png")
                if os.path.exists(path):
                    frames[direction].append(pygame.image.load(path).convert_alpha())
                else:
                    frames[direction].append(self.make_placeholder(direction, frame_num))
        return frames

    def make_placeholder(self, direction, frame_num):
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        body_color = (60, 120, 220)
        pygame.draw.rect(surface, body_color, (8, 8, 16, 20))
        pygame.draw.circle(surface, (255, 200, 160), (16, 10), 6)
        offset = frame_num - 1
        if direction == "down":
            pygame.draw.rect(surface, (40, 80, 180), (10 + offset, 26, 4, 6))
            pygame.draw.rect(surface, (40, 80, 180), (18 - offset, 26, 4, 6))
        elif direction == "up":
            pygame.draw.rect(surface, (40, 80, 180), (10, 26, 4, 6))
            pygame.draw.rect(surface, (40, 80, 180), (18, 26, 4, 6))
        elif direction == "left":
            pygame.draw.rect(surface, (40, 80, 180), (6, 22 + offset, 6, 4))
        elif direction == "right":
            pygame.draw.rect(surface, (40, 80, 180), (20, 22 + offset, 6, 4))
        return surface

    def set_tile_position(self, tile_x, tile_y):
        self.pixel_x = float(tile_x * TILE_SIZE)
        self.pixel_y = float(tile_y * TILE_SIZE)
        self.rect.x = int(self.pixel_x)
        self.rect.y = int(self.pixel_y)

    def get_tile_position(self):
        return int(self.pixel_x // TILE_SIZE), int(self.pixel_y // TILE_SIZE)

    def move(self, dx, dy, collision_check):
        self.moving = dx != 0 or dy != 0
        if dx < 0:
            self.direction = 2
        elif dx > 0:
            self.direction = 3
        elif dy < 0:
            self.direction = 1
        elif dy > 0:
            self.direction = 0

        new_x = self.pixel_x + dx * PLAYER_SPEED
        new_y = self.pixel_y + dy * PLAYER_SPEED

        test_rect = pygame.Rect(int(new_x), int(new_y), TILE_SIZE, TILE_SIZE)
        if collision_check(test_rect):
            self.pixel_x = new_x
            self.pixel_y = new_y
            self.rect.x = int(self.pixel_x)
            self.rect.y = int(self.pixel_y)
            return True
        return False

    def update(self):
        self.update_animation(self.moving)
        if not self.moving:
            return
        self.moving = False

    def draw(self, surface, camera_x, camera_y):
        direction_name = self.DIRECTIONS[self.direction]
        frame = self.frames[direction_name][self.frame_index]
        draw_x = int(self.pixel_x) - camera_x
        draw_y = int(self.pixel_y) - camera_y
        surface.blit(frame, (draw_x, draw_y))


class NPCSprite:
    def __init__(self, x, y, npc_type):
        self.tile_x = x
        self.tile_y = y
        self.npc_type = npc_type
        self.image = self.load_image()
        self.rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def load_image(self):
        filename = "guide.png" if self.npc_type == "guide" else "battle_trainer.png"
        path = os.path.join(ASSETS_SPRITES, "npcs", filename)
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
        return self.make_placeholder()

    def make_placeholder(self):
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        if self.npc_type == "guide":
            color = (100, 200, 100)
        else:
            color = (200, 60, 60)
        pygame.draw.rect(surface, color, (6, 6, 20, 24))
        pygame.draw.circle(surface, (255, 210, 170), (16, 10), 7)
        return surface

    def draw(self, surface, camera_x, camera_y):
        draw_x = self.tile_x * TILE_SIZE - camera_x
        draw_y = self.tile_y * TILE_SIZE - camera_y
        surface.blit(self.image, (draw_x, draw_y))


class PokemonBattleSprite:
    IDLE_BOB_AMOUNT = 3
    HIT_FLASH_FRAMES = 3
    FAINT_DURATION = 30

    def __init__(self, sprite_path, x, y, is_back=False):
        self.base_x = x
        self.base_y = y
        self.is_back = is_back
        self.image = self.load_image(sprite_path)
        self.idle_timer = 0
        self.bob_offset = 0
        self.hit_flash = 0
        self.fainting = False
        self.faint_timer = 0
        self.alpha = 255
        self.slide_offset = 0

    def load_image(self, sprite_path):
        if os.path.exists(sprite_path):
            return pygame.image.load(sprite_path).convert_alpha()
        return self.make_placeholder()

    def make_placeholder(self):
        surface = pygame.Surface((96, 96), pygame.SRCALPHA)
        color = (80, 140, 220) if self.is_back else (220, 80, 80)
        pygame.draw.ellipse(surface, color, (10, 20, 76, 60))
        pygame.draw.circle(surface, color, (70 if not self.is_back else 26, 30), 20)
        pygame.draw.circle(surface, WHITE, (74 if not self.is_back else 30, 26), 6)
        pygame.draw.circle(surface, BLACK, (76 if not self.is_back else 32, 26), 3)
        return surface

    def trigger_hit(self):
        self.hit_flash = self.HIT_FLASH_FRAMES

    def trigger_faint(self):
        self.fainting = True
        self.faint_timer = 0

    def update(self):
        if self.fainting:
            self.faint_timer += 1
            self.slide_offset = self.faint_timer * 2
            self.alpha = max(0, 255 - self.faint_timer * 8)
            return

        self.idle_timer += 1
        if self.idle_timer % 40 < 20:
            self.bob_offset = self.IDLE_BOB_AMOUNT
        else:
            self.bob_offset = 0

        if self.hit_flash > 0:
            self.hit_flash -= 1

    def draw(self, surface):
        if self.fainting and self.alpha <= 0:
            return

        draw_x = self.base_x
        draw_y = self.base_y + self.bob_offset + self.slide_offset

        image = self.image.copy()
        if self.hit_flash > 0 and self.hit_flash % 2 == 1:
            red_overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
            red_overlay.fill((255, 0, 0, 120))
            image.blit(red_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        if self.fainting:
            image.set_alpha(self.alpha)

        surface.blit(image, (draw_x, draw_y))

    def is_faint_done(self):
        return self.fainting and self.alpha <= 0


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

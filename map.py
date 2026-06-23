import pygame

from config import (
    IMPASSABLE_TILES,
    TILE_COLORS,
    TILE_GRASS_SHORT,
    TILE_GRASS_TALL,
    TILE_GRASS_ELITE,
    TILE_SIZE,
)
from map_data import ISLAND_MAP, MAP_HEIGHT, MAP_WIDTH


class GameMap:
    def __init__(self):
        self.grid = ISLAND_MAP
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.tile_surfaces = self.build_tile_surfaces()

    def build_tile_surfaces(self):
        surfaces = {}
        for tile_id, color in TILE_COLORS.items():
            surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surface.fill(color)
            if tile_id == TILE_GRASS_SHORT:
                pygame.draw.line(surface, (80, 160, 60), (4, 20), (28, 8), 1)
                pygame.draw.line(surface, (80, 160, 60), (10, 28), (26, 16), 1)
            elif tile_id == TILE_GRASS_TALL:
                for gx in range(4, 28, 6):
                    pygame.draw.line(surface, (40, 100, 30), (gx, 28), (gx + 2, 10), 2)
            elif tile_id == TILE_GRASS_ELITE:
                for gx in range(2, 28, 5):
                    pygame.draw.line(surface, (20, 70, 25), (gx, 28), (gx + 1, 8), 3)
                    pygame.draw.line(surface, (15, 55, 20), (gx + 2, 26), (gx + 3, 12), 2)
            elif tile_id == 1:
                pygame.draw.circle(surface, (200, 180, 120), (10, 10), 2)
                pygame.draw.circle(surface, (200, 180, 120), (22, 20), 2)
            surfaces[tile_id] = surface
        return surfaces

    def get_tile(self, tile_x, tile_y):
        if tile_x < 0 or tile_y < 0 or tile_x >= self.width or tile_y >= self.height:
            return 0
        return self.grid[tile_y][tile_x]

    def is_passable(self, tile_x, tile_y):
        tile = self.get_tile(tile_x, tile_y)
        return tile not in IMPASSABLE_TILES

    def is_grass(self, tile_x, tile_y):
        tile = self.get_tile(tile_x, tile_y)
        return tile in (TILE_GRASS_SHORT, TILE_GRASS_TALL, TILE_GRASS_ELITE)

    def is_tall_grass(self, tile_x, tile_y):
        return self.get_tile(tile_x, tile_y) == TILE_GRASS_TALL

    def is_elite_grass(self, tile_x, tile_y):
        return self.get_tile(tile_x, tile_y) == TILE_GRASS_ELITE

    def rect_collides(self, rect, npc_rects):
        corners = [
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        ]
        for px, py in corners:
            tile_x = px // TILE_SIZE
            tile_y = py // TILE_SIZE
            if not self.is_passable(tile_x, tile_y):
                return True
        for npc_rect in npc_rects:
            if rect.colliderect(npc_rect):
                return True
        return False

    def draw(self, surface, camera_x, camera_y, screen_width, screen_height):
        start_x = max(0, camera_x // TILE_SIZE)
        start_y = max(0, camera_y // TILE_SIZE)
        end_x = min(self.width, start_x + screen_width // TILE_SIZE + 2)
        end_y = min(self.height, start_y + screen_height // TILE_SIZE + 2)

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_id = self.grid[y][x]
                tile_surface = self.tile_surfaces.get(tile_id, self.tile_surfaces[0])
                draw_x = x * TILE_SIZE - camera_x
                draw_y = y * TILE_SIZE - camera_y
                surface.blit(tile_surface, (draw_x, draw_y))

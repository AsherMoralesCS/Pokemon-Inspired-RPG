from map_data import GUIDE_NPC_POS, BATTLE_NPC_POS


class GuideNPC:
    TUTORIAL_DIALOGUE = [
        "Welcome to Starfall Island!",
        "I'm here to help you get started on your journey.",
        "Walk through grass patches to encounter wild Pokemon and gain EXP.",
        "The small patch has weaker foes. The large patch is tougher.",
        "The dark elite brush to the northeast holds the strongest wild Pokemon.",
        "Type matchups matter! Water beats Fire, Fire beats Grass, Grass beats Water.",
        "Train in the elite area, then challenge the Island Champion there.",
        "Defeat all three of their Pokemon to win!",
        "Controls: Arrows to move, SPACE to interact, P to view Pokemon.",
    ]

    HEAL_DIALOGUE = ["Your Pokemon have been fully healed!"]

    GREETING_DIALOGUE = ["Your Pokemon look healthy. Good luck out there!"]

    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.name = "Guide"

    def get_interaction_dialogue(self, tutorial_completed, needs_healing):
        if not tutorial_completed:
            return list(self.TUTORIAL_DIALOGUE)
        if needs_healing:
            return list(self.HEAL_DIALOGUE)
        return list(self.GREETING_DIALOGUE)

    def get_rect(self, tile_size):
        import pygame
        return pygame.Rect(
            self.tile_x * tile_size,
            self.tile_y * tile_size,
            tile_size,
            tile_size,
        )

    def is_adjacent_to(self, player_tile_x, player_tile_y):
        dx = abs(self.tile_x - player_tile_x)
        dy = abs(self.tile_y - player_tile_y)
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)


class BattleNPC:
    TRAINER_NAME = "Island Champion"
    TEAM = [
        ("water_stage3", 32),
        ("grass_stage3", 33),
        ("fire_stage3", 35),
    ]

    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.name = self.TRAINER_NAME
        self.defeated = False

    def get_team(self):
        return list(self.TEAM)

    def get_rect(self, tile_size):
        import pygame
        return pygame.Rect(
            self.tile_x * tile_size,
            self.tile_y * tile_size,
            tile_size,
            tile_size,
        )

    def is_adjacent_to(self, player_tile_x, player_tile_y):
        dx = abs(self.tile_x - player_tile_x)
        dy = abs(self.tile_y - player_tile_y)
        return (dx == 1 and dy == 0) or (dx == 0 and dy == 1)


class NPCManager:
    def __init__(self):
        self.guide = GuideNPC(GUIDE_NPC_POS[0], GUIDE_NPC_POS[1])
        self.battle_npc = BattleNPC(BATTLE_NPC_POS[0], BATTLE_NPC_POS[1])

    def get_all_npcs(self):
        return [self.guide, self.battle_npc]

    def get_npc_rects(self, tile_size):
        return [npc.get_rect(tile_size) for npc in self.get_all_npcs()]

    def check_interaction(self, player_tile_x, player_tile_y):
        if self.guide.is_adjacent_to(player_tile_x, player_tile_y):
            return "guide", self.guide
        if not self.battle_npc.defeated and self.battle_npc.is_adjacent_to(
            player_tile_x, player_tile_y
        ):
            return "battle", self.battle_npc
        return None, None

    def party_needs_healing(self, party):
        for pokemon in party:
            if pokemon.hp_current < pokemon.max_hp or pokemon.is_fainted():
                return True
        return False

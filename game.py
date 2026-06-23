import random

import pygame

from battle import BattleScene
from config import (
    HIGH_GRASS_ENCOUNTER_RATE,
    HIGH_GRASS_LEVEL_RANGE,
    LARGE_GRASS_ENCOUNTER_RATE,
    LARGE_GRASS_LEVEL_RANGE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SMALL_GRASS_ENCOUNTER_RATE,
    SMALL_GRASS_LEVEL_RANGE,
    TILE_SIZE,
    WHITE,
)
from moves import MoveLookup
from map import GameMap
from map_data import PLAYER_START_POS, RESPAWN_POS
from npc import NPCManager
from pokemon import Pokemon
from sprites import NPCSprite, PlayerSprite
from ui import DialogueBox, get_font, PokemonStatusScreen, StarterSelectScreen
from pokemon import (
    create_starter_pokemon,
    create_wild_pokemon,
    pokemon_from_save_dict,
)


WILD_SPECIES = ["water_stage1", "grass_stage1", "fire_stage1"]
WILD_SPECIES_HIGH = ["water_stage3", "grass_stage3", "fire_stage3"]


class Game:
    STATE_OVERWORLD = "overworld"
    STATE_DIALOGUE = "dialogue"
    STATE_BATTLE = "battle"
    STATE_STARTER = "starter"
    STATE_VICTORY = "victory"
    STATE_POKEMON = "pokemon"
    STATE_SAVE_EXIT = "save_exit"

    def __init__(self, screen, username, player_data, db_manager):
        self.screen = screen
        self.username = username
        self.player_data = player_data
        self.db = db_manager
        self.state = self.STATE_OVERWORLD

        self.game_map = GameMap()
        self.npc_manager = NPCManager()
        self.dialogue_box = DialogueBox()
        self.starter_screen = StarterSelectScreen()
        self.pokemon_status = PokemonStatusScreen()
        self.move_lookup = MoveLookup()
        self.font = get_font(28)

        pos = player_data.get("position", {"x": PLAYER_START_POS[0], "y": PLAYER_START_POS[1]})
        self.player_sprite = PlayerSprite(pos["x"] * TILE_SIZE, pos["y"] * TILE_SIZE)
        self.npc_sprites = [
            NPCSprite(self.npc_manager.guide.tile_x, self.npc_manager.guide.tile_y, "guide"),
            NPCSprite(
                self.npc_manager.battle_npc.tile_x,
                self.npc_manager.battle_npc.tile_y,
                "battle",
            ),
        ]

        self.party = []
        self.load_party()

        if self.npc_manager.battle_npc.defeated is False:
            self.npc_manager.battle_npc.defeated = player_data.get("battle_npc_defeated", False)

        self.guide_tutorial_completed = player_data.get("guide_tutorial_completed", False)

        self.battle_scene = None
        self.pending_battle = None
        self.steps_since_encounter = 0
        self.show_starter_if_needed()

        self.victory_timer = 0
        self.return_to_login = False
        self.game_completed = player_data.get("game_completed", False)
        self.save_exit_timer = 0
        self.save_exit_message = ""
        self.save_exit_saved = False

    def load_party(self):
        self.party = []
        for member in self.player_data.get("party", []):
            self.party.append(pokemon_from_save_dict(member))

    def show_starter_if_needed(self):
        if not self.party:
            self.state = self.STATE_STARTER

    def get_active_pokemon(self):
        if self.party:
            return self.party[0]
        return None

    def heal_party(self):
        for pokemon in self.party:
            pokemon.heal_full()

    def open_pokemon_menu(self):
        pokemon = self.get_active_pokemon()
        if pokemon is None:
            return
        self.pokemon_status.show(pokemon, self.move_lookup)
        self.state = self.STATE_POKEMON

    def close_pokemon_menu(self):
        self.pokemon_status.hide()
        self.state = self.STATE_OVERWORLD

    def respawn_at_guide(self):
        self.player_sprite.set_tile_position(RESPAWN_POS[0], RESPAWN_POS[1])

    def start_save_and_exit(self):
        self.state = self.STATE_SAVE_EXIT
        self.save_exit_timer = 90
        self.save_exit_message = "Saving..."
        self.save_exit_saved = False

    def update_save_exit(self):
        self.save_exit_timer -= 1
        if not self.save_exit_saved and self.save_exit_timer <= 60:
            self.save_player_data()
            self.save_exit_saved = True
            self.save_exit_message = "Game Saved"
        if self.save_exit_timer <= 0:
            self.return_to_login = True

    def save_player_data(self):
        pos_x, pos_y = self.player_sprite.get_tile_position()
        data = {
            "party": [p.to_save_dict() for p in self.party],
            "position": {"x": pos_x, "y": pos_y},
            "game_completed": self.game_completed,
            "battle_npc_defeated": self.npc_manager.battle_npc.defeated,
            "guide_tutorial_completed": self.guide_tutorial_completed,
        }
        account = self.db.get_account(self.username)
        if account:
            account.update(data)
            self.db.save()

    def get_camera(self):
        cam_x = self.player_sprite.pixel_x - SCREEN_WIDTH // 2 + TILE_SIZE // 2
        cam_y = self.player_sprite.pixel_y - SCREEN_HEIGHT // 2 + TILE_SIZE // 2
        max_cam_x = self.game_map.width * TILE_SIZE - SCREEN_WIDTH
        max_cam_y = self.game_map.height * TILE_SIZE - SCREEN_HEIGHT
        cam_x = max(0, min(cam_x, max_cam_x))
        cam_y = max(0, min(cam_y, max_cam_y))
        return int(cam_x), int(cam_y)

    def collision_check(self, rect):
        npc_rects = self.npc_manager.get_npc_rects(TILE_SIZE)
        return not self.game_map.rect_collides(rect, npc_rects)

    def handle_event(self, event):
        if self.state == self.STATE_SAVE_EXIT:
            return

        if self.state == self.STATE_STARTER:
            if self.starter_screen.handle_event(event):
                chosen = self.starter_screen.chosen_id
                starter = create_starter_pokemon(chosen)
                self.party = [starter]
                self.save_player_data()
                self.state = self.STATE_OVERWORLD
            return

        if self.state == self.STATE_BATTLE and self.battle_scene:
            self.battle_scene.handle_event(event)
            if self.battle_scene.is_done():
                self.on_battle_end()
            return

        if self.state == self.STATE_VICTORY:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.return_to_login = True
            return

        if self.state == self.STATE_POKEMON:
            self.pokemon_status.handle_event(event)
            if not self.pokemon_status.is_visible():
                self.state = self.STATE_OVERWORLD
            return

        if self.dialogue_box.visible:
            self.dialogue_box.handle_event(event)
            if not self.dialogue_box.visible:
                self.state = self.STATE_OVERWORLD
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.open_pokemon_menu()
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z):
                self.try_interact()
            elif event.key == pygame.K_ESCAPE:
                self.start_save_and_exit()

    def try_interact(self):
        tile_x, tile_y = self.player_sprite.get_tile_position()
        interaction_type, npc = self.npc_manager.check_interaction(tile_x, tile_y)
        if interaction_type == "guide":
            needs_healing = self.npc_manager.party_needs_healing(self.party)
            if needs_healing:
                self.heal_party()
            if not self.guide_tutorial_completed:
                dialogue_lines = npc.get_interaction_dialogue(False, needs_healing)
                self.guide_tutorial_completed = True
            else:
                dialogue_lines = npc.get_interaction_dialogue(True, needs_healing)
            self.dialogue_box.show(npc.name, dialogue_lines)
            self.save_player_data()
            self.state = self.STATE_DIALOGUE
        elif interaction_type == "battle":
            self.start_trainer_battle(npc)

    def start_trainer_battle(self, npc):
        team = []
        for species_id, level in npc.get_team():
            pokemon = create_wild_pokemon(species_id, level)
            team.append(pokemon)
        player_pokemon = self.get_active_pokemon()
        if player_pokemon is None:
            return
        battle_pokemon = pokemon_from_save_dict(player_pokemon.to_save_dict())
        battle_pokemon.reset_battle_stages()
        self.battle_scene = BattleScene(
            self.screen,
            battle_pokemon,
            team,
            battle_type="trainer",
            trainer_name=npc.name,
        )
        self.state = self.STATE_BATTLE

    def start_wild_battle(self, level_range, species_pool=None):
        pool = species_pool or WILD_SPECIES
        species_id = random.choice(pool)
        level = random.randint(level_range[0], level_range[1])
        wild = create_wild_pokemon(species_id, level)
        player_pokemon = self.get_active_pokemon()
        if player_pokemon is None:
            return
        battle_pokemon = pokemon_from_save_dict(player_pokemon.to_save_dict())
        battle_pokemon.reset_battle_stages()
        self.battle_scene = BattleScene(
            self.screen,
            battle_pokemon,
            [wild],
            battle_type="wild",
        )
        self.state = self.STATE_BATTLE

    def check_grass_encounter(self, moved):
        if not moved:
            return
        tile_x, tile_y = self.player_sprite.get_tile_position()
        if not self.game_map.is_grass(tile_x, tile_y):
            return

        if self.game_map.is_elite_grass(tile_x, tile_y):
            rate = HIGH_GRASS_ENCOUNTER_RATE
            level_range = HIGH_GRASS_LEVEL_RANGE
            species_pool = WILD_SPECIES_HIGH
        elif self.game_map.is_tall_grass(tile_x, tile_y):
            rate = LARGE_GRASS_ENCOUNTER_RATE
            level_range = LARGE_GRASS_LEVEL_RANGE
            species_pool = WILD_SPECIES
        else:
            rate = SMALL_GRASS_ENCOUNTER_RATE
            level_range = SMALL_GRASS_LEVEL_RANGE
            species_pool = WILD_SPECIES

        if random.random() < rate:
            self.start_wild_battle(level_range, species_pool)

    def on_battle_end(self):
        result_data = self.battle_scene.get_result()
        result = result_data["result"]

        if result == "defeat":
            player_pokemon = result_data["player_pokemon"]
            player_pokemon.reset_battle_stages()
            player_pokemon.heal_full()
            self.party[0] = player_pokemon
            self.respawn_at_guide()
            self.save_player_data()
            self.dialogue_box.show(
                "Guide",
                ["You rushed back safely. Your Pokemon have been fully healed!"],
            )
            self.state = self.STATE_DIALOGUE
            self.battle_scene = None
            return

        if result == "victory":
            player_pokemon = result_data["player_pokemon"]
            player_pokemon.reset_battle_stages()
            self.party[0] = player_pokemon
            if result_data.get("game_completed"):
                self.game_completed = True
                self.npc_manager.battle_npc.defeated = True
                self.save_player_data()
                self.state = self.STATE_VICTORY
            else:
                self.save_player_data()

        self.battle_scene = None
        self.state = self.STATE_OVERWORLD

    def update(self):
        if self.state == self.STATE_SAVE_EXIT:
            self.update_save_exit()
            return

        if self.state == self.STATE_BATTLE and self.battle_scene:
            self.battle_scene.update()
            return

        if self.state == self.STATE_VICTORY:
            self.victory_timer += 1
            return

        if self.state == self.STATE_POKEMON:
            return

        if self.state != self.STATE_OVERWORLD:
            return

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1

        moved = False
        if dx != 0 or dy != 0:
            moved = self.player_sprite.move(dx, dy, self.collision_check)
            if moved:
                self.check_grass_encounter(True)

        self.player_sprite.update()

    def draw(self):
        if self.state == self.STATE_STARTER:
            self.starter_screen.draw(self.screen)
            return

        if self.state == self.STATE_BATTLE and self.battle_scene:
            self.battle_scene.draw()
            return

        if self.state == self.STATE_VICTORY:
            self.screen.fill((20, 40, 20))
            title = self.font.render("YOU WIN!", True, WHITE)
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 260))
            hint_font = get_font(18)
            hint = hint_font.render(
                "You are the Island Champion! Press ENTER to return to login.",
                True,
                WHITE,
            )
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 320))
            return

        cam_x, cam_y = self.get_camera()
        self.game_map.draw(self.screen, cam_x, cam_y, SCREEN_WIDTH, SCREEN_HEIGHT)
        for npc_sprite in self.npc_sprites:
            npc_sprite.draw(self.screen, cam_x, cam_y)
        self.player_sprite.draw(self.screen, cam_x, cam_y)
        self.dialogue_box.draw(self.screen)
        self.pokemon_status.draw(self.screen)

        hint_font = get_font(14)
        controls = hint_font.render(
            "Arrows: Move | SPACE: Interact | P: Pokemon | ESC: Save & Exit",
            True,
            WHITE,
        )
        self.screen.blit(controls, (10, 10))

        if self.state == self.STATE_SAVE_EXIT:
            self.draw_save_exit_overlay()

    def draw_save_exit_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))
        message_font = get_font(32)
        text = message_font.render(self.save_exit_message, True, WHITE)
        self.screen.blit(
            text,
            (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 16),
        )

    def should_return_to_login(self):
        return self.return_to_login

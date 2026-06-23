import os
import random

import pygame

from calc import DamageCalculator
from config import (
    BATTLE_BG,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from evolution import EvolutionHandler
from moves import MoveLookup
from sprites import PokemonBattleSprite
from ui import BattleMenu, get_font, HPBar, MessageLog, XPBar


class BattleAI:
    def __init__(self, move_lookup):
        self.move_lookup = move_lookup

    def choose_move(self, pokemon):
        move_ids = pokemon.get_moves()
        typed_move = self.move_lookup.get_typed_move_for_type(pokemon.get_pokemon_type())
        weights = []
        for move_id in move_ids:
            if move_id == typed_move:
                weights.append(3)
            else:
                weights.append(1)
        return random.choices(move_ids, weights=weights, k=1)[0]


class BattleScene:
    STATE_INTRO = "intro"
    STATE_MENU = "menu"
    STATE_ACTION = "action"
    STATE_MESSAGE = "message"
    STATE_FAINT = "faint"
    STATE_EXP = "exp"
    STATE_EVOLVE = "evolve"
    STATE_SWITCH = "switch"
    STATE_VICTORY = "victory"
    STATE_DEFEAT = "defeat"
    STATE_DONE = "done"

    def __init__(self, screen, player_pokemon, enemy_team, battle_type="wild", trainer_name=""):
        self.screen = screen
        self.player_pokemon = player_pokemon
        self.enemy_team = list(enemy_team)
        self.enemy_index = 0
        self.enemy_pokemon = self.enemy_team[self.enemy_index]
        self.battle_type = battle_type
        self.trainer_name = trainer_name

        self.calculator = DamageCalculator()
        self.move_lookup = MoveLookup()
        self.ai = BattleAI(self.move_lookup)
        self.evolution_handler = EvolutionHandler()

        self.state = self.STATE_INTRO
        self.message_queue = []
        self.pending_messages = []
        self.result = None
        self.leveled_up = False
        self.evolved_pokemon = None
        self.evolution_flash = 0
        self.game_completed = False
        self.next_state_after_messages = None

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.player_sprite = PokemonBattleSprite(
            self.player_pokemon.get_sprite_back_path(), 80, 320, is_back=True
        )
        self.enemy_sprite = PokemonBattleSprite(
            self.enemy_pokemon.get_sprite_front_path(), 580, 80, is_back=False
        )

        self.player_hp_bar = HPBar(80, 520, 200, 18)
        self.enemy_hp_bar = HPBar(580, 160, 200, 18)
        self.player_xp_bar = XPBar(80, 542, 200, 8)
        self.message_log = MessageLog(20, 580, SCREEN_WIDTH - 40)
        self.battle_menu = BattleMenu(520, 400, 420, 160)
        self.font = get_font(18)
        self.big_font = get_font(24)

        self._sync_bars()
        self._setup_intro_messages()

    def _setup_intro_messages(self):
        if self.battle_type == "trainer":
            self.message_queue = [
                self.trainer_name + " wants to battle!",
                "Go! " + self.player_pokemon.get_name() + "!",
                self.trainer_name + " sent out " + self.enemy_pokemon.get_name() + "!",
            ]
        else:
            self.message_queue = [
                "A wild " + self.enemy_pokemon.get_name() + " appeared!",
            ]
        self.state = self.STATE_MESSAGE

    def _sync_bars(self):
        self.player_hp_bar.set_hp(self.player_pokemon.hp_current, self.player_pokemon.max_hp)
        self.enemy_hp_bar.set_hp(self.enemy_pokemon.hp_current, self.enemy_pokemon.max_hp)
        self.player_xp_bar.set_progress(
            self.player_pokemon.get_exp_in_level(),
            self.player_pokemon.get_exp_to_next(),
        )

    def _reload_enemy_sprite(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.enemy_sprite = PokemonBattleSprite(
            self.enemy_pokemon.get_sprite_front_path(), 580, 80, is_back=False
        )

    def handle_event(self, event):
        if self.state == self.STATE_MENU:
            choice = self.battle_menu.handle_event(event)
            if choice and choice != "navigate":
                self.battle_menu.hide()
                self.execute_turn(choice)
        elif self.state == self.STATE_MESSAGE:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                    self.advance_message()
        elif self.state == self.STATE_DEFEAT:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                    self.state = self.STATE_DONE
                    self.result = "defeat"

    def advance_message(self):
        if self.message_queue:
            msg = self.message_queue.pop(0)
            self.message_log.set_message(msg)
            return

        if self.next_state_after_messages == self.STATE_EXP:
            self.next_state_after_messages = None
            self.award_exp()
            return
        if self.next_state_after_messages == self.STATE_VICTORY:
            self.next_state_after_messages = None
            self.state = self.STATE_VICTORY
            if self.message_log.message:
                pass
            self.finish_victory()
            return
        if self.next_state_after_messages == self.STATE_MENU:
            self.next_state_after_messages = None
            self._show_battle_menu()
            return
        if self.next_state_after_messages == "done":
            self.next_state_after_messages = None
            self.state = self.STATE_DONE
            self.result = "victory"
            return

        self.state = self.STATE_MENU
        self._show_battle_menu()

    def _show_battle_menu(self):
        self.move_lookup.validate_pokemon_moves(self.player_pokemon)
        self.battle_menu.set_moves(
            self.move_lookup.get_pokemon_moves(self.player_pokemon),
            self.move_lookup,
        )

    def execute_turn(self, player_move_id):
        if player_move_id not in self.player_pokemon.get_moves():
            return
        self.state = self.STATE_ACTION
        player_move = self.move_lookup.get_move(player_move_id)
        enemy_move_id = self.ai.choose_move(self.enemy_pokemon)
        enemy_move = self.move_lookup.get_move(enemy_move_id)

        player_first = self.determine_turn_order()
        actions = []
        if player_first:
            actions.append(("player", player_move_id, player_move))
            actions.append(("enemy", enemy_move_id, enemy_move))
        else:
            actions.append(("enemy", enemy_move_id, enemy_move))
            actions.append(("player", player_move_id, player_move))

        self.message_queue = []
        for actor, move_id, move in actions:
            if self.player_pokemon.is_fainted() or self.enemy_pokemon.is_fainted():
                break
            actor_pokemon = self.player_pokemon if actor == "player" else self.enemy_pokemon
            target = self.enemy_pokemon if actor == "player" else self.player_pokemon
            sprite = self.player_sprite if actor == "player" else self.enemy_sprite
            target_sprite = self.enemy_sprite if actor == "player" else self.player_sprite

            self.message_queue.append(actor_pokemon.get_name() + " used " + move["name"] + "!")

            if move["healing"]:
                heal = self.calculator.calculate_healing(actor_pokemon)
                healed = actor_pokemon.apply_healing(heal)
                self.message_queue.append(actor_pokemon.get_name() + " recovered " + str(healed) + " HP!")
            elif move["category"] == "defensive":
                actor_pokemon.raise_defense_stage(move["defense_stage_effect"])
                self.message_queue.append(actor_pokemon.get_name() + "'s Defense rose!")
            else:
                if move["attack_stage_effect"] > 0:
                    actor_pokemon.raise_attack_stage(move["attack_stage_effect"])
                    self.message_queue.append(actor_pokemon.get_name() + "'s Attack rose!")
                damage = self.calculator.calculate_damage(actor_pokemon, target, move)
                target.apply_damage(damage)
                target_sprite.trigger_hit()
                effectiveness = self.calculator.get_effectiveness_text(
                    move["type"], target.get_pokemon_type()
                )
                self.message_queue.append("It dealt " + str(damage) + " damage!")
                if effectiveness:
                    self.message_queue.append(effectiveness)

        self._sync_bars()
        self.state = self.STATE_MESSAGE
        if self.message_queue:
            self.message_log.set_message(self.message_queue.pop(0))

        if self.enemy_pokemon.is_fainted():
            self.enemy_sprite.trigger_faint()
            self.state = self.STATE_FAINT
        elif self.player_pokemon.is_fainted():
            self.player_sprite.trigger_faint()
            self.state = self.STATE_FAINT

    def determine_turn_order(self):
        player_speed = self.calculator.get_effective_speed(
            self.player_pokemon.get_speed(),
            self.player_pokemon.speed_stages,
        )
        enemy_speed = self.calculator.get_effective_speed(
            self.enemy_pokemon.get_speed(),
            self.enemy_pokemon.speed_stages,
        )
        if player_speed > enemy_speed:
            return True
        if enemy_speed > player_speed:
            return False
        return random.choice([True, False])

    def handle_faint_done(self):
        if self.enemy_pokemon.is_fainted():
            self.message_queue = [self.enemy_pokemon.get_name() + " fainted!"]
            self.next_state_after_messages = self.STATE_EXP
            self.state = self.STATE_MESSAGE
            self.message_log.set_message(self.message_queue.pop(0))
        elif self.player_pokemon.is_fainted():
            self.message_queue = [self.player_pokemon.get_name() + " fainted..."]
            self.state = self.STATE_DEFEAT
            self.message_log.set_message(self.message_queue[0])
            self.message_queue = []

    def award_exp(self):
        exp_gain = self.enemy_pokemon.get_exp_yield()
        exp_messages = self.player_pokemon.add_exp(exp_gain)
        self.leveled_up = len(exp_messages) > 1
        self.message_queue = list(exp_messages)
        self._sync_bars()

        evolved, evo_msg = self.evolution_handler.check_and_evolve(self.player_pokemon)
        if evo_msg:
            self.evolved_pokemon = evolved
            self.player_pokemon = evolved
            self.message_queue.append(evo_msg)
            self.evolution_flash = 60
            self.player_sprite = PokemonBattleSprite(
                self.player_pokemon.get_sprite_back_path(), 80, 320, is_back=True
            )

        if self.battle_type == "trainer" and self.enemy_index < len(self.enemy_team) - 1:
            self.enemy_index += 1
            self.enemy_pokemon = self.enemy_team[self.enemy_index]
            self.enemy_pokemon.reset_battle_stages()
            self._reload_enemy_sprite()
            self._sync_bars()
            self.message_queue.append(
                self.trainer_name + " sent out " + self.enemy_pokemon.get_name() + "!"
            )
            self.next_state_after_messages = self.STATE_MENU
        elif self.battle_type == "trainer":
            self.game_completed = True
            self.message_queue.append("You defeated " + self.trainer_name + "!")
            self.message_queue.append("Congratulations! You are the Island Champion!")
            self.next_state_after_messages = self.STATE_VICTORY
        else:
            self.message_queue.append("You won the battle!")
            self.next_state_after_messages = self.STATE_VICTORY

        self.state = self.STATE_MESSAGE
        if self.message_queue:
            self.message_log.set_message(self.message_queue.pop(0))

    def finish_victory(self):
        self.message_queue = ["Press SPACE to continue."]
        self.state = self.STATE_MESSAGE
        self.message_log.set_message(self.message_queue.pop(0))
        self.next_state_after_messages = "done"

    def update(self):
        self.player_sprite.update()
        self.enemy_sprite.update()
        self.player_hp_bar.update()
        self.enemy_hp_bar.update()
        self.player_xp_bar.update()
        if self.evolution_flash > 0:
            self.evolution_flash -= 1

        if self.state == self.STATE_FAINT:
            if self.enemy_pokemon.is_fainted() and self.enemy_sprite.is_faint_done():
                self.handle_faint_done()
            elif self.player_pokemon.is_fainted() and self.player_sprite.is_faint_done():
                self.handle_faint_done()

    def is_done(self):
        return self.state == self.STATE_DONE

    def get_result(self):
        return {
            "result": self.result,
            "player_pokemon": self.player_pokemon,
            "game_completed": self.game_completed,
            "leveled_up": self.leveled_up,
        }

    def draw(self):
        self.screen.fill(BATTLE_BG)
        pygame.draw.ellipse(self.screen, (30, 50, 70), (0, 400, SCREEN_WIDTH, 304))

        if self.evolution_flash > 0 and self.evolution_flash % 6 < 3:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flash.fill(WHITE)
            flash.set_alpha(120)
            self.screen.blit(flash, (0, 0))

        self.enemy_sprite.draw(self.screen)
        self.player_sprite.draw(self.screen)

        enemy_panel = pygame.Rect(480, 20, 260, 80)
        pygame.draw.rect(self.screen, (40, 40, 60), enemy_panel)
        pygame.draw.rect(self.screen, WHITE, enemy_panel, 2)
        enemy_name = self.font.render(
            self.enemy_pokemon.get_name() + " Lv" + str(self.enemy_pokemon.level), True, WHITE
        )
        self.screen.blit(enemy_name, (490, 30))
        self.enemy_hp_bar.draw(self.screen)

        player_panel = pygame.Rect(20, 480, 260, 80)
        pygame.draw.rect(self.screen, (40, 40, 60), player_panel)
        pygame.draw.rect(self.screen, WHITE, player_panel, 2)
        player_name = self.font.render(
            self.player_pokemon.get_name() + " Lv" + str(self.player_pokemon.level), True, WHITE
        )
        self.screen.blit(player_name, (30, 490))
        self.player_hp_bar.draw(self.screen)
        self.player_xp_bar.draw(self.screen)

        self.message_log.draw(self.screen)
        self.battle_menu.draw(self.screen)

        if self.state == self.STATE_DEFEAT:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            text = self.big_font.render("GAME OVER", True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 280))
            hint = self.font.render("Press SPACE to continue", True, WHITE)
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 330))

        if self.state == self.STATE_VICTORY and not self.message_queue:
            pass

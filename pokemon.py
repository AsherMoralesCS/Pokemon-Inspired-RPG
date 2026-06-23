import json
import math
import os

from config import BASE_DIR, EXP_LEVEL_BASE, MAX_STAT_STAGES, POKEMON_DB_PATH, STARTER_LEVEL
from moves import build_move_set, validate_move_set


_pokemon_database = None


def get_pokemon_database():
    global _pokemon_database
    if _pokemon_database is None:
        _pokemon_database = PokemonDatabase()
    return _pokemon_database


def get_exp_for_level(level):
    if level <= 1:
        return 0
    return EXP_LEVEL_BASE * (level - 1) * (level - 1)


class PokemonDatabase:
    def __init__(self):
        self.species = {}
        self.load()

    def load(self):
        with open(POKEMON_DB_PATH, "r", encoding="utf-8") as file:
            self.species = json.load(file)

    def get_species(self, species_id):
        return self.species.get(species_id)

    def get_starter_ids(self):
        return ["water_stage1", "grass_stage1", "fire_stage1"]


class Pokemon:
    def __init__(self, species_id, level=1, exp=0, hp_current=None,
                 attack_stages=0, defense_stages=0, speed_stages=0,
                 evolution_stage=None):
        self.db = get_pokemon_database()
        self.species_id = species_id
        self.species_data = self.db.get_species(species_id)
        if self.species_data is None:
            raise ValueError("Unknown species: " + species_id)

        self.level = level
        self.exp = exp
        self.attack_stages = attack_stages
        self.defense_stages = defense_stages
        self.speed_stages = speed_stages
        self.evolution_stage = evolution_stage or self.species_data["evolution_stage"]
        self.moves = []

        self.max_hp = self.calculate_stat("hp")
        if hp_current is None:
            self.hp_current = self.max_hp
        else:
            self.hp_current = min(hp_current, self.max_hp)

        self.assign_moves()

    def get_name(self):
        return self.species_data["name"]

    def get_pokemon_type(self):
        return self.species_data["type"]

    def get_exp_to_next(self):
        return get_exp_for_level(self.level + 1) - get_exp_for_level(self.level)

    def get_exp_in_level(self):
        return self.exp - get_exp_for_level(self.level)

    def is_fainted(self):
        return self.hp_current <= 0

    def assign_moves(self):
        self.moves = build_move_set(self.get_pokemon_type())
        validate_move_set(self.moves, self.get_pokemon_type())

    def get_moves(self):
        return list(self.moves)

    def calculate_stat(self, stat_name):
        base = self.species_data["base_stats"][stat_name]
        growth = self.species_data["stat_growth"][stat_name]
        return int(base + math.floor(growth * self.level))

    def get_attack(self):
        return self.calculate_stat("attack")

    def get_defense(self):
        return self.calculate_stat("defense")

    def get_special_attack(self):
        return self.calculate_stat("special_attack")

    def get_special_defense(self):
        return self.calculate_stat("special_defense")

    def get_speed(self):
        return self.calculate_stat("speed")

    def get_exp_yield(self):
        base_yield = self.species_data["base_exp_yield"]
        return base_yield * self.level

    def recalculate_stats(self):
        old_max = self.max_hp
        self.max_hp = self.calculate_stat("hp")
        if old_max > 0:
            ratio = self.hp_current / old_max
            self.hp_current = max(1, int(self.max_hp * ratio))
        else:
            self.hp_current = self.max_hp

    def heal_full(self):
        self.hp_current = self.max_hp
        self.reset_battle_stages()

    def reset_battle_stages(self):
        self.attack_stages = 0
        self.defense_stages = 0
        self.speed_stages = 0

    def modify_attack_stage(self, stages):
        self.attack_stages = max(-MAX_STAT_STAGES, min(MAX_STAT_STAGES, self.attack_stages + stages))

    def modify_defense_stage(self, stages):
        self.defense_stages = max(-MAX_STAT_STAGES, min(MAX_STAT_STAGES, self.defense_stages + stages))

    def modify_speed_stage(self, stages):
        self.speed_stages = max(-MAX_STAT_STAGES, min(MAX_STAT_STAGES, self.speed_stages + stages))

    def add_exp(self, amount):
        messages = []
        self.exp += amount
        messages.append(self.get_name() + " gained " + str(amount) + " EXP!")
        while self.level < 100 and self.exp >= get_exp_for_level(self.level + 1):
            self.level_up()
            messages.append(self.get_name() + " grew to level " + str(self.level) + "!")
        return messages

    def level_up(self):
        self.level += 1
        old_hp = self.hp_current
        self.recalculate_stats()
        self.hp_current = min(self.max_hp, old_hp + (self.max_hp - old_hp))

    def apply_damage(self, damage):
        self.hp_current = max(0, self.hp_current - damage)
        return damage

    def apply_healing(self, amount):
        before = self.hp_current
        self.hp_current = min(self.max_hp, self.hp_current + amount)
        return self.hp_current - before

    def raise_attack_stage(self, stages):
        self.modify_attack_stage(stages)

    def raise_defense_stage(self, stages):
        self.modify_defense_stage(stages)

    def raise_speed_stage(self, stages):
        self.modify_speed_stage(stages)

    def to_save_dict(self):
        return {
            "species_id": self.species_id,
            "level": self.level,
            "exp": self.exp,
            "hp_current": self.hp_current,
            "evolution_stage": self.evolution_stage,
            "moves": self.get_moves(),
        }

    def get_sprite_front_path(self):
        return os.path.join(BASE_DIR, self.species_data["sprite_front"])

    def get_sprite_back_path(self):
        return os.path.join(BASE_DIR, self.species_data["sprite_back"])

    def can_evolve(self):
        evolve_level = self.species_data.get("evolve_level")
        evolves_to = self.species_data.get("evolves_to")
        if evolves_to is None or evolve_level is None:
            return False
        return self.level >= evolve_level

    def get_evolves_to(self):
        return self.species_data.get("evolves_to")


def pokemon_from_save_dict(data):
    pokemon = Pokemon(
        species_id=data["species_id"],
        level=data["level"],
        exp=data["exp"],
        hp_current=data["hp_current"],
        evolution_stage=data.get("evolution_stage"),
    )
    pokemon.reset_battle_stages()
    validate_move_set(pokemon.get_moves(), pokemon.get_pokemon_type())
    return pokemon


def create_wild_pokemon(species_id, level):
    pokemon = Pokemon(species_id, level=level)
    pokemon.heal_full()
    return pokemon


def create_pokemon_from_species(species_id, level=1):
    return Pokemon(species_id, level=level)


def create_starter_pokemon(species_id):
    level = STARTER_LEVEL
    exp = get_exp_for_level(level)
    pokemon = Pokemon(species_id, level=level, exp=exp)
    pokemon.heal_full()
    validate_move_set(pokemon.get_moves(), pokemon.get_pokemon_type())
    return pokemon

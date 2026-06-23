import math

from config import (
    ATTACK_STAGE_MULTIPLIER,
    DEFENSE_STAGE_REDUCTION,
    HEAL_PERCENT,
    MAX_STAT_STAGES,
)


TYPE_CHART = {
    "water": {"water": 1.0, "fire": 2.0, "grass": 0.5, "normal": 1.0},
    "fire": {"water": 0.5, "fire": 1.0, "grass": 2.0, "normal": 1.0},
    "grass": {"water": 2.0, "fire": 0.5, "grass": 1.0, "normal": 1.0},
    "normal": {"water": 1.0, "fire": 1.0, "grass": 1.0, "normal": 1.0},
}


class DamageCalculator:
    def __init__(self):
        self.type_chart = TYPE_CHART

    def get_type_multiplier(self, move_type, defender_type):
        move_row = self.type_chart.get(move_type, self.type_chart["normal"])
        return move_row.get(defender_type, 1.0)

    def get_effective_attack(self, base_attack, attack_stages):
        stages = min(MAX_STAT_STAGES, max(-MAX_STAT_STAGES, attack_stages))
        if stages >= 0:
            multiplier = 1.0 + ATTACK_STAGE_MULTIPLIER * stages
            multiplier = min(multiplier, 4.0)
        else:
            multiplier = math.pow(1.0 - DEFENSE_STAGE_REDUCTION, -stages)
        return int(base_attack * multiplier)

    def get_effective_speed(self, base_speed, speed_stages):
        stages = min(MAX_STAT_STAGES, max(-MAX_STAT_STAGES, speed_stages))
        if stages >= 0:
            multiplier = 1.0 + ATTACK_STAGE_MULTIPLIER * stages
            multiplier = min(multiplier, 4.0)
        else:
            multiplier = math.pow(1.0 - DEFENSE_STAGE_REDUCTION, -stages)
        return int(base_speed * multiplier)

    def get_defense_multiplier(self, defense_stages):
        stages = min(MAX_STAT_STAGES, max(-MAX_STAT_STAGES, defense_stages))
        if stages >= 0:
            return math.pow(1.0 - DEFENSE_STAGE_REDUCTION, stages)
        multiplier = 1.0 + ATTACK_STAGE_MULTIPLIER * (-stages)
        return min(multiplier, 4.0)

    def get_effective_base_power(self, move, level):
        if move["category"] != "offensive":
            return move["base_power"]
        return move["base_power"] + int(level * move["scaling_factor"])

    def calculate_damage(self, attacker, defender, move):
        if move["category"] != "offensive":
            return 0

        effective_attack = self.get_effective_attack(
            attacker.get_attack(),
            attacker.attack_stages,
        )
        effective_power = self.get_effective_base_power(move, attacker.level)
        type_multiplier = self.get_type_multiplier(move["type"], defender.get_pokemon_type())
        raw_damage = (effective_power + effective_attack) * type_multiplier
        defense_multiplier = self.get_defense_multiplier(defender.defense_stages)
        final_damage = int(raw_damage * defense_multiplier)
        return max(1, final_damage)

    def calculate_healing(self, pokemon):
        return max(1, int(pokemon.max_hp * HEAL_PERCENT))

    def get_effectiveness_text(self, move_type, defender_type):
        multiplier = self.get_type_multiplier(move_type, defender_type)
        if multiplier >= 2.0:
            return "It's super effective!"
        if multiplier <= 0.5:
            return "It's not very effective..."
        return ""

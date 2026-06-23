MOVES = {
    "aqua_shot": {
        "name": "Aqua Shot",
        "type": "water",
        "category": "offensive",
        "base_power": 20,
        "scaling_factor": 1.5,
        "attack_stage_effect": 0,
        "defense_stage_effect": 0,
        "healing": False,
    },
    "ember_strike": {
        "name": "Ember Strike",
        "type": "fire",
        "category": "offensive",
        "base_power": 20,
        "scaling_factor": 1.5,
        "attack_stage_effect": 0,
        "defense_stage_effect": 0,
        "healing": False,
    },
    "vine_whip": {
        "name": "Vine Whip",
        "type": "grass",
        "category": "offensive",
        "base_power": 20,
        "scaling_factor": 1.5,
        "attack_stage_effect": 0,
        "defense_stage_effect": 0,
        "healing": False,
    },
    "iron_guard": {
        "name": "Iron Guard",
        "type": "normal",
        "category": "defensive",
        "base_power": 0,
        "scaling_factor": 0,
        "attack_stage_effect": 0,
        "defense_stage_effect": 1,
        "healing": False,
    },
    "scratch": {
        "name": "Scratch",
        "type": "normal",
        "category": "offensive",
        "base_power": 10,
        "scaling_factor": 0.8,
        "attack_stage_effect": 1,
        "defense_stage_effect": 0,
        "healing": False,
    },
    "recover": {
        "name": "Recover",
        "type": "normal",
        "category": "healing",
        "base_power": 0,
        "scaling_factor": 0,
        "attack_stage_effect": 0,
        "defense_stage_effect": 0,
        "healing": True,
    },
}

TYPE_TO_MOVE = {
    "water": "aqua_shot",
    "fire": "ember_strike",
    "grass": "vine_whip",
}

NORMAL_MOVE_IDS = ["iron_guard", "scratch", "recover"]


def get_typed_move_for_type(pokemon_type):
    return TYPE_TO_MOVE.get(pokemon_type, "scratch")


def build_move_set(pokemon_type):
    typed_move = get_typed_move_for_type(pokemon_type)
    move_set = [typed_move] + list(NORMAL_MOVE_IDS)
    validate_move_set(move_set, pokemon_type)
    return move_set


def validate_move_set(move_ids, pokemon_type):
    if len(move_ids) != 4:
        raise ValueError(
            "Pokemon must know exactly 4 moves, got " + str(len(move_ids))
        )

    if len(set(move_ids)) != 4:
        raise ValueError("Pokemon move set must contain 4 unique moves")

    typed_move = get_typed_move_for_type(pokemon_type)
    if typed_move not in move_ids:
        raise ValueError(
            "Pokemon must know its primary type move: " + typed_move
        )

    type_moves = [move_id for move_id in move_ids if MOVES[move_id]["type"] == pokemon_type]
    if len(type_moves) != 1:
        raise ValueError(
            "Pokemon must know exactly 1 move matching its primary type"
        )

    normal_moves = [move_id for move_id in move_ids if MOVES[move_id]["type"] == "normal"]
    if len(normal_moves) != 3:
        raise ValueError("Pokemon must know exactly 3 Normal-type moves")

    for move_id in move_ids:
        if move_id not in MOVES:
            raise ValueError("Unknown move: " + move_id)

    return True


class MoveLookup:
    def __init__(self):
        self.moves = MOVES

    def get_move(self, move_id):
        return self.moves.get(move_id)

    def get_move_name(self, move_id):
        move = self.get_move(move_id)
        if move:
            return move["name"]
        return move_id

    def get_pokemon_moves(self, pokemon):
        return list(pokemon.get_moves())

    def get_typed_move_for_type(self, pokemon_type):
        return get_typed_move_for_type(pokemon_type)

    def validate_pokemon_moves(self, pokemon):
        return validate_move_set(pokemon.get_moves(), pokemon.get_pokemon_type())

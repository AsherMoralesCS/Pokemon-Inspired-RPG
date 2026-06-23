from pokemon import Pokemon


class EvolutionHandler:
    def __init__(self):
        self.pending_evolution = None
        self.evolution_message = ""

    def check_and_evolve(self, pokemon):
        if not pokemon.can_evolve():
            return pokemon, None

        evolves_to = pokemon.get_evolves_to()
        if evolves_to is None:
            return pokemon, None

        old_name = pokemon.get_name()
        new_pokemon = Pokemon(
            species_id=evolves_to,
            level=pokemon.level,
            exp=pokemon.exp,
            hp_current=pokemon.hp_current,
        )
        new_pokemon.reset_battle_stages()
        new_pokemon.recalculate_stats()
        new_pokemon.hp_current = min(new_pokemon.max_hp, pokemon.hp_current + 10)

        message = old_name + " evolved into " + new_pokemon.get_name() + "!"
        self.pending_evolution = new_pokemon
        self.evolution_message = message
        return new_pokemon, message

    def clear_pending(self):
        self.pending_evolution = None
        self.evolution_message = ""

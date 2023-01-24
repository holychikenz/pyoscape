from .character import *
import numpy as np


class Combat:
    """
    Combat module: Very simple, just to get an idea
    """

    def __init__(self):
        pass

    def get_defensive_accuracy_rating(self, target):
        defense_level = target.defense
        agility = target.agility
        defense_level_rating = defense_level * 5
        hard_to_hit = target.enchantments.get("Hard to Hit", 0)
        hard_to_hit_bonus = max(20, agility * (1 + hard_to_hit))
        ice_armor = target.enchantments.get("Ice Armor", 0)
        rooted = target.enchantments.get("Rooted", 0)
        rooted_bonus = max(20, agility * (1 + rooted))
        final_agility = agility + hard_to_hit_bonus - ice_armor - rooted_bonus
        agility_rating_mult = (1.5 * final_agility + 60) / 120
        return defense_level_rating * agility_rating_mult

    def get_affinity_value(self, a, b):
        return b

    def get_offensive_accuracy_rating(self, target, ability=None):
        accuracy_affinity_ratings = target.offensive_accuracy_affinity_rating
        attack_level = target.attack
        mastery_level = target.attack_mastery
        scaled_affinity_accuracy_sum = 0
        ability = ability if ability is not None else Ability()
        for (affinity_index, scaling) in ability.accuracy_scaling.items():
            scaled_affinity_accuracy_sum += self.get_affinity_value(
                accuracy_affinity_ratings, scaling
            )
        level_rating = attack_level * 3
        return (mastery_level + level_rating + scaled_affinity_accuracy_sum * 3) * ability.base_accuracy_coeff

    def chance_to_hit(self, attacker, defender, ability=None):
        nimble = 0
        target_bonus_mult_final = 1 + nimble
        source_bonus_mult = 1
        target_accuracy_rating = max(1.1, self.get_defensive_accuracy_rating(defender) * target_bonus_mult_final)
        source_accuracy_rating = max(1.1, self.get_offensive_accuracy_rating(attacker, ability) * source_bonus_mult)
        clash = source_accuracy_rating / target_accuracy_rating
        clash_log = np.log10(source_accuracy_rating) / np.log10(target_accuracy_rating)
        return (clash + clash_log) / 2

    def damage_to_target(self, attacker, defender, ability=None):
        hit_chance = self.chance_to_hit(attacker, defender, ability)
        protection = 300/(300 + defender.protection + defender.defense_mastery)
        resistance = 120/(80 + defender.resistance + defender.constitution_mastery)
        return min(hit_chance, 1.0) * protection


class Combatant:
    def __init__(self, **kwargs):
        # Setup combat stats and affinities
        self.hitpoints = kwargs.get("hitpoints", 1)
        self.speed = kwargs.get("speed", 2.0)
        self.attack = kwargs.get("attack", 1)
        self.attack_mastery = kwargs.get("attack_mastery", 0)
        self.constitution_mastery = kwargs.get("constitution_mastery", 0)
        self.defense = kwargs.get("defense", 1)
        self.defense_mastery = kwargs.get("defense_mastery", 0)
        self.strength = kwargs.get("strength", 1)
        self.ranged = kwargs.get("ranged", 1)
        self.magic = kwargs.get("magic", 1)
        # Defenses
        self.agility = kwargs.get("agility", 0)
        self.protection = kwargs.get("protection", 0)
        self.resistance = kwargs.get("resistance", 0)
        # Affinities
        self.offensive_accuracy_affinity_rating = kwargs.get("offensive_affinity", 1.0)
        # Enchantments
        self.enchantments = kwargs.get("enchantments", dict())


class Ability:
    def __init__(self, **kwargs):
        self.accuracy_scaling = kwargs.get('accuracy_scaling', dict())
        self.base_accuracy_coeff = kwargs.get('base_accuracy', 1.0)

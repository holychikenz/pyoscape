from .gathering import *
from .character import *
import numpy as np


class Fishing(Gathering):
    player = None

    def __init__(self, character, location_data, **kwargs):
        self.player = character
        self.items = self.player.item_data
        self.locations = select_action_locations(location_data, self.items, "Action-Fishing")
        self.use_castnet = kwargs.get("castnet", False)
        self.use_driftwood = kwargs.get("driftwood", False)
        self.accuracy = kwargs.get("accuracy", 10000)
        if self.use_castnet:
            from tensorflow import keras
            from .litemodel import LiteModel
            tf_castnet_trials = keras.models.load_model('Castnet_Trials')
            tf_castnet_resources = keras.models.load_model('Castnet_CalcResource')
            self.castnet_average_tries_to_finish_node = LiteModel.from_keras_model(tf_castnet_trials)
            self.castnet_calculate_node_resources = LiteModel.from_keras_model(tf_castnet_resources)
        if self.use_driftwood:
            import joblib
            self.driftwood_average_tries_to_finish_node = joblib.load('AvgTrials.pkl')
            self.driftwood_calculate_node_resources = joblib.load('CalcResources.pkl')
        self.alt_experience = kwargs.get("alt_experience", None)
        # Fishing gear

    # Fishing specific attributes
    def fishing_bonus(self):
        # Enchantments, gear
        pass

    def get_action_primary_attribute(self):
        return 'fishing_level'

    def get_maximum_experience(self):
        zone_xp_list = [self.zone_experience_rate(loc.name) for (k, loc) in self.locations.items()]
        return max(zone_xp_list)

    def _effective_level(self):
        set_bonus = 1 + self.player.fishing_set_bonus
        level = self.player.fishing_level
        gear_base = self.player.fishing_bonus
        bait = self.player.bait_fishing_bonus * (1 + self.player.enchantments.get('deadliestCatch', 0) * 0.05)
        return level + bait + gear_base * set_bonus

    def _bait_power(self):
        set_bonus = 1 + self.player.fishing_set_bonus
        gear_base = self.player.bait_power
        gear_enchant = self.player.enchantments.get('pungentBait', 0) * 3 \
                       - self.player.enchantments.get('fishingMagnetism') * 2
        bait = self.player.bait_bait_power * (1 + self.player.enchantments.get('deadliestCatch', 0) * 0.05)
        return (gear_base + gear_enchant) * set_bonus + bait

    def _bonus_rarity(self):
        set_bonus = 1 + self.player.fishing_set_bonus
        gear_base = self.player.bonus_rarity
        gear_enchant = self.player.enchantments.get('fishingMagnetism') * 2
        bait = self.player.bait_bonus_rarity * (1 + self.player.enchantments.get('deadliestCatch', 0) * 0.05)
        return (gear_base + gear_enchant) * set_bonus + bait

    def _reel_power(self):
        set_bonus = 1 + self.player.fishing_set_bonus
        gear_base = self.player.reel_power
        gear_enchant = self.player.enchantments.get('reinforcedLine', 0) * 3 \
                       - self.player.enchantments.get('fishingMagnetism') * 2
        bait = self.player.bait_reel_power * (1 + self.player.enchantments.get('deadliestCatch', 0) * 0.05)
        return (gear_base + gear_enchant) * set_bonus + bait

    def _node_rates(self, location):
        frequency_dict = dict()
        boosted_frequency_dict = dict()
        for (k, v) in location.nodes.items():
            frequency = (v.frequency + self._bonus_rarity()) * (1 + self._effective_level() / 360)
            frequency = min(frequency, v.max_frequency)

            boosted_frequency = max(0, frequency)
            frequency_dict[k] = max(0, frequency)
            boosted_frequency_dict[k] = boosted_frequency
        total_frequency = sum([v for (k, v) in boosted_frequency_dict.items()])
        return {k: v / total_frequency for (k, v) in boosted_frequency_dict.items()}

    def _loot_rates(self, node, **kwargs):
        frequency_dict = dict()
        boosted_frequency_dict = dict()
        single_drop = kwargs.get('single', False)
        for (idd, loot) in node.loot.items():
            frequency = (loot.frequency + self._bonus_rarity()) * (1 + self._effective_level() / 360)
            frequency = min(frequency, loot.max_frequency)
            if loot.item_class == "fiber":
                frequency = frequency * (1 + self.player.enchantments.get('fiberFinder', 0) * 0.25)
            boosted_frequency = max(0, frequency)
            frequency_dict[idd] = max(0, frequency)
            boosted_frequency_dict[idd] = boosted_frequency

        total_frequency = sum([v for (k, v) in boosted_frequency_dict.items()])
        return {k: v / total_frequency for (k, v) in boosted_frequency_dict.items()}

    def _node_base_chance(self, location):
        fishing_enchant = self.player.enchantments.get("fishing", 0)  # TODO, add to player.enchantments
        # Changed bait_power from 420 to 200, 0.2 to 0.3
        return 0.4 + (self._effective_level() - location.level * 1.25) / 275 + (fishing_enchant * 0.025) + (
                self._bait_power() / 200)

    def _average_tries_to_find_node(self, location):
        average_tries = 0
        chance_to_reach_this_attempt = 1
        base_chance = self._node_base_chance(location)
        fishing_enchant = self.player.enchantments.get('fishing', 0)

        for nodeFindFailures in range(7):
            chance_this_attempt = min(1, base_chance + fishing_enchant * 0.025 + nodeFindFailures / 6)
            average_tries += chance_this_attempt * chance_to_reach_this_attempt * (nodeFindFailures + 1)
            chance_to_reach_this_attempt *= 1 - chance_this_attempt
        return average_tries

    def _average_node_size(self, location, node):
        nodes = self.accuracy
        return self._calculate_node_resources(node, location, trials=nodes)

    def _calculate_node_resources(self, node, location, **kwargs):
        zone_level = location.level
        min_base = node.minimum_base_amount
        max_base = node.maximum_base_amount
        trials = kwargs.get('trials', 1)
        if self.use_castnet:
            return self.castnet_calculate_node_resources.predict_single(
                [zone_level, min_base, max_base, self._effective_level(), self._bait_power()])[0]
        elif self.use_driftwood:
            return self.driftwood_calculate_node_resources.predict(
                [[zone_level, min_base, max_base, self._effective_level(), self._bait_power()]])[0]
        else:
            return _calculate_node_resources_jit_fishing(zone_level, min_base, max_base, self._effective_level(),
                                                         self._bait_power(),
                                                         trials)

    def _node_sizes(self, location):
        return {k: self._average_node_size(location, v) for (k, v) in location.nodes.items()}

    def _node_actions(self, location):
        return {k: self._average_tries_to_finish_node(location, v) for (k, v) in location.nodes.items()}

    def _average_tries_to_finish_node(self, location, node, **kwargs):
        zone_level = location.level
        min_base = node.minimum_base_amount
        max_base = node.maximum_base_amount
        fishing_level = self.player.fishing_level + self.player.fishing_bonus
        bait_power = self.player.bait_power
        base_chance = self._node_base_chance(location)
        fishing_enchant = self.player.enchantments.get('fishing', 0)
        if self.use_castnet:
            return \
                self.castnet_average_tries_to_finish_node.predict_single([base_chance, zone_level, min_base, max_base,
                                                                          fishing_level, bait_power, fishing_enchant])[
                    0]
        elif self.use_driftwood:
            return self.driftwood_average_tries_to_finish_node.predict([[base_chance, zone_level, min_base, max_base,
                                                                         fishing_level, bait_power, fishing_enchant]])[
                0]
        else:
            return _average_tries_to_finish_node_jit_fishing(base_chance, zone_level, min_base, max_base, fishing_level,
                                                             bait_power, fishing_enchant, self.accuracy)

    def zone_experience_rate(self, location_name):
        """
        Experience per hour
        """
        location = self.get_location_by_name(location_name)
        if location.level > self.player.fishing_level:
            return 0
        if self.alt_experience is not None:
            return self.alt_experience.get(location_name, 0) * self.zone_action_rate(location_name)

        node_rates = self._node_rates(location)
        node_sizes = self._node_sizes(location)
        node_actions = self._node_actions(location)
        haste = self.player.enchantments.get('haste', 0)

        base_time = location.base_duration / 1000 / (1 + haste * 0.04)
        node_search_time = max(1, base_time * 1.75 * (1 - (self._bait_power() / 400)))
        a_find = self._average_tries_to_find_node(location)
        loot_search_time = max(1, base_time / 1.25 * (200 / (self._reel_power() + 200)))

        total_experience = 0
        total_time = 0
        for (name, rate) in node_rates.items():
            total_time += (node_search_time * a_find + loot_search_time * node_actions[name]) * rate
            avg_size = node_sizes[name]
            loot_rates = self._loot_rates(location.nodes[name])
            for (itemid, loot) in location.nodes[name].loot.items():
                item_stats = self.player.item_data[str(itemid)]
                total_experience += loot_rates[itemid] * avg_size * rate * item_stats.get("experience", 30)
        return total_experience / total_time * 3600

    def zone_action_rate(self, location_name):
        """
        Action rate (per hour)
        """
        location = self.get_location_by_name(location_name)
        if location.level > self.player.fishing_level:
            return 0

        node_rates = self._node_rates(location)
        node_sizes = self._node_sizes(location)
        node_actions = self._node_actions(location)
        haste = self.player.enchantments.get('haste', 0)

        base_time = location.base_duration / 1000 / (1 + haste * 0.04)
        node_search_time = max(1, base_time * 1.75 * (1 - (self._bait_power() / 400)))
        a_find = self._average_tries_to_find_node(location)
        loot_search_time = max(1, base_time / 1.25 * (200 / (self._reel_power() + 200)))

        total_actions = 0
        total_time = 0
        for (name, rate) in node_rates.items():
            total_time += (node_search_time * a_find + loot_search_time * node_actions[name]) * rate
            total_actions += node_sizes[name] * rate
        return total_actions / total_time * 3600


Gathering.register(Fishing)

# Numba JITFishing section
try:
    from numba import jit


    @jit()
    def _calculate_node_resources_jit_fishing(zone_level, min_base, max_base, fishing_level, bait_power, trials):
        total_resources = 0
        for i in range(trials):
            maximum_node_size = np.floor(max_base + (np.random.rand() * (fishing_level - zone_level) / 8) + np.floor(
                np.random.rand() * bait_power / 20))
            minimum_node_size = np.floor(min_base + (np.random.rand() * (fishing_level - zone_level) / 6) + np.floor(
                np.random.rand() * bait_power / 10))

            lucky_chance = 0.05 + (bait_power / 2000)
            if np.random.rand() <= lucky_chance:
                minimum_node_size *= 1.5
                maximum_node_size *= 3.0

            delta = abs(maximum_node_size - minimum_node_size)
            small = min(maximum_node_size, minimum_node_size)
            total_resources += np.floor(np.random.rand() * delta + small)
        return total_resources / trials

except ImportError:
    def jit(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


    def _calculate_node_resources_jit_fishing(zone_level, min_base, max_base, fishing_level, bait_power, trials):
        maximum_node_size = np.floor(max_base + (np.random.rand(trials) * (fishing_level - zone_level) / 8) + np.floor(
            np.random.rand(trials) * bait_power / 20))
        minimum_node_size = np.floor(min_base + (np.random.rand(trials) * (fishing_level - zone_level) / 6) + np.floor(
            np.random.rand(trials) * bait_power / 10))

        lucky_chance = 0.05 + (bait_power / 2000)
        lucky_rolls = np.random.rand(trials) <= lucky_chance
        minimum_node_size = minimum_node_size * (1 + 0.5 * lucky_rolls)
        maximum_node_size = maximum_node_size * (1 + 2.0 * lucky_rolls)

        delta = abs(maximum_node_size - minimum_node_size)
        small = np.min([maximum_node_size, minimum_node_size], axis=0)
        total_resources = sum(np.floor(np.random.rand(trials) * delta + small))
        return total_resources / trials


@jit
def _average_tries_to_finish_node_jit_fishing(base_chance, zone_level, min_base, max_base, fishing_level, bait_power,
                                              fishing, trials):
    node_resources = np.array(
        [int(_calculate_node_resources_jit_fishing(zone_level, min_base, max_base, fishing_level, bait_power, 1)) for
         _ in range(trials)])
    min_node_count = min(node_resources)
    max_node_count = max(node_resources)
    node_average = []
    for total_node_resources in range(min_node_count, max_node_count + 1):
        total_tries_sub = 0.0
        for n_res in range(total_node_resources, 0, -1):
            never_tell_me_the_odds = min(1.0, base_chance + fishing * 0.025 + n_res / 48)
            total_tries_sub += 1 / never_tell_me_the_odds
        node_average.append(total_tries_sub)
    node_average = np.array(node_average)
    return np.mean(node_average[(node_resources - min_node_count)])

from abc import ABC

import numpy as np
from .gathering import *
from .character import *


class Foraging(Gathering, ABC):
    player = None

    def __init__(self, character, location_data, **kwargs):
        self.player = character
        self.items = self.player.item_data
        self.locations = select_action_locations(location_data, self.items, "Action-Foraging")
        self.alt_experience = kwargs.get("alt_experience", None)

    def get_action_primary_attribute(self):
        return 'foraging_level'

    def get_maximum_experience(self):
        zone_xp_list = [self.zone_experience_rate(loc.name) for (k, loc) in self.locations.items()]
        return max(zone_xp_list)

    def _effective_level(self):
        return self.player.foraging_level + self.player.foraging_bonus * (1 + self.player.foraging_set_bonus)

    def _node_rates(self, location):
        frequency_dict = dict()
        for (k, v) in location.nodes.items():
            frequency = v.frequency
            # This can be modified based on special enchants
            if "tree" in v.tags:
                frequency += self.player.enchantments.get("nature", 0)
            if "plants" in v.tags:
                frequency += self.player.enchantments.get("herbalist", 0)
            if "seeds" in v.tags:
                frequency += self.player.enchantments.get("seedHarvesting", 0)
            frequency = min(v.max_frequency, frequency)
            frequency_dict[k] = max(0, frequency)
        total_frequency = sum([v for (k, v) in frequency_dict.items()])
        return {k: v / total_frequency for (k, v) in frequency_dict.items()}

    def _average_node_size(self, location, node):
        return (node.maximum_base_amount + node.minimum_base_amount) / 2

    def _node_sizes(self, location):
        return {k: self._average_node_size(location, v) for (k, v) in location.nodes.items()}

    def _node_actions(self, location):
        return self._node_sizes(location)

    def zone_experience_rate(self, location_name):
        location = self.get_location_by_name(location_name)
        if location.level > self.player.foraging_level:
            return 0
        if self.alt_experience is not None:
            return self.alt_experience.get(location_name, 0) * self.zone_action_rate(location_name)
        haste = self.player.enchantments.get('haste', 0)
        rate_modifier = (self._effective_level() + 99) / 100 * (1 + haste * 0.04)
        item_hist = self.location_item_histogram(location_name, key='id')
        summed_weighted_xp = 0
        for (k, v) in item_hist.items():
            item_stats = self.player.item_data[str(k)]
            xp = item_stats.get("experience", 1)
            summed_weighted_xp += v * xp
        return summed_weighted_xp * rate_modifier * 3600000 / location.base_duration

    def zone_action_rate(self, location_name):
        location = self.get_location_by_name(location_name)
        if location.level > self.player.foraging_level:
            return 0
        haste = self.player.enchantments.get('haste', 0)
        rate_modifier = (self._effective_level() + 99) / 100 * (1 + haste * 0.04)
        return rate_modifier * 3600000 / location.base_duration


Gathering.register(Foraging)
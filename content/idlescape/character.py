import json


class Character:
    """
    Character stats and bonuses for fishing, foraging, and mining.
    """
    def __init__(self, **kwargs):
        self.item_data = select_items(kwargs.get("datafile", "data/items.json"))
        # Fishing
        self.fishing_level = kwargs.get("fishing_level", 1)
        self.fishing_bonus = kwargs.get("fishing_bonus", 1)
        self.fishing_set_bonus = kwargs.get("fishing_set_bonus", 0.0)
        self.bait_preservation = kwargs.get("bait_preservation", 0)
        self.bait_power = kwargs.get("bait_power", 0)
        self.reel_power = kwargs.get("reel_power", 0)
        self.bonus_rarity = kwargs.get("bonus_rarity", 0)
        # Mining
        self.mining_level = kwargs.get("mining_level", 0)
        self.mining_bonus = kwargs.get("mining_bonus", 0)
        self.mining_set_bonus = kwargs.get("mining_set_bonus", 0.0)
        # Foraging
        self.foraging_level = kwargs.get("foraging_level", 0)
        self.foraging_bonus = kwargs.get("foraging_bonus", 0)
        self.foraging_set_bonus = kwargs.get("foraging_set_bonus", 0.0)
        # Enchantments
        self.enchantments = kwargs.get("enchantments", dict())


def select_items(data_file):
    with open(data_file) as jj:
        data = json.load(jj)
        return data

import json


class Character:
    """
    Character stats and bonuses for fishing, foraging, and mining.
    """

    def __init__(self, **kwargs):
        self.item_data = select_items(kwargs.get("datafile", "data/items.json"))
        self.item_lookup_table = {v['name']:k for (k, v) in self.item_data.items()}
        self.equipment_set = kwargs.get("equipment_set", None)
        # Fishing
        self.fishing_level = kwargs.get("fishing_level", 1)
        self.fishing_bonus = kwargs.get("fishing_bonus", 0)
        self.bait_fishing_bonus = kwargs.get("bait_fishing_bonus", 0)
        self.fishing_set_bonus = kwargs.get("fishing_set_bonus", 0.0)
        self.bait_preservation = kwargs.get("bait_preservation", 0)
        self.bait_power = kwargs.get("bait_power", 0)
        self.bait_bait_power = kwargs.get("bait_bait_power", 0)
        self.reel_power = kwargs.get("reel_power", 0)
        self.bait_reel_power = kwargs.get("bait_reel_power", 0)
        self.bait_bonus_rarity = kwargs.get("bait_bonus_rarity", 0)
        # Mining
        self.mining_level = kwargs.get("mining_level", 1)
        self.mining_bonus = kwargs.get("mining_bonus", 0)
        self.mining_set_bonus = kwargs.get("mining_set_bonus", 0.0)
        # Foraging
        self.foraging_level = kwargs.get("foraging_level", 1)
        self.foraging_bonus = kwargs.get("foraging_bonus", 0)
        self.foraging_set_bonus = kwargs.get("foraging_set_bonus", 0.0)
        # Smithing
        self.smithing_level = kwargs.get("smithing_level", 1)
        self.smithing_mastery = kwargs.get("smithing_mastery", 0)
        self.smithing_bonus = kwargs.get("smithing_bonus", 0)
        # Enchantments
        self.enchantments = kwargs.get("enchantments", dict())

    def assign_equipment(self, eq_set):
        self.equipment_set = eq_set
        self._update_stats()

    def _reset_stats(self):
        self.fishing_bonus = 0
        self.fishing_set_bonus = 0
        self.bait_preservation = 0
        self.bait_power = 0
        self.reel_power = 0
        self.bonus_rarity = 0
        self.mining_bonus = 0
        self.mining_set_bonus = 0
        self.foraging_bonus = 0
        self.foraging_set_bonus = 0
        self.smithing_bonus = 0

    def _update_stats(self):
        """
        Tally Stats from equipment set
        """
        if self.equipment_set is None:
            return
        self._reset_stats()
        mining_set_count = 0
        foraging_set_count = 0
        fishing_set_count = 0
        for item_slot in self.equipment_set.slots:
            component = self.equipment_set.equipment_component(item_slot)
            actual_item = self.get_item_by_name(component.name)
            if actual_item is None:
                continue
            augment_level = component.augment
            equipment_stats = actual_item.get('equipmentStats', dict())
            tool_boost = equipment_stats.get('toolBoost', [])
            aug_bonus = equipment_stats.get('augmentationBonus', [])
            item_set = equipment_stats.get('itemSet', [])
            for tb in tool_boost:
                if tb['skill'] == 'mining':
                    self.mining_bonus += tb['boost']
                if tb['skill'] == 'foraging':
                    self.foraging_bonus += tb['boost']
                if tb['skill'] == 'fishing':
                    self.fishing_bonus += tb['boost']
                if tb['skill'] == 'fishingBaitPower':
                    self.bait_power += tb['boost']
                if tb['skill'] == 'fishingReelPower':
                    self.reel_power += tb['boost']
                if tb['skill'] == 'fishingRarityPower':
                    self.bonus_rarity += tb['boost']
            for ab in aug_bonus:
                if ab['stat'] == 'toolBoost.mining':
                    self.mining_bonus += ab['value'] * augment_level
                if ab['stat'] == 'toolBoost.foraging':
                    self.foraging_bonus += ab['value'] * augment_level
                if ab['stat'] == 'toolBoost.fishing':
                    self.fishing_bonus += ab['value'] * augment_level
                if ab['stat'] == 'toolBoost.fishingBaitPower':
                    self.bait_power += ab['value'] * augment_level
                if ab['stat'] == 'toolBoost.fishingReelPower':
                    self.reel_power += ab['value'] * augment_level
                if ab['stat'] == 'toolBoost.fishingRarityPower':
                    self.bonus_rarity += ab['value'] * augment_level
            # Check bait
            fishing_bait = actual_item.get('fishingBait', {})
            self.bait_fishing_bonus = fishing_bait.get('level', 0)
            self.bait_bait_power = fishing_bait.get('bait', 0)
            self.bait_reel_power = fishing_bait.get('reel', 0)
            self.bait_bonus_rarity = fishing_bait.get('bonus', 0)
            if 10007 in item_set:
                mining_set_count += 1
            if 10005 in item_set:
                foraging_set_count += 1
            if 10001 in item_set:
                fishing_set_count += 1
        if mining_set_count == 3:
            self.mining_set_bonus = 0.2
        if mining_set_count == 4:
            self.mining_set_bonus = 0.4
        if foraging_set_count == 3:
            self.foraging_set_bonus = 0.2
        if foraging_set_count == 4:
            self.foraging_set_bonus = 0.4
        if fishing_set_count == 3:
            self.fishing_set_bonus = 0.2
        if fishing_set_count == 4:
            self.fishing_set_bonus = 0.4


    def get_item_by_name(self, name):
        index = self.item_lookup_table.get(name, None)
        if index is None:
            return None
        return self.item_data[index]


class EquipmentSet:
    """
    Character equipment set. A single character can have multiples (for different zones
    and gathering styles)
    """

    def __init__(self, item_data, **kwargs):
        self.slots = ['helm', 'body', 'legs', 'shield', 'weapon', 'boots', 'gloves', 'cape', 'arrows',
                      'ring', 'necklace', 'pickaxe', 'hatchet', 'hoe', 'tongs', 'tome', 'tacklebox', 'bait']
        for slot in self.slots:
            setattr(self, f'{slot}', kwargs.get(slot, None))
            setattr(self, f'{slot}_augment', kwargs.get(f'{slot}_augment', 0))
        self.item_data = item_data

    def matching_items(self, slot, **kwargs):
        flip = kwargs.get("flip", False)
        related_skill = kwargs.get("related_skill", None)
        ret_dict = dict()
        if slot == 'bait':
            for (k, v) in self.item_data.items():
                if v.get('fishingBait', None) is not None:
                    ret_dict[k] = v.get("name", '')
        for (k, v) in self.item_data.items():
            if v.get("class", "") != 'equipment':
                continue
            if v.get("equipmentStats", dict()).get("slot", "") != slot:
                continue
            if related_skill is not None:
                if v.get("relatedSkill", "") != related_skill:
                    continue
            ret_dict[k] = v.get("name", '')
        if flip:
            ret_dict = {v: k for (k, v) in ret_dict.items()}
        return ret_dict

    def equipment_component(self, slot, **kwargs):
        return EquipmentComponent(string=f"{getattr(self,slot)}_{getattr(self,slot+'_augment')}")


class EquipmentComponent:
    def __init__(self, **kwargs):
        from_string = kwargs.get('string', None)
        self.name = kwargs.get('name', None)
        self.slot = kwargs.get('slot', None)
        self.augment = kwargs.get('augment', 0)
        if from_string is not None:
            self.from_string(from_string)

    def as_string(self):
        return f'{self.name}_{self.augment}'

    def from_string(self, istring):
        split_string = istring.split("_")
        self.name = split_string[0]
        self.augment = int(split_string[1])

def select_items(data_file):
    with open(data_file) as jj:
        data = json.load(jj)
        for (k, v) in data.items():
            data[k]['name'] = data[k]['name'].replace("'", "")
        return data

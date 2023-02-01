import json
import numpy as np


class Smithing:
    def __init__(self, character, forge_list, **kwargs):
        with open(forge_list) as json_file:
            self.forges = json.load(json_file)
        self.player = character

    def information(self, forge, bar, intensity):
        level = self.player.smithing_level
        mastery = self.player.smithing_mastery
        gear_level = self.player.smithing_bonus
        total_level = level + mastery + gear_level

        haste = 1 + self.player.enchantments.get("haste", 0) * 0.04
        efficiency = self.player.enchantments.get("efficiency", 0) * 0.01
        pyro = self.player.enchantments.get("pyromancy", 0) * 0.05
        pure_metals = self.player.enchantments.get("pureMetals", 0) * 0.04
        metallurgy = self.player.enchantments.get("metallurgy", 0) * 0.6

        active_forge_data = self.forges[str(forge)]
        active_bar_data = self.player.item_data[str(bar)]
        forge_speed_mult = active_forge_data['forgeSpeedMult']
        forge_intensity_mult = active_forge_data['forgeIntensitySpeedMult']
        forge_xp_mult = active_forge_data['forgeXPMult']
        forge_bonus_bars = active_forge_data['forgeBonusBars']
        forge_intensity_bonus_bars = active_forge_data['forgeIntensityBonusBars']
        forge_intensity_heat_cost_mult = active_forge_data['forgeIntensityHeatCostMult']
        forge_intensity_material_cost_mult = active_forge_data['forgeIntensityMaterialCostMult']
        forge_heat_cost = active_forge_data['forgeHeatCost']
        forge_material_cost = active_forge_data['forgeMaterialCost']

        bar_time = active_bar_data['time']
        bar_experience = active_bar_data['experience']
        bar_resources = active_bar_data['requiredResources'][0]
        bar_level = active_bar_data.get("level", 1)

        bar_tier = max(1, round(bar_level / (13.5 + metallurgy)))
        effective_intensity = intensity - bar_tier
        power_mult = 360 / (360 + 2.5 * mastery + total_level - 1)
        total_time = bar_time * forge_speed_mult * forge_intensity_mult ** effective_intensity * \
            power_mult / haste / 1000
        experience = bar_experience * forge_xp_mult
        output_amount = 1 + forge_bonus_bars * forge_intensity_bonus_bars ** effective_intensity + efficiency

        heat_multiplier = forge_intensity_heat_cost_mult ** effective_intensity * forge_heat_cost * (1 - pyro)
        material_multiplier = forge_intensity_material_cost_mult ** effective_intensity * forge_material_cost * (
                1 - pure_metals)

        def mult_choice(x):
            return heat_multiplier if x == '2' else material_multiplier

        cost_dict = {self.player.item_data[k]['name']: np.ceil(v * mult_choice(k)) for (k, v) in bar_resources.items()}
        this_information = {
            "time": total_time,
            "experience": experience,
            "output": output_amount,
            "cost": cost_dict
        }
        return this_information

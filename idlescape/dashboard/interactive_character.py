import panel as pn
from ..character import Character, EquipmentSet
from ..foraging import Foraging
from ..mining import Mining
from ..fishing import Fishing
import json


class InteractiveCharacter:

    def __init__(self, item_file, location_file):
        self.level_widget_list = None
        self.equipment_widget_list = None
        self.enchant_widget_list = None
        self.callback = None
        # Hacky Hack
        # Player Stats and Levels
        self.player_stats = json.loads(pn.state.cookies.get("interactive_character", "{}").replace("'", "\""))
        self.player = Character(datafile=item_file, **self.player_stats)
        self.mining = Mining(self.player, location_file)
        self.foraging = Foraging(self.player, location_file)
        self.fishing = Fishing(self.player, location_file)
        # Player equipment sets (one for each action)
        self.player_mining_equipment = json.loads(pn.state.cookies.get("mining_equipment", "{}").replace("'", "\""))
        self.player_foraging_equipment = json.loads(pn.state.cookies.get("foraging_equipment", "{}").replace("'", "\""))
        self.player_fishing_equipment = json.loads(pn.state.cookies.get("fishing_equipment", "{}").replace("'", "\""))
        self.mining_gear = EquipmentSet(self.player.item_data, **self.player_mining_equipment)
        self.foraging_gear = EquipmentSet(self.player.item_data, **self.player_foraging_equipment)
        self.fishing_gear = EquipmentSet(self.player.item_data, **self.player_fishing_equipment)

    def _apply_connectors_(self):
        pass

    def _update_values_(self, event):
        for widget in self.level_widget_list:
            widget.update_value()
            self.player_stats[widget.attribute] = widget.widget.value
        for widget in self.equipment_widget_list:
            widget.update_value()
            if widget.related_skill == 'mining':
                self.player_mining_equipment[widget.attribute] = widget.widget.value
            if widget.related_skill == 'foraging':
                self.player_foraging_equipment[widget.attribute] = widget.widget.value
            if widget.related_skill == 'fishing':
                self.player_fishing_equipment[widget.attribute] = widget.widget.value
        for widget in self.enchant_widget_list:
            widget.update_value()
        self.player_stats['enchantments'] = self.player.enchantments
        pn.state.cookies["interactive_character"] = self.player_stats
        pn.state.cookies["mining_equipment"] = self.player_mining_equipment
        pn.state.cookies["foraging_equipment"] = self.player_foraging_equipment
        pn.state.cookies["fishing_equipment"] = self.player_fishing_equipment
        # Need to figure this out
        self.callback(event)

    def assign_equipment(self, action_name):
        if action_name == 'mining_level':
            self.player.assign_equipment(self.mining_gear)
        if action_name == 'foraging_level':
            self.player.assign_equipment(self.foraging_gear)
        if action_name == 'fishing_level':
            self.player.assign_equipment(self.fishing_gear)

    def assign_callback(self, callback):
        self.callback = callback

    def level_widgets(self):
        self.level_widget_list = [
            WidgetAttachment(self.player, 'mining_level',
                             pn.widgets.EditableIntSlider(name="Mining Level", start=1, end=200, step=1)),
            WidgetAttachment(self.player, 'foraging_level',
                             pn.widgets.EditableIntSlider(name="Foraging Level", start=1, end=200, step=1)),
            WidgetAttachment(self.player, 'fishing_level',
                             pn.widgets.EditableIntSlider(name="Fishing Level", start=1, end=200, step=1)),
        ]
        for widget_ptr in self.level_widget_list:
            widget_ptr.widget.param.watch(self._update_values_, 'value')
        return [widget_ptr.widget for widget_ptr in self.level_widget_list]

    def _gear_widget(self, equipment, slot, skill, **kwargs):
        related_skill = kwargs.get('related_skill', None)
        choices = ['None'] + list(equipment.matching_items(slot, related_skill=related_skill, flip=True).keys())
        widget = pn.widgets.Select(options=choices, width=200)
        gear_name = WidgetAttachment(equipment, slot, widget, related_skill=skill)
        gear_name.widget.param.watch(self._update_values_, 'value')
        # Augment
        gear_aug = WidgetAttachment(equipment, f'{slot}_augment', pn.widgets.IntInput(start=0, end=50, step=1,width=50),
                                    related_skill=skill)
        gear_aug.widget.param.watch(self._update_values_, 'value')
        panel = pn.Row(gear_name.widget, gear_aug.widget, width=500)
        self.equipment_widget_list.append(gear_name)
        self.equipment_widget_list.append(gear_aug)
        return panel

    def equipment_widgets(self):
        self.equipment_widget_list = []
        eq_widgets = [
            pn.Row('Mining Equipment'),
            self._gear_widget(self.mining_gear, 'pickaxe', 'mining'),
            self._gear_widget(self.mining_gear, 'helm', 'mining', related_skill='mining'),
            self._gear_widget(self.mining_gear, 'body', 'mining', related_skill='mining'),
            self._gear_widget(self.mining_gear, 'legs', 'mining', related_skill='mining'),
            pn.Row('Foraging Equipment'),
            self._gear_widget(self.foraging_gear, 'hatchet', 'foraging'),
            self._gear_widget(self.foraging_gear, 'helm', 'foraging', related_skill='foraging'),
            self._gear_widget(self.foraging_gear, 'body', 'foraging', related_skill='foraging'),
            self._gear_widget(self.foraging_gear, 'legs', 'foraging', related_skill='foraging'),
            pn.Row('Fishing Equipment'),
            self._gear_widget(self.fishing_gear, 'tacklebox', 'fishing'),
            self._gear_widget(self.fishing_gear, 'helm', 'fishing', related_skill='fishing'),
            self._gear_widget(self.fishing_gear, 'body', 'fishing', related_skill='fishing'),
            self._gear_widget(self.fishing_gear, 'legs', 'fishing', related_skill='fishing'),
            self._gear_widget(self.fishing_gear, 'bait', 'fishing'),
        ]
        return eq_widgets

    def enchant_widgets(self):
        basic_enchants = ['haste', 'gathering', 'empoweredGathering']
        foraging_enchants = ['nature', 'herbalist', 'seedHarvesting', 'embers']
        mining_enchants = ['superheating']
        fishing_enchants = ['fishing', 'pungentBait', 'reinforcedLine', 'fishingMagnetism', 'baitPreservation',
                            'fiberFinder', 'deadliestCatch']
        possible_enchants = basic_enchants + foraging_enchants + mining_enchants + fishing_enchants
        self.enchant_widget_list = [
            WidgetAttachment(self.player.enchantments, iter_val,
                             pn.widgets.IntInput(name=iter_val.capitalize(), start=0, end=8, step=1))
            for iter_val in possible_enchants
        ]
        for widget_ptr in self.enchant_widget_list:
            widget_ptr.widget.param.watch(self._update_values_, 'value')
        return [widget_ptr.widget for widget_ptr in self.enchant_widget_list]


class WidgetAttachment:
    def __init__(self, reference_object, attribute, widget, **kwargs):
        self.related_skill = kwargs.get("related_skill", None)
        self.widget = widget
        self.reference_object = reference_object
        self.attribute = attribute
        if isinstance(self.reference_object, dict):
            self.widget.value = self.reference_object.get(self.attribute, 0)
        else:
            self.widget.value = getattr(self.reference_object, self.attribute)

    def update_value(self):
        if isinstance(self.reference_object, dict):
            self.reference_object[self.attribute] = self.widget.value
        else:
            setattr(self.reference_object, self.attribute, self.widget.value)

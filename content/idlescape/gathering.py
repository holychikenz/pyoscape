import numpy as np
import json
from abc import ABC, abstractmethod
import pandas as pd


class Gathering(ABC):
    @abstractmethod
    def get_maximum_experience(self):
        pass

    @abstractmethod
    def get_action_primary_attribute(self):
        pass

    @abstractmethod
    def _node_rates(self, location):
        pass

    @abstractmethod
    def _node_sizes(self, location):
        pass

    @abstractmethod
    def _node_actions(self, location):
        pass

    def _loot_rates(self, node):
        frequency_dict = dict()
        count_dict = dict()
        for (idd, loot) in node.loot.items():
            frequency = np.min([loot.frequency, loot.max_frequency])
            frequency_dict[idd] = max(0, frequency)
            count_dict[idd] = (loot.min_amount + loot.max_amount) / 2
        total_frequency = sum([v for (k, v) in frequency_dict.items()])
        return {k: v / total_frequency * count_dict[k] for (k, v) in frequency_dict.items()}

    @abstractmethod
    def zone_action_rate(self, location_name):
        pass

    def list_of_actions(self):
        return self.locations.keys()

    def get_location_by_name(self, name):
        if name not in self.list_of_actions():
            raise IndexError(f'{name} not in {self.list_of_actions()}')
        return self.locations[name]

    def location_item_histogram(self, location_name, **kwargs):
        location = self.get_location_by_name(location_name)
        key = kwargs.get('key', 'name')
        interval = kwargs.get('interval', 'action')

        node_rates = self._node_rates(location)
        node_sizes = self._node_sizes(location)
        node_actions = self._node_actions(location)
        action_rate = self.zone_action_rate(location_name) if (interval == 'hour') else 1

        items = dict()
        total_actions = 0
        for (name, rate) in node_rates.items():
            avg_size = node_sizes[name]
            total_actions += node_actions[name] * rate
            loot_rates = self._loot_rates(location.nodes[name])
            for (itemid, loot) in location.nodes[name].loot.items():
                base_rate = items.get(itemid, 0) + loot_rates[itemid] * avg_size * rate * action_rate
                items[itemid] = base_rate
        if key == 'name':
            return pd.Series({self.items[str(k)]['name']: v / total_actions for (k, v) in items.items()})
        else:
            return pd.Series({k: v / total_actions for (k, v) in items.items()})


class Location:
    def __init__(self, name, loc_id, action_type, base_duration, level):
        self.name = name
        self.loc_id = loc_id
        self.action_type = action_type
        self.base_duration = base_duration
        self.level = level
        self.nodes = dict()

    def list_of_nodes(self):
        return self.nodes.keys()


class Node:
    def __init__(self, node_id, frequency, max_frequency, minimum_base_amount, maximum_base_amount, tags):
        self.node_id = node_id
        self.frequency = frequency
        self.max_frequency = max_frequency
        self.minimum_base_amount = minimum_base_amount
        self.maximum_base_amount = maximum_base_amount
        self.tags = tags
        self.loot = dict()

    def list_of_loot(self):
        return self.loot.keys()


class NodeLoot:
    def __init__(self, idd, frequency, max_frequency, min_amount, max_amount, item_class):
        self.id = idd
        self.frequency = frequency
        self.max_frequency = max_frequency
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.item_class = item_class


def find_required_level(df):
    try:
        return df["accessRequirements"]["requiredSkills"][0]["level"]
    except:
        print(f'Could not find req. level in {df["name"]}')
        return 0


def select_action_locations(datafile, item_data, action_type):
    locations = None
    with open(datafile) as j:
        locations = json.load(j)
    results = dict()
    for (k, v) in locations.items():
        if v['actionType'] == action_type:
            loc_name = v.get("name", "")
            loc_id = v.get("locID", 0)
            loc_duration = v.get("baseDuration", 0)
            loc_level = find_required_level(v)
            this_location = Location(loc_name, loc_id, action_type, loc_duration, loc_level)
            node_list = v.get("nodes", [{"nodeID": "",
                                         "frequency": 1,
                                         "minimumBaseAmount": 1,
                                         "loot": v.get("loot", [])}])
            for node in node_list:
                node_id = node.get("nodeID", "")
                node_frequency = node.get("frequency", 1)
                node_max_freq = node.get("maxFrequency", node_frequency)
                node_min_base = node.get("minimumBaseAmount", 1)
                node_max_base = node.get("maximumBaseAmount", node_min_base)
                node_tags = node.get("tags", [])
                this_node = Node(node_id, node_frequency, node_max_freq, node_min_base, node_max_base, node_tags)
                for loot in node["loot"]:
                    loot_id = loot.get("id", 0)
                    loot_freq = loot.get("frequency", 1)
                    loot_max_freq = loot.get("maxFrequency", loot_freq)
                    loot_min_amount = loot.get("minAmount", 1)
                    loot_max_amount = loot.get("maxAmount", loot_min_amount)
                    item_class = item_data[str(loot_id)].get("class", "")
                    this_loot = NodeLoot(loot_id, loot_freq, loot_max_freq, loot_min_amount, loot_max_amount, item_class)
                    this_node.loot[loot["id"]] = this_loot
                this_location.nodes[node["nodeID"]] = this_node
            results[v['name']] = this_location
    return results
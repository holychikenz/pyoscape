import numpy as np
from copy import copy, deepcopy


class Sequencer:
    """
    Simulate a leveling curve with events occurring throughout.
    Example: Mining
        - {'level': 5, 'mining_bonus': 10, 'info': 'bronze tool'}
        - {'level': 20, 'mining_bonus': 20, 'info': 'iron tool'}
        - {'level': 40, 'mining_bonus': 30, 'info': 'mithril tool'}
        - {'level': 60, 'mining_bonus': 40, 'info': 'adamantite tool'}
        - {'level': 80, 'mining_bonus': 50, 'info': 'runite tool'}
        - {'level': 100, 'mining_bonus': 60, 'info': 'stygian tool'}
        - {'hours': 900, 'mining_bonus': 10, 'info': 'stygian tool'}
    Sequence triggers can be of set('level', 'hours', ...)
    """

    def __init__(self, action, **kwargs):
        self.player = action.player
        self.action = action
        self.action_type = action.get_action_primary_attribute()
        self.sequence_list = kwargs.get('sequence', [])
        self.level_sequencer = []
        self.hour_sequencer = []
        for seq in self.sequence_list:
            if 'level' in seq:
                self.level_sequencer.append(seq)
            elif 'hours' in seq:
                self.hour_sequencer.append(seq)
        self.level_sequencer = sorted(self.level_sequencer, key=lambda x: x['level'])
        self.hour_sequencer = sorted(self.hour_sequencer, key=lambda x: x['hours'])

    def simulate_by_time(self, time_axis, **kwargs):
        level_axis = []
        custom_xp = kwargs.get('custom_xp', False)
        xp_gen = ExperienceTable() if custom_xp else RSExperienceTable()
        action_clone = copy(self.action)
        player_clone = deepcopy(self.player)
        action_clone.player = player_clone
        hour_sequencer = copy(self.hour_sequencer)
        level_sequencer = copy(self.level_sequencer)
        delta_t = time_axis[1] - time_axis[0]
        experience_rate = []
        sequence_log = []
        total_experience = 0
        for timer in time_axis:
            # Gain experience and level up
            current_experience_rate = action_clone.get_maximum_experience() * delta_t
            experience_rate.append(current_experience_rate / delta_t)
            total_experience += current_experience_rate
            current_level = xp_gen.level(total_experience)
            setattr(player_clone, self.action_type, current_level)
            level_axis.append(current_level)
            # Check sequencer for events
            for hour_sequence in hour_sequencer:
                if hour_sequence['hours'] <= timer:
                    for (k, v) in hour_sequence.items():
                        if (k != 'hours') and (k != 'info'):
                            if 'enchantments' in k:
                                subkey = k.split(':')[-1]
                                player_clone.enchantments[subkey] = max(player_clone.enchantments.get(subkey, 0), v)
                            else:
                                setattr(player_clone, k, max(getattr(player_clone, k), v))
            for level_sequence in level_sequencer:
                if level_sequence['level'] <= current_level:
                    for (k, v) in level_sequence.items():
                        if (k != 'level') and (k != 'info'):
                            if 'enchantments' in k:
                                subkey = k.split(':')[-1]
                                player_clone.enchantments[subkey] = max(player_clone.enchantments.get(subkey, 0), v)
                            else:
                                setattr(player_clone, k, max(getattr(player_clone, k), v))
        level_axis = np.array(level_axis)
        experience_rate = np.array(experience_rate)
        return level_axis, experience_rate, sequence_log


class ExperienceTable:
    """
    Generate the RS xp table
    """

    def __init__(self):
        self.levels = np.arange(1, 200, 1)
        self.total_xp = np.floor(
            50e3 * (self.levels - 1 + ((self.levels - 1) / 10) ** 2 + np.heaviside(self.levels - 101, 0) * (
                    (self.levels - 101) / 2) ** 3))

    def experience(self, level):
        return self.total_xp[level == self.levels][0]

    def level(self, experience):
        return self.levels[experience >= self.total_xp][-1]


class RSExperienceTable:
    """
    Generate the RS xp table
    """

    def __init__(self):
        self.levels = np.arange(1, 200, 1)
        self.delta = np.roll(0.25 * np.floor((self.levels - 1 + 300 * 2 ** ((self.levels - 1) / 7))), 1)
        self.delta[0] = 0
        self.total_xp = np.floor(np.cumsum(self.delta))

    def experience(self, level):
        return self.total_xp[level == self.levels][0]

    def level(self, experience):
        return self.levels[experience >= self.total_xp][-1]

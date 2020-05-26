from typing import Mapping

class IntentionDefinition:
    def __init__(self, is_unique: bool, is_required: bool):
        self.is_unique = is_unique
        self.is_required = is_required


class IntentionAlreadyAssignedError(Exception):
    def __init__(self, intention_name: str, source_entry: 'IntentionCollection', current_value: object, desired_value: object):
        self.intention_name = intention_name
        self.source_entry = source_entry
        self.current_value = current_value
        self.desired_value = desired_value


class IntentionCollection:
    def __init__(self, intentions_def_map: Mapping[str, object]):
        self._intentions = {}
        self._intentions_def_map = intentions_def_map
        # Create keys for each intention in this entry.
        for prop in self._intentions_def_map.keys():
            self._intentions[prop] = None

    @classmethod
    def copy_construct_from(cls, rhs: 'IntentionCollection') -> 'IntentionCollection':
        new_intentions = cls(rhs._intentions_def_map)
        for prop_name in rhs._intentions_def_map:
            val = rhs.get_intention(prop_name)
            if val is not None:
                new_intentions.attempt_set_intention(prop_name, val)
        return new_intentions

    def get_intention(self, intention_name: str) -> object:
        return self._intentions[intention_name]

    def attempt_set_intention(self, intention_name: str, desired_value: object):
        current_value = self._intentions[intention_name]
        if desired_value is None or desired_value == current_value:
            return False
        if current_value is not None:
            raise IntentionAlreadyAssignedError(intention_name, self, current_value, desired_value)
        else:
            self._intentions[intention_name] = desired_value
            return True

    def is_complete(self) -> bool:
        # Are *all* required intentions fulfilled?
        for name, prop_def in self._intentions_def_map:
            if prop_def.is_required:
                if self._intentions[name] is None:
                    # We can short circuit on the first empty required intention.
                    return False
        return True
        

from typing import Mapping

class PropertyDefinition:
    def __init__(self, is_unique: bool, is_required: bool):
        self.is_unique = is_unique
        self.is_required = is_required


class PropertyAlreadyAssignedError(Exception):
    def __init__(self, property_name: str, source_entry: 'PropertyCollection', current_value: object, desired_value: object):
        self.property_name = property_name
        self.source_entry = source_entry
        self.current_value = current_value
        self.desired_value = desired_value


class PropertyCollection:
    def __init__(self, properties_def_map: Mapping[str, object]):
        self._properties = {}
        self._properties_def_map = properties_def_map
        # Create keys for each property in this entry.
        for prop in self._properties_def_map.keys():
            self._properties[prop] = None

    @classmethod
    def copy_construct_from(cls, rhs: 'PropertyCollection') -> 'PropertyCollection':
        new_properties = cls(rhs._properties_def_map)
        for prop_name in rhs._properties_def_map:
            val = rhs.get_property(prop_name)
            if val is not None:
                new_properties.attempt_set_property(prop_name, val)
        return new_properties

    def get_property(self, property_name: str) -> object:
        return self._properties[property_name]

    def attempt_set_property(self, property_name: str, desired_value: object):
        current_value = self._properties[property_name]
        if desired_value is None or desired_value == current_value:
            return False
        if current_value is not None:
            raise PropertyAlreadyAssignedError(property_name, self, current_value, desired_value)
        else:
            self._properties[property_name] = desired_value
            return True

    def is_complete(self) -> bool:
        # Are *all* required properties fulfilled?
        for name, prop_def in self._properties_def_map:
            if prop_def.is_required:
                if self._properties[name] is None:
                    # We can short circuit on the first empty required property.
                    return False
        return True
        

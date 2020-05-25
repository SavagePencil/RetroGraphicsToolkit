from typing import List, Mapping, Optional
from enum import IntFlag
from Property import PropertyCollection, PropertyDefinition
from IndexedColorArray import IndexedColorArray

class Pattern(PropertyCollection):
    class InvalidFlipEnumerationError(Exception):
        def __init__(self, invalid_enum):
            self.invalid_enum = invalid_enum


    class Flip(IntFlag):
        NONE = 0
        HORIZ = 1
        VERT = 2
        HORIZ_VERT = HORIZ | VERT


    # Static Vars
    PROPERTY_FLIPS_ALLOWED = "Flips Allowed"

    PROPERTY_SPECIFIC_PATTERN_SET_INDEX = "Pattern Set Index"

    sProperty_def_map = {
          PROPERTY_FLIPS_ALLOWED: PropertyDefinition(is_unique=False, is_required=True)
        , PROPERTY_SPECIFIC_PATTERN_SET_INDEX: PropertyDefinition(is_unique=False, is_required=False)
    }

    def __init__(self, index_array: IndexedColorArray, initial_properties_map: Mapping[str, object]):
        super().__init__(Pattern.sProperty_def_map)

        # Set the initial properties
        for initial_prop_name, initial_prop_val in initial_properties_map.items():
            self.attempt_set_property(initial_prop_name, initial_prop_val)

        self.index_array = index_array

        # Create the hash for each orientation supported.  This will let
        # us detect if a given pattern matches another, and which orientation
        # it requires.
        self._flip_to_hash = [None] * len(list(Pattern.Flip))

        # We always allow no flip.
        self._flip_to_hash[Pattern.Flip.NONE] = self._calculate_hash_for_flip(Pattern.Flip.NONE)

        # Now see which flips are permitted and calculate hashes for those.
        flips = self.get_property(Pattern.PROPERTY_FLIPS_ALLOWED)
        if flips & Pattern.Flip.HORIZ == Pattern.Flip.HORIZ:
            self._flip_to_hash[Pattern.Flip.HORIZ] = self._calculate_hash_for_flip(Pattern.Flip.HORIZ)
        if flips & Pattern.Flip.VERT == Pattern.Flip.VERT:
            self._flip_to_hash[Pattern.Flip.VERT] = self._calculate_hash_for_flip(Pattern.Flip.VERT)
        if flips & Pattern.Flip.HORIZ_VERT == Pattern.Flip.HORIZ_VERT:
            self._flip_to_hash[Pattern.Flip.HORIZ_VERT] = self._calculate_hash_for_flip(Pattern.Flip.HORIZ_VERT)


    def get_hash_for_flip(self, flip: 'Pattern.Flip') -> Optional[int]:
        return self._flip_to_hash[flip]

    def create_index_array_for_flip(self, flip: 'Pattern.Flip') -> IndexedColorArray:
        range_params_x = None
        range_params_y = None
        if flip == Pattern.Flip.NONE:
            range_params_x = (0, self.index_array.width, 1)
            range_params_y = (0, self.index_array.height, 1)
        elif flip == Pattern.Flip.HORIZ:
            range_params_x = (self.index_array.width - 1, -1, -1)
            range_params_y = (0, self.index_array.height, 1)
        elif flip == Pattern.Flip.VERT:
            range_params_x = (0, self.index_array.width, 1)
            range_params_y = (self.index_array.height - 1, -1, -1)
        elif flip == Pattern.Flip.HORIZ_VERT:
            range_params_x = (self.index_array.width - 1, -1, -1)
            range_params_y = (self.index_array.height - 1, -1, -1)
        else:
            raise Pattern.InvalidFlipEnumerationError(flip)

        new_indexed_array = []
        value_to_index = {}

        # Walk through the pixel array according to the flip direction.
        # We'll create a map of pixels -> unique indices, along with
        # an array of the indexed image.
        for y in range(range_params_y[0], range_params_y[1], range_params_y[2]):
            for x in range(range_params_x[0], range_params_x[1], range_params_x[2]):
                value = self.index_array.get_value(x, y)

                idx = 0
                if value in value_to_index:
                    # Already seen it.  Get the index for it.
                    idx = value_to_index[value]
                else:
                    # This is a new, unique color.  
                    # Add it *IN THE DETERMINISTIC ORDER IT WAS DISCOVERED*.
                    idx = len(value_to_index.values())
                    value_to_index[value] = idx

                # Append the unique color index.
                new_indexed_array.append(idx)

        # Create the object version.
        ret_val = IndexedColorArray(self.index_array.width, self.index_array.height, new_indexed_array)
        return ret_val

    # Calculate the hash value for a given flip orientation.
    def _calculate_hash_for_flip(self, flip: 'Pattern.Flip') -> int:
        index_array = self.create_index_array_for_flip(flip)
        hash_val = hash(tuple(index_array.array))
        return hash_val
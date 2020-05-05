from ColorEntry import ColorEntry
from BitSet import BitSet

class Palette:
    def __init__(self, num_slots):
        self.colors = []
        while num_slots > 0:
            self.colors.append(ColorEntry())
            num_slots = num_slots - 1

    def get_flattened_palette(self):
        # Start blank
        ret_pal = [None] * len(self.colors)

        # Assume all slots are unassigned to begin with
        unassigned_bitset = BitSet(len(self.colors))
        unassigned_bitset.set_all()

        # Find those with slots and assign them first.
        unassigned_colors = []
        for color in self.colors:
            slot = color.properties.get_property(ColorEntry.PROPERTY_SLOT)
            if slot is not None:
                ret_pal[slot] = ColorEntry.copy_construct_from(color)
                unassigned_bitset.clear_bit(slot)
            else:
                unassigned_colors.append(color)
        
        # Now pick slots for the unassigned colors
        curr_unassigned_idx = unassigned_bitset.get_next_set_bit_index(0)
        while len(unassigned_colors) > 0:
            color = unassigned_colors.pop()
            ret_pal[curr_unassigned_idx] = ColorEntry.copy_construct_from(color)

            # Find the next open slot.
            curr_unassigned_idx = unassigned_bitset.get_next_set_bit_index(curr_unassigned_idx + 1)

        return ret_pal
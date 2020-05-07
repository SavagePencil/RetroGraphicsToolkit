from ColorEntry import ColorEntry
from BitSet import BitSet

class Palette:
    def __init__(self, num_slots):
        self.colors = []
        while num_slots > 0:
            self.colors.append(ColorEntry())
            num_slots = num_slots - 1

    def get_remap_from_colors_to_flattened_palette(self):
        # Assume all slots are unassigned to begin with
        unassigned_bitset = BitSet(len(self.colors))
        unassigned_bitset.set_all()

        # Track which original color remapped to which index.
        remap_indices = [None] * len(self.colors)

        # Find those with slots and assign them first.
        unassigned_color_indices = []
        for color_idx in range(len(self.colors)):
            color = self.colors[color_idx]
            slot = color.properties.get_property(ColorEntry.PROPERTY_SLOT)
            if slot is None:
                # No fixed slot.  But is there anything in it?
                if color.is_empty() == False:
                    # Something in it.  Flag it as unassigned.
                    unassigned_color_indices.append(color_idx)
            else:
                # It's a color with a fixed slot, so assign it now.
                unassigned_bitset.clear_bit(slot)
                remap_indices[color_idx] = slot
        
        # Now pick slots for the unassigned colors
        curr_unassigned_idx = unassigned_bitset.get_next_set_bit_index(0)
        while len(unassigned_color_indices) > 0:
            color_idx = unassigned_color_indices.pop()
            remap_indices[color_idx] = curr_unassigned_idx

            # Find the next open slot.
            curr_unassigned_idx = unassigned_bitset.get_next_set_bit_index(curr_unassigned_idx + 1)

        return remap_indices

    def get_flattened_palette_from_remap(self, remap_indices):
        # Start blank
        ret_pal = [ColorEntry()] * len(self.colors)

        for src_idx in range(len(remap_indices)):
            dest_idx = remap_indices[src_idx]
            if dest_idx is not None:
                src_color = self.colors[src_idx]
                ret_pal[dest_idx] = ColorEntry.copy_construct_from(src_color)

        return ret_pal

    def get_flattened_palette(self):
        remap_indices = self.get_remap_from_colors_to_flattened_palette()

        return self.get_flattened_palette_from_remap(remap_indices)
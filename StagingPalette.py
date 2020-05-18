from typing import Mapping
from ColorEntry import ColorEntry
from BitSet import BitSet

# The staging palette holds ColorEntries, which have properties that determine
# which pixel values will end up in which slot when transformed into a final
# palette.
class StagingPalette:
    def __init__(self, num_slots: int):
        self.color_entries = []
        while num_slots > 0:
            self.color_entries.append(ColorEntry())
            num_slots = num_slots - 1

    def create_final_palette_mapping(self) -> Mapping[int, int]:
        # This returns a mapping of color entry indices to
        # final palette indices.  We need to do this because
        # the color entries aren't in any particular order, but
        # the final palette requires a specific order.
        # For example, color entry #2 may specify a slot value
        # of 7.  In this case, there would be a mapping of 2 : 7.

        # Start with all color entries unassigned.
        unassigned_source_bitset = BitSet(len(self.color_entries))
        unassigned_source_bitset.set_all()

        # Start with all final palette slots unassigned.
        unassigned_dest_bitset = BitSet(len(self.color_entries))
        unassigned_dest_bitset.set_all()

        color_entry_index_to_final_slot_map = {}

        # Find any that have a specific slot and map them first.
        for color_entry_index in range(len(self.color_entries)):
            color_entry = self.color_entries[color_entry_index]

            if color_entry.is_empty():
                # Don't care about colors that are empty.
                unassigned_source_bitset.clear_bit(color_entry_index)
            else:
                # See if this has a slot.
                slot = color_entry.properties.get_property(ColorEntry.PROPERTY_SLOT)
                if slot is not None:
                    # Map to this slot.
                    color_entry_index_to_final_slot_map[color_entry_index] = slot

                    # This entry has been assigned.
                    unassigned_source_bitset.clear_bit(color_entry_index)

                    # The destination slot has been assigned.
                    unassigned_dest_bitset.clear_bit(color_entry_index)

        # Let's go back through any that are unassigned in the source list.
        unassigned_source_idx = unassigned_source_bitset.get_next_set_bit_index(0)
        unassigned_dest_idx = unassigned_dest_bitset.get_next_set_bit_index(0)
        while unassigned_source_idx is not None:
            color_entry_index_to_final_slot_map[unassigned_source_idx] = unassigned_dest_idx

            # Clear currents
            unassigned_source_bitset.clear_bit(unassigned_source_idx)
            unassigned_dest_bitset.clear_bit(unassigned_dest_idx)

            # Advance
            unassigned_source_idx = unassigned_source_bitset.get_next_set_bit_index(unassigned_source_idx + 1)
            unassigned_dest_idx = unassigned_dest_bitset.get_next_set_bit_index(unassigned_dest_idx + 1)

        return color_entry_index_to_final_slot_map
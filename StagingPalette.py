from ColorEntry import ColorEntry
from BitSet import BitSet

# The staging palette holds ColorEntries, which have properties that determine
# which pixel values will end up in which slot when transformed into a final
# palette.
class StagingPalette:
    def __init__(self, num_slots):
        self.color_entries = []
        while num_slots > 0:
            self.color_entries.append(ColorEntry())
            num_slots = num_slots - 1

    def create_final_palette_mapping(self):
        # This returns a mapping of color entry indices to
        # final palette indices.  We need to do this because
        # the color entries aren't in any particular order, but
        # the final palette requires a specific order.
        # For example, color entry #2 may specify a slot value
        # of 7.  In this case, there would be a mapping of 2 : 7.

        # Start with all color entries unassigned.
        unassigned_bitset = BitSet(len(self.color_entries))
        unassigned_bitset.set_all()

        # Start with all final palette slots unassigned.
        unassigned_slot_bitset = BitSet(len(self.color_entries))
        unassigned_slot_bitset.set_all()

        color_entry_index_to_final_slot_map = {}

        # Find any that have a specific slot and map them first.
        for color_entry_index in range(len(self.color_entries)):
            color_entry = self.color_entries[color_entry_index]
            slot = color_entry.properties.get_property(ColorEntry.PROPERTY_SLOT)
            if slot is not None:
                # Map to this slot.
                color_entry_index_to_final_slot_map[color_entry_index] = slot

                # This entry has been assigned.
                unassigned_bitset.clear_bit(color_entry_index)

                # The destination slot has been assigned.
                unassigned_slot_bitset
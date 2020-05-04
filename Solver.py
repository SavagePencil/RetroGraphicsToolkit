from ColorEntry import ColorEntry
from Tile import Tile
from FSM import FSM, State

class Move:
    def __init__(self, tile, palette, reason):
        self.tile = tile
        self.palette = palette
        self.reason = reason


class PaletteWIPState:
    def __init__(self, src_palette, slot_array, unassigned_color_entries_set):
        self.src_palette = src_palette

        # Do a deep copy of the slot array
        self.slot_array = []
        for slot_idx in range(len(src_palette.slots)):
            color_entry = slot_array[slot_idx]
            self.slot_array.append(color_entry)

        # Do a deep copy of the unassigned colors.
        self.unassigned_color_entries_set = set()
        for color_entry in unassigned_color_entries_set:
            self.unassigned_color_entries_set.add(color_entry)

    def get_num_available(self):
        free_slots = len(self.src_palette.slots)

        # Count any assigned slots.
        for slot_idx in range(len(self.slot_array)):
            color_entry = self.slot_array[slot_idx]
            if color_entry is not None:
                free_slots = free_slots - 1

        # Now any committed--but unassigned!--slots.
        free_slots = free_slots - len(self.unassigned_color_entries_set)

    def can_merge_into_palette(self, test_entry):
        # Test against assigned (slot) colors.
        for entry in self.slot_array:
            if entry is not None:
                if PaletteWIPState.can_merge(entry, test_entry):
                    return True

        # Test against the unassigned colors.
        for entry in self.unassigned_color_entries_set:
            if entry is not None:
                if PaletteWIPState.can_merge(entry, test_entry):
                    return True

        return False

    def get_mergeable_set(self, color_entry_set_to_test):
        ret_val = set()
        for test_entry in color_entry_set_to_test:
            if self.can_merge_into_palette(test_entry):
                ret_val.add(test_entry)
        
        return ret_val

    def attempt_merge_into_palette(self, color_entry):
        # Does this new entry have a slot assigned?
        slot_idx = color_entry.properties.get_property(ColorEntry.PROPERTY_SLOT)
        if slot_idx is not None:
            # Make sure it's in range.
            if slot_idx < 0 or slot_idx >= len(self.slot_array):
                # TODO make an exception
                raise Exception()

            existing_entry = self.slot_array[slot_idx]
            
            # Does one already exist?
            if existing_entry is not None:
                # See if they'll merge.
                if False == PaletteWIPState.can_merge(existing_entry, color_entry):
                    # TODO make an exception
                    raise Exception()
                # Otherwise, assume they're merged.
                # TODO:  do some sort of OR with old and new?
            else:
                # No pre-existing value; add it in.
                # TODO:  Check that this fits.
                self.slot_array[slot_idx] = color_entry
        else:
            # No slot specified, so see if it will match one of the un-assigned entries.
            matched_existing = None
            for existing_entry in self.unassigned_color_entries_set:
                if PaletteWIPState.can_merge(existing_entry, color_entry):
                    matched_existing = existing_entry
                    break

            # Did we match anybody?
            if matched_existing is None:
                # Add it.
                # TODO:  Check that this fits.
                self.unassigned_color_entries_set.add(color_entry)

    @staticmethod
    def can_merge(color_entry_a, color_entry_b):
        # Colors will merge unless both entries have values specified that don't match.
        color_a = color_entry_a.properties.get_property(ColorEntry.PROPERTY_COLOR)
        color_b = color_entry_b.properties.get_property(ColorEntry.PROPERTY_COLOR)
        if color_a is not None and color_b is not None and color_a != color_b:
            return False
        
        # Names will merge if both entries have the same value.
        # TODO:  Add ability for named colors to be non-exclusive.
        name_a = color_entry_a.properties.get_property(ColorEntry.PROPERTY_NAME)
        name_b = color_entry_b.properties.get_property(ColorEntry.PROPERTY_NAME)
        if name_a != name_b:
            return False

        # Slots will merge unless both entries have values specified that don't match.
        slot_a = color_entry_a.properties.get_property(ColorEntry.PROPERTY_SLOT)
        slot_b = color_entry_b.properties.get_property(ColorEntry.PROPERTY_SLOT)
        if slot_a is not None and slot_b is not None and slot_a != slot_b:
            return False

        # Otherwise, we're good.
        return True


class SolverInstance:
    def __init__(self, uncommitted_tile_set, committed_tile_to_palette_map, palette_states, move_history):
        # Do a deep copy of the uncommitted tiles
        self.uncommitted_tile_set = set()
        for tile in uncommitted_tile_set:
            self.uncommitted_tile_set.add(tile)

        # Do a deep copy of the comitted tiles and the palette they're mapped to
        self.committed_tile_to_palette_map = {}
        for tile, palette in committed_tile_to_palette_map:
            self.committed_tile_to_palette_map[tile] = palette

        # Create new palette states from the previous (these do a deep copy)
        self.palette_states_map = {}
        for palette, palette_state in palette_states:
            slot_array = palette_state.slot_array
            unassigned_color_entries_set = palette_state.unassigned_color_entries_set

            new_palette_state = PaletteWIPState(palette, slot_array, unassigned_color_entries_set)
            self.palette_states_map[palette] = new_palette_state

        # Deep copy the move history.
        self.move_history = []
        for move in move_history:
            tile = move.tile
            palette = move.palette
            reason = move.reason
            new_move = Move(tile, palette, reason)
            self.move_history.append(new_move)

        # What moves have we got queued up?
        self.move_queue = []

        self._fsm = FSM(self)
        self._fsm.start(FindCommitments)

    def add_move(self, move):
        self.move_queue.append(move)

    def commit_tile_to_palette(self, tile, palette):
        # Remove from the uncommitted set.
        self.uncommitted_tile_set.remove(tile)

        # Add to the commitments.
        self.committed_tile_to_palette_map[tile] = palette


class FindCommitments(State):
    @staticmethod
    def on_update(context):
        # Iterate through all uncommitted tiles and see if any
        # have a palette ID specified.
        for tile in context.uncommitted_tile_set:
            dest_palette = tile.properties.get_property(Tile.PROPERTY_PALETTE)
            if dest_palette is not None:
                move = Move(tile, dest_palette, "Tile Committed to Palette at Solver Start")
                context.add_move(move)

        return SolverProcess


class SolverProcess(State):
    @staticmethod
    def on_update(context):
        # If we're out of uncommitted tiles, that means we're done!
        if len(context.uncommitted_tile_state) == 0:
            return Success
        
        # If we have moves in the queue, do them.
        if len(context.move_queue) > 0:
            return ExecuteMoves

        # No moves in the queue, so make an assessment of where to go.
        return Assessment


class Success(State):
    pass

class Failure(State):
    pass

class ExecuteMoves(State):
    @staticmethod
    def on_update(context):
        # If we're out of moves, go back to the Solver.
        if len(context.move_queue) == 0:
            return SolverProcess

        # Take the first move from the queue.
        move = context.move_queue.popleft()

        tile = move.tile
        palette = move.palette

        # Assign the palette property to the tile.
        tile.properties.attempt_set_property(Tile.PROPERTY_PALETTE, palette)

        working_palette_set = context.palette_states_map[palette]

        # Now assign all of the colors to the palette.
        entries = tile.color_map.get_entries()

        for entry in entries:
            working_palette_set.attempt_merge_into_palette(entry)

        # TODO:  Catch errors and move to failure.

        # Make it committed.
        context.commit_tile_to_palette(tile, palette)

        # Stay in this state.
        return None


class Assessment(State):
    pass

class MakeDecision(State):
    pass
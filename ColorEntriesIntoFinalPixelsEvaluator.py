import math
from constraint_solver import ConstraintSolver, Evaluator, Move
from ColorEntry import ColorEntry
from FinalPalette import FinalPixel

class ColorEntriesIntoFinalPixelsEvaluator(Evaluator):
    # Static Vars

    # Color Entries with a slot specified take precedence
    SCORE_ADJUST_HAS_SLOT = -1000000

    # Higher numbered destination slots go later than lower ones
    SCORE_ADJUST_PER_DESTINATION_INDEX = 1000

    class PotentialMove:
        def __init__(self, move, base_score):
            self.move = move
            self.base_score = base_score

    class ChangeList:
        def __init__(self, property_name_list):
            self.property_name_list = property_name_list

    @classmethod
    def factory_constructor(cls, source_index, source):
        return ColorEntriesIntoFinalPixelsEvaluator(source_index, source)

    def __init__(self, source_index, source):
        super().__init__(source_index, source)

        # Create a map of destination indices to potential moves.
        # For this situation (color to color), there aren't multiple possible
        # moves for each mapping:  we either fit or we don't.
        self._destination_to_potential_move = {}

    def get_list_of_best_moves(self):
        best_score = math.inf
        best_moves = []

        # Assess the score based on conditions
        for potential_move in self._destination_to_potential_move.values():
            # Make sure this is actually a move, and not a "None" telling us
            # that we can't move to that destination.
            if potential_move is not None:
                score = potential_move.base_score

                # Adjust the base score on situation

                # Higher destination indices get a worse score so that we fill up earlier slots sooner (aesthetics!)
                penalty = potential_move.move.dest_index * ColorEntriesIntoFinalPixelsEvaluator.SCORE_ADJUST_PER_DESTINATION_INDEX
                score = score + penalty

                if score < best_score:
                    best_score = score
                    best_moves.clear()
                    best_moves.append(potential_move.move)
                elif score == best_score:
                    best_moves.append(potential_move.move)

        return (best_score, best_moves)

    def update_moves_for_destination(self, destination_index, destination):
        # If we have a "None" move list for this destination, that's because 
        # we've already determined that we can't make a move into it.  
        # We are operating under the assertion that "if I couldn't move into 
        # it before, I can't move into it now."
        if (destination_index in self._destination_to_potential_move) and (self._destination_to_potential_move[destination_index] is None):
            return

        # Otherwise, we either haven't seen the move before or we're about to update our existing one.
        # In either event, start by assuming we won't get this to fit.
        self._destination_to_potential_move[destination_index] = None

        change_list = self._get_changes_to_fit(destination_index, destination)

        if change_list is not None:
            # We can make a move!
            move = Move(self.source_index, destination_index, change_list)

            # Get score based on changes
            score = self._get_score_for_move(move)

            potential_move = ColorEntriesIntoFinalPixelsEvaluator.PotentialMove(move, score)
            self._destination_to_potential_move[destination_index] = potential_move

    @staticmethod
    def apply_changes(source, destination, change_list):
        # We may only care about a subset of properties to apply
        for prop_name_change in change_list:
            if prop_name_change == ColorEntry.PROPERTY_COLOR:
                pixel_value = source.properties.get_property(prop_name_change)
                destination.attempt_write_pixel_value(pixel_value)

    @staticmethod
    def is_destination_empty(destination_index, destination):
        # Returns True if the FinalPixel has nothing set.
        return destination.get_pixel_value() is None

    def _get_changes_to_fit(self, destination, destination_index):
        changes = []

        # Test color
        dest_pixel = destination.get_pixel_value()

        # Cases:
        # 1. Dest is Something:  Not OK to move in
        # 2. Dest is None:  OK to move in 
        if dest_pixel is not None:
            # Nope!
            return None

        change = ColorEntry.PROPERTY_COLOR
        changes.append(change)

        # Test slot
        src_slot = self.source.properties.get_property(ColorEntry.PROPERTY_SLOT)
        dest_slot = destination_index

        # Cases:
        # 1. Source has a Slot specified:  Only if it matches the destination's slot
        # 2. Source has no Slot specified:  All good.
        if src_slot is not None:
            # Case 1
            if src_slot != dest_slot:
                # Nope!
                return None
            else:
                change = ColorEntry.PROPERTY_SLOT
                changes.append(change)
            
        return ColorEntriesIntoFinalPixelsEvaluator.ChangeList(changes)

    def _get_score_for_move(self, move):
        score = 0

        # Tally score for changes.
        for prop_name_change in move.change_list:
            # Moves that require a slot change get a better score so that they take priority
            if prop_name_change == ColorEntry.PROPERTY_SLOT:
                score = score + ColorEntriesIntoFinalPixelsEvaluator.SCORE_ADJUST_HAS_SLOT

        return score
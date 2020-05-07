import math
from ColorEntry import ColorEntry
from constraint_solver import Evaluator, Move

class ColorsIntoColorsEvaluator(Evaluator):
    # Static vars
    COST_ADD_COLOR = 1
    COST_ADD_SLOT = 100
    COST_ADD_NAME = 1000

    s_change_to_cost_map = {
        ColorEntry.PROPERTY_COLOR : COST_ADD_COLOR
        , ColorEntry.PROPERTY_SLOT : COST_ADD_SLOT
        , ColorEntry.PROPERTY_NAME : COST_ADD_NAME
    }

    SCORE_ADJUST_ONLY_ONE_MOVE = -10000
    SCORE_ADJUST_FREE_MOVE = -math.inf

    class PotentialMove:
        def __init__(self, move, base_score):
            self.move = move
            self.base_score = base_score

    class ChangeList:
        def __init__(self, property_name_value_tuple_list):
            self.property_name_value_tuple_list = property_name_value_tuple_list

    @classmethod
    def factory_constructor(cls, source_index, source):
        return ColorsIntoColorsEvaluator(source_index, source)

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
        # If we only have one move, increase the value
        num_moves = 0
        for potential_move in self._destination_to_potential_move.values():
            if potential_move is not None:
                num_moves = num_moves + 1

        only_one_move = (num_moves == 1)

        for potential_move in self._destination_to_potential_move.values():
            # Make sure this is actually a move, and not a "None" telling us
            # that we can't move to that destination.
            if potential_move is not None:
                score = potential_move.base_score

                # Check for special conditions.
                # Is this our only move?
                if only_one_move == True:
                    score = score + ColorsIntoColorsEvaluator.SCORE_ADJUST_ONLY_ONE_MOVE

                # Are there no changes to make this move?
                if len(potential_move.move.change_list.property_name_value_tuple_list) == 0:
                    # It's free!
                    score = score + ColorsIntoColorsEvaluator.SCORE_ADJUST_FREE_MOVE

                if potential_move.base_score < best_score:
                    best_score = score
                    best_moves.clear()
                    best_moves.append(potential_move.move)
                elif potential_move.base_score == best_score:
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

        change_list = self._get_changes_to_fit(destination)

        if change_list is not None:
            # We can make a move!
            move = Move(self.source_index, destination_index, change_list)

            # Get score based on changes
            score = ColorsIntoColorsEvaluator._get_score_for_changes(change_list)

            potential_move = ColorsIntoColorsEvaluator.PotentialMove(move, score)
            self._destination_to_potential_move[destination_index] = potential_move

    @staticmethod
    def apply_changes(source, destination, change_list):
        for property_name_value_tuple in change_list.property_name_value_tuple_list:
            # Each change is a tuple of property name and params.
            prop_name = property_name_value_tuple[0]

            # Get the value from the source and apply it to the dest.
            src_val = source.properties.get_property(prop_name)
            destination.properties.attempt_set_property(prop_name, src_val)

    @staticmethod
    def is_destination_empty(destination):
        # Returns True if the ColorEntry has nothing set.
        return destination.is_empty()

    def _get_changes_to_fit(self, destination):
        changes = []

        # Test color
        src_color = self.source.properties.get_property(ColorEntry.PROPERTY_COLOR)
        dest_color = destination.properties.get_property(ColorEntry.PROPERTY_COLOR)

        # Cases:
        # 1. Both None:  OK to match, no changes
        # 2. Src is None, Dest is Something:  OK to match, no changes
        # 3. Src is Something, Dest is None:  OK to match, requires change
        # 4. Src is Something, Dest is Something:  Only OK to match if both values are the same.
        if src_color is not None:
            if dest_color is None:
                # Case 3
                change = (ColorEntry.PROPERTY_COLOR, src_color)
                changes.append(change)
            else:
                # Case 4
                if src_color != dest_color:
                    # FAIL
                    return None

        # Test slot
        src_slot = self.source.properties.get_property(ColorEntry.PROPERTY_SLOT)
        dest_slot = destination.properties.get_property(ColorEntry.PROPERTY_SLOT)

        # Cases:
        # 1. Both None:  OK to match, no changes
        # 2. Src is None, Dest is Something:  OK to match, no changes
        # 3. Src is Something, Dest is None:  OK to match, requires change
        # 4. Src is Something, Dest is Something:  Only OK to match if both values are the same.
        if src_slot is not None:
            if dest_slot is None:
                # Case 3
                change = (ColorEntry.PROPERTY_SLOT, src_slot)
                changes.append(change)
            else:
                # Case 4
                if src_slot != dest_slot:
                    # FAIL
                    return None

        # Test name
        src_name = self.source.properties.get_property(ColorEntry.PROPERTY_NAME)
        dest_name = destination.properties.get_property(ColorEntry.PROPERTY_NAME)

        # Cases:
        # 1. Both None:  OK to match, no changes
        # 2. Src is None, Dest is Something:  DO NOT match; names are unique.
        # 3. Src is Something, Dest is None:  Only OK to match if dest is empty for ALL OTHER fields.
        # 4. Src is Something, Dest is Something:  Only OK to match if both values are the same.
        if src_name is None:
            if dest_name is not None:
                # Case 2
                # FAIL
                return None
        else:
            if dest_name is None:
                # Case 3
                if dest_slot is not None or dest_color is not None:
                    # FAIL
                    return None
                else:
                    change = (ColorEntry.PROPERTY_NAME, src_name)
                    changes.append(change)
            else:
                # Case 4
                if src_name != dest_name:
                    # FAIL
                    return None

        return ColorsIntoColorsEvaluator.ChangeList(changes)

    @staticmethod
    def _get_score_for_changes(change_list):
        score = 0

        if len(change_list.property_name_value_tuple_list) == 0:
            # No changes means it's free.
            return -math.inf

        # Pay a cost for each move
        for change in change_list.property_name_value_tuple_list:
            # Each change is a tuple of property name and params.
            change_key = change[0]
            cost = ColorsIntoColorsEvaluator.s_change_to_cost_map[change_key]
            score = score + cost

        return score
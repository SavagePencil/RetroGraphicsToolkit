import math
from typing import List, Tuple, Mapping, Optional
from constraint_solver import ConstraintSolver, Evaluator, Move
from Pattern import Pattern

class PatternsIntoPatternHashMapsEvaluator(Evaluator):
    # Static Vars
    # We take patterns which have fewer flip options 
    # before those with more options.
    SCORE_PENALTY_PER_FLIP_OPTION = 10

    # We prefer not to add a new pattern when 
    # we could match an existing one.
    SCORE_PENALTY_ADD_NEW_PATTERN = 10000

    # We prefer not flipping patterns when possible.
    SCORE_ADJUST_NO_FLIPPING = -1

    # Matches are "free"
    SCORE_ADJUST_FREE_MOVE = -math.inf

    class PotentialMove:
        def __init__(self, move: Move, base_score: int):
            self.move = move
            self.base_score = base_score

    class ChangeList:
        def __init__(self, matched_pattern_idx: int, flips_to_match: Pattern.Flip):
            # Who did we match, and which flips were necessary?

            # If we were added to a map, instead of matching an existing one,
            # this will be None.
            self.matched_pattern_idx = matched_pattern_idx
            self.flips_to_match = flips_to_match

    @classmethod
    def factory_constructor(cls, source_index: int, source: Pattern) -> 'PatternsIntoPatternHashMapsEvaluator':
        return PatternsIntoPatternHashMapsEvaluator(source_index, source)

    def __init__(self, source_index: int, source: Pattern):
        super().__init__(source_index, source)

        # Create a map of destinations to possible moves.
        # This isn't 1:1, as there can be multiple ways for a
        # pattern to be moved into a given map.
        self._destination_to_potential_move_list = {}

    def get_list_of_best_moves(self) -> Tuple[int, List[Move]]:
        best_score = math.inf
        best_moves = []

        # Assess the score based on conditions
        # If we only have one move, increase the value
        num_moves = 0
        for potential_move_list in self._destination_to_potential_move_list.values():
            if potential_move_list is not None:
                for potential_move in potential_move_list:
                    num_moves = num_moves + 1

        only_one_move = (num_moves == 1)

        # Iterate through all potential moves.
        for potential_move_list in self._destination_to_potential_move_list.values():
            if potential_move_list is not None:
                for potential_move in potential_move_list:
                    score = potential_move.base_score

                    # Check for special conditions.
                    change_list = potential_move.move.change_list

                    # If we matched somebody, and we only have one move, take it!
                    if only_one_move and (change_list.matched_pattern_idx is not None):
                        # We matched somebody, and no other choices...it's free!
                        score = score + PatternsIntoPatternHashMapsEvaluator.SCORE_ADJUST_FREE_MOVE

                    if score < best_score:
                        best_score = score
                        best_moves.clear()
                        best_moves.append(potential_move.move)
                    elif score == best_score:
                        best_moves.append(potential_move.move)

        return (best_score, best_moves)

    def update_moves_for_destination(self, destination_index: int, destination: Mapping[int, Tuple[int, Pattern.Flip]]):
        # If we have a "None" move list for this destination, that's because 
        # we've already determined that we can't make a move into it.  
        # We are operating under the assertion that "if I couldn't move into 
        # it before, I can't move into it now."
        if (destination_index in self._destination_to_potential_move_list) and (self._destination_to_potential_move_list[destination_index] is None):
            return

        # Otherwise, we either haven't seen the move before or we're about to update our existing one.
        # In either event, start by assuming we won't get this to fit.
        self._destination_to_potential_move_list[destination_index] = None

        change_lists = self._get_changes_to_fit(destination_index, destination)
        if (change_lists is not None) and (len(change_lists) > 0):
            # We can make moves!
            potential_move_list = []
            for change_list in change_lists:
                move = Move(self.source_index, destination_index, change_list)

                score = PatternsIntoPatternHashMapsEvaluator._get_score_for_changes(change_list)

                potential_move = PatternsIntoPatternHashMapsEvaluator.PotentialMove(move, score)
                potential_move_list.append(potential_move)

            self._destination_to_potential_move_list[destination_index] = potential_move_list

    @staticmethod
    def apply_changes(source: Pattern, destination: Mapping[int, Tuple[int, Pattern.Flip]], change_list: 'PatternsIntoPatternHashMapsEvaluator.ChangeList'):
        
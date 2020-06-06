import math
from typing import List, Tuple, Optional
from rgtk.constraint_solver import ConstraintSolver, Evaluator, Move
from rgtk.BitSet import BitSet

class SubsetsToBitSetsEvaluator(Evaluator):
    # Static Vars
    SCORE_ADJUST_PER_BIT_CONTRIBUTED = -1

    class PotentialMove:
        def __init__(self, move: Move, base_score: int):
            self.move = move
            self.base_score = base_score

    class ChangeList:
        def __init__(self, changed_bits: BitSet):
            self.changed_bits = changed_bits

    @classmethod
    def factory_constructor(cls, source_index: int, source: BitSet) -> 'SubsetsToBitSetsEvaluator':
        return SubsetsToBitSetsEvaluator(source_index, source)

    def __init__(self, source_index: int, source: BitSet):
        super().__init__(source_index, source)

        # Create a map of destinations to possible moves.
        # Unlike some solvers, there's only one way to fit a
        # subset into a BitSet, so it isn't a list.
        self._destination_to_potential_move = {}

    def get_list_of_best_moves(self) -> Tuple[int, List[Move]]:
        best_score = math.inf
        best_moves = []

        # Iterate through all potential moves.
        for potential_move in self._destination_to_potential_move.values():
            if potential_move is not None:
                score = potential_move.base_score

                if score < best_score:
                    best_score = score
                    best_moves.clear()
                    best_moves.append(potential_move.move)
                elif score == best_score:
                    best_moves.append(potential_move.move)

        return (best_score, best_moves)

    def update_moves_for_destination(self, destination_index: int, destination: BitSet):
        # If we have a "None" for this destination, that's because 
        # we've already determined that we can't make a move into it.  
        # We are operating under the assertion that "if I couldn't move into 
        # it before, I can't move into it now."
        if (destination_index in self._destination_to_potential_move) and (self._destination_to_potential_move[destination_index] is None):
            return

        # Otherwise, we either haven't seen the move before or we're about to update our existing one.
        # In either event, start by assuming we won't get this to fit.
        self._destination_to_potential_move[destination_index] = None

        change_list = self._get_changes_to_fit(destination)

        if (change_list is not None):
            # We can make a move!
            move = Move(self.source_index, destination_index, change_list)

            score = self._get_score_for_changes(change_list, destination)

            potential_move = SubsetsToBitSetsEvaluator.PotentialMove(move, score)

            self._destination_to_potential_move[destination_index] = potential_move

    @staticmethod
    def apply_changes(source: BitSet, destination: BitSet, change_list: 'SubsetsToBitSetsEvaluator.ChangeList'):
        destination.union_with(change_list.changed_bits)

    @staticmethod
    def is_destination_empty(destination: BitSet) -> bool:
        # Our output set is always discrete.
        return False

    def _get_changes_to_fit(self, destination: BitSet):
        # Identify how many bits differ
        changed = self.source.get_difference_bitset(destination)

        # Mask this with the source
        changed.intersect_with(self.source)

        # Even if there is no overlap whatsoever, 
        # flag this as a valid move so that we can get rid of it.
        return SubsetsToBitSetsEvaluator.ChangeList(changed)

    def _get_score_for_changes(self, change_list: 'SubsetsToBitSetsEvaluator.ChangeList', destination: BitSet) -> int:
        if change_list.changed_bits.are_all_clear():
            # If there are no changes, this is "free" and we can get rid of it.
            return -math.inf

        score = 0

        # Give a bonus based on how many bits this contributes.
        score += change_list.changed_bits.get_num_bits_set() * SubsetsToBitSetsEvaluator.SCORE_ADJUST_PER_BIT_CONTRIBUTED

        return score
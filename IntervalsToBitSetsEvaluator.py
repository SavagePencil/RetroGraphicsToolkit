import math
from typing import List, Tuple, Optional
from constraint_solver import ConstraintSolver, Evaluator, Move
from Interval import Interval
from BitSet import BitSet

class IntervalsToBitSetsEvaluator(Evaluator):
    # Static Vars

    # Larger intervals will get a better score.
    SCORE_ADJUST_PER_INTERVAL_ITEM = -10

    # Those with the fewest possible destinations get a better score
    # so that they are prioritized.
    # This is different than how we use moves.  Example:
    # Let's say we have interval 111 that we're workig into BitSet 000001.
    # 000001
    # 111     <- 1st possible destination
    #  111    <- 2nd
    #   111   <- 3rd
    SCORE_PER_POSSIBLE_DESTINATION = 10000

    class PotentialMove:
        def __init__(self, move: Move, base_score: int):
            self.move = move
            self.base_score = base_score

    # Our change list is, itself, a valid interval that this interval
    # can fit within.  For example, let's say we are trying to fit
    # something that is 3 items wide, and have this BitSet:
    # 1000001 <- BitSet
    # ABCDEFG <- Bit Indices
    # Our 3-item-wide interval can fit in the range B->F.
    class ChangeList:
        def __init__(self, possible_interval:Interval):
            self.possible_interval = possible_interval

    @classmethod
    def factory_constructor(cls, source_index: int, source: Interval) -> 'IntervalsToBitSetsEvaluator':
        return IntervalsToBitSetsEvaluator(source_index, source)

    def __init__(self, source_index: int, source: Interval):
        super().__init__(source_index, source)

        # Create a map of destinations to possible moves.
        # This isn't 1:1, as there can be multiple ways for 
        # an interval to be moved into a given palette.
        self._destination_to_potential_move_list = {}

    def get_list_of_best_moves(self) -> Tuple[int, List[Move]]:
        best_score = math.inf
        best_moves = []

        # Iterate through all potential moves.
        for potential_move_list in self._destination_to_potential_move_list.values():
            if potential_move_list is not None:
                for potential_move in potential_move_list:
                    score = potential_move.base_score

                    # TODO Check for special conditions.

                    if score < best_score:
                        best_score = score
                        best_moves.clear()
                        best_moves.append(potential_move.move)
                    elif score == best_score:
                        best_moves.append(potential_move.move)

        return (best_score, best_moves)


    def update_moves_for_destination(self, destination_index: int, destination: BitSet):
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

                score = IntervalsToBitSetsEvaluator._get_score_for_changes(self.source, change_list)

                potential_move = IntervalsToBitSetsEvaluator.PotentialMove(move, score)
                potential_move_list.append(potential_move)

            self._destination_to_potential_move_list[destination_index] = potential_move_list

    @staticmethod
    def apply_changes(source: Interval, destination: BitSet, change_list: 'IntervalsToBitSetsEvaluator.ChangeList'):
        # Apply our changes, which is a run of bits to set, 
        # starting at the BEGINNING of the interval in our change list.
        start_bit_idx = change_list.possible_interval.slot_range[0]

        # We run until the end of our SOURCE'S length, 
        # which may be smaller than the interval we're in.
        end_bit_idx = start_bit_idx + source.length
        for bit_idx in range(start_bit_idx, end_bit_idx):
            destination.set_bit(bit_idx)

    @staticmethod
    def is_destination_empty(destination: BitSet) -> bool:
        return destination.are_all_clear()

    def _get_changes_to_fit(self, destination_index: int, destination: BitSet) -> Optional[List['IntervalsToBitSetsEvaluator.ChangeList']]:
        change_lists = []

        # Find the intervals where our source Interval can fit.
        # e.g., if our Interval were a length of 3, and our BitSet looked like this:
        # 00100001000  <- BitSet
        # ABCDEFGHIJK  <- Bit Pos
        # ChangeLists = [(D->G), (I->K)]
        range_start_idx = self.source.slot_range[0]
        range_end_idx = self.source.slot_range[1]

        source_len = self.source.length

        # We'll start at the range's beginning, and stop when we either go off the BitSet or hit the end range.
        curr_clear_bit_idx = destination.get_next_unset_bit_index(range_start_idx)
        while (curr_clear_bit_idx is not None) and (curr_clear_bit_idx <= range_end_idx):
            # We are on a zero.  Find the next one value, which will bound our search.
            next_set_bit_idx = destination.get_next_set_bit_index(curr_clear_bit_idx)
            if next_set_bit_idx is None:
                # If we ran off the edge, set the bound at the last value.
                next_set_bit_idx = destination.get_num_bits()
            
            if next_set_bit_idx > range_end_idx:
                # Make it bound to our top end of the range.
                next_set_bit_idx = range_end_idx + 1
            
            # How many zeroes do we have?
            zeroes_left = next_set_bit_idx - curr_clear_bit_idx

            if zeroes_left > source_len:
                valid_interval = Interval((curr_clear_bit_idx, next_set_bit_idx - 1), zeroes_left)
                change_lists.append(IntervalsToBitSetsEvaluator.ChangeList(valid_interval))

            # Find the next zero AFTER our one.
            curr_clear_bit_idx = destination.get_next_unset_bit_index(next_set_bit_idx)

        return change_lists

    @staticmethod
    def _get_score_for_changes(source: Interval, change_list: 'IntervalsToBitSetsEvaluator.ChangeList') -> int:
        score = 0

        # Larger intervals will get a better score so that they get prioritized.
        score += source.length * IntervalsToBitSetsEvaluator.SCORE_ADJUST_PER_INTERVAL_ITEM

        # Those with the fewest possible destinations get a better score
        # so that they are prioritized.
        # This is different than how we use moves.  Example:
        # Let's say we have interval 111 that we're workig into BitSet 000001.
        # 000001
        # 111     <- 1st possible destination
        #  111    <- 2nd
        #   111   <- 3rd
        if change_list is not None:
            interval_len = source.length
            num_destinations = change_list.possible_interval.length - interval_len
            score += num_destinations * IntervalsToBitSetsEvaluator.SCORE_PER_POSSIBLE_DESTINATION
        

        return score
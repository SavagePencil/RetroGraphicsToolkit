import math
from typing import List, Tuple, Optional
from rgtk.constraint_solver import ConstraintSolver, Evaluator, Move
from rgtk.Interval import Interval
from rgtk.BitSet import BitSet

class IntervalsToBitSetsEvaluator(Evaluator):
    # Static Vars

    # Larger intervals will get a better score.
    SCORE_ADJUST_PER_INTERVAL_ITEM = -100

    # Those with the fewest possible destinations get a better score
    # so that they are prioritized.  Put another way:  we penalize
    # intervals that have a lot of possible destinations.
    # This is different than how we use moves.  Example:
    # Let's say we have interval 111 that we're workig into BitSet 000001.
    # 000001
    # 111     <- 1st possible destination
    #  111    <- 2nd
    #   111   <- 3rd
    SCORE_PER_POSSIBLE_DESTINATION = 100000

    # Those leaving larger fragmentation blocks are prioritized so
    # that larger intervals can be fitted in later, rather than have
    # a bunch of tiny fragments.
    SCORE_PER_FRAGMENT_SIZE = -1

    class PotentialMove:
        def __init__(self, move: Move, base_score: int, smallest_fragment: int, largest_fragment: int):
            self.move = move
            self.base_score = base_score

            # The Potential Move holds the fragment details for scoring.
            # These aren't germane to the moves themselves, so we keep them here.
            self.smallest_fragment = smallest_fragment
            self.largest_fragment = largest_fragment

    class ChangeList:
        def __init__(self, possible_interval: Interval, chosen_interval: Interval):
            self.possible_interval = possible_interval
            self.chosen_interval = chosen_interval

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

                    # Those leaving larger fragments are prioritized over those that leave smaller ones.
                    # This is mostly to pick a winner within a given interval's choices.
                    largest_fragment = potential_move.largest_fragment
                    score += largest_fragment * IntervalsToBitSetsEvaluator.SCORE_PER_FRAGMENT_SIZE

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

        change_lists_fragment_infos = self._get_changes_to_fit(destination_index, destination)
        change_lists = change_lists_fragment_infos[0]
        fragment_infos = change_lists_fragment_infos[1]

        if (change_lists is not None) and (len(change_lists) > 0):
            # We can make moves!
            potential_move_list = []
            for change_list_idx in range(len(change_lists)):
                change_list = change_lists[change_list_idx]
                fragment_info = fragment_infos[change_list_idx]

                move = Move(self.source_index, destination_index, change_list)

                score = IntervalsToBitSetsEvaluator._get_score_for_changes(self.source, change_list)

                smallest_fragment = fragment_info[0]
                largest_fragment = fragment_info[1]

                potential_move = IntervalsToBitSetsEvaluator.PotentialMove(move, score, smallest_fragment, largest_fragment)
                potential_move_list.append(potential_move)

            self._destination_to_potential_move_list[destination_index] = potential_move_list

    @staticmethod
    def apply_changes(source: Interval, destination: BitSet, change_list: 'IntervalsToBitSetsEvaluator.ChangeList'):
        # Apply our changes, which is a run of bits to set.
        for bit_idx in range(change_list.chosen_interval.begin, change_list.chosen_interval.end + 1):
            destination.set_bit(bit_idx)

    @staticmethod
    def is_destination_empty(destination: BitSet) -> bool:
        return destination.are_all_clear()

    def _get_changes_to_fit(self, destination_index: int, destination: BitSet) -> Tuple[List['IntervalsToBitSetsEvaluator.ChangeList'], List[Tuple[int, int]]]:
        change_lists = []
        fragment_infos = []

        # Find the intervals where our source Interval can fit.
        # e.g., if our Interval were a length of 3, and our BitSet looked like this:
        # 00100001000  <- BitSet
        # ABCDEFGHIJK  <- Bit Pos
        # ChangeLists = [(D->G), (I->K)]
        range_start_idx = self.source.begin
        range_end_idx = self.source.end

        source_len = self.source.length

        # We'll start at the range's beginning, and stop when we either go off the BitSet or hit the end range.
        curr_clear_bit_idx = destination.get_next_unset_bit_index(range_start_idx)
        while (curr_clear_bit_idx is not None) and (curr_clear_bit_idx <= range_end_idx):
            # We are on a zero within the begin..end range of our source's interval.

            # Find the next one value, which will bound our search.
            next_set_bit_idx = destination.get_next_set_bit_index(curr_clear_bit_idx)
            if next_set_bit_idx is None:
                # If we ran off the edge, set the bound at the last value.
                next_set_bit_idx = destination.get_num_bits()
            
            if next_set_bit_idx > range_end_idx:
                # Make it bound to our top end of the range.
                next_set_bit_idx = range_end_idx + 1
            
            # How big is this new interval?
            possible_interval = Interval.create_from_fixed_range(curr_clear_bit_idx, next_set_bit_idx - 1)
            if possible_interval.length >= source_len:
                # Our interval will fit within this one.  Now pick an interval *within* the possible
                # that fits our source and introduces the least fragmentation.
                change_list_fragment_info = self._get_best_change_list_for_possible_interval(possible_interval, destination)
                change_list = change_list_fragment_info[0]
                fragment_info = change_list_fragment_info[1]
                change_lists.append(change_list)
                fragment_infos.append(fragment_info)

            # Find the next zero AFTER our one.
            curr_clear_bit_idx = destination.get_next_unset_bit_index(next_set_bit_idx)

        return (change_lists, fragment_infos)

    def _get_best_change_list_for_possible_interval(self, possible_interval: Interval, destination: BitSet) -> Tuple['IntervalsToBitSetsEvaluator.ChangeList', Tuple[int, int]]:
        # Figure out where the best place within the possible interval
        # to assign ourselves.  We want the source block to be 
        # positioned as close as possible to another block to 
        # minimize fragmentation.
        # Example 1:  
        #   Our block consists of BBB
        #   We have the following BitSet:
        #     0011000000000
        #         ^^^^^^    <- Possible interval
        #   BAD:
        #     00110BBB00000
        #     001100BBB0000
        #     0011000BBB000
        #         ^^^^^^
        #   BEST:
        #     0011BBB000000 <- No fragmentation introduced
        # 
        # Example 2:
        #   Our block constists of BBB
        #   We have the following BitSet:
        #     1100000000000
        #         ^^^^^     <- Possible interval
        #
        #   No perfect choice here.  Default to minimizing known
        #   fragmentation:
        #     1100BBB000000
        #         ^^^^^     <- Only introduced a 2-spot fragment

        # 10000001
        # 01234567
        #   ^^^    Potential Interval (2->4)
        # Bits to Left:  1, Bits to Right:  2

        # Look to the left of the BEGINNING of our interval.
        left_set_bit_idx = destination.get_previous_set_bit_index(possible_interval.begin)
        num_bits_to_left = 0
        if left_set_bit_idx is not None:
            num_bits_to_left = possible_interval.begin - left_set_bit_idx - 1

        # Look to the right of the END of our interval.
        right_set_bit_idx = destination.get_next_set_bit_index(possible_interval.end)
        num_bits_to_right = destination.get_num_bits() - possible_interval.end - 1
        if right_set_bit_idx is not None:
            num_bits_to_right = right_set_bit_idx - possible_interval.end - 1

        if num_bits_to_left <= num_bits_to_right:
            # We choose to the left.
            chosen_interval = Interval.create_fixed_length_at_start_point(possible_interval.begin, self.source.length)

            # Smallest is the distance from our left edge to the nearest 1.
            smallest_fragment = num_bits_to_left
            # Largest is the distance from the right edge of the possible interval
            # PLUS the difference between our possible and source lengths.
            largest_fragment = num_bits_to_right + (possible_interval.length - self.source.length)

            # Return a tuple of (change list, (smallest, largest))
            # We do this because we don't want the change list to hold fragment details
            # (since those will change after subsequent moves), but we don't want to have
            # to recalculate the fragments separately.
            return (IntervalsToBitSetsEvaluator.ChangeList(possible_interval, chosen_interval), (smallest_fragment, largest_fragment))
        else:
            # Go to the right edge.
            chosen_interval = Interval.create_fixed_length_from_end_point(possible_interval.end, self.source.length)

            # Smallest is the distance from our right edge to the nearest 1.
            smallest_fragment = num_bits_to_right
            # Largest is the distance from the left edge of the possible interval
            # PLUS the difference between our possible and source lengths.
            largest_fragment = num_bits_to_left + (possible_interval.length - self.source.length)

            # Return a tuple of (change list, (smallest, largest))
            # We do this because we don't want the change list to hold fragment details
            # (since those will change after subsequent moves), but we don't want to have
            # to recalculate the fragments separately.
            return (IntervalsToBitSetsEvaluator.ChangeList(possible_interval, chosen_interval), (smallest_fragment, largest_fragment))


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
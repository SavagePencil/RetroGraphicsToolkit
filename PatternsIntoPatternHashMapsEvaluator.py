import math
from typing import List, Tuple, Mapping, Optional
from constraint_solver import ConstraintSolver, Evaluator, Move
from Pattern import Pattern

class PatternsIntoPatternHashMapsEvaluator(Evaluator):
    # Static Vars
    # We take patterns which have fewer hash/flip options 
    # before those with more options.
    SCORE_PENALTY_PER_UNIQUE_HASH_OPTION = 10

    # We prefer not to add a new pattern when 
    # we could match an existing one.
    SCORE_PENALTY_ADD_NEW_PATTERN = 10000

    # We prefer not flipping patterns when possible.
    SCORE_ADJUST_NO_FLIPPING = -1

    # When we only have one move, those are "free"
    SCORE_ADJUST_FREE_MOVE = -math.inf

    class PotentialMove:
        def __init__(self, move: Move, base_score: int):
            self.move = move
            self.base_score = base_score

    class ChangeList:
        def __init__(self, source_pattern_idx: int, matches_existing_entry: bool, flips_to_match: Pattern.Flip):
            # Who is getting mapped?
            self.source_pattern_idx = source_pattern_idx

            # Record whether this is MATCHES an existing entry or if we're ADDING it.
            self.matches_existing_entry = matches_existing_entry

            # Which flips were necessary to match?
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

                score = self._get_score_for_changes(change_list)

                potential_move = PatternsIntoPatternHashMapsEvaluator.PotentialMove(move, score)
                potential_move_list.append(potential_move)

            self._destination_to_potential_move_list[destination_index] = potential_move_list

    @staticmethod
    def apply_changes(source: Pattern, destination: Mapping[int, Tuple[int, Pattern.Flip]], change_list: 'PatternsIntoPatternHashMapsEvaluator.ChangeList'):
        # What we want to do is look at the change list and determine one of two things:
        # 1. Whether we are ADDING a new pattern to the map
        # 2. Whether we are MATCHING a pattern to an existing one, and which flips are required

        # What's the index of the source pattern?
        source_pattern_idx = change_list.source_pattern_idx

        # Get the hash for the flips identified in the change list.
        flip = change_list.flips_to_match
        hash_val = source.get_hash_for_flip(flip)

        # Do we have an entry in the map for that hash?
        if hash_val in destination:
            # Append this pattern to the list.
            match_list = destination[hash_val]
            match_list.append((source_pattern_idx, flip))
        else:
            # Our destination map doesn't have this one...yet.
            # Create a new list for it.
            match_list = [(source_pattern_idx, flip)]
            destination[hash_val] = match_list

    @staticmethod
    def is_destination_empty(destination: Mapping[int, Tuple[int, Pattern.Flip]]) -> bool:
        # Maps are always instantiated.
        return False

    def _get_changes_to_fit(self, destination_index: int, destination: Mapping[int, Tuple[int, Pattern.Flip]]) -> Optional[List['PatternsIntoPatternHashMapsEvaluator.ChangeList']]:
        # Make sure this pattern is allowed to go into this destination.
        assigned_pattern_set = self.source.get_property(Pattern.PROPERTY_SPECIFIC_PATTERN_SET_INDEX)
        if (assigned_pattern_set is not None) and (assigned_pattern_set != destination_index):
            # This pattern wants to be assigned to a specific pattern set, and it's not this one.
            return None
        
        change_lists = []

        # Look at each hash for this source and see if it matches anything currently in the map.
        for flip in list(Pattern.Flip):
            hash_val = self.source.get_hash_for_flip(flip)
            if hash_val is not None:
                # This is a valid flip for this pattern.
                # Have we seen it before?
                matches_existing_entry = hash_val in destination
                change_list = PatternsIntoPatternHashMapsEvaluator.ChangeList(source_pattern_idx=self.source_index, matches_existing_entry=matches_existing_entry, flips_to_match=flip)
                change_lists.append(change_list)

        return change_lists

    def _get_score_for_changes(self, change_list: 'PatternsIntoPatternHashMapsEvaluator.ChangeList') -> int:
        score = 0

        if change_list.matches_existing_entry == False:
            # We prefer not to add a new pattern when 
            # we could match an existing one.
            score += PatternsIntoPatternHashMapsEvaluator.SCORE_PENALTY_ADD_NEW_PATTERN

        # We prefer not flipping patterns when possible.
        if change_list.flips_to_match == Pattern.Flip.NONE:
            score += PatternsIntoPatternHashMapsEvaluator.SCORE_ADJUST_NO_FLIPPING

        # We take patterns which have fewer *UNIQUE* hashes 
        # before those with more options, so that they get prioritized.
        unique_hashes = set()
        for flip in list(Pattern.Flip):
            hash_val = self.source.get_hash_for_flip(flip)
            if hash_val is not None:
                unique_hashes.add(hash_val)
        score += len(unique_hashes) * PatternsIntoPatternHashMapsEvaluator.SCORE_PENALTY_PER_UNIQUE_HASH_OPTION

        return score
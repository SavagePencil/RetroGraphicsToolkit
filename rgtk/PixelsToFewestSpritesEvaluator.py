import math
from typing import List, Tuple, Optional
from rgtk.constraint_solver import ConstraintSolver, Evaluator, Move
from rgtk.BitSet import BitSet

class PixelsToFewestSpritesEvaluator(Evaluator):
    class Source:
        def __init__(self, pixel_to_potential_sprites_bitset: BitSet, pixel_adjacency_bitset: BitSet, sprite_pixel_coverages: List[BitSet]):
            # Which sprites *could* this pixel belong to?
            self.pixel_to_potential_sprites_bitset = pixel_to_potential_sprites_bitset

            # Which pixels is this pixel adjacent to?  They may be across multiple sprites.  That's OK.
            self.pixel_adjacency_bitset = pixel_adjacency_bitset

            # Which pixels do all of the sprites in the world cover?
            self.sprite_pixel_coverages = sprite_pixel_coverages

    class Destination:
        def __init__(self):
            self.sprite_index = None

    # Static Vars
    # Highly connected pixels get solved AFTER those with fewer connections.
    SCORE_PENALTY_PER_NEW_PIXEL_ADJACENCY = 10000

    # Prioritize sprites that contribute more pixels to the solution.
    SCORE_BONUS_PER_NEW_PIXEL_IN_SPRITE = -1

    class PotentialMove:
        def __init__(self, move: Move, base_score: int):
            self.move = move
            self.base_score = base_score

    class ChangeList:
        def __init__(self, dest_sprite_index: int, added_pixels_bitset: BitSet):
            # Which sprite got added as a result of this move?
            self.dest_sprite_index = dest_sprite_index

            # Which pixels got added as a result of this move?
            self.added_pixels_bitset = added_pixels_bitset

    @classmethod
    def factory_constructor(cls, source_index: int, source: 'PixelsToFewestSpritesEvaluator.Source') -> 'PixelsToFewestSpritesEvaluator':
        return PixelsToFewestSpritesEvaluator(source_index, source)

    def __init__(self, source_index: int, source: 'PixelsToFewestSpritesEvaluator.Source'):
        super().__init__(source_index, source)

        # Create a map of destinations to possible moves.
        # There may be multiple ways for a given pixel to be
        # moved to the same destination, so we keep a list
        # of moves.
        self._destination_to_potential_move_list = {}

        # We'll keep a running tally of which pixels we are still adjacent to,
        # starting with our initial set.  As sprites are chosen, they will
        # reduce which ones are still available.
        self._remaining_adjacent_pixels_bitset = BitSet.copy_construct_from(source.pixel_adjacency_bitset)

    def get_list_of_best_moves(self) -> Tuple[int, List[Move]]:
        best_score = math.inf
        best_moves = []

        # Iterate through all potential moves.
        for potential_move_list in self._destination_to_potential_move_list.values():
            if potential_move_list is not None:
                for potential_move in potential_move_list:
                    score = potential_move.base_score

                    if score < best_score:
                        best_score = score
                        best_moves.clear()
                        best_moves.append(potential_move.move)
                    elif score == best_score:
                        best_moves.append(potential_move.move)

        return (best_score, best_moves)

    def update_moves_for_destination(self, destination_index: int, destination: 'PixelsToFewestSpritesEvaluator.Destination'):
        # If we have a "None" for this destination, that's because 
        # we've already determined that we can't make a move into it.  
        # We are operating under the assertion that "if I couldn't move into 
        # it before, I can't move into it now."
        if (destination_index in self._destination_to_potential_move_list) and (self._destination_to_potential_move_list[destination_index] is None):
            return

        # Otherwise, we either haven't seen the move before or we're about to update our existing one.
        # In either event, start by assuming we won't get this to fit.
        self._destination_to_potential_move_list[destination_index] = None

        change_lists = None

        if destination.sprite_index is None:
            # This is an empty destination, so find the best sprite(s) to suggest.
            change_lists = self._get_changes_for_new_destination()
        else:
            # Before building change lists, we need to do two things:
            #   1. See if this sprite is at all relevant to us
            #   2. See if this sprite removed any of our adjacent pixels
            #      when it was committed.

            # Legit sprite.
            sprite_idx = destination.sprite_index

            # Do we have any connection to this sprite?
            if self.source.pixel_to_potential_sprites_bitset.is_set(sprite_idx):
                # Yes, this is a sprite that could be related to this pixel.

                # Which pixels does this sprite cover?
                coverage = self.source.sprite_pixel_coverages[sprite_idx]

                # Does this sprite already cover this pixel?
                if coverage.is_set(self.source_index):
                    # Yes, this is a free move for us.  No changes required.
                    change_lists = [None]
                else:
                    # See if this sprite took away any of our adjacencies.
                    changed = self.source.get_difference_bitset(coverage)

                    # Mask it with ourselves.
                    self._remaining_adjacent_pixels_bitset.intersect_with(changed)

                    # We won't be moving into it.

        if (change_lists is not None):
            # We can make at least one move!
            potential_move_list = []
            for change_list in change_lists:
                move = Move(self.source_index, destination_index, change_list)

                score = self._get_score_for_changes(change_list)

                potential_move = PixelsToFewestSpritesEvaluator.PotentialMove(move, score)
                potential_move_list.append(potential_move)

            self._destination_to_potential_move_list[destination_index] = potential_move_list

    @staticmethod
    def apply_changes(source: 'PixelsToFewestSpritesEvaluator.Source', destination: 'PixelsToFewestSpritesEvaluator.Destination', change_list: 'PixelsToFewestSpritesEvaluator.ChangeList'):
        if change_list is not None:
            destination.sprite_index = change_list.dest_sprite_index

    @staticmethod
    def is_destination_empty(destination: 'PixelsToFewestSpritesEvaluator.Destination') -> bool:
        # A destination is empty if it doesn't have a sprite index in it.
        return destination.sprite_index is None

    def _get_changes_for_new_destination(self) -> Optional[List['PixelsToFewestSpritesEvaluator.ChangeList']]:
        change_lists = []

        # The destination is empty.
        # Find out which sprite(s) would make the best move.
        sprite_idx = self.source.pixel_to_potential_sprites_bitset.get_next_set_bit_index(0)
        while sprite_idx is not None:
            # Which pixels does this sprite cover?
            coverage = self.source.sprite_pixel_coverages[sprite_idx]

            # How does that compare to what we're still adjacent to?
            intersect = self._remaining_adjacent_pixels_bitset.get_intersection_bitset(coverage)

            change_list = PixelsToFewestSpritesEvaluator.ChangeList(dest_sprite_index=sprite_idx, added_pixels_bitset=intersect)
            change_lists.append(change_list)

            sprite_idx = self.source.pixel_to_potential_sprites_bitset.get_next_set_bit_index(sprite_idx + 1)

        return change_lists

    def _get_score_for_changes(self, change_list: 'PixelsToFewestSpritesEvaluator.ChangeList') -> int:
        if change_list is None:
            # If there are no changes, this is "free" and we can get rid of it.
            return -math.inf

        score = 0

        # We are incentivized to take pixels with fewer adjacencies, so penalize those with
        # high degree.
        num_adjacencies = self._remaining_adjacent_pixels_bitset.get_num_bits_set()
        score += num_adjacencies * PixelsToFewestSpritesEvaluator.SCORE_PENALTY_PER_NEW_PIXEL_ADJACENCY

        # We want to choose sprites that bring in a lot of additional pixels with it.
        num_pixels_added = change_list.added_pixels_bitset.get_num_bits_set()
        score += num_pixels_added * PixelsToFewestSpritesEvaluator.SCORE_BONUS_PER_NEW_PIXEL_IN_SPRITE

        return score
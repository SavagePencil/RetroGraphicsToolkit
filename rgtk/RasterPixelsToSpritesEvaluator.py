import math
from typing import List, Tuple, Optional
from rgtk.constraint_solver import ConstraintSolver, Evaluator, Move
from rgtk.BitSet import BitSet

class RasterPixelsToSpritesEvaluator(Evaluator):
    class Source:
        def __init__(self, pixel_to_potential_sprites_bitset: BitSet, sprite_pixel_coverages: List[BitSet]):
            # Which sprites *could* this pixel belong to?
            self.pixel_to_potential_sprites_bitset = pixel_to_potential_sprites_bitset

            # Which pixels do all of the sprites in the world cover?
            self.sprite_pixel_coverages = sprite_pixel_coverages

    class PotentialMove:
        def __init__(self, move: Move, base_score: int):
            self.move = move
            self.base_score = base_score

    # Abstract base class that defines an interface for Change Lists in moves.
    class ChangeList:
        def __init__(self):
            pass

        def apply_changes(self, destination: BitSet):
            raise Exception("Not implemented in child class.")

    # Invalid change list used when it is not our source's turn.
    class InvalidSourceChangeList(ChangeList):
        def __init__(self):
            super().__init__()

        def apply_changes(self, destination: BitSet):
            raise Exception("Attempted to apply a move for a pixel that was not next in the raster order.")

    # Valid change list used when it *IS* our source's turn.
    class ValidChangeList(ChangeList):
        def __init__(self, dest_sprite_index: int, added_pixels_bitset: BitSet, overlapped_pixels_bitset: BitSet):
            super().__init__()

            # Which sprite got added as a result of this move?
            self.dest_sprite_index = dest_sprite_index

            # Which pixels got added as a result of this move?
            self.added_pixels_bitset = added_pixels_bitset

            # How many pixels was that?
            # This isn't used, as it was discovered that overlapping pixels was
            # a better heuristic for minimal sprite coverage.
            # self.num_pixels_added = added_pixels_bitset.get_num_bits_set()

            # How much does this overlap with previously covered pixels?
            self.overlapped_pixels_bitset = overlapped_pixels_bitset

            # How many pixels was that?
            self.num_pixels_overlapped = overlapped_pixels_bitset.get_num_bits_set()

        def apply_changes(self, destination):
            destination.union_with(self.added_pixels_bitset)


    @classmethod
    def factory_constructor(cls, source_index: int, source: 'RasterPixelsToSpritesEvaluator.Source') -> 'RasterPixelsToSpritesEvaluator':
        return RasterPixelsToSpritesEvaluator(source_index, source)

    def __init__(self, source_index: int, source: 'RasterPixelsToSpritesEvaluator.Source'):
        super().__init__(source_index, source)

        # Create a map of destinations to possible moves.
        # There may be multiple ways for a given pixel to be
        # moved to the same destination, so we keep a list
        # of moves.
        self._destination_to_potential_move_list = {}

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

    def update_moves_for_destination(self, destination_index: int, destination: BitSet):
        # We have three cases:
        # 1. The destination already contains us, in which case we issue a free move.
        # 2. We are NOT the next pixel up, so we issue a fake move that keeps us
        #    in the running until we are called up.
        # 3. We ARE the next pixel to solve for in the destination, in which case
        #    we create all of our possible moves
        if destination.is_set(self.source_index):
            # Case 1:  A previous move already covered this pixel.
            # We'll just move into the destination.
            # Create a move that is "free" and has no change list to worry about.
            move = Move(source_index=self.source_index, dest_index=destination_index, change_list=None)
            potential_move = RasterPixelsToSpritesEvaluator.PotentialMove(move=move, base_score=-math.inf)
            self._destination_to_potential_move_list[destination_index] = [potential_move]
        else:
            # Are we the next pixel in the queue?
            next_pixel_idx = destination.get_next_unset_bit_index(0)
            if next_pixel_idx != self.source_index:
                # Case 2:  We are NOT the next pixel up.  This will be the most common situation.
                # As a result, we'll create a dummy move the first time we hit this case and
                # then use that as our default move subsequently.
                if destination_index not in self._destination_to_potential_move_list:
                    # We need *a* move to signal to the constraint solver that we're not completely 
                    # at a dead end, so give a move that will raise an exception if it is attempted to be used.
                    invalid_change = RasterPixelsToSpritesEvaluator.InvalidSourceChangeList()
                    move = Move(source_index=self.source_index, dest_index=destination_index, change_list=invalid_change)
                    # Create a move with an awful score.
                    potential_move = RasterPixelsToSpritesEvaluator.PotentialMove(move=move, base_score=math.inf)
                    self._destination_to_potential_move_list[destination_index] = [potential_move]
            else:
                # Case 3:  We're up!
                # We'll submit *all* of our potential sprites as candidates,
                # with this in mind: 
                # All of our potential sprites start on the same raster line as we're on
                candidate_lists = []
                sprite_idx = self.source.pixel_to_potential_sprites_bitset.get_next_set_bit_index(0)
                while sprite_idx is not None:
                    # Record which bits got changed (these are the unique bits, which may be
                    # different than what our sprite originally covered due to previous moves
                    # overlapping).
                    sprite_coverage = self.source.sprite_pixel_coverages[sprite_idx]

                    overlap = sprite_coverage.get_intersection_bitset(destination)

                    changed = sprite_coverage.get_difference_bitset(destination)
                    changed.intersect_with(sprite_coverage)

                    change_list = RasterPixelsToSpritesEvaluator.ValidChangeList(dest_sprite_index=sprite_idx, added_pixels_bitset=changed, overlapped_pixels_bitset=overlap)
                    candidate_lists.append(change_list)

                    sprite_idx = self.source.pixel_to_potential_sprites_bitset.get_next_set_bit_index(sprite_idx + 1)

                # This may go against the spirit of the solver, but because we know that it uses a BFS approach
                # we want to put the change lists we think will have the most success FIRST in the list so that
                # they get explored before others.  We don't want to omit the other options, just prioritize those
                # with an heuristic.
                change_lists = []
                while len(candidate_lists) > 0:
                    best_pixels_idx = -1
                    best_pixels_value = math.inf
                    # Find the one matching the best heuristic.
                    for candidate_idx, candidate in enumerate(candidate_lists):
                        # HEURISTIC:  MOST PIXELS BEING ADDED
                        # In testing, this produced worse results than choosing
                        # sprites with the lowest overlap of already-chosen pixels.
                        #pixels_value = candidate.num_pixels_added
                        # HEURISTIC:  FEWEST OVERLAP
                        pixels_value = candidate.num_pixels_overlapped

                        if pixels_value < best_pixels_value:
                            best_pixels_value = pixels_value
                            best_pixels_idx = candidate_idx

                    change_lists.append(candidate_lists[best_pixels_idx])
                    candidate_lists.pop(best_pixels_idx)

                potential_moves = []
                for change_list in change_lists:
                    move = Move(source_index=self.source_index, dest_index=destination_index, change_list=change_list)
                    # Create a potential move with an equal score for all of these moves, so that they all get evaluated.
                    potential_move = RasterPixelsToSpritesEvaluator.PotentialMove(move=move, base_score=0)
                    potential_moves.append(potential_move)

                self._destination_to_potential_move_list[destination_index] = potential_moves

    @staticmethod
    def apply_changes(source: 'RasterPixelsToSpritesEvaluator.Source', destination: BitSet, change_list: 'RasterPixelsToSpritesEvaluator.ChangeList'):
        if change_list is not None:
            change_list.apply_changes(destination)

    @staticmethod
    def is_destination_empty(destination: BitSet) -> bool:
        # Our output is always discrete.  We're never empty.
        return False

    def _get_score_for_changes(self, change_list: 'RasterPixelsToSpritesEvaluator.ChangeList', destination: BitSet) -> int:
        score = 0

        if change_list is None:
            # If there are no changes, this is "free" and we can get rid of it.
            score = -math.inf
        else:
            # If we're the next pixel in the raster scan, give our moves a high priority.  Otherwise
            # push 'em off.
            next_pixel_idx = destination.get_next_unset_bit_index(0)
            if next_pixel_idx == self.source_index:
                # We're next up.  Keep 'em equal.
                score = 0
            else:
                # We're not next in the queue.  Don't do anything.
                score = math.inf

        return score
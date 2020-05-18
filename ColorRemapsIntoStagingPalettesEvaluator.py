import math
from typing import List, Tuple, Optional
from constraint_solver import ConstraintSolver, Evaluator, Move
from ColorsIntoColorsEvaluator import ColorsIntoColorsEvaluator
from ColorRemap import ColorRemap
from StagingPalette import StagingPalette

class ColorRemapsIntoStagingPalettesEvaluator(Evaluator):
    # Static Vars
    SCORE_ADJUST_ONLY_ONE_MOVE = -10000
    SCORE_ADJUST_FREE_MOVE = -math.inf
    SCORE_ADJUST_EACH_COLOR_IN_REMAP = -1
    SCORE_ADJUST_EACH_COLOR_MATCHING = -100

    class PotentialMove:
        def __init__(self, move: Move, base_score: int):
            self.move = move
            self.base_score = base_score

    class ChangeList:
        def __init__(self, color_into_color_moves: List[Move]):
            # We keep a list of moves for our color remap's colors into the dest palette.
            self.color_into_color_moves = color_into_color_moves

    @classmethod
    def factory_constructor(cls, source_index: int, source: ColorRemap) -> 'ColorRemapsIntoStagingPalettesEvaluator':
        return ColorRemapsIntoStagingPalettesEvaluator(source_index, source)

    def __init__(self, source_index: int, source: ColorRemap):
        super().__init__(source_index, source)

        # Create a map of destinations to possible moves.
        # This isn't 1:1, as there can be multiple ways for a
        # set of colors to be moved into a given palette.
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
                    # Is this our only move?
                    if only_one_move == True:
                        score = score + ColorRemapsIntoStagingPalettesEvaluator.SCORE_ADJUST_ONLY_ONE_MOVE

                    # Are there no changes to make this move?
                    if len(potential_move.move.change_list.color_into_color_moves) == 0:
                        # It's free!
                        score = score + ColorRemapsIntoStagingPalettesEvaluator.SCORE_ADJUST_FREE_MOVE

                    # How many colors are in our remap?
                    num_colors = len(self.source.color_entries)
                    score = score + (num_colors * ColorRemapsIntoStagingPalettesEvaluator.SCORE_ADJUST_EACH_COLOR_IN_REMAP)

                    if score < best_score:
                        best_score = score
                        best_moves.clear()
                        best_moves.append(potential_move.move)
                    elif score == best_score:
                        best_moves.append(potential_move.move)

        return (best_score, best_moves)

    def update_moves_for_destination(self, destination_index: int, destination: StagingPalette):
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

                score = ColorRemapsIntoStagingPalettesEvaluator._get_score_for_changes(change_list)

                potential_move = ColorRemapsIntoStagingPalettesEvaluator.PotentialMove(move, score)
                potential_move_list.append(potential_move)

            self._destination_to_potential_move_list[destination_index] = potential_move_list

    @staticmethod
    def apply_changes(source: ColorRemap, destination: StagingPalette, change_list: 'ColorRemapsIntoStagingPalettesEvaluator.ChangeList'):
        # This class doesn't apply any changes to the Palette object itself.

        # Apply our ColorsIntoColors changes, which is a list of Moves.
        for color_into_color_move in change_list.color_into_color_moves:
            src_color_idx = color_into_color_move.source_index
            src_color = source.color_entries[src_color_idx]

            dest_palette_color_idx = color_into_color_move.dest_index
            dest_palette_color = destination.color_entries[dest_palette_color_idx]

            color_into_color_change_list = color_into_color_move.change_list
            ColorsIntoColorsEvaluator.apply_changes(src_color, dest_palette_color, color_into_color_change_list)

    @staticmethod
    def is_destination_empty(destination: StagingPalette) -> bool:
        # Palettes are always instantiated.
        return False

    def _get_changes_to_fit(self, destination_index: int, destination: StagingPalette) -> Optional[List['ColorRemapsIntoStagingPalettesEvaluator.ChangeList']]:
        # Check this remap to see if it has a palette assigned.  If it does, does it match the destination?
        assigned_palette = self.source.get_property(ColorRemap.PROPERTY_PALETTE)
        if (assigned_palette is not None) and (assigned_palette != destination_index):
            # We have a remap that wants to be assigned to a specific palette, and it's not this one.
            return None

        # Take the colors in the source and execute a solver to map them to the palette's colors.
        palette_colors = destination.color_entries

        solver = ConstraintSolver(self.source.color_entries, palette_colors, ColorsIntoColorsEvaluator, None)
        while solver.is_exhausted() == False:
            solver.update()

        # Did we have any solutions?
        solutions = solver.solutions
        if len(solutions) == 0:
            # No solutions means we can't fit.
            return None
        
        change_lists = []
        # Each solution is a possible way to fit the remap into the palette
        for solution in solutions:
            # A solution is just a list of Moves.  Make each solution into its own ChangeList.
            change_list = ColorRemapsIntoStagingPalettesEvaluator.ChangeList(solution)
            change_lists.append(change_list)

        return change_lists

    @staticmethod
    def _get_score_for_changes(change_list: 'ColorRemapsIntoStagingPalettesEvaluator.ChangeList') -> int:
        score = 0

        # For every color that matches (i.e., no changes), add to the score
        for color_into_color_move in change_list.color_into_color_moves:
            # Go through each color-into-color move.
            property_name_value_tuple_list = color_into_color_move.change_list.property_name_value_tuple_list
            if len(property_name_value_tuple_list) == 0:
                score = score + ColorRemapsIntoStagingPalettesEvaluator.SCORE_ADJUST_EACH_COLOR_MATCHING

        return score
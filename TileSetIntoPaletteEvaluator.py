import math
from constraint_solver import ConstraintSolver, Evaluator, Move
from ColorsIntoColorsEvaluator import ColorsIntoColorsEvaluator
from Tile import Tile
from Palette import Palette

class TileSetIntoPaletteEvaluator(Evaluator):
    # Static Vars
    SCORE_ADJUST_ONLY_ONE_MOVE = -10000
    SCORE_ADJUST_FREE_MOVE = -math.inf
    SCORE_ADJUST_EACH_COLOR_IN_TILE = -1
    SCORE_ADJUST_EACH_COLOR_MATCHING = -100

    class PotentialMove:
        def __init__(self, move, base_score):
            self.move = move
            self.base_score = base_score

    @classmethod
    def factory_constructor(cls, source_index, source):
        return TileSetIntoPaletteEvaluator(source_index, source)

    def __init__(self, source_index, source):
        super().__init__(source_index, source)

        # Create a map of destinations to possible moves.
        # This isn't 1:1, as there can be multiple ways for a
        # tile to be moved into a given palette.
        self._destination_to_potential_move_list = {}

    def get_list_of_best_moves(self):
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
                        score = score + TileSetIntoPaletteEvaluator.SCORE_ADJUST_ONLY_ONE_MOVE

                    # Are there no changes to make this move?
                    if len(potential_move.move.change_list) == 0:
                        # It's free!
                        score = score + TileSetIntoPaletteEvaluator.SCORE_ADJUST_FREE_MOVE

                    # How many colors are in our tile?
                    num_colors = len(self.source.color_map.get_entries())
                    score = score + (num_colors * TileSetIntoPaletteEvaluator.SCORE_ADJUST_EACH_COLOR_IN_TILE)

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
        if (destination_index in self._destination_to_potential_move_list) and (self._destination_to_potential_move_list[destination_index] is None):
            return

        # Otherwise, we either haven't seen the move before or we're about to update our existing one.
        # In either event, start by assuming we won't get this to fit.
        self._destination_to_potential_move_list[destination_index] = None

        change_lists = self._get_changes_to_fit(destination)
        if (change_lists is not None) and (len(change_lists) > 0):
            # We can make moves!
            potential_move_list = []
            for change_list in change_lists:
                move = Move(self.source_index, destination_index, change_list)

                score = TileSetIntoPaletteEvaluator._get_score_for_changes(change_list)

                potential_move = TileSetIntoPaletteEvaluator.PotentialMove(move, score)
                potential_move_list.append(potential_move)

            self._destination_to_potential_move_list[destination_index] = potential_move_list

    def apply_changes(self, destination, change_list):
        # Our changes lists are (dest_palette_color_index, [list of (property, value)])
        for change in change_list:
            dest_palette_color_index = change[0]
            prop_val_list = change[1]

            dest_color = destination.colors[dest_palette_color_index]
            for prop_val_tuple in prop_val_list:
                prop_name = prop_val_tuple[0]
                prop_val = prop_val_tuple[1]
                dest_color.properties.attempt_set_property(prop_name, prop_val)

    def _get_changes_to_fit(self, destination):
        # Check this tile to see if it has a palette assigned.  If it does, does it match the destination?
        assigned_palette = self.source.properties.get_property(Tile.PROPERTY_PALETTE)
        if (assigned_palette is not None) and (assigned_palette != destination):
            # We have a tile that wants to be assigned to a specific palette, and it's not this one.
            return None

        # Take the colors in the source tile and execute a solver to map them to the palette's colors.
        tile_colors = list(self.source.color_map.get_entries())
        palette_colors = destination.colors

        solver = ConstraintSolver(tile_colors, palette_colors, ColorsIntoColorsEvaluator)
        while solver.is_complete() == False:
            solver.update()

        # Did we have any solutions?
        solutions = solver.solutions
        if len(solutions) == 0:
            # No solutions means we can't fit.
            return None
        
        changes = []
        # Each solution is a possible way to fit the tile into the palette
        for solution in solutions:
            # The Color-to-Color evaluator gives us a list of moves that needs translation for Tile-to-Palette.
            # We'll consolidate all changes down.
            palette_color_index_to_change_list = {}

            for move in solution:
                dest_palette_entry_index = move.dest_index

                if dest_palette_entry_index not in palette_color_index_to_change_list:
                    palette_color_index_to_change_list[dest_palette_entry_index] = []

                for change in move.change_list:
                    # Change is a tuple of (property name, property value)
                    palette_color_index_to_change_list[dest_palette_entry_index].append(change)

            # Flatten the dictionary.
            changes_for_solution = []
            for palette_color_index, change_list in palette_color_index_to_change_list.items():
                index_changes_tuple = (palette_color_index, change_list)
                changes_for_solution.append(index_changes_tuple)

            changes.append(changes_for_solution)
        
        return changes

    @staticmethod
    def _get_score_for_changes(change_list):
        score = 0

        # For every color that matches (i.e., no changes), add to the score
        for change in change_list:
            # Change is (palette color index, [property name, property value] list)
            prop_change_list = change[1]
            if len(prop_change_list) == 0:
                score = score + TileSetIntoPaletteEvaluator.SCORE_ADJUST_EACH_COLOR_MATCHING

        return score
import math
from ColorEntry import ColorEntry
from Tile import Tile
from ColorMap import ColorMap
from Palette import Palette
from constraint_solver import ConstraintSolver
from ColorsIntoColorsEvaluator import ColorsIntoColorsEvaluator
from TileSetIntoPaletteEvaluator import TileSetIntoPaletteEvaluator

def demo_flags():

    ##############################################################################
    # PALETTES
    palette_A = Palette(5)
    palette_B = Palette(5)

    ##############################################################################
    # GLOBAL COLORS
    clear_color = ColorEntry()
    clear_color.properties.attempt_set_property(ColorEntry.PROPERTY_NAME, "Clear")
    clear_color.properties.attempt_set_property(ColorEntry.PROPERTY_FORCED_PALETTE, palette_B)
    clear_color.properties.attempt_set_property(ColorEntry.PROPERTY_SLOT, 0)

    special_color_remaps = {}
        
    ##############################################################################
    # TILES
    # USA
    color_map_USA = ColorMap(special_color_remaps)
    color_map_USA.add_color("red")
    color_map_USA.add_color("white")
    color_map_USA.add_color("blue")

    tile_USA = Tile("USA", color_map_USA)

    # ITA
    color_map_ITA = ColorMap(special_color_remaps)
    color_map_ITA.add_color("red")
    color_map_ITA.add_color("white")
    color_map_ITA.add_color("green")

    tile_ITA = Tile("ITA", color_map_ITA)

    # LIT
    color_map_LIT = ColorMap(special_color_remaps)
    color_map_LIT.add_color("yellow")
    color_map_LIT.add_color("green")
    color_map_LIT.add_color("red")

    tile_LIT = Tile("LIT", color_map_LIT)

    # PAL
    color_map_PAL = ColorMap(special_color_remaps)
    color_map_PAL.add_color("light blue")
    color_map_PAL.add_color("yellow")

    tile_PAL = Tile("PAL", color_map_PAL)

    # CAN
    color_map_CAN = ColorMap(special_color_remaps)
    color_map_CAN.add_color("red")
    color_map_CAN.add_color("white")

    tile_CAN = Tile("CAN", color_map_CAN)

    # FIN
    color_map_FIN = ColorMap(special_color_remaps)
    color_map_FIN.add_color("blue")
    color_map_FIN.add_color("white")

    tile_FIN = Tile("FIN", color_map_FIN)

    # MIC
    color_map_MIC = ColorMap(special_color_remaps)
    color_map_MIC.add_color("light blue")
    color_map_MIC.add_color("white")

    tile_MIC = Tile("MIC", color_map_MIC)

    # CHN
    color_map_CHN = ColorMap(special_color_remaps)
    color_map_CHN.add_color("red")
    color_map_CHN.add_color("yellow")

    tile_CHN = Tile("CHN", color_map_CHN)

    ##############################################################################
    # SOLVER INIT
    src_tile_list = []

    src_tile_list.append(tile_USA)
    src_tile_list.append(tile_ITA)
    src_tile_list.append(tile_LIT)
    src_tile_list.append(tile_PAL)
    src_tile_list.append(tile_CAN)
    src_tile_list.append(tile_FIN)
    src_tile_list.append(tile_MIC)
    src_tile_list.append(tile_CHN)

    dest_palette_list = []
    dest_palette_list.append(palette_A)
    dest_palette_list.append(palette_B)

    solver = ConstraintSolver(src_tile_list, dest_palette_list, TileSetIntoPaletteEvaluator)
    while solver.is_complete() == False:
        solver.update()

    print(f"Found {len(solver.solutions)} tile into palettes solutions!")
    # Find those with the fewest or best colors.
    best_num_colors = math.inf
    worst_num_colors = -math.inf
    best_solutions = []
    worst_solutions = []
    for solution in solver.solutions:
        unique_colors = set()
        for move in solution:
            src_palette = move.dest_index
            change_list = move.change_list
            for change in change_list:
                color_index = change[0]
                unique_color_tuple = (src_palette, color_index)
                unique_colors.add(unique_color_tuple)
        
        num_colors = len(unique_colors)
        if num_colors < best_num_colors:
            best_num_colors = num_colors
            best_solutions = []
            best_solutions.append(solution)
        elif num_colors == best_num_colors:
            best_solutions.append(solution)

        if num_colors > worst_num_colors:
            worst_num_colors = num_colors
            worst_solutions = []
            worst_solutions.append(solution)
        elif num_colors == worst_num_colors:
            worst_solutions.append(solution)
        
    print(f"Found {len(best_solutions)} best solutions with {best_num_colors} colors.")
    print(f"Found {len(worst_solutions)} worst solutions with {worst_num_colors} colors.")



def demo_colors():
    # Source nodes
    source_node_list = []

    src_red_1 = ColorEntry()
    src_red_1.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (255,0,0))
    src_red_1.properties.attempt_set_property(ColorEntry.PROPERTY_SLOT, 1)
    source_node_list.append(src_red_1)

    src_red_3 = ColorEntry()
    src_red_3.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (255,0,0))
    src_red_3.properties.attempt_set_property(ColorEntry.PROPERTY_SLOT, 3)
    source_node_list.append(src_red_3)

    src_green_2 = ColorEntry()
    src_green_2.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (0,255,0))
    src_green_2.properties.attempt_set_property(ColorEntry.PROPERTY_SLOT, 2)
    source_node_list.append(src_green_2)

    src_blue = ColorEntry()
    src_blue.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (0,0,255))
    source_node_list.append(src_blue)

    src_yellow = ColorEntry()
    src_yellow.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (255,255,0))
    source_node_list.append(src_yellow)

    # Dest nodes
    dest_node_list = []

    dest_blue_0 = ColorEntry()
    dest_blue_0.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (0,0,255))
    dest_blue_0.properties.attempt_set_property(ColorEntry.PROPERTY_SLOT, 0)
    dest_node_list.append(dest_blue_0)

    dest_green = ColorEntry()
    dest_green.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (0,255,0))
    dest_node_list.append(dest_green)

    dest_red = ColorEntry()
    dest_red.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (255,0,0))
    dest_node_list.append(dest_red)

    dest_clear_1 = ColorEntry()
    dest_node_list.append(dest_clear_1)

    dest_clear_2 = ColorEntry()
    dest_node_list.append(dest_clear_2)

    # Start the solver.
    solver = ConstraintSolver(source_node_list, dest_node_list, ColorsIntoColorsEvaluator)

    while False == solver.is_complete():
        solver.update()

    solutions = solver.solutions

    print(f"Found {len(solutions)} colors into colors solutions.")


demo_colors()

demo_flags()
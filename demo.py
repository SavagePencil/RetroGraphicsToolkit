import math
from ColorEntry import ColorEntry
from Tile import Tile
from ColorMap import ColorMap
from Palette import Palette
from constraint_solver import ConstraintSolver
from ColorsIntoColorsEvaluator import ColorsIntoColorsEvaluator
from TileSetIntoPaletteEvaluator import TileSetIntoPaletteEvaluator
from PIL import Image
from PixelArray import PixelArray

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

    print(f"Found {len(solver.solutions)} tile-into-palettes solutions!")
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
            for color_into_color_move in change_list.color_into_color_moves:
                color_index = color_into_color_move.dest_index
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

    # Pick a best solution and flatten it.
    solution = best_solutions[0]
    solver.apply_solution(solution)

    print("Solution:")
    for dest_palette_idx in range(len(dest_palette_list)):
        print(f"\tPalette {dest_palette_idx}:")
        palette = dest_palette_list[dest_palette_idx]
        flattened_pal = palette.get_flattened_palette()
        for color_idx in range(len(flattened_pal)):
            print(f"\t\t{color_idx}: {flattened_pal[color_idx].properties.get_property(ColorEntry.PROPERTY_COLOR)}")

        # Find all tiles mapped to this palette.
        tiles_in_palette = []
        for move in solution:
            if dest_palette_idx == move.dest_index:
                src_tile_idx = move.source_index
                src_tile = src_tile_list[src_tile_idx]
                tiles_in_palette.append(src_tile)
        
        print(f"\tTiles in Palette:")
        if len(tiles_in_palette) == 0:
            print(f"\t\tNone")
        else:
            for tile in tiles_in_palette:
                print(f"\t\t{tile.name}")


    print("Done!")



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

    print(f"Found {len(solutions)} colors-into-colors solutions.")


def demo_font():
    ##############################################################################
    # PIXEL ARRAYS
    parent_image = Image.open("font.png").convert("RGB")
    pixel_arrays = []
    unique_color_lists = []
    remapped_color_lists = []
    tile_width = 8
    tile_height = 8
    start_y = 0
    start_x = 0
    # Font comes in as green.  Remap to white.
    special_color_remap = {(0,255,0):(255,255,255)}

    # Chop out each pixel array from the larger image.
    for y in range(start_y, parent_image.height, tile_height):
        for x in range(start_x, parent_image.width, tile_width):
            px_array = PixelArray(parent_image, x, y, tile_width, tile_height)
            px_array.quantize(8, 2)
            pixel_arrays.append(px_array)

            # Extract all unique colors
            curr_index = 0
            pixel_color_to_unique_index = {}
            unique_color_list = []
            for pixel_color in px_array.pixels:
                if pixel_color not in pixel_color_to_unique_index:
                    # This is a new, unique color.
                    pixel_color_to_unique_index[pixel_color] = curr_index
                    curr_index = curr_index + 1
                    unique_color_list.append(pixel_color)
            
            unique_color_lists.append(unique_color_list)

            # Now see which ones need to be remapped
            remapped_color_list = []
            for unique_color in unique_color_list:
                if unique_color in special_color_remap:
                    # Remapped.
                    remapped_color = special_color_remap[unique_color]
                    remapped_color_list.append(remapped_color)
                else:
                    # Keep it as-is.
                    remapped_color_list.append(unique_color)

            remapped_color_lists.append(remapped_color_list)

    ##############################################################################
    # STAGING PALETTES
    staging_palettes = []
    staging_palette_bg_only = []
    staging_palette_sprites = []
    num_entries = 16

    while num_entries > 0:
        staging_palette_bg_only.append(ColorEntry())
        staging_palette_sprites.append(ColorEntry())
        num_entries = num_entries - 1
    
    staging_palettes.append(staging_palette_bg_only)
    staging_palettes.append(staging_palette_sprites)

    # TODO:  CHANGE CONSTRAINT SOLVER TO WORK ON ARRAY OF REMAPPED COLORS INTO STAGING PALETTES

    solver = ConstraintSolver(remapped_color_lists, staging_palettes, TileSetIntoPaletteEvaluator)
    while solver.is_complete() == False:
        solver.update()

    # TODO find the best one.
    solution = solver.solutions[0]
    


demo_colors()

demo_flags()

demo_font()
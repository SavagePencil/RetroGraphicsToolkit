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
from ColorRemap import ColorRemap
from StagingPalette import StagingPalette
from ColorRemapsIntoStagingPalettesEvaluator import ColorRemapsIntoStagingPalettesEvaluator
from FinalPalette import FinalPalette

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

    solver = ConstraintSolver(src_tile_list, dest_palette_list, TileSetIntoPaletteEvaluator, True)
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
    solver = ConstraintSolver(source_node_list, dest_node_list, ColorsIntoColorsEvaluator, True)

    while False == solver.is_complete():
        solver.update()

    solutions = solver.solutions

    print(f"Found {len(solutions)} colors-into-colors solutions.")


def demo_font():
    ##############################################################################
    # PIXEL ARRAYS
    parent_image = Image.open("font.png").convert("RGB")
    color_remaps = []

    # Font comes in as green.  Remap to white.
    white_entry = ColorEntry()
    white_entry.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (255,255,255))
    special_color_remap = {(0,255,0): white_entry}

    # Treat the image as one large color remapping problem.  We'll divvy up into tiles later.
    px_array = PixelArray(parent_image, 0, 0, parent_image.width, parent_image.height)
    px_array.quantize((8,8,8), (2,2,2))

    # Extract all unique colors
    pixel_value_set = set()
    unique_pixel_values_list = []

    for pixel_value in px_array.pixels:
        if pixel_value not in pixel_value_set:
            # This is a new, unique color.  Add it *IN THE DETERMINISTIC ORDER IT WAS DISCOVERED*.
            unique_pixel_values_list.append(pixel_value)
            # Add it to the set for faster lookup (but it won't have a deterministic order).
            pixel_value_set.add(pixel_value)
    
    color_remap_font = ColorRemap({}, unique_pixel_values_list, special_color_remap)
    color_remaps.append(color_remap_font)

    ##############################################################################
    # STAGING PALETTES
    staging_palettes = []
    staging_palette_bg_only = StagingPalette(16)
    staging_palette_sprites = StagingPalette(16)

    staging_palettes.append(staging_palette_bg_only)
    staging_palettes.append(staging_palette_sprites)

    ##############################################################################
    # SOLUTION FOR COLOR REMAPS -> STAGING PALETTES
    remap_to_staging_solver = ConstraintSolver(color_remaps, staging_palettes, ColorRemapsIntoStagingPalettesEvaluator, True)
    while remap_to_staging_solver.is_complete() == False:
        remap_to_staging_solver.update()

    # TODO find the best one.
    remap_to_staging_solution = remap_to_staging_solver.solutions[0]

    for move in remap_to_staging_solution:
        # Let the corresponding color remap process these moves.
        source_remap = color_remaps[move.source_index]
        source_remap.remap_to_staging_palette(move, staging_palettes)

    # Now apply the solution to the staging palettes.
    remap_to_staging_solver.apply_solution(remap_to_staging_solution)

    ##############################################################################
    # FINAL PALETTES
    final_palettes = []
    final_palette_bg_only = FinalPalette(16)
    final_palette_sprites = FinalPalette(16)
    
    final_palettes.append(final_palette_bg_only)
    final_palettes.append(final_palette_sprites)
    
    ##############################################################################
    # CREATE MAPPING OF STAGING -> FINAL PALETTES
    stage_to_final_maps = []
    for palette_idx in range(len(staging_palettes)):
        # Each staging palette corresponds to one final palette.
        staging_palette = staging_palettes[palette_idx]
        final_palette = final_palettes[palette_idx]

        stage_to_final_map = staging_palette.create_final_palette_mapping()
        stage_to_final_maps.append(stage_to_final_map)

        # Assign the pixel values from the map.
        for stage_idx, final_idx in stage_to_final_map.items():
            color_entry = staging_palette.color_entries[stage_idx]
            pixel_value = color_entry.properties.get_property(ColorEntry.PROPERTY_COLOR)
            final_palette.final_pixels[final_idx].attempt_write_pixel_value(pixel_value)

    ##############################################################################
    # APPLY STAGING -> FINAL TO REMAPS
    for color_remap in color_remaps:
        # Find the staging palette in the list of palettes
        palette_idx = None
        remap_staging_palette = color_remap.staging_palette
        for staging_palette_idx in range(len(staging_palettes)):
            if remap_staging_palette is staging_palettes[staging_palette_idx]:
                # Found it.
                palette_idx = staging_palette_idx
                break

        # Assign the final palette.
        final_palette = final_palettes[palette_idx]
        color_remap.final_palette = final_palette
    
        # Now do the staging -> final index mapping.
        stage_to_final_map = stage_to_final_maps[palette_idx]
        for color_idx in range(len(color_remap.staging_palette_indices)):
            staging_idx = color_remap.staging_palette_indices[color_idx]
            final_idx = stage_to_final_map[staging_idx]
            color_remap.final_palette_indices[color_idx] = final_idx

    ##############################################################################
    # CONVERT TO INDEXED PATTERNS
    pattern_width = 8
    pattern_height = 8
    start_x = 8
    start_y = 8

    pattern = []
    for y in range(start_y, start_y + pattern_height):
        for x in range(start_x, start_x + pattern_width):
            pixel_value = px_array.get_pixel_value(x, y)

            # Find corresponding index.
            color_index = color_remap_font.source_pixel_value_to_index[pixel_value]

            # Find final palette slot.
            final_palette_slot = color_remap_font.final_palette_indices[color_index]

            pattern.append(final_palette_slot)


    print("Done!")


#demo_colors()

#demo_flags()

demo_font()
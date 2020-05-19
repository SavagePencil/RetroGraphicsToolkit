import math
from PIL import Image
from ColorEntry import ColorEntry
from constraint_solver import ConstraintSolver
from ColorsIntoColorsEvaluator import ColorsIntoColorsEvaluator
from PixelArray import PixelArray
from ColorRemap import ColorRemap
from StagingPalette import StagingPalette
from ColorRemapsIntoStagingPalettesEvaluator import ColorRemapsIntoStagingPalettesEvaluator
from FinalPalette import FinalPalette
import Quantize
from Interval import Interval
from IntervalsToBitSetsEvaluator import IntervalsToBitSetsEvaluator
from BitSet import BitSet

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

    while False == solver.is_exhausted():
        solver.update()

    solutions = solver.solutions

    print(f"Found {len(solutions)} colors-into-colors solutions.")


def demo_font():
    ##############################################################################
    # STAGING PALETTES
    staging_palettes = []
    staging_palette_bg_only = StagingPalette(16)
    staging_palette_sprites = StagingPalette(16)

    staging_palettes.append(staging_palette_bg_only)
    staging_palettes.append(staging_palette_sprites)

    ##############################################################################
    # PIXEL ARRAYS
    parent_image = Image.open("font.png").convert("RGB")
    color_remaps = []

    # Font comes in as green.  Remap to white.
    white_entry = ColorEntry()
    white_entry.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (255,255,255))
    white_entry.properties.attempt_set_property(ColorEntry.PROPERTY_SLOT, 7)
    white_entry.properties.attempt_set_property(ColorEntry.PROPERTY_FORCED_PALETTE, 1)
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
    # SOLUTION FOR COLOR REMAPS -> STAGING PALETTES
    remap_to_staging_solver = ConstraintSolver(color_remaps, staging_palettes, ColorRemapsIntoStagingPalettesEvaluator, True)
    while remap_to_staging_solver.is_exhausted() == False:
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

        # Print each palette.
        print(f"Palette {palette_idx}:")
        for final_pixel_idx in range(len(final_palette.final_pixels)):
            final_pixel = final_palette.final_pixels[final_pixel_idx]
            pixel_value = final_pixel.get_pixel_value()
            if pixel_value is not None:
                # Quantize it from 8 bits per channel (RGB) to 2 bits per channel (SMS)
                quantized_pixel_value = Quantize.quantize_tuple_to_target(pixel_value, (2**8,2**8,2**8), (2**2,2**2,2**2))
                print(f"  {final_pixel_idx}: RGB: {pixel_value} / Quantized: {quantized_pixel_value}")


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
    patterns_indexed = []

    for start_y in range(0, px_array.height, pattern_height):
        for start_x in range(0, px_array.width, pattern_width):
            # Carve out each pattern.
            pattern = []
            for y in range(start_y, start_y + pattern_height):
                for x in range(start_x, start_x + pattern_width):
                    pixel_value = px_array.get_pixel_value(x, y)

                    # Find corresponding index.
                    color_index = color_remap_font.source_pixel_value_to_index[pixel_value]

                    # Find final palette slot.
                    final_palette_slot = color_remap_font.final_palette_indices[color_index]

                    pattern.append(final_palette_slot)

            patterns_indexed.append(pattern)

    ##############################################################################
    # CONVERT TO 1BPP PATTERNS
    pattern_width = 8
    pattern_height = 8
    patterns_1bpp = []
    color_indices_1bpp = []

    # Get the "0s" color
    color_indices_1bpp.append(color_remap_font.final_palette_indices[0])
    # Get the "1s" color
    color_indices_1bpp.append(color_remap_font.final_palette_indices[1])

    for start_y in range(0, px_array.height, pattern_height):
        for start_x in range(0, px_array.width, pattern_width):
            # Carve out each pattern.
            pattern = []
            for y in range(start_y, start_y + pattern_height):
                byte_value = 0
                for x in range(start_x, start_x + pattern_width):
                    pixel_value = px_array.get_pixel_value(x, y)

                    # Find corresponding index.
                    color_index = color_remap_font.source_pixel_value_to_index[pixel_value]

                    if color_index == 0:
                        # Just shift
                        byte_value = byte_value << 1
                    elif color_index == 1:
                        # Shift, then OR in a 1 bit.
                        byte_value = byte_value << 1
                        byte_value = byte_value | 1
                    else:
                        raise Exception("Attempted to convert image to 1bpp, but it had a color index that wasn't 0 or 1!")

                pattern.append(byte_value)
    
            patterns_1bpp.append(pattern)

    print("Done!")

def demo_flags():
    ##############################################################################
    # STAGING PALETTES
    staging_palettes = []
    staging_palette_factory_A = StagingPalette(5)
    staging_palette_factory_B = StagingPalette(5)

    staging_palettes.append(staging_palette_factory_A)
    staging_palettes.append(staging_palette_factory_B)

    ##############################################################################
    # PIXEL ARRAYS
    parent_image = Image.open("flags.png").convert("RGB")
    color_remaps = []
    pixel_arrays = []

    # Load the image and then divvy up into separate tiles.
    pattern_width = 8
    pattern_height = 8

    for start_y in range(0, parent_image.height, pattern_height):
        for start_x in range(0, parent_image.width, pattern_width):
            px_array = PixelArray(parent_image, start_x, start_y, pattern_width, pattern_height)
            px_array.quantize((8,8,8), (2,2,2))

            pixel_arrays.append(px_array)

            # Extract all unique colors
            pixel_value_set = set()
            unique_pixel_values_list = []

            for pixel_value in px_array.pixels:
                if pixel_value not in pixel_value_set:
                    # This is a new, unique color.  Add it *IN THE DETERMINISTIC ORDER IT WAS DISCOVERED*.
                    unique_pixel_values_list.append(pixel_value)
                    # Add it to the set for faster lookup (but it won't have a deterministic order).
                    pixel_value_set.add(pixel_value)
            
            color_remap = ColorRemap({}, unique_pixel_values_list, {})
            color_remaps.append(color_remap)

    ##############################################################################
    # SOLUTION FOR COLOR REMAPS -> STAGING PALETTES
    remap_to_staging_solver = ConstraintSolver(color_remaps, staging_palettes, ColorRemapsIntoStagingPalettesEvaluator, None)
    while remap_to_staging_solver.is_exhausted() == False:
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
    final_palette_factory_A = FinalPalette(5)
    final_palette_factory_B = FinalPalette(5)
    
    final_palettes.append(final_palette_factory_A)
    final_palettes.append(final_palette_factory_B)
    
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

        # Print each palette.
        print(f"Palette {palette_idx}:")
        for final_pixel_idx in range(len(final_palette.final_pixels)):
            final_pixel = final_palette.final_pixels[final_pixel_idx]
            pixel_value = final_pixel.get_pixel_value()
            if pixel_value is not None:
                # Quantize it from 8 bits per channel (RGB) to 2 bits per channel (SMS)
                quantized_pixel_value = Quantize.quantize_tuple_to_target(pixel_value, (2**8,2**8,2**8), (2**2,2**2,2**2))
                print(f"  {final_pixel_idx}: RGB: {pixel_value} / Quantized: {quantized_pixel_value}")


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
    patterns_indexed = []

    for pixel_array_idx in range(len(pixel_arrays)):
        pattern = []
        pixel_array = pixel_arrays[pixel_array_idx]
        color_remap = color_remaps[pixel_array_idx]

        # Walk through each pixel and remap it to indexed color.
        for y in range(0, pixel_array.height):
            for x in range(0, pixel_array.width):
                pixel_value = pixel_array.get_pixel_value(x, y)

                # Find corresponding index.
                color_index = color_remap.source_pixel_value_to_index[pixel_value]

                # Find final palette slot.
                final_palette_slot = color_remap.final_palette_indices[color_index]

                pattern.append(final_palette_slot)

        patterns_indexed.append(pattern)

    print("Done!")



def demo_VRAM():
    intervals = []
    interval_font = Interval(slot_range=(20,20), length=96)
    interval_player_sprite = Interval(slot_range=(0,255), length=6)
    interval_enemy_sprite = Interval(slot_range=(0,255), length=2)
    interval_bg1 = Interval(slot_range=(0,447), length=1)
    interval_bg2 = Interval(slot_range=(256,447), length=1)
    interval_bg3 = Interval(slot_range=(256,447), length=1)
    intervals.append(interval_font)
    intervals.append(interval_player_sprite)
    intervals.append(interval_enemy_sprite)
    intervals.append(interval_bg1)
    intervals.append(interval_bg2)
    intervals.append(interval_bg3)

    bitsets = []
    VRAMPositions = BitSet(448)
    bitsets.append(VRAMPositions)

    interval_to_VRAM_solver = ConstraintSolver(sources=intervals, destinations=bitsets, evaluator_class=IntervalsToBitSetsEvaluator, debugging=True)
    while (len(interval_to_VRAM_solver.solutions) == 0) and (interval_to_VRAM_solver.is_exhausted() == False):
        interval_to_VRAM_solver.update()

    # How'd the solution go?
    solution = interval_to_VRAM_solver.solutions[0]
    for move in solution:
        # The "source" will be one of our intervals, and since we're only doing one BitSet, our "destination" will always be the VRAMPositions array.
        # Dig into the change list to figure out which slot was actually chosen.
        source_interval = intervals[move.source_index]
        dest_interval = move.change_list.possible_interval
        src_pos = dest_interval.slot_range[0]
        end_pos = src_pos + source_interval.length - 1
        leftover = dest_interval.slot_range[1] - end_pos
        if src_pos == end_pos:
            print(f"Interval {move.source_index} will occupy location {src_pos}, with {leftover} spaces remaining.")
        else:
            print(f"Interval {move.source_index} will occupy locations {src_pos} thru {end_pos}, with {leftover} spaces remaining.")

    print("Done!")


#demo_colors()

#demo_font()

#demo_flags()

demo_VRAM()
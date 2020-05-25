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
from Pattern import Pattern
import Quantize
from Interval import Interval
from IntervalsToBitSetsEvaluator import IntervalsToBitSetsEvaluator
from BitSet import BitSet
from PatternsIntoPatternHashMapsEvaluator import PatternsIntoPatternHashMapsEvaluator
from IndexedColorArray import IndexedColorArray
from NameTableEntry import NameTableEntry

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
    unique_pixel_values_list = px_array.generate_deterministic_unique_pixel_list()
    
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
    # CONVERT TO INDEXED ARRAYS
    pattern_width = 8
    pattern_height = 8
    indexed_arrays = []

    for start_y in range(0, px_array.height, pattern_height):
        for start_x in range(0, px_array.width, pattern_width):
            # Carve out each pattern.
            remapped_indices = []
            for y in range(start_y, start_y + pattern_height):
                for x in range(start_x, start_x + pattern_width):
                    pixel_value = px_array.get_pixel_value(x, y)

                    # Find corresponding index.
                    color_index = color_remap_font.source_pixel_value_to_index[pixel_value]

                    # Find final palette slot.
                    final_palette_slot = color_remap_font.final_palette_indices[color_index]

                    remapped_indices.append(final_palette_slot)

            indexed_arrays.append(IndexedColorArray(pattern_width, pattern_height, remapped_indices))

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
            unique_pixel_values_list = px_array.generate_deterministic_unique_pixel_list()

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
    interval_font = Interval.create_fixed_length_at_start_point(begin=20, length=96)
    interval_player_sprite = Interval(begin=0, end=255, length=6)
    interval_enemy_sprite = Interval(begin=0, end=255, length=2)
    interval_bg1 = Interval(begin=0, end=447, length=1)
    interval_bg2 = Interval(begin=256, end=447, length=1)
    interval_bg3 = Interval(begin=256, end=447, length=1)
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
        dest_interval = move.change_list.chosen_interval
        if dest_interval.begin == dest_interval.end:
            print(f"Interval {move.source_index}: ({source_interval.begin}, {source_interval.end}) with length {source_interval.length} will occupy location {dest_interval.begin}.")
        else:
            print(f"Interval {move.source_index}: ({source_interval.begin}, {source_interval.end}) with length {source_interval.length} will occupy locations {dest_interval.begin} thru {dest_interval.end}")

    print("Done!")

def demo_unique_tiles():
    ##############################################################################
    # PIXEL ARRAYS
    parent_image = Image.open("font.png").convert("RGB")

    pixel_arrays = []

    # Load the image and then divvy up into separate tiles.
    pattern_width = 8
    pattern_height = 8

    for start_y in range(0, parent_image.height, pattern_height):
        for start_x in range(0, parent_image.width, pattern_width):
            px_array = PixelArray(parent_image, start_x, start_y, pattern_width, pattern_height)
            px_array.quantize((8,8,8), (2,2,2))

            pixel_arrays.append(px_array)

    ##############################################################################
    # PATTERNS
    patterns = []
    pattern_property_map_flips =  {
        Pattern.PROPERTY_FLIPS_ALLOWED : Pattern.Flip.HORIZ
    }
    for pixel_array in pixel_arrays:
        index_array = pixel_array.generate_indexed_color_array()
        pattern = Pattern(index_array=index_array, initial_properties_map=pattern_property_map_flips)
        patterns.append(pattern)

    ##############################################################################
    # PATTERN SOLVING
    dest_map = {}
    dest_maps = [dest_map]

    solver = ConstraintSolver(sources=patterns, destinations=dest_maps, evaluator_class=PatternsIntoPatternHashMapsEvaluator, debugging=None)
    while((len(solver.solutions) == 0) and (solver.is_exhausted() == False)):
        solver.update()

    # How'd we do?
    solution = solver.solutions[0]
    solver.apply_solution(solution)

    # Count uniques.
    unique_patterns = []
    for move in solution:
        matched = move.change_list.matching_pattern_object_ref
        if matched is None:
            # We didn't match anybody else, so we're unique.
            src_pattern_idx = move.source_index
            unique_pattern = patterns[src_pattern_idx]
            unique_patterns.append(unique_pattern)

    print(f"Started with {len(patterns)} patterns, and resulted in {len(unique_patterns)} after solving.")

    # Print matches.
    for move in solution:
        change_list = move.change_list
        if change_list.matching_pattern_object_ref is not None:
            # See if we can find the pattern object used.
            matched_pattern_idx = None
            matched_pattern = change_list.matching_pattern_object_ref()
            for pattern_idx in range(len(patterns)):
                test_pattern = patterns[pattern_idx]
                if test_pattern == matched_pattern:
                    matched_pattern_idx = pattern_idx
                    break

            if matched_pattern_idx is None:
                # Just print the hash
                print(f"Pattern {move.source_index} matched a Pattern object with hash {hash(change_list.matching_pattern_object_ref())} with flips {change_list.flips_to_match.name}.")
            else:
                print(f"Pattern {move.source_index} matched Pattern {matched_pattern_idx} with flips {change_list.flips_to_match.name}.")

    print("Done!")

def demo_nametable():
    ##############################################################################
    # PIXEL ARRAY
    font_image = Image.open("font.png").convert("RGB")
    font_pixel_array = PixelArray(font_image, 0, 0, font_image.width, font_image.height)
    font_pixel_array.quantize((8,8,8), (2,2,2))

    flags_image = Image.open("flags.png").convert("RGB")
    flags_pixel_array = PixelArray(flags_image, 0, 0, flags_image.width, flags_image.height)
    flags_pixel_array.quantize((8,8,8), (2,2,2))

    src_pixel_arrays = [font_pixel_array, flags_pixel_array]

    ##############################################################################
    # COLOR REMAP
    # Solve the color remap problem *FIRST*.  This will give us a set of indexed
    # color arrays that we can use to find unique patterns.

    # FONT
    # Extract all unique colors
    font_unique_pixel_values_list = font_pixel_array.generate_deterministic_unique_pixel_list()

    # Font comes in as green.  Remap to white.
    white_entry = ColorEntry()
    white_entry.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, (255,255,255))
    font_special_color_remap = {(0,255,0): white_entry}

    font_color_remap = ColorRemap(initial_properties_map={}, unique_pixel_values_list=font_unique_pixel_values_list, color_remap=font_special_color_remap)

    # FLAGS
    # Extract all unique colors
    flags_unique_pixel_values_list = flags_pixel_array.generate_deterministic_unique_pixel_list()

    flags_color_remap = ColorRemap(initial_properties_map={}, unique_pixel_values_list=flags_unique_pixel_values_list, color_remap={})

    # COLOR REMAPS
    color_remaps = [font_color_remap, flags_color_remap]

    ##############################################################################
    # STAGING PALETTES
    staging_palette_sprites = StagingPalette(16)
    staging_palette_bg_only = StagingPalette(16)

    staging_palettes = [staging_palette_sprites, staging_palette_bg_only]

    ##############################################################################
    # SOLUTION FOR COLOR REMAPS -> STAGING PALETTES
    remap_to_staging_solver = ConstraintSolver(color_remaps, staging_palettes, ColorRemapsIntoStagingPalettesEvaluator, None)
    while (len(remap_to_staging_solver.solutions) == 0) and (remap_to_staging_solver.is_exhausted() == False):
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
    # SOURCE PATTERN CREATION
    # We'll create a unique pattern for each entry in the image.  Later we'll
    # merge those that we want to dupe-strip (or can be flipped to be dupes).
    src_pattern_sets = []

    pattern_property_map_flips =  {
        Pattern.PROPERTY_FLIPS_ALLOWED : Pattern.Flip.HORIZ
    }

    # Go through each large image and dice it up into smaller Patterns.
    for image_array_idx in range(len(src_pixel_arrays)):
        src_pixel_array = src_pixel_arrays[image_array_idx]
        color_remap = color_remaps[image_array_idx]

        src_patterns = []

        pattern_width = 8
        pattern_height = 8

        for start_y in range(0, src_pixel_array.height, pattern_height):
            for start_x in range(0, src_pixel_array.width, pattern_width):
                # Convert each section of pixels into the *staging* palette indices.
                # This may seem backwards.  Why not just rez up a pixel array, and then
                # get the indexed color array?
                # Here's why we do it this way:
                #   We want a consistent color mapping for the WHOLE image.  This will
                #   let us load the whole pattern data with one color remap.  Let's say
                #   we have a pattern in our image that is totally black, and another
                #   pattern that is totally white.  If we create an IndexedColorArray
                #   for each of these patterns, they will be identical, because they
                #   have only one color (they'll both be all zeroes).
                #   But we've already mapped the colors for the image as a whole, 
                #   so those two will get unique values when remapped against them.
                remapped_indices = []
                for y in range(start_y, start_y + pattern_height):
                    for x in range(start_x, start_x + pattern_width):
                        pixel = src_pixel_array.get_pixel_value(x, y)
                        remapped_index = color_remap.convert_pixel_value_to_staging_index(pixel)
                        remapped_indices.append(remapped_index)
                
                indexed_array = IndexedColorArray(width=pattern_width, height=pattern_height, indexed_array=remapped_indices)
                pattern = Pattern(index_array=indexed_array, initial_properties_map=pattern_property_map_flips)
                src_patterns.append(pattern)

        # Add all source patterns.
        src_pattern_sets.append(src_patterns)

    ##############################################################################
    # UNIQUE PATTERN SOLVING
    dest_map = {}
    dest_maps = [dest_map]

    unique_patterns_lists = []
    src_idx_to_dest_pattern_flip_lists = []

    # Execute a solver for each pattern set, but we'll merge all into the same destination.
    for pattern_set in src_pattern_sets:
        solver = ConstraintSolver(sources=pattern_set, destinations=dest_maps, evaluator_class=PatternsIntoPatternHashMapsEvaluator, debugging=None)
        while((len(solver.solutions) == 0) and (solver.is_exhausted() == False)):
            solver.update()

        solution = solver.solutions[0]
        solver.apply_solution(solution)

        # Go through the solution and find the ones that were *added*, as these will be
        # considered our "unique" patterns.  All those that *matched* will point to them.
        # Example:  
        #   'b' is index 1, and 'c' is index 2, and 'd' is index 3.
        #   'b' and 'd' are horizontal flips, while 'c' is its own thing.
        #
        #   'b' points to 'b', since it was the original.
        #   'c' points to 'c', for the same reason.
        #   'd' points to 'b', with a horizontal flip.
        #
        #   So we have 2 unique patterns ('b' and 'c'), and 'd' points to 'b' with a flip.
        unique_patterns_list = []
        src_idx_to_unique_flip_list = [None] * len(pattern_set)
        for move in solution:
            change_list = move.change_list

            unique_pattern = None
            if change_list.matching_pattern_object_ref is None:
                # Add this one to the unique list.
                unique_pattern = pattern_set[move.source_index]
                unique_patterns_list.append(unique_pattern)
            else:
                # Get the unique pattern we matched out of the change list.
                unique_pattern = change_list.matching_pattern_object_ref()

            # Now add the src -> unique + flip.
            src_idx_to_unique_flip_list[move.source_index] = (unique_pattern, change_list.flips_to_match)

        unique_patterns_lists.append(unique_patterns_list)
        src_idx_to_dest_pattern_flip_lists.append(src_idx_to_unique_flip_list)

    ##############################################################################
    # VRAM POSITIONING
    # Create intervals for each of the unique tiles.

    intervals = []

    # The font must begin at a specific location.
    font_VRAM_interval = Interval.create_fixed_length_at_start_point(20, len(unique_patterns_lists[0]))
    intervals.append(font_VRAM_interval)

    # Can go anywhere.  We'll treat them as contiguous, but we could just as easily split them up into multiples.
    flag_VRAM_interval = Interval(begin=0, end=448, length=len(unique_patterns_lists[1]))
    intervals.append(flag_VRAM_interval)

    # Find a home for them.
    bitsets = []
    VRAMPositions = BitSet(448)
    bitsets.append(VRAMPositions)

    interval_to_VRAM_solver = ConstraintSolver(sources=intervals, destinations=bitsets, evaluator_class=IntervalsToBitSetsEvaluator, debugging=None)
    while (len(interval_to_VRAM_solver.solutions) == 0) and (interval_to_VRAM_solver.is_exhausted() == False):
        interval_to_VRAM_solver.update()

    # How'd the solution go?
    solution = interval_to_VRAM_solver.solutions[0]

    # Track where each pattern interval will go.
    VRAM_dests = [None] * len(intervals)

    for move in solution:
        # The "source" will be one of our intervals, and since we're only doing one BitSet, our "destination" will always be the VRAMPositions array.
        # Dig into the change list to figure out which slot was actually chosen.
        source_interval = intervals[move.source_index]
        dest_interval = move.change_list.chosen_interval
        if dest_interval.begin == dest_interval.end:
            print(f"Interval {move.source_index}: ({source_interval.begin}, {source_interval.end}) with length {source_interval.length} will occupy location {dest_interval.begin}.")
        else:
            print(f"Interval {move.source_index}: ({source_interval.begin}, {source_interval.end}) with length {source_interval.length} will occupy locations {dest_interval.begin} thru {dest_interval.end}")

        VRAM_dests[move.source_index] = dest_interval.begin

    pattern_to_VRAM_loc_map = {}

    # Map each unique pattern to its VRAM loc.
    for unique_list_idx in range(len(unique_patterns_lists)):
        unique_pattern_list = unique_patterns_lists[unique_list_idx]
        VRAM_dest = VRAM_dests[unique_list_idx]

        for unique_idx in range(len(unique_pattern_list)):
            unique_pattern = unique_pattern_list[unique_idx]
            VRAM_pos = VRAM_dest + unique_idx
            pattern_to_VRAM_loc_map[unique_pattern] = VRAM_pos

    ##############################################################################
    # NAMETABLE CREATION
    # Tie it all together to create an array of patterns, flips, palettes, and
    # VRAM locations.
    nametables = []
    for nametable_idx in range(len(src_pattern_sets)):
        nametable = []

        # Let's find our palette index.
        color_remap = color_remaps[nametable_idx]
        our_palette = color_remap.staging_palette
        for palette_idx in range(len(staging_palettes)):
            staging_palette = staging_palettes[palette_idx]
            if staging_palette is our_palette:
                break

        # Iterate through all the source patterns.
        src_pattern_set = src_pattern_sets[nametable_idx]
        for src_pattern_idx in range(len(src_pattern_set)):
            # Find its unique correspondence, and any flips.
            src_idx_to_dest_pattern_flip_list = src_idx_to_dest_pattern_flip_lists[nametable_idx]
            unique_flip_tuple = src_idx_to_dest_pattern_flip_list[src_pattern_idx]

            unique_pattern = unique_flip_tuple[0]
            flips = unique_flip_tuple[1]

            # Find the VRAM loc.
            VRAM_pos = pattern_to_VRAM_loc_map[unique_pattern]

            # We have everything we need to build the nametable entry.
            nametable_entry = NameTableEntry(VRAM_loc=VRAM_pos, palette_index=palette_idx, flips=flips)
            nametable.append(nametable_entry)
        
        nametables.append(nametable)

    print("Done!")

#demo_colors()

#demo_font()

#demo_flags()

#demo_VRAM()

#demo_unique_tiles()

demo_nametable()
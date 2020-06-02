import os

from PIL import Image

from rgtk.BitSet import BitSet
from rgtk.ColorEntry import ColorEntry
from rgtk.ColorRemap import ColorRemap
from rgtk.ColorRemapsIntoStagingPalettesEvaluator import ColorRemapsIntoStagingPalettesEvaluator
from rgtk.constraint_solver import ConstraintSolver
from rgtk.IndexedColorArray import IndexedColorArray
from rgtk.Interval import Interval
from rgtk.IntervalsToBitSetsEvaluator import IntervalsToBitSetsEvaluator
from rgtk.NameTableEntry import NameTableEntry
from rgtk.Pattern import Pattern
from rgtk.PatternsIntoPatternHashMapsEvaluator import PatternsIntoPatternHashMapsEvaluator
from rgtk.PixelArray import PixelArray
from rgtk.StagingPalette import StagingPalette

##############################################################################
# PIXEL ARRAY

# Track the path relative to this script.
our_dir = os.path.dirname(__file__)

font_image = Image.open(os.path.join(our_dir, "assets/font.png")).convert("RGB")
font_pixel_array = PixelArray(font_image, 0, 0, font_image.width, font_image.height)
font_pixel_array.quantize((8,8,8), (2,2,2))

flags_image = Image.open(os.path.join(our_dir, "assets/flags.png")).convert("RGB")
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
white_entry.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (255,255,255))
font_special_color_remap = {(0,255,0): white_entry}

font_color_remap = ColorRemap(initial_intentions_map={}, unique_pixel_values_list=font_unique_pixel_values_list, color_remap=font_special_color_remap)

# FLAGS
# Extract all unique colors
flags_unique_pixel_values_list = flags_pixel_array.generate_deterministic_unique_pixel_list()

flags_color_remap = ColorRemap(initial_intentions_map={}, unique_pixel_values_list=flags_unique_pixel_values_list, color_remap={})

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

pattern_intention_map_flips =  {
    Pattern.INTENTION_FLIPS_ALLOWED : Pattern.Flip.HORIZ
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
            pattern = Pattern(index_array=indexed_array, initial_intentions_map=pattern_intention_map_flips)
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
    src_idx_to_unique_flip_list = [None] * len(pattern_set)
    for move in solution:
        change_list = move.change_list

        dest_pattern = None
        if change_list.matching_pattern_object_ref is None:
            # Add this one to the unique list.
            dest_pattern = pattern_set[move.source_index]
        else:
            # Get the pattern we matched out of the change list.
            dest_pattern = change_list.matching_pattern_object_ref()

        # Now add the src -> dest + flip.
        src_idx_to_unique_flip_list[move.source_index] = (dest_pattern, change_list.flips_to_match)

    # Arrange the uniques in corresponding order to the source indices.
    # We have to do this as a separate pass because the order of moves
    # (the loop above) is non-deterministic, and we want to retain the
    # original order of the source indices.
    unique_patterns_list = []
    for source_idx in range(len(src_idx_to_unique_flip_list)):
        source_pattern = pattern_set[source_idx]

        # Is this one unique?
        dest_flip_tuple = src_idx_to_unique_flip_list[source_idx]
        dest_pattern = dest_flip_tuple[0]

        if source_pattern == dest_pattern:
            # If source matches dest, we aren't remapped (i.e., we're unique.)
            unique_patterns_list.append(dest_pattern)

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
import math
import os

from PIL import Image

from rgtk.BitSet import BitSet
from rgtk.constraint_solver import ConstraintSolver
from rgtk.IndexedColorArray import IndexedColorArray
from rgtk.PixelArray import PixelArray
import rgtk.Quantize
from rgtk.RasterPixelsToSpritesEvaluator import RasterPixelsToSpritesEvaluator

##############################################################################
# PIXEL ARRAYS
# Assets are relative to this script's directory.
our_dir = os.path.dirname(__file__)

parent_image = Image.open(os.path.join(our_dir, "assets/swim_left_1.png")).convert("RGB")
px_array = PixelArray(parent_image, 0, 0, parent_image.width, parent_image.height)
px_array.quantize((8,8,8), (2,2,2))

# Transform the image into an indexed array where 0s are clear and 1s are opaque.
clear_color = (255,255,255)
idx_image = []
for pixel in px_array.pixels:
    if pixel == clear_color:
        idx_image.append(0)
    else:
        idx_image.append(1)

indexed_array = IndexedColorArray(width=parent_image.width, height=parent_image.height, indexed_array=idx_image)

##############################################################################
# PIXEL IDENTIFICATION
# Identify all of the pixels in the source image that are important.
# We follow these rules:
# 1. Pixels are entered into our list in order of left-to-right, top-to-bottom
# 
# ...we do this so that our raster solver algorithm can easily find the next
# pixel that needs coverage.

# Our color to ignore.
clear_color = 0

# Identify all of the pixels in the image.
pixel_pos_to_unique_pixel_idx = {}
pixel_list = []
x_min = math.inf
x_max = -math.inf
y_min = math.inf
y_max = -math.inf
for y in range(indexed_array.height):
    for x in range(indexed_array.width):
        pixel_val = indexed_array.get_value(x, y)
        if pixel_val != clear_color:
            # We've got a valid pixel.  Track it with an unique index.
            idx = len(pixel_list)
            pixel_pos = (x, y)
            pixel_pos_to_unique_pixel_idx[pixel_pos] = idx
            pixel_list.append(pixel_pos)

            # Calculate our minimum bounding area.
            x_min = min(x_min, x)
            x_max = max(x_max, x)
            y_min = min(y_min, y)
            y_max = max(y_max, y)

##############################################################################
# CREATE POTENTIAL SPRITES
# Create all *potential* sprites that contain at least one pixel and follow
# these rules:
#   1. They fit within our bounding areas
#   2. They have at least one pixel inside of them
#
# ...we do it this way to eliminate noise.

sprite_width = 8
sprite_height = 8

potential_sprite_upper_left_positions = []
potential_sprite_pixel_coverage_bitsets = []

for y_start in range(y_min, y_max + 1):
    for x_start in range(x_min, x_max + 1):
        # Track which pixel indices are in this sprite.
        pixel_indices_in_sprite = []
        for y in range(y_start, y_start + sprite_height):
            for x in range(x_start, x_start + sprite_width):
                if (x, y) in pixel_pos_to_unique_pixel_idx:
                    pixel_index = pixel_pos_to_unique_pixel_idx[(x,y)]
                    pixel_indices_in_sprite.append(pixel_index)

        # Did we have any pixels?
        if len(pixel_indices_in_sprite) > 0:
            # Yes.  Create a potential sprite with all of the pixels it covers
            # into a bit set.
            coverage = BitSet(len(pixel_list))
            for pixel_index in pixel_indices_in_sprite:
                coverage.set_bit(pixel_index)

            # Append the positions and the coverages in separate lists
            # (we'll just use the coverage set for the solver)
            potential_sprite_upper_left_positions.append((x_start, y_start))
            potential_sprite_pixel_coverage_bitsets.append(coverage)

# Sanity check:  How many sprites hold the first pixel index?
print(f"Sprites holding pixel 0 (location {pixel_list[0]}):")
num_containing = 0
for sprite_idx in range(len(potential_sprite_upper_left_positions)):
    coverage = potential_sprite_pixel_coverage_bitsets[sprite_idx]
    if coverage.is_set(0):
        ul_pos = potential_sprite_upper_left_positions[sprite_idx]
        num_containing += 1
        print(f"\t{num_containing}: {ul_pos}")

##############################################################################
# ASSOCIATE PIXELS WITH POTENTIAL SPRITES
# We'll *ALSO* associate individual pixels with specific sprites, 
# following these rules:
#   1. Only choose sprites that contain our pixel
#   2. Only choose sprites that share the same *Y-POSITION* as our pixel
#
# ...you can think of this as a series of sprites that act as a 
# "sliding window" on the same Y-value as our pixel.  
# We do this so that our raster solver only considers sprites 
# relevant to *this* pixel.
#
# It would be more efficient to do this as part of the previous step,
# but this makes it clearer.

# Track which sprites are relevant to each pixel.
pixel_to_sprite_bitsets = []
count = len(pixel_list)
while count > 0:
    pixel_to_sprite_bitsets.append(BitSet(len(potential_sprite_upper_left_positions)))
    count -= 1

for sprite_idx, sprite_pos in enumerate(potential_sprite_upper_left_positions):
    # Which pixels do we cover?
    coverage = potential_sprite_pixel_coverage_bitsets[sprite_idx]

    pixel_idx = coverage.get_next_set_bit_index(0)
    while pixel_idx is not None:
        pixel_pos = pixel_list[pixel_idx]

        # Are they on the same Y level?
        if pixel_pos[1] == sprite_pos[1]:
            # Yes.  Associate this sprite with this pixel.
            pixel_to_sprite_bitset = pixel_to_sprite_bitsets[pixel_idx]
            pixel_to_sprite_bitset.set_bit(sprite_idx)

        # Next.
        pixel_idx = coverage.get_next_set_bit_index(pixel_idx + 1)

##############################################################################
# EXECUTE SOLVER

# THIS SOLUTION MAPS PIXELS INTO PIXELS VIA SPRITES
sources = []
for pixel_idx in range(len(pixel_list)):
    pixel_to_sprite_bitset = pixel_to_sprite_bitsets[pixel_idx]
    source = RasterPixelsToSpritesEvaluator.Source(pixel_to_potential_sprites_bitset=pixel_to_sprite_bitset, sprite_pixel_coverages=potential_sprite_pixel_coverage_bitsets)
    sources.append(source)

dest_pixel_bitset = BitSet(len(pixel_list))
solver = ConstraintSolver(sources=sources, destinations=[dest_pixel_bitset], evaluator_class=RasterPixelsToSpritesEvaluator, debugging=None)

solution_count = 0
best_solutions = None
best_pixels_list = None
best_sprites_list = None

# Solver will stop when it is either exhausted or finds this many solutions.
max_solutions = 250

while (len(solver.solutions) < max_solutions ) and (solver.is_exhausted() == False):
    solver.update()

    if len(solver.solutions) != solution_count:
        # Compare the previous best against the new one.
        solution = solver.solutions[solution_count]

        sprites_list = []
        pixels_list = []
        for move in solution:
            if move.change_list is not None:
                pixels_list.append(move.source_index)
                sprites_list.append(move.change_list.dest_sprite_index)

        if (best_sprites_list is None) or (len(sprites_list) < len(best_sprites_list)):
            # A new best solution.
            best_solution = solution
            best_sprites_list = sprites_list
            best_pixels_list = pixels_list

            print(f"A new best!  Solution {solution_count} has {len(best_sprites_list)} sprites: {best_sprites_list}")

        # Update count
        solution_count = len(solver.solutions)

print(f"Best solution had {len(best_sprites_list)} sprites:")
for dest_index in best_sprites_list:
    dest_sprite = potential_sprite_upper_left_positions[dest_index]
    print(f"\t{dest_sprite}")
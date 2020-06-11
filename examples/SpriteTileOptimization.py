import math
import os

from PIL import Image

from rgtk.BitSet import BitSet
from rgtk.constraint_solver import ConstraintSolver
from rgtk.IndexedColorArray import IndexedColorArray
from rgtk.PixelArray import PixelArray
import rgtk.Quantize
from rgtk.SubsetsToBitSetsEvaluator import SubsetsToBitSetsEvaluator

##############################################################################
# PIXEL ARRAYS
# Assets are relative to this script's directory.
our_dir = os.path.dirname(__file__)

parent_image = Image.open(os.path.join(our_dir, "assets/demo_frame.png")).convert("RGB")
px_array = PixelArray(parent_image, 0, 0, parent_image.width, parent_image.height)
px_array.quantize((8,8,8), (2,2,2))

# Transform the image into an indexed array where 0s are clear and 1s are opaque.
clear_color = (85,85,85)
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

# Our color to ignore.
clear_color = 0

# Identify all of the pixels in the image.
pixel_pos_to_unique_pixel_idx = {}
pixel_list = []
for y in range(indexed_array.height):
    for x in range(indexed_array.width):
        pixel_val = indexed_array.get_value(x, y)
        if pixel_val != clear_color:
            # We've got a valid pixel.  Track it with an unique index.
            idx = len(pixel_pos_to_unique_pixel_idx.values())
            pixel_pos = (x, y)
            pixel_pos_to_unique_pixel_idx[pixel_pos] = idx
            pixel_list.append(pixel_pos)

# We'll track each pixel's coverage with a bit set.  One bit for each unique
# pixel.
dest_pixel_bitset = BitSet(len(pixel_pos_to_unique_pixel_idx.values()))

##############################################################################
# CREATE POTENTIAL SPRITES
# Create all *potential* sprites that contain at least one pixel.
sprite_width = 8
sprite_height = 8

potential_sprite_upper_left_positions = []
potential_sprite_pixel_coverage_bitsets = []

# We create sprites in areas beyond the canvas of the original image because
# there may be an optimization that isn't aligned with the source.
for y_start in range(-sprite_height + 1, indexed_array.height + sprite_height - 1):
    for x_start in range(-sprite_width + 1, indexed_array.width + sprite_width - 1):
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
            coverage = BitSet(dest_pixel_bitset.get_num_bits())
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
# EXECUTE SOLVER

# THIS SOLUTION MAPS SPRITES INTO PIXELS
solver = ConstraintSolver(sources=potential_sprite_pixel_coverage_bitsets, destinations=[dest_pixel_bitset], evaluator_class=SubsetsToBitSetsEvaluator, debugging=None)

solution_count = 0
best_solutions = None
best_sprites_set = None

while (len(solver.solutions) < 100 ) and (solver.is_exhausted() == False):
    solver.update()

    if len(solver.solutions) != solution_count:
        # Compare the previous best against the new one.
        solution = solver.solutions[solution_count]

        unique_sprites = set()
        for move in solution:
            if move.change_list.changed_bits.are_all_clear() == False:
                source_index = move.source_index
                unique_sprites.add(source_index)

        if (best_sprites_set is None) or (len(unique_sprites) < len(best_sprites_set)):
            # A new best solution.
            best_solution = solution
            best_sprites_set = unique_sprites

            indices = []
            for index in unique_sprites:
                indices.append(str(index))

            indices_str = " ".join(indices)

            print(f"A new best!  Solution {solution_count} has {len(best_sprites_set)} sprites: {indices_str}")

        # Update count
        solution_count = len(solver.solutions)

print(f"Best solution had {len(best_sprites_set)} sprites:")
for dest_index in best_sprites_set:
    dest_sprite = potential_sprite_upper_left_positions[dest_index]
    print(f"\t{dest_sprite}")
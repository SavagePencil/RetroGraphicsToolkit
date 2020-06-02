import os

from PIL import Image

from rgtk.constraint_solver import ConstraintSolver
from rgtk.Pattern import Pattern
from rgtk.PatternsIntoPatternHashMapsEvaluator import PatternsIntoPatternHashMapsEvaluator
from rgtk.PixelArray import PixelArray

##############################################################################
# PIXEL ARRAYS
# Assets are relative to this script's directory.
our_dir = os.path.dirname(__file__)

parent_image = Image.open(os.path.join(our_dir, "assets/font.png")).convert("RGB")

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
pattern_intention_map_flips =  {
    Pattern.INTENTION_FLIPS_ALLOWED : Pattern.Flip.HORIZ
}
for pixel_array in pixel_arrays:
    index_array = pixel_array.generate_indexed_color_array()
    pattern = Pattern(index_array=index_array, initial_intentions_map=pattern_intention_map_flips)
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


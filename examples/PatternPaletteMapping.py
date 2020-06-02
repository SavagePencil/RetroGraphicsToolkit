import os

from PIL import Image

from rgtk.ColorEntry import ColorEntry
from rgtk.ColorRemap import ColorRemap
from rgtk.ColorRemapsIntoStagingPalettesEvaluator import ColorRemapsIntoStagingPalettesEvaluator
from rgtk.constraint_solver import ConstraintSolver
from rgtk.FinalPalette import FinalPalette
from rgtk.IndexedColorArray import IndexedColorArray
from rgtk.PixelArray import PixelArray
from rgtk import Quantize
from rgtk.StagingPalette import StagingPalette

##############################################################################
# STAGING PALETTES
staging_palettes = []
staging_palette_bg_only = StagingPalette(16)
staging_palette_sprites = StagingPalette(16)

staging_palettes.append(staging_palette_bg_only)
staging_palettes.append(staging_palette_sprites)

##############################################################################
# PIXEL ARRAYS

# Assets are relative to this script's directory.
our_dir = os.path.dirname(__file__)

parent_image = Image.open(os.path.join(our_dir, "assets/font.png")).convert("RGB")
color_remaps = []

# Font comes in as green.  Remap to white.
white_entry = ColorEntry()
white_entry.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (255,255,255))
white_entry.intentions.attempt_set_intention(ColorEntry.INTENTION_SLOT, 7)
white_entry.intentions.attempt_set_intention(ColorEntry.INTENTION_FORCED_PALETTE, 1)
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
        pixel_value = color_entry.intentions.get_intention(ColorEntry.INTENTION_COLOR)
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

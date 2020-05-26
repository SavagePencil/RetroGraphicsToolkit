from typing import List, Mapping
from Intention import IntentionCollection, IntentionDefinition
from ColorEntry import ColorEntry
from StagingPalette import StagingPalette
from constraint_solver import Move

class ColorRemap(IntentionCollection):
    # Static vars
    INTENTION_PALETTE = "Palette"

    sIntention_def_map = { 
        INTENTION_PALETTE: IntentionDefinition(False, True)
    }

    def __init__(self, initial_intentions_map: Mapping[str, object], unique_pixel_values_list: List[object], color_remap: Mapping[object, ColorEntry]):
        super().__init__(ColorRemap.sIntention_def_map)

        # Set the initial intentions
        for initial_prop_name, initial_prop_val in initial_intentions_map.items():
            self.attempt_set_intention(initial_prop_name, initial_prop_val)

        # Maps source pixel values -> index values
        self.source_pixel_value_to_index = {}

        # Uses the index above to map to the ColorEntry desired.
        self.color_entries = []
        for curr_index in range(len(unique_pixel_values_list)):
            pixel_value = unique_pixel_values_list[curr_index]

            # Assign the pixel value to an index
            self.source_pixel_value_to_index[pixel_value] = curr_index

            # Assign the output color entry, which will either be:
            #   a) the remapped entry, if one was indicated in the color remap.
            #   b) the pixel value, if no remap was specified.
            if pixel_value in color_remap:
                # Case A:  Remap was specified.
                remap_entry = color_remap[pixel_value]
                self.color_entries.append(remap_entry)
            else:
                # Case B:  No remap was specified.
                new_entry = ColorEntry()
                new_entry.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, pixel_value)
                self.color_entries.append(new_entry)

        # Now see if any of our remap colors force this graphic to a specific palette.
        for color_entry in self.color_entries:
            forced_pal = color_entry.intentions.get_intention(ColorEntry.INTENTION_FORCED_PALETTE)
            if forced_pal is not None:
                self.attempt_set_intention(ColorRemap.INTENTION_PALETTE, forced_pal)

        # Track all of our staging palette values.
        self.staging_palette = None
        self.staging_palette_indices = [None] * len(self.color_entries)

        # Track all of our final palette values.
        self.final_palette = None
        self.final_palette_indices = [None] * len(self.color_entries)

    def remap_to_staging_palette(self, remap_to_staging_palette_move: Move, staging_palettes: List[StagingPalette]):
        # The move parameter is a ColorRemapsIntoStagingPalettes move,
        # which tells us which palette we're going to.
        dest_palette_index = remap_to_staging_palette_move.dest_index
        self.staging_palette = staging_palettes[dest_palette_index]

        # Now iterate through the change list to remap each of our
        # source color indices to the staging palette indices.
        for move in remap_to_staging_palette_move.change_list.color_into_color_moves:
            color_index = move.source_index
            staging_index = move.dest_index

            self.staging_palette_indices[color_index] = staging_index

    # Returns the corresponding index from the original unique color list.
    def convert_pixel_value_to_unique_index(self, pixel_value:object) -> int:
        return self.source_pixel_value_to_index[pixel_value]

    # Returns the corresponding index from the staging palette remapping.
    def convert_pixel_value_to_staging_index(self, pixel_value:object) -> int:
        unique_idx = self.convert_pixel_value_to_unique_index(pixel_value)
        staging_idx = self.staging_palette_indices[unique_idx]
        return staging_idx

    # Returns the corresponding index from the final palette remapping.
    def convert_pixel_value_to_final_index(self, pixel_value:object) -> int:
        unique_idx = self.convert_pixel_value_to_unique_index(pixel_value)
        staging_idx = self.final_palette_indices[unique_idx]
        return staging_idx

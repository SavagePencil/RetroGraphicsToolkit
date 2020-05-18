from typing import List, Mapping
from Property import PropertyCollection, PropertyDefinition
from ColorEntry import ColorEntry
from StagingPalette import StagingPalette
from constraint_solver import Move

class ColorRemap(PropertyCollection):
    # Static vars
    PROPERTY_PALETTE = "Palette"

    sProperty_def_map = { 
        PROPERTY_PALETTE: PropertyDefinition(False, True)
    }

    def __init__(self, initial_properties_map: Mapping[str, object], unique_pixel_values_list: List[object], color_remap: Mapping[object, ColorEntry]):
        super().__init__(ColorRemap.sProperty_def_map)

        # Set the initial properties
        for initial_prop_name, initial_prop_val in initial_properties_map.items():
            self.attempt_set_property(initial_prop_name, initial_prop_val)

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
                new_entry.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, pixel_value)
                self.color_entries.append(new_entry)

        # Now see if any of our remap colors force this graphic to a specific palette.
        for color_entry in self.color_entries:
            forced_pal = color_entry.properties.get_property(ColorEntry.PROPERTY_FORCED_PALETTE)
            if forced_pal is not None:
                self.attempt_set_property(ColorRemap.PROPERTY_PALETTE, forced_pal)

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

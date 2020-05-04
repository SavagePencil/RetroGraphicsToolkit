from ColorEntry import ColorEntry

class ColorMap:
    def __init__(self, special_color_to_entry_map):
        self._map = {}
        self._special_color_to_entry_map = special_color_to_entry_map

    def add_color(self, color):
        # Is this color not already in our map?
        if color not in self._map:
            # See if the color is in our list of special re-maps first.
            dest_entry = None
            if color in self._special_color_to_entry_map:
                dest_entry = self._special_color_to_entry_map[color]
            else:
                # Create a new color entry based on the pixel value.
                dest_entry = ColorEntry()
                dest_entry.properties.attempt_set_property(ColorEntry.PROPERTY_COLOR, color)

            self._map[color] = dest_entry

    def load_from_pixel_array(self, pixel_array):
        for pixel in pixel_array.pixels:
            self.add_color(pixel)

    def get_entries(self):
        return set(self._map.values())

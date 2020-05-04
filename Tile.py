from Property import PropertyDefinition, PropertyCollection
from ColorEntry import ColorEntry

class Tile:
    # Static vars
    PROPERTY_PALETTE = "Palette"

    sProperty_def_map = { 
        PROPERTY_PALETTE: PropertyDefinition(False, True)
    }

    def __init__(self, name, color_map):
        self.name = name
        self.properties = PropertyCollection(Tile.sProperty_def_map)
        self.color_map = color_map

        # Iterate through the color map.  If any colors dictate a palette,
        # attempt to assign it to ourselves.
        entries = self.color_map.get_entries()
        for entry in entries:
            palette = entry.properties.get_property(ColorEntry.PROPERTY_FORCED_PALETTE)
            if palette is not None:
                self.properties.attempt_set_property(Tile.PROPERTY_PALETTE, palette)
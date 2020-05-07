from Property import PropertyDefinition, PropertyCollection

class ColorEntry:
    # Static vars
    PROPERTY_COLOR = "Color"
    PROPERTY_SLOT = "Slot"
    PROPERTY_NAME = "Name"
    PROPERTY_FORCED_PALETTE = "RequiresPalette"

    sProperty_def_map = { 
        PROPERTY_COLOR: PropertyDefinition(False, True)
        , PROPERTY_SLOT: PropertyDefinition(False, False)
        , PROPERTY_FORCED_PALETTE: PropertyDefinition(False, False)
        , PROPERTY_NAME: PropertyDefinition(True, False) }

    def __init__(self):
        self.properties = PropertyCollection(ColorEntry.sProperty_def_map)

    @classmethod
    def copy_construct_from(cls, rhs):
        new_entry = cls()
        new_entry.properties = PropertyCollection.copy_construct_from(rhs.properties)

        return new_entry

    def is_empty(self):
        # A ColorEntry is considered empty if it has no properties set.
        for prop_name in ColorEntry.sProperty_def_map.keys():
            if self.properties.get_property(prop_name) is not None:
                # We're not empty if we have a property set
                return False
        
        # We're empty!
        return True
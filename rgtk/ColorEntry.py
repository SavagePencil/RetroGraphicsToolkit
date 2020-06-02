from rgtk.Intention import IntentionDefinition, IntentionCollection

class ColorEntry:
    # Static vars
    INTENTION_COLOR = "Color"
    INTENTION_SLOT = "Slot"
    INTENTION_NAME = "Name"
    INTENTION_FORCED_PALETTE = "RequiresPalette"

    sIntention_def_map = { 
        INTENTION_COLOR: IntentionDefinition(is_unique=False, is_required=True)
        , INTENTION_SLOT: IntentionDefinition(is_unique=False, is_required=False)
        , INTENTION_FORCED_PALETTE: IntentionDefinition(is_unique=False, is_required=False)
        , INTENTION_NAME: IntentionDefinition(is_unique=True, is_required=False) }

    def __init__(self):
        self.intentions = IntentionCollection(ColorEntry.sIntention_def_map)

    @classmethod
    def copy_construct_from(cls, rhs: 'ColorEntry') -> 'ColorEntry':
        new_entry = cls()
        new_entry.intentions = IntentionCollection.copy_construct_from(rhs.intentions)

        return new_entry

    def is_empty(self) -> bool:
        # A ColorEntry is considered empty if it has no intentions set.
        for prop_name in ColorEntry.sIntention_def_map.keys():
            if self.intentions.get_intention(prop_name) is not None:
                # We're not empty if we have an intention set
                return False
        
        # We're empty!
        return True
from rgtk.Pattern import Pattern

class NameTableEntry:
    # Static Vars
    def __init__(self, VRAM_loc: int, palette_index: int, flips: Pattern.Flip):
        self.VRAM_loc = VRAM_loc
        self.palette_index = palette_index
        self.flips = flips
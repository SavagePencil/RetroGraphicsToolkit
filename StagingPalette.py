from ColorEntry import ColorEntry

# The staging palette holds ColorEntries, which have properties that determine
# which pixel values will end up in which slot when transformed into a final
# palette.
class StagingPalette:
    def __init__(self, num_slots):
        self.color_entries = []
        while num_slots > 0:
            self.color_entries.append(ColorEntry())
            num_slots = num_slots - 1

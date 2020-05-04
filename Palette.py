from ColorEntry import ColorEntry

class Palette:
    def __init__(self, num_slots):
        self.colors = []
        while num_slots > 0:
            self.colors.append(ColorEntry())
            num_slots = num_slots - 1
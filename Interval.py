from typing import Tuple

class Interval:
    def __init__(self, slot_range: Tuple[int, int], length: int):
        self.slot_range = slot_range
        self.length = length

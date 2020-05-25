from typing import List, Mapping

class IndexedColorArray:
    def __init__(self, width: int, height: int, indexed_array: List[int]):
        self.width = width
        self.height = height
        self.array = indexed_array

    # Remaps the contents of the array via a lookup table.
    # For example if our indexed array is all 0s and 1s,
    # the remap could be an array of 2 elements with the 
    # value for 0s and the value for 1s.
    def remap_contents(self, content_remap_list: List[int]):
        for idx in range(len(self.array)):
            content = self.array[idx]
            new_val = content_remap_list[content]
            self.array[idx] = new_val

    def get_value(self, x: int, y: int) -> int:
        idx = (y * self.width) + x
        return self.array[idx]

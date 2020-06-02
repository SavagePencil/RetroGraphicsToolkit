from typing import Tuple, Mapping, List
from rgtk import Quantize
from PIL import Image
from rgtk.IndexedColorArray import IndexedColorArray

class PixelArray:
    def __init__(self, src_img: Image, src_x: int, src_y: int, width: int, height: int):
        self.width = width
        self.height = height

        self.pixels = []

        for row in range(src_y, src_y + height):
            for col in range(src_x, src_x + width):
                pixel = src_img.getpixel((col, row))
                self.pixels.append(pixel)

    def get_pixel_value(self, x: int, y: int) -> object:
        idx = (y * self.width) + x
        return self.pixels[idx]

    def quantize(self, src_bits_tuple: Tuple, target_bits_tuple: Tuple):
        src_maxes = tuple([2**bpp for bpp in src_bits_tuple])
        target_maxes = tuple([2**bpp for bpp in target_bits_tuple])

        for pixel_idx in range(0, len(self.pixels)):
            old_color = self.pixels[pixel_idx]
            new_color = Quantize.quantize_tuple_to_source(old_color, src_maxes, target_maxes)            
            self.pixels[pixel_idx] = new_color

    def generate_pixel_to_index_map(self) -> Mapping[object, int]:
        pixel_to_index_map = {}

        for pixel in self.pixels:
            if pixel not in pixel_to_index_map:
                # It's unique.
                index = len(pixel_to_index_map)
                pixel_to_index_map[pixel] = index

        return pixel_to_index_map

    # Generates a DETERMINISTIC list of the unique pixels, determined
    # by walking the pixel array from left to right, top to bottom.
    def generate_deterministic_unique_pixel_list(self) -> List[object]:
        unique_pixels = []

        # Keep a set around for faster lookup.
        pixels_seen_set = set()
        
        for pixel in self.pixels:
            if pixel not in pixels_seen_set:
                # Append this to the uniques list.
                unique_pixels.append(pixel)

                # And add it to the set for faster lookup.
                pixels_seen_set.add(pixel)
        
        return unique_pixels

    def generate_indexed_color_array(self) -> IndexedColorArray:
        pixel_to_index_map = self.generate_pixel_to_index_map()
        indexed_array = []
        for pixel in self.pixels:
            idx = pixel_to_index_map[pixel]
            indexed_array.append(idx)

        return IndexedColorArray(width=self.width, height=self.height, indexed_array=indexed_array)


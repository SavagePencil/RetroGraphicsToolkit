from typing import Tuple
import Quantize
from PIL import Image

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

import Quantize

class PixelArray:
    def __init__(self, src_img, src_x, src_y, width, height):
        self._width = width
        self._height = height

        self.pixels = []

        for row in range(src_y, src_y + height):
            for col in range(src_x, src_x + width):
                pixel = src_img.getpixel((col, row))
                self.pixels.append(pixel)

    def quantize(self, src_bpp, target_bpp):
        src_maxes = tuple([2**bpp for bpp in src_bpp])
        target_maxes = tuple([2**bpp for bpp in target_bpp])

        for pixel_idx in range(0, len(self.pixels)):
            old_color = self.pixels[pixel_idx]
            new_color = Quantize.quantize_tuple_to_source(old_color, src_maxes, target_maxes)            
            self.pixels[pixel_idx] = new_color

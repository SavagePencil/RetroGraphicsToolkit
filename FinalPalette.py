from ColorEntry import ColorEntry

# The final palette holds color (pixel) values in an array
class FinalPalette:
    def __init__(self, num_slots: int):
        self.final_pixels = []
        while num_slots > 0:
            self.final_pixels.append(FinalPixel())
            num_slots = num_slots - 1


class FinalPixel:
    def __init__(self):
        self._pixel_value = None

    def attempt_write_pixel_value(self, pixel_value: object):
        # These are write-once.
        if self._pixel_value is not None:
            if pixel_value != self._pixel_value:
                raise Exception()
        
        self._pixel_value = pixel_value

    def get_pixel_value(self) -> object:
        return self._pixel_value
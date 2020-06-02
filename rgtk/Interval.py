# Thrown when the begin is less than the end.
class IntervalIncorrectOrderError(Exception):
    def __init__(self, begin, end):
        self.begin = begin
        self.end = end


# Thrown when the length is <= 0 OR if the length
# cannot fit within the range specified.
class IntervalInvalidLengthError(Exception):
    def __init__(self, begin, end, length):
        self.begin = begin
        self.end = end
        self.length = length

# The interval class represents a range of values, with
# a length value defining how much space is required
# within that range.  For example, you may only need
# one space, but that one space can occur anywhere within
# the range of 0 to 10.  If you need a fixed position,
# length should be precisely the range of begin -> end.
# Note that begin and end are INCLUSIVE.
class Interval:
    def __init__(self, begin: int, end: int, length: int):
        self.begin = begin
        self.end = end
        self.length = length

        if end < begin:
            raise IntervalIncorrectOrderError(begin, end)

        total_range = end - begin + 1
        if (total_range < length) or (length <= 0):
            raise IntervalInvalidLengthError(begin, end, length)

    @classmethod
    def create_fixed_length_at_start_point(cls, begin: int, length: int) -> 'Interval':
        end = begin + length - 1
        new_interval = cls(begin, end, length)
        return new_interval

    @classmethod
    def create_fixed_length_from_end_point(cls, end: int, length: int) -> 'Interval':
        begin = end - length + 1
        new_interval = cls(begin, end, length)
        return new_interval


    @classmethod
    def create_from_fixed_range(cls, begin: int, end: int) -> 'Interval':
        length = end - begin + 1
        new_interval = cls(begin, end, length)
        return new_interval
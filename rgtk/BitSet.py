from typing import Optional

class MismatchedBitSetLengthError(Exception):
    def __init__(self):
        pass

class BitSet:
    def __init__(self, num_bits: int):
        self._bitset = 0
        self._num_bits = num_bits

    @classmethod
    def copy_construct_from(cls, rhs: 'BitSet') -> 'BitSet':
        new_entry = cls(rhs._num_bits)
        new_entry._bitset = rhs._bitset

        return new_entry

    def get_num_bits(self) -> int:
        return self._num_bits

    def is_set(self, bit_idx: int) -> bool:
        mask = 1 << bit_idx
        truth = (self._bitset & mask) != 0
        return truth
    
    def set_bit(self, bit_idx: int):
        mask = 1 << bit_idx
        self._bitset = self._bitset | mask

    def clear_bit(self, bit_idx: int):
        all_on = (1 << self._num_bits) - 1
        target = 1 << bit_idx
        mask = all_on ^ target
        self._bitset = self._bitset & mask

    def clear_all(self):
        self._bitset = 0

    def set_all(self):
        self._bitset = (1 << self._num_bits) - 1

    def get_next_unset_bit_index(self, start_idx: int) -> Optional[int]:
        for idx in range(start_idx, self._num_bits):
            if self.is_set(idx) == False:
                return idx
        return None

    def get_next_set_bit_index(self, start_idx: int) -> Optional[int]:
        for idx in range(start_idx, self._num_bits):
            if self.is_set(idx) == True:
                return idx
        return None

    def get_previous_unset_bit_index(self, start_idx: int) -> Optional[int]:
        for idx in range(start_idx, 0, -1):
            if self.is_set(idx) == False:
                return idx
        return None

    def get_previous_set_bit_index(self, start_idx: int) -> Optional[int]:
        for idx in range(start_idx, 0, -1):
            if self.is_set(idx) == True:
                return idx
        return None

    def are_all_set(self) -> bool:
        all_on = (1 << self._num_bits) - 1
        return self._bitset & all_on == all_on

    def are_all_clear(self) -> bool:
        return self._bitset == 0

    def get_num_bits_set(self) -> int:
        bits_set = 0
        temp_val = self._bitset
        while (temp_val != 0):
            if temp_val & 1 == 1:
                bits_set += 1
            temp_val = temp_val >> 1

        return bits_set

    def get_union_bitset(self, other: 'BitSet') -> 'BitSet':
        if self._num_bits != other._num_bits:
            raise MismatchedBitSetLengthError()

        union = self._bitset | other._bitset
        ret_val = BitSet(self._num_bits)
        ret_val._bitset = union
        return ret_val

    def get_intersection_bitset(self, other: 'BitSet') -> 'BitSet':
        if self._num_bits != other._num_bits:
            raise MismatchedBitSetLengthError()

        union = self._bitset & other._bitset
        ret_val = BitSet(self._num_bits)
        ret_val._bitset = union
        return ret_val

    def get_difference_bitset(self, other: 'BitSet') -> 'BitSet':
        if self._num_bits != other._num_bits:
            raise MismatchedBitSetLengthError()

        diff = self._bitset ^ other._bitset
        ret_val = BitSet(self._num_bits)
        ret_val._bitset = diff
        return ret_val

    def union_with(self, other: 'BitSet'):
        if self._num_bits != other._num_bits:
            raise MismatchedBitSetLengthError()

        self._bitset = self._bitset | other._bitset

    def intersect_with(self, other: 'BitSet'):
        if self._num_bits != other._num_bits:
            raise MismatchedBitSetLengthError()

        self._bitset = self._bitset & other._bitset

    def difference_with(self, other: 'BitSet'):
        if self._num_bits != other._num_bits:
            raise MismatchedBitSetLengthError()

        self._bitset = self._bitset ^ other._bitset

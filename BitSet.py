class BitSet:
    def __init__(self, num_bits: int):
        self._bitset = 0
        self._num_bits = num_bits

    @classmethod
    def copy_construct_from(cls, rhs: 'BitSet') -> 'BitSet':
        new_entry = cls(rhs._num_bits)
        new_entry._bitset = rhs._bitset

        return new_entry

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

    def get_next_unset_bit_index(self, start_idx: int) -> int:
        for idx in range(start_idx, self._num_bits):
            if self.is_set(idx) == False:
                return idx
        return None

    def get_next_set_bit_index(self, start_idx: int) -> int:
        for idx in range(start_idx, self._num_bits):
            if self.is_set(idx) == True:
                return idx
        return None

    def are_all_set(self) -> bool:
        all_on = (1 << self._num_bits) - 1
        return self._bitset & all_on == all_on

    def are_all_clear(self) -> bool:
        return self._bitset == 0


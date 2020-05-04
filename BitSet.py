class BitSet:
    def __init__(self, num_bits):
        self._bitset = 0
        self._num_bits = num_bits

    @classmethod
    def copy_construct_from(cls, rhs):
        new_entry = cls(rhs._num_bits)
        new_entry._bitset = rhs._bitset

        return new_entry

    def is_set(self, bit_idx):
        mask = 1 << bit_idx
        truth = (self._bitset & mask) != 0
        return truth
    
    def set_bit(self, bit_idx):
        mask = 1 << bit_idx
        self._bitset = self._bitset | mask

    def clear_bit(self, bit_idx):
        all_on = (1 << self._num_bits) - 1
        target = 1 << bit_idx
        mask = all_on ^ target
        self._bitset = self._bitset & mask

    def clear_all(self):
        self._bitset = 0

    def set_all(self):
        self._bitset = (1 << self._num_bits) - 1

    def get_next_unset_bit_index(self, start_idx):
        for idx in range(start_idx, self._num_bits):
            if self.is_set(idx) == False:
                return idx
        return None

    def get_next_set_bit_index(self, start_idx):
        for idx in range(start_idx, self._num_bits):
            if self.is_set(idx) == True:
                return idx
        return None

    def are_all_set(self):
        all_on = (1 << self._num_bits) - 1
        return self._bitset & all_on == all_on

    def are_all_clear(self):
        return self._bitset == 0


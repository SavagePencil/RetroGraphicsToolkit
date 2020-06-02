from typing import Tuple

def quantize_to_source(val: int, src_max: int, target_max: int) -> int:
    target_val = quantize_to_target(val, src_max, target_max)

    vals_per_step = (src_max - 1) / (target_max - 1)

    ret_val = int(target_val * vals_per_step)
    return ret_val

def quantize_to_target(val: int, src_max: int, target_max: int) -> int:
    return int(round((val / (src_max - 1)) * (target_max - 1)) )

def quantize_tuple_to_source(val_tuple: Tuple, src_max_tuple: Tuple, target_max_tuple: Tuple) -> Tuple:
    quantized_list = []

    for i in range(len(src_max_tuple)):
        src_max = src_max_tuple[i]
        target_max = target_max_tuple[i]

        orig_val = val_tuple[i]
        quantized_val = quantize_to_source(orig_val, src_max, target_max)
        quantized_list.append(quantized_val)

    ret_val = tuple(quantized_list)
    return ret_val

def quantize_tuple_to_target(val_tuple: Tuple, src_max_tuple: Tuple, target_max_tuple: Tuple) -> Tuple:
    quantized_list = []

    for i in range(len(src_max_tuple)):
        src_max = src_max_tuple[i]
        target_max = target_max_tuple[i]

        orig_val = val_tuple[i]
        quantized_val = quantize_to_target(orig_val, src_max, target_max)
        quantized_list.append(quantized_val)

    ret_val = tuple(quantized_list)
    return ret_val


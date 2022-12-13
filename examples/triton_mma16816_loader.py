from typing import *

from matshow import *

instr_shape = (16, 8, 16)
mat_shape = (8, 8)


def load(tile_shape: Tuple[int, int], order: Tuple[int, int], k_order: int, wpt: int):
    need_trans = k_order != order[0]
    num_ptrs = tile_shape[order[0]
                          ] // (wpt if need_trans else 1) // instr_shape[order[0]]
    num_ptrs = max(num_ptrs, 2)

    load_stride_in_mat = [0, 0]
    load_stride_in_mat[k_order] = 2
    load_stride_in_mat[k_order ^ 1] = wpt * \
        (instr_shape[k_order ^ 1]) // mat_shape[k_order ^ 1]

    p_load_stride_in_mat = load_stride_in_mat[order[0]]
    s_mat_stride = load_stride_in_mat[order[1]
                                      ] // (instr_shape[order[1]] // mat_shape[order[1]])

    mat_arr_stride = 1 if k_order == 1 else wpt
    warp_off_stride = instr_shape[k_order ^ 1] // mat_shape[k_order ^ 1]


def compute_mat_off()

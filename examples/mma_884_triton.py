from typing import *

from matshow import *


def compute_offsets(thread: int, is_a_row: bool, is_b_row, fpw: List[int], spw: List[int], rep: List[int],
                    wpt: List[int]):
    lane = thread % 32
    warp = thread // 32

    # (warp1, warp1) is a coord in tile
    warp12 = warp // wpt[0]
    warp0 = warp % wpt[0]  # warp coord
    warp1 = warp12 % wpt[1]

    # warp to abs-coord in tile
    warp_m_off = warp0 * spw[0]
    warp_n_off = warp1 * spw[1]

    # quad to abs-
    quad_m_off = (lane & 16) // 4 * fpw[0]
    quad_n_off = (lane & 16) // 4 * fpw[1]

    pair_m_off = lane % 16 // 4
    pair_m_off = pair_m_off % fpw[0]
    pair_m_off = pair_m_off * 4

    pair_n_off = lane % 16 // 4
    pair_n_off = pair_n_off // fpw[0]
    pair_n_off = pair_n_off % fpw[1]
    pair_n_off = pair_n_off * 4

    pair_m_off = pair_m_off * rep[0] // 2
    quad_m_off = quad_m_off * rep[0] // 2
    pair_n_off = pair_n_off * rep[1] // 2
    quad_n_off = quad_n_off * rep[1] // 2

    lane_m_off = pair_m_off + quad_m_off
    lane_n_off = pair_n_off + quad_n_off

    # A offset
    offset_am = warp_m_off + lane_m_off
    offset_ak = lane & 3
    # B offset
    offset_bn = warp_n_off + lane_n_off
    offset_bk = lane & 3

    if is_a_row:
        offset_am = offset_am + thread % 4
        offset_ak = 0
    if is_b_row:
        offset_bn = offset_bn + thread % 4
        offset_bk = 0

    return offset_am, offset_ak, offset_bk, offset_bn


def get_compute_offsets(thread: int, a_order, b_order, a_shape, b_shape):
    is_a_row = a_order[0] != 0
    is_b_row = b_order[0] != 0
    fpw = [2, 2, 1]
    is_a_vec4 = (not is_a_row) and a_shape[a_order[0]] <= 16
    is_b_vec4 = is_b_row and b_shape[b_order[0]] <= 16
    pack_size0 = 1 if (is_a_row or is_a_vec4) else 2
    pack_size1 = 2 if is_b_row and (not is_b_vec4) else 1

    rep = [2 * pack_size0, 2 * pack_size1, 1]
    spw = [fpw[0] * 4 * rep[0], fpw[1] * 4 * rep[1], 1]

    wpt = [1, 1]

    offset_am, offset_ak, offset_bk, offset_bn = compute_offsets(
        thread, is_a_row, is_b_row, fpw, spw, rep, wpt)
    print(offset_am, offset_ak, offset_bk, offset_bn)


def load_A(shape: List[int], order: List[int], vec: int, per_phase: int, max_phase: int):
    is_a_row = order[0] != 0
    is_a_vec4 = (not is_a_row) and shape[order[0]] <= 16
    pack_size0 = 1 if (is_a_row or is_a_vec4) else 2

    fpw = [2, 2, 1]  # a warp has 2x2 8x8 matrices
    rep_m = 2 * pack_size0
    rep_k = 1
    spw_m = fpw[0] * 4 * rep_m
    rep = [rep_m, 0, rep_k]
    spw = [spw_m, 0, 1]

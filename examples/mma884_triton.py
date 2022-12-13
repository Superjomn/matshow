from matshow import *
from matshow.widgets.gpu import WarpDataLayout
from typing import *
import numpy as np


class MMA884Loader:
    def __init__(self, a_shape: List[int], b_shape: List[int], c_shape: List[int],
                 a_order: List[int], b_order: List[int], c_order: List[int],
                 wpt: List[int]):
        self.a_shape = a_shape
        self.b_shape = b_shape
        self.c_shape = c_shape

        self.a_order = a_order
        self.b_order = b_order
        self.c_order = c_order

        self.wpt = wpt

        # is row mojor
        self.is_a_row = self.a_order[0] != 0
        self.is_b_row = self.b_order[0] != 0

        self.is_a_vec4 = (not self.is_a_row) and self.a_shape[a_order[0]] <= 16
        self.is_b_vec4 = self.is_b_row and b_shape[b_order[0]] <= 16
        self.pack_size0 = 1 if (self.is_a_row or self.is_a_vec4) else 2
        self.pack_size1 = 2 if (self.is_b_row and (not self.is_b_vec4)) else 1

        self.fpw = [2, 2, 1]
        self.rep = (2 * self.pack_size0, 2 * self.pack_size1, 1)
        self.spw = (self.fpw[0] * 4 * self.rep[0],
                    self.fpw[1] * 4 * self.rep[1], 1)

        self.stride_am = a_shape[1] if self.is_a_row else 1
        self.stride_ak = 1 if self.is_a_row else a_shape[0]
        self.stride_a = [self.stride_ak if self.is_a_row else self.stride_am,
                         self.stride_am if self.is_a_row else self.stride_ak]

        self.stride_bk = b_shape[1] if self.is_b_row else 1
        self.stride_bn = 1 if self.is_b_row else b_shape[0]
        self.stride_b = [
            self.stride_bn if self.is_b_row else self.stride_bk,
            self.stride_bk if self.is_b_row else self.stride_bn]

        self.stride_rep_m = self.wpt[0] * self.fpw[0] * 8
        self.stride_rep_n = self.wpt[1] * self.fpw[1] * 8
        self.stride_rep_k = 1

    def compute_off(self, thread: int):
        '''
        thread: thread id in the CTA
        '''
        lane = thread % 32
        warp = thread // 32

        warp0 = warp % self.wpt[0]
        warp12 = warp // self.wpt[0]
        warp1 = warp12 % self.wpt[1]
        warp_m_off = warp0 * self.spw[0]
        warp_n_off = warp1 * self.spw[1]
        # quad offset
        quad_m_off = (lane & 16) // 4 * self.fpw[0]
        quad_n_off = (lane & 16) // 4 * self.fpw[1]
        # pair offset
        pair_m_off = lane % 16 // 4
        pair_m_off = pair_m_off % self.fpw[0]
        pair_m_off = pair_m_off * 4

        pair_n_off = lane % 16 // 4
        pair_n_off = pair_n_off % self.fpw[1]
        pair_n_off = pair_n_off * 4

        # scale
        pair_m_off = pair_m_off * (self.rep[0] // 2)
        quad_m_off = quad_m_off * (self.rep[0] // 2)
        pair_n_off = pair_n_off * (self.rep[1] // 2)
        quad_n_off = quad_n_off * (self.rep[1] // 2)


def draw_mma884_C(is_a_vec4: bool, is_b_vec4: bool, shape: List[int], shape_per_cta: List[int],
                  ord_a=[1, 0], ord_b=[1, 0],
                  wpt: List[int] = [1, 1]):
    '''
    Get ids from the m and n axis.
    '''
    fpw = [2, 2, 1]
    warps = np.product(wpt)
    assert warps == 1
    is_a_row = ord_a[0] != 0
    is_b_row = ord_b[0] != 0
    pack_size0 = 1 if is_a_row or is_a_vec4 else 2
    pack_size1 = 2 if is_b_row and (not is_b_vec4) else 1
    rep = [2 * pack_size0, 2 * pack_size1, 1]
    spw = [fpw[0] * 4 * rep[0], fpw[1] * 4 * rep[1], 1]

    def thread_to_cells(thread: int):
        lane = thread % 32
        warp = thread // 32

        warp_0 = warp % wpt[0]
        warp_12 = warp // wpt[0]
        warp_1 = warp % wpt[1]

        # warp offset
        off_warp_m = warp_0 * spw[0]
        off_warp_n = warp_1 * spw[1]
        # quad offset
        off_quad_m = (lane & 16) // 4 * fpw[0]
        off_quad_n = (lane & 16) // 4 * fpw[1]
        # pair offset
        off_pair_m = (lane % 16) // 4
        off_pair_m = off_pair_m % fpw[0]
        off_pair_m = off_pair_m * 4
        off_pair_n = (lane % 16) // 4
        off_pair_n = off_pair_n // fpw[0]
        off_pair_n = off_pair_n % fpw[1]
        off_pair_n = off_pair_n * 4

        # scale
        off_pair_m = off_pair_m * (rep[0] // 2)
        off_quad_m = off_quad_m * (rep[0] // 2)
        off_pair_n = off_pair_n * (rep[1] // 2)
        off_quad_n = off_quad_n * (rep[1] // 2)

        # quad pair offset
        off_lane_m = off_pair_m + off_quad_m
        off_lane_n = off_pair_n + off_quad_n
        # a, b offset
        offset_a_m = off_warp_m + off_lane_m
        offset_b_n = off_warp_n + off_lane_n
        # i indices
        offset_c_m = (lane & 1) + offset_a_m
        idx_m = []
        for m in range(shape[0], shape_per_cta[0]):
            for mm in range(rep[0]):
                idx_m.append(offset_c_m + m + mm * 2)
        offset_c_n = (lane & 2) + off_warp_n + off_pair_n
        idx_n = []
        for n in range(shape[1], shape_per_cta[1]):
            for nn in range(rep[1]):
                idx_n.append(offset_c_n + n + nn // 2 * 4 + nn % 2 * 2 * fpw[1] * rep[1])
                idx_n.append(offset_c_n + n + nn // 2 * 4 + nn % 2 * 2 * fpw[1] * rep[1] + 1)

        for m in idx_m:
            for n in idx_n:
                yield (m, n)

        c_mat = WarpDataLayout(shape=shape, label="C")
        c_mat.set_thread_to_cells_map(thread_to_cells)
        c_mat.draw()
        c_mat.show()


draw_mma884_C(shape=[32, 16], shape_per_cta=[32, 16], is_a_vec4=True, is_b_vec4=True)

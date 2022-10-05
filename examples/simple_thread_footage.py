import math

import matshow
from matshow import gpu, relation

# ====== View =====
CTA = matshow.TensorView([4, 8], cell_config=matshow.CellConfig(
    width=10, fill=matshow.Widget.fill_colors[0]))
A = matshow.TensorView([16, 16], cell_config=matshow.CellConfig(
    width=10, fill=matshow.Widget.fill_colors[1]))
B = matshow.TensorView([16, 8], cell_config=matshow.CellConfig(
    width=10, fill=matshow.Widget.fill_colors[2]))
C = matshow.TensorView([16, 8], cell_config=matshow.CellConfig(
    width=10, fill=matshow.Widget.fill_colors[3]))

# CTA.drawer.text("CTA", 40, pos=('mid', 'mid'), fill=matshow.colors.GRAY)
A.drawer.text("A", 30, pos=('mid', 'mid'), fill=matshow.colors.GRAY)
B.drawer.text("B", 30, pos=('mid', 'mid'), fill=matshow.colors.GRAY)
C.drawer.text("C", 30, pos=('mid', 'mid'), fill=matshow.colors.GRAY)

stack = matshow.Stack(widgets=[A.drawer, B.drawer, C.drawer], cstride=2)

# Mapping logic
CTA_to_C = matshow.Relation(C)
C_to_A = matshow.Relation(A)
C_to_B = matshow.Relation(B)

CTA.add_relation(CTA_to_C)
C.add_relation(C_to_A)
C.add_relation(C_to_B)

threads = CTA.numel()


def C_to_A_fn(C_off):
    shape = C.shape
    cstride = 1
    sstride = shape[1]
    row = C_off // sstride
    col = C_off % sstride
    # entire row of A
    A_row_stride = A.shape[1]
    return range(row * A_row_stride, (row + 1) * A_row_stride)


def C_to_B_fn(C_off):
    shape = C.shape
    cstride = 1
    sstride = shape[1]
    row = C_off // sstride
    col = C_off % sstride
    # entire row of A
    B_col_stride = B.shape[1]
    res = []
    for i in range(B.shape[0]):
        res.append(col + i * B_col_stride)
    return res


size_per_thread = math.ceil(C.numel() / threads)
CTA_to_C.set_map(lambda tid: range(
    size_per_thread * tid, size_per_thread * (tid + 1)))
C_to_A.set_map(C_to_A_fn)
C_to_B.set_map(C_to_B_fn)

#import cProfile
#cProfile.run('gpu.create_animation(stack, "./cta.gif", C, range(threads), duration=0.1)')
gpu.create_animation(stack, "./cta.gif", C, range(C.numel()), duration=0.1)

import random
from typing import *

from matshow import *
from matshow import colors
from matshow.widgets.gpu import WarpDataLayout

M = 16
N = 8
K = 32

cell_size = 40

############ Operands ###########

A = WarpDataLayout(shape=(M, K), cell_size=cell_size, label="$a")
B = WarpDataLayout(shape=(K, N), cell_size=cell_size, label="$b")

############# main view ########
operand_view = HStack()  # contains two operands
operand_view.add(A)
operand_view.add(B)

overall_view = VStack(widgets=[operand_view, ])
view = LabeledWidget("mma.m16n8k32.u8 layout",
                     fontsize=60, main_widget=overall_view)


def A_thread_to_data_coors(thread: int):
    lane = thread % 32
    group = lane // 4
    thread_in_group = lane % 4
    for i in range(16):
        row = group if (0 <= i < 4) or (8 <= i < 12) else group + 8
        col = thread_in_group * 4 + \
            (i & 0x3) if i < 8 else thread_in_group * 4 + (i & 0x3) + 16
        yield row, col


def B_thread_to_data_coors(thread: int):
    lane = thread % 32
    group = lane // 4
    thread_in_group = lane % 4
    for i in range(8):
        row = thread_in_group * 8 + (i & 0x7)
        col = group
        yield row, col


A.set_thread_to_cells_map(A_thread_to_data_coors)
B.set_thread_to_cells_map(B_thread_to_data_coors)

view.draw()
view.show()

view.save("./mma_16832.png")

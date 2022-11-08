import random
from typing import *

from matshow import *
from matshow import colors

M = 16
N = 8
K = 32

cell_size = 40

############ Operands ###########
A = Matrix(shape=(M, K), border=1, margin=(20, 20),
           cell_config=CellConfig(width=cell_size))
B = Matrix(shape=(K, N), border=1, margin=(20, 20),
           cell_config=CellConfig(width=cell_size))
#A.text("A", fontsize=20, fill=colors.GRAY1)
#B.text("B", fontsize=20, fill=colors.GRAY1)

############# mma ###########
MMA = Matrix(shape=(M, N), border=1, margin=(20, 20))

############# main view ########


A_view = LabeledWidget("$a", fontsize=40, main_widget=A)
B_view = LabeledWidget("$a", fontsize=40, main_widget=B)

operand_view = HStack()  # contains two operands
operand_view.add(A_view)
operand_view.add(B_view)

overall_view = VStack(widgets=[operand_view, ])
view = LabeledWidget("mma.m16n8k32.u8", fontsize=40, main_widget=overall_view)


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


thread_colors = [colors.RGB(*[random.randint(0, 256)
                            for i in range(3)]) for i in range(32)]

for thread in range(32):
    for (row, col) in A_thread_to_data_coors(thread):
        cell = A.get_cell(row, col)
        cell.fill = thread_colors[thread]
        cell.text("t%d" % thread, fontsize=cell_size//2, fill=colors.YELLOW1)

    labeled = False
    for (row, col) in B_thread_to_data_coors(thread):
        cell = B.get_cell(row, col)
        cell.fill = thread_colors[thread]
        cell.text("t%d" % thread, fontsize=cell_size//2, fill=colors.YELLOW1)


draw_, im = create_canvas(size=view.outer_size, fill=colors.WHITE)
view.draw(draw_)
im.show("demo")

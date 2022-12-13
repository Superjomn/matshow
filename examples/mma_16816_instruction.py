import random
from typing import *

import click

from matshow import HStack, LabeledWidget, VStack
from matshow.widgets.gpu import WarpDataLayout

M = 16
N = 8
K = 16

cell_size = 40

A = WarpDataLayout(shape=(M, K), label="$a")
B = WarpDataLayout(shape=(K, N), label="$b")
C = WarpDataLayout(shape=(M, N), label="accumulator $c/$d")


def A_thread_to_cells(threadid: int) -> List[Tuple[int, int]]:
    lane = threadid % 32
    group_id = lane >> 2
    threadid_in_group = lane % 4
    for i in range(8):
        row = group_id if 0 <= i < 2 or 4 <= i < 6 else group_id + 8
        col = threadid_in_group * 2 + \
            (i & 0x1) if i < 4 else threadid_in_group * 2 + (i & 0x1) + 8
        yield row, col


def B_thread_to_cells(threadid: int) -> List[Tuple[int, int]]:
    lane = threadid % 32
    group_id = lane >> 2
    threadid_in_group = lane % 4

    for i in range(4):
        row = threadid_in_group * 2 + (i & 0x1) if i < 2 else \
            threadid_in_group * 2 + (i & 0x1) + 8
        col = group_id
        yield row, col


def C_thread_to_cells(threadid: int) -> List[Tuple[int, int]]:
    lane = threadid % 32
    group_id = lane >> 2
    threadid_in_group = lane % 4
    for i in range(4):
        row = group_id if i < 2 else group_id + 8
        col = threadid_in_group * 2 + (i & 0x1)
        yield row, col


A.set_thread_to_cells_map(A_thread_to_cells)
B.set_thread_to_cells_map(B_thread_to_cells)
C.set_thread_to_cells_map(C_thread_to_cells)

# ========================== View ###########################
main_view = LabeledWidget(label="mma.m16n8k16.f16/bf16", fontsize=40)


@click.command()
@click.option("--draw", type=click.Choice(["ABC", "AB", "C"], case_sensitive=False), default="ABC", show_default=True)
@click.option("-o", "--output", default="./mma.16816.png", show_default=True)
@click.option("-s", "--show/--no-show", "show")
def draw(draw, output, show):
    if draw == "AB":
        view = draw_AB()
    elif draw == "ABC":
        view = draw_ABC()
    elif draw == "C":
        view = draw_C()

    view.draw()

    if show:
        view.show()
    view.save(output)


def draw_ABC():
    content_view = HStack([A, B, C])
    main_view.set_main_widget(content_view)
    return main_view


def draw_C():
    main_view.set_main_widget(C)
    return main_view


def draw_AB():
    content_view = HStack([A, B])
    main_view.set_main_widget(content_view)
    return main_view


if __name__ == '__main__':
    draw()

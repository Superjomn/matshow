import random
from typing import *

import click
import numpy as np

from matshow import *
from matshow.widgets.gpu import WarpDataLayout


def wpt(shape=(4, 8)):
    mat = WarpDataLayout(
        shape=shape, label="threadsPerWarp: [4,8]", random_seed=2)

    def thread_to_cells(threadid: int) -> List[Tuple[int, int]]:
        r = threadid // shape[1]
        c = threadid % shape[1]
        yield r, c

    mat.set_thread_to_cells_map(thread_to_cells)

    mat.draw()
    mat.show()


def spw(wpt=(4, 8), sizePerThread=(2, 2)):
    shapePerThread = np.array(wpt) * np.array(sizePerThread)
    mat = WarpDataLayout(
        shape=shapePerThread, label="threadsPerWarp=[4,8]; sizePerThread=[2,2]", random_seed=2)

    def thread_to_cells(threadid: int) -> List[Tuple[int, int]]:
        r = threadid // wpt[1]
        c = threadid % wpt[1]
        for i in range(np.product(sizePerThread)):
            rr = r * 2 + i // sizePerThread[1]
            cc = c * 2 + i % sizePerThread[1]
            yield rr, cc

    mat.set_thread_to_cells_map(thread_to_cells)

    mat.draw()
    mat.show()


def memory_swizzle_widget(label: str, swizzled: bool):
    data_shape = np.array((8, 8))

    per_phase = 1
    max_phase = 8
    num_banks = 32

    def swizzle(row, offset):
        phase = row // per_phase % max_phase
        return offset ^ phase

    def offsets(row):
        for col in range(data_shape[1]):
            bank_id = (row * data_shape[1] + col) * 4 // 4 % 32
            col = swizzle(row, col) if swizzled else col
            yield bank_id, row, col

    view = LabeledWidget(label=label, fontsize=20)
    mat = Matrix(shape=data_shape, cell_config=Matrix.CellConfig(
        width=40), margin=(20, 10))

    random.seed(0)
    bank_colors = [colors.RGB(*[random.randint(0, 256)
                              for i in range(3)]) for i in range(num_banks)]
    for row in range(data_shape[0]):
        for bank_id, row, col in offsets(row):
            print(row, col)
            cell = mat.get_cell(row, col)
            cell.fill = bank_colors[bank_id]
            cell.text("%d" % bank_id, fontsize=15 if col ==
                      0 else 10, fill="red" if col == 0 else "black")

    view.set_main_widget(mat)
    return view


def swizzle():
    normal_view = memory_swizzle_widget("normal (bankid)", swizzled=False)
    swizzle_view = memory_swizzle_widget("swizzle (bankid)", swizzled=True)
    view = HStack(widgets=[normal_view, swizzle_view])
    view.draw()
    view.show()


@click.command()
@click.option("-r", "--run", default="wpt")
def main(run):
    if run == 'wpt':
        wpt()
    elif run == 'spw':
        spw()
    elif run == 'memory_swizzle':
        swizzle()


if __name__ == '__main__':
    main()

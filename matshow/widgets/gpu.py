import random
from typing import *

from matshow import *


class WarpDataLayout(LabeledWidget):
    '''
    Widget for visualizing the data layout of warp-wize GPU instructions.
    '''

    def __init__(self, shape: List[int], label,
                 thread_to_cell_map: Callable[[int], List[Tuple[int, int]]] = None,
                 fontsize=40, cell_size: int = 40, random_seed: int = 0):
        '''
        shape: shape of the data.
        label: label of the matrix.
        fontsize: font size of the label.
        thread_to_cells_map: a method mapping thread id to cell coordinates.
        '''
        super(WarpDataLayout, self).__init__(label, fontsize)

        self.cell_size = cell_size
        self.matrix = Matrix(shape=shape, border=1, margin=(20, 20),
                             cell_config=Matrix.CellConfig(width=self.cell_size))
        self.set_main_widget(self.matrix)

        self.thread_to_cells_map = thread_to_cell_map
        if self.thread_to_cells_map:
            self._colorize_cells()

        random.seed(random_seed)
        self.thread_colors = [colors.RGB(*[random.randint(0, 256)
                                           for i in range(3)]) for i in range(32)]

        # keep a snapshot of the map from thread to cell
        self.tid_to_cell_summary = []

    def set_thread_to_cells_map(self, thread_to_cell_map: Callable[[int], List[Tuple[int, int]]]):
        self.thread_to_cells_map = thread_to_cell_map
        self._colorize_cells()

    def _colorize_cells(self):
        self.tid_to_cell_summary.clear()
        for thread in range(32):
            this_thread = []
            for (row, col) in self.thread_to_cells_map(thread):
                cell = self.matrix.get_cell(row, col)
                cell.fill = self.thread_colors[thread]
                cell.text("t%d" % thread, fontsize=self.cell_size //
                                                   2, fill=colors.YELLOW1)
                this_thread.append((row, col))
            self.tid_to_cell_summary.append(this_thread)

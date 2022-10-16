from typing import *

from matshow import *
from matshow import relation as rel
from matshow.relation import Node as RelNode

queue = []
visited = set()
# create a matrix


def create_matrix(nrows: int, ncols: int, cell_config, start: int) -> TensorView:
    queue.append(start)
    # === view ===
    drawer = Tensor(shape=(nrows, ncols), cell_config=cell_config,
                    border=3, outline=Widget.border_colors[0])

    # === poplute ===

    def callback():
        global queue

        size = len(queue)
        for i in range(size):
            cur = queue[0]
            queue = queue[1:]

            if cur in visited:
                continue

            r = cur // ncols
            c = cur % ncols

            offsets = [-1, 0, 1, 0, -1]
            offset = r * ncols + c
            visited.add(offset)

            drawer.get_cell(offset).fill = Widget.fill_hl_colors[0]

            for i in range(4):
                x = c + offsets[i]
                y = r + offsets[i + 1]
                if x >= 0 and x < ncols and y >= 0 and y < nrows:
                    next = y * ncols + x
                    if next not in visited:
                        queue.append(next)
        return len(queue) > 0

    stack = Stack([drawer], cstride=1)

    create_animation_by_callback(
        stack, "./flood_fill.gif", callback, duration=0.1)


if __name__ == '__main__':
    create_matrix(20, 20, CellConfig(), start=100)

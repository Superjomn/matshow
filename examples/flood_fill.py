from typing import *

from matshow import *

queue = []
visited = set()


def create_matrix(nrows: int, ncols: int, cell_config, start: int, obstacles: Set[int] = None) -> TensorView:
    obstacles = obstacles if obstacles else set()
    queue.append(start)
    # === view ===
    matrix = Tensor(shape=(nrows, ncols), cell_config=cell_config,
                    border=3, outline=Widget.border_colors[0])
    view = Stack([matrix], margin=(20, 20), fill=colors.WHITE)
    view.set_label("Flood Fill Demo", fontsize=40)

    # draw obstacles
    for x in obstacles:
        matrix.get_cell(x).fill = colors.BLACK
        matrix.get_cell(x).text("X", fontsize=20)

    # === poplute ===

    def callback():
        global queue

        size = len(queue)
        for i in range(size):
            cur = queue[0]
            queue = queue[1:]

            if cur in visited or cur in obstacles:
                continue

            r = cur // ncols
            c = cur % ncols

            offsets = [-1, 0, 1, 0, -1]
            offset = r * ncols + c
            visited.add(offset)

            matrix.get_cell(offset).fill = Widget.fill_hl_colors[0]

            for i in range(4):
                x = c + offsets[i]
                y = r + offsets[i + 1]
                if x >= 0 and x < ncols and y >= 0 and y < nrows:
                    next = y * ncols + x
                    if next not in visited:
                        queue.append(next)
        return len(queue) > 0

    create_animation_by_callback(
        view, "./flood_fill.gif", callback, duration=0.1)


if __name__ == '__main__':
    obstacles = set([15 + 20*i for i in range(19)] +
                    [28 + 20*i for i in range(19)])
    obstacles.remove(15 + 10 * 20)
    obstacles.remove(28 + 13 * 20)
    create_matrix(20, 20, CellConfig(), start=100, obstacles=obstacles)

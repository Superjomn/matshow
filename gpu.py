import math

import draw
import relation
from relation import Relation
from typing import *
from draw import TensorDrawer, Rectangle, Widget, Stack


class TensorView(relation.Node):
    def __init__(self, shape: List[int]):
        super(TensorView, self).__init__(0, 31)
        self._shape = shape
        assert math.prod(shape) == 32, "a warp should contain 32 threads"
        self.drawer = TensorDrawer(shape=shape, cell_config=TensorDrawer.CellConfig(fill=Widget.fill_colors[0]),
                                   border=3, outline=Widget.border_colors[0])

        self.default_cell_color = self.drawer.cell_config.fill

    def _activate_impl(self, offset):
        '''
        Activate a cell.
        '''
        cell: Rectangle = self.drawer.get_cell(offset)
        cell.fill = Widget.fill_hl_colors[0]

    def _deactivate_impl(self, offset):
        cell: Rectangle = self.drawer.get_cell(offset)
        cell.fill = self.default_cell_color

    @property
    def shape(self):
        return self._shape


if __name__ == '__main__':
    warp = TensorView([4, 8])
    data = TensorView([4, 8])
    relation = Relation(data)
    relation.set_map(lambda i: i ^ 8)
    warp.add_relation(relation)
    stack = Stack([warp.drawer, data.drawer], cstride=2)

    for i in range(32):
        warp.activate(i)

        draw_, canvas = draw.create_canvas()
        stack.draw(draw_)

        canvas.save('./tmp-%d.png' % i, "PNG")

        warp.deactivate(i)

    import imageio

    images = []
    for i in range(32):
        filename = './tmp-%d.png' % i
        images.append(imageio.imread(filename))
    imageio.mimsave('movie.gif', images, 'GIF', duration=1)

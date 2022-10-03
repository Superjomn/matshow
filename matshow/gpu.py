import math
import os
import tempfile
from typing import *

from matshow import draw, relation
from matshow.draw import Rectangle, Stack, Tensor, Widget
from matshow.relation import Relation

CellConfig = Tensor.CellConfig


class TensorView(relation.Node):
    def __init__(self, shape: List[int], cell_config=Tensor.CellConfig(), activate_fill=(Widget.fill_hl_colors[1], Widget.fill_hl_colors[0])):
        super(TensorView, self).__init__(0, 31)
        self._shape = shape
        self.drawer = Tensor(shape=shape, cell_config=cell_config,
                             border=3, outline=Widget.border_colors[0])

        self.activate_fill = activate_fill

        self.default_cell_color = self.drawer.cell_config.fill

    def numel(self):
        return math.prod(self.shape)

    def _activate_impl(self, offset):
        '''
        Activate a cell.
        '''
        cell: Rectangle = self.drawer.get_cell(offset)
        if not cell:
            return  # overflow
        cell.fill = self.activate_fill[0]

    def _mark_impl(self, offset):
        cell: Rectangle = self.drawer.get_cell(offset)
        if not cell:
            return  # overflow
        cell.fill = self.activate_fill[1]

    def _deactivate_impl(self, offset):
        cell: Rectangle = self.drawer.get_cell(offset)
        cell.fill = self.default_cell_color

    @property
    def shape(self):
        return self._shape


def create_animation(main_widget: Widget, path: str, src_node: TensorView, activates=List[int], duration=1):
    with tempfile.TemporaryDirectory() as tmpdir:
        image_paths = []
        draw_, canvas = draw.create_canvas(main_widget.region_size())
        for i in activates:
            src_node.activate(i)
            main_widget.draw(draw_)
            img_path = os.path.join(tmpdir, '%d.png' % i)
            image_paths.append(img_path)
            canvas.save(img_path, "PNG")

            src_node.mark(i)

        draw.to_animation(image_paths, path, duration=duration)


if __name__ == '__main__':
    warp = TensorView([4, 8])
    data = TensorView([4, 8])
    relation = Relation(data)
    relation.set_map(lambda i: i ^ 8)
    warp.add_relation(relation)
    stack = Stack([warp.drawer, data.drawer], cstride=2)

    create_animation(stack, "./movie.gif", warp, range(32))

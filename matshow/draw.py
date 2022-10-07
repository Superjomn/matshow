__all__ = [
    'Widget', 'Rectangle', 'Stack', 'Tensor', 'to_animation',
    'Ruler',
    'create_canvas',
]

import abc
import math
from collections import OrderedDict, namedtuple
from typing import *

import imageio
from PIL import Image, ImageDraw, ImageFont

from matshow import colors

try:
    import torch
finally:
    class torch:
        class Tensor:
            pass

RESOLUTION = 1


def font(size):
    '''
    :param size:
    :return:
    '''
    path = "/Users/chunwei/Downloads/JetBrainsMono-2.242/fonts/ttf/JetBrainsMono-Light.ttf"
    font = ImageFont.truetype(path, size)
    return font


class Ruler:
    def __init__(self, width: int, height: int, resolution: int = 10, offset: Tuple[int, int] = None,
                 parent: "Ruler" = None):
        '''
        :param resolution: how many pieces the ruler has.
        :param width: relative width in current ruler system.
        :param height: relative height in current ruler system.
        :param offset: relative offset in parent ruler system.
        :param parent: the parent Ruler system.
        '''
        self.resolution = resolution
        self.parent = parent
        if offset:
            assert self.parent, "offset only works in parent Ruler system"
        self.offset = offset if offset else (0, 0)
        self.width = width
        self.height = height

    @property
    def piece(self) -> Tuple[int, int]:
        '''
        piece in x,y
        '''
        if not self.parent:
            return self.width / self.resolution, self.height / self.resolution
        piece = self.parent.piece
        return self.width * piece[0], self.height * piece[1]

    @property
    def abs_width(self):
        pass


class Widget(abc.ABC):
    Text = namedtuple('Text', 'content, fontsize, offset, fill')

    def __init__(self):
        self.texts: List[Widget.Text] = []

    @abc.abstractmethod
    def draw(self, draw_: ImageDraw, offset: tuple[int, int]):
        raise NotImplemented

    @abc.abstractmethod
    def region_size(self) -> Tuple[int, int]:
        raise NotImplemented

    def text(self, content: str, fontsize: int, fill=colors.BLACK,
             pos: Tuple[int, int] = ('mid', 'mid')):
        '''
        :param poses: one of ('mid', 'left', 'right', 'top', 'bottom)
        '''
        VALID_POS = ('mid', 'left', 'right', 'top', 'bottom')
        assert pos[0] in VALID_POS and pos[1] in VALID_POS
        chars = len(content)
        the_font = font(fontsize)
        # get the true size with the font
        text_size = the_font.getsize(content)

        def get_offset(sizes: int, poses: str, i: int):
            assert len(sizes) == len(poses)

            pos = poses[i]
            size = sizes[i]
            if pos == 'mid':
                if i == 1:  # y
                    return max(size // 2 - text_size[i] // 2, 0)
                return max(size // 2 - text_size[i] // 2, 0)
            elif pos == 'left':
                return 0
            elif pos == 'right':
                return size - text_size[i]
            elif pos == 'top':
                return 0
            elif pos == 'bottom':
                return size - text_size[i]
            else:
                assert False, "pos: %s is not supported" % pos

        size = self.region_size()
        offset = [get_offset(size, pos, i) for i in range(2)]

        text = Widget.Text(content, fontsize, offset, fill)
        self.texts.append(text)

    fill_colors = [
        colors.ANTIQUEWHITE,
        colors.AQUAMARINE1,
        colors.AZURE2,
        colors.BISQUE1,
        colors.CADETBLUE,
        colors.DARKSEAGREEN3,
        colors.LIGHTPINK1,
    ]

    fill_hl_colors = [
        colors.HOTPINK,
        colors.ORANGERED1,
        colors.SALMON,
        colors.YELLOW1,
    ]

    border_colors = [
        colors.BANANA,
        colors.BLUEVIOLET,
        colors.BURNTSIENNA,
        colors.BLUE4,
    ]


class Rectangle(Widget):
    def __init__(self, width, height, fill, outline, border):
        super(Rectangle, self).__init__()
        self.width = width
        self.height = height
        self.fill = fill
        self.outline = outline
        self.border = border

    def __repr__(self):
        return '<Rectangle %s>' % hash(self)

    def draw(self, draw_: ImageDraw, offset):
        self.offset = offset
        coor = [self.offset[0], self.offset[1], self.offset[0] + self.width + 2 * self.border,
                self.offset[1] + self.width + 2 * self.border]
        draw_.rectangle(coor,
                        fill=self.fill,
                        outline=self.outline,
                        width=self.border)

        # draw texts
        for txt in self.texts:
            off = (
                offset[0] + self.border + txt.offset[0],
                offset[1] + self.border + txt.offset[1],
            )
            draw_.text(text=txt.content, xy=off,
                       font=font(txt.fontsize), fill=txt.fill)

    def _draw_text(self, draw_: ImageDraw):
        for txt in self.texts:
            draw_.text(txt.content, font=font(txt.fontsize),
                       offset=txt.offset, fill=txt.fill)

    def region_size(self) -> Tuple[int, int]:
        width = self.width + 2 * self.border
        height = self.height + 2 * self.border
        return (width, height,)

    @property
    def region_coor(self) -> Tuple[List[int]]:
        '''
        return four coordinates of the rectangle region this widget covers.
        '''
        xl = (self.x, self.y)
        xr = (self.x + self.width + self.border * 2, self.y)
        yl = (self.x, self.y + self.height)
        yr = (self.x + self.width + self.border * 2,
              self.y + self.height + self.border * 2)
        return (xl, xr, yl, yr,)

    @property
    def x(self) -> int:
        return self.offset[0]

    @property
    def y(self) -> int:
        return self.offset[1]


class Stack(Widget):
    def __init__(self, widgets: List[Widget] = None, cstride=1, border=0, fill=None, outline=None):
        super(Stack, self).__init__()
        self.cstride = cstride
        self.border = border
        self.fill = fill
        self.outline = outline
        self.widgets = [] if not widgets else widgets

    def add(self, widget: Widget):
        assert widget != self, "recursion found"
        self.widgets.append(widget)

    def __repr__(self):
        return '<Stack #%d %s>' % (len(self.widgets), hash(self))

    def set_border(self, border: int):
        self.border = border

    def set_fill(self, fill):
        self.fill = fill

    def set_outline(self, outline):
        self.outline = outline

    def get_cell(self, offset):
        if type(self.widgets[0]) is Stack:
            stride = self.widgets[0].total_stride
            idx = offset // stride
            return self.widgets[idx].get_cell(offset % stride)
        if offset >= len(self.widgets):
            return None
        return self.widgets[offset]

    @property
    def total_stride(self):
        assert self.widgets
        cls = type(self.widgets[0])
        for other in self.widgets[1:]:
            assert type(
                other) is cls, "in total_stride, all the widgets should be the same type"
        if cls is Stack:
            return self.cstride * self.widgets[0].total_stride
        return self.cstride

    def draw(self, draw_: ImageDraw, offset=(0, 0)):
        # assert len(self.widgets) % self.cstride == 0
        if self.border > 0:
            draw_.rectangle(self.region_coor(offset), width=self.border, fill=self.fill,
                            outline=self.outline)
        offset_y = offset[1] + self.border
        for i in range(math.ceil(len(self.widgets) / self.cstride)):
            offset_x = offset[0] + self.border
            max_col_size = 0
            for j in range(self.cstride):
                abs_offset = i * self.cstride + j
                if abs_offset >= len(self.widgets):
                    break
                cur = self.widgets[abs_offset]
                assert cur != self
                cur.draw(draw_, (offset_x, offset_y))
                offset_x += cur.region_size()[0]
                max_col_size = max(max_col_size, cur.region_size()[1])
            offset_y += max_col_size  # no overlap

        # draw texts
        for txt in self.texts:
            off = (offset[0] + self.border + txt.offset[0],
                   offset[1] + self.border + txt.offset[1])
            draw_.text(text=txt.content, xy=off,
                       font=font(txt.fontsize), fill=txt.fill)

    def region_size(self) -> Tuple[int, int]:
        x0, y0, x1, y1 = self.region_coor((0, 0))
        return [x1 - x0, y1 - y0]

    def region_coor(self, offset) -> Tuple[int, int, int, int]:
        max_x_size = 0
        max_y_size = 0
        for i in range(math.ceil(len(self.widgets) / self.cstride)):
            x_size = 0
            y_size = 0
            for j in range(self.cstride):
                abs_offset = i * self.cstride + j
                if abs_offset >= len(self.widgets):
                    break
                cur = self.widgets[i * self.cstride + j]
                x_size += cur.region_size()[0]
                y_size = max(y_size, cur.region_size()[1])
            max_x_size = max(max_x_size, x_size)
            max_y_size += y_size

        xr = offset[0] + max_x_size + 2 * self.border
        yr = offset[1] + max_y_size + 2 * self.border
        return (*offset, xr, yr)


def create_canvas(size=(500, 300), fill=(128, 128, 128)) -> Tuple[ImageDraw.ImageDraw, Image.Image]:
    im = Image.new('RGB', size, fill)
    draw = ImageDraw.Draw(im)
    return draw, im


class Tensor(Widget):
    class CellConfig:
        def __init__(self, width: int = 20, height: int = None, fill=colors.SANDYBROWN, border=1,
                     outline=colors.SEAGREEN4):
            self.width = width
            self.height = height if height else width
            self.fill = fill
            self.border = border
            self.outline = outline

        @property
        def dict_(self) -> Dict[str, int]:
            return dict(width=self.width,
                        height=self.height,
                        fill=self.fill,
                        border=self.border,
                        outline=self.outline)

    def __init__(self, shape: List[int], data: torch.Tensor = None, border=0, outline=None,
                 cell_config=CellConfig(20, 20)):
        super(Tensor, self).__init__()
        assert len(
            shape) <= 3, "Tensor with more than 3 dimensions is not visualized yet."
        self.border = border
        self.outline = outline
        self.cell_config = cell_config
        self.shape = shape
        self.data = data if data else [i for i in range(math.prod(self.shape))]
        self.stack = self.get_main()

    def draw(self, draw_: ImageDraw, offset=(0, 0), fill=None, border=0):
        self.stack.draw(draw_, offset)

        # draw texts
        for txt in self.texts:
            off = (offset[0] + self.border + txt.offset[0],
                   offset[1] + self.border + txt.offset[1])
            draw_.text(text=txt.content, xy=off,
                       font=font(txt.fontsize), fill=txt.fill)

    def region_size(self) -> Tuple[int, int]:
        size = self.stack.region_size()
        size[0] = size[0] + 2 * self.border
        size[1] = size[1] + 2 * self.border
        return size

    def get_cell(self, offset):
        return self.stack.get_cell(offset)

    def get_main(self):
        rank = len(self.shape)
        if rank == 1:
            stack = Stack(cstride=self.shape[0], border=2,
                          outline=Widget.border_colors[0])
            for i in range(self.shape[0]):
                cell = Rectangle(**self.cell_config.dict_)
                stack.add(cell)
        elif rank == 2:
            stack = Stack(cstride=self.shape[1], border=2,
                          outline=Widget.border_colors[0])
            for i in range(self.shape[0] * self.shape[1]):
                cell = Rectangle(**self.cell_config.dict_)
                stack.add(cell)
        elif rank == 3:
            stack = Stack(cstride=self.shape[0], border=2,
                          outline=Widget.border_colors[0])
            for i in range(self.shape[0]):
                row = Stack(
                    cstride=self.shape[1], border=2, fill=Widget.border_colors[1])
                for j in range(self.shape[1] * self.shape[2]):
                    cell = Rectangle(**self.cell_config.dict_)
                    row.add(cell)
                stack.add(row)
        return stack


def to_animation(image_paths: List[str], gif_path: str, duration: int = 1):
    images = [imageio.imread(path) for path in image_paths]
    print('gif_path', gif_path)
    imageio.mimsave(gif_path, images, 'GIF', duration=duration)


if __name__ == '__main__':
    draw, canvas = create_canvas(size=(2200, 2200))

    '''
    rec = Rectangle(40, 40, fill=colors.TURQUOISE.tuple_, outline=colors.THISTLE4, border=2)
    rec.text('1', fontsize=20, fill=colors.RED1, offset=(4, 4))
    recs = [rec for i in range(20)]

    main = Stack(cstride=3)
    table0 = Stack(recs, 4, border=4, outline=colors.SGIBEET)
    table1 = Stack([rec for i in range(20)], border=2, outline=Widget.border_colors[0], cstride=10)

    main.add(table0)
    main.add(table1)
    main.add(table0)
    main.add(table1)
    main.add(table0)
    main.add(table1)

    main.draw(draw)
    '''

    tensor = Tensor(shape=[16, 16], cell_config=Tensor.CellConfig(width=40))
    tensor.draw(draw)

    canvas.show('demo')

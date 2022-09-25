import math

from PIL import Image, ImageDraw, ImageFont
from typing import *
import colors
from collections import namedtuple, OrderedDict
import abc


def font(size):
    path = "C:/Users/yanch/Downloads/JetBrainsMono-2.242/fonts/ttf/JetBrainsMono-Light.ttf"
    return ImageFont.truetype(path, size)


class Widget(abc.ABC):
    Text = namedtuple('Text', 'content, fontsize, offset, fill')

    def __init__(self):
        self.texts: List[Widget.Text] = []

    @abc.abstractmethod
    def draw(self, draw_: ImageDraw, offset: tuple[int, int]):
        NotImplemented

    @abc.abstractmethod
    def region_size(self) -> Tuple[int, int]:
        NotImplemented

    def text(self, content: str, fontsize: int, offset: Tuple[int, int], fill=colors.BLACK):
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
            off = (offset[0] + self.border + txt.offset[0],
                   offset[1] + self.border + txt.offset[1])
            draw_.text(text=txt.content, xy=off, font=font(txt.fontsize), fill=txt.fill)

    def _draw_text(self, draw_: ImageDraw):
        for txt in self.texts:
            draw_.text(txt.content, font=font(txt.fontsize), offset=txt.offset, fill=txt.fill)

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
        yr = (self.x + self.width + self.border * 2, self.y + self.height + self.border * 2)
        return (xl, xr, yl, yr,)

    @property
    def x(self) -> int:
        return self.offset[0]

    @property
    def y(self) -> int:
        return self.offset[1]


class Stack(Widget):
    def __init__(self, widgets: List[Widget] = [], cstride=1, border=0, fill=None, outline=None):
        super(Stack, self).__init__()
        self.cstride = cstride
        self.border = border
        self.fill = fill
        self.outline = outline
        self.widgets = widgets

    def add(self, widget: Widget):
        self.widgets.append(widget)

    def set_border(self, border: int):
        self.border = border

    def set_fill(self, fill):
        self.fill = fill

    def set_outline(self, outline):
        self.outline = outline

    def draw(self, draw_: ImageDraw, offset=(0, 0)):
        assert len(self.widgets) % self.cstride == 0
        if self.border > 0:
            draw_.rectangle(self.region_coor(offset), width=self.border, fill=self.fill,
                            outline=self.outline)
        offset_y = offset[1] + self.border
        for i in range(len(self.widgets) // self.cstride):
            offset_x = offset[0] + self.border
            max_col_size = 0
            for j in range(self.cstride):
                cur = self.widgets[i * self.cstride + j]
                cur.draw(draw_, (offset_x, offset_y))
                offset_x += cur.region_size()[0]
                max_col_size = max(max_col_size, cur.region_size()[1])
            offset_y += max_col_size  # no overlap

        # draw texts
        for txt in self.texts:
            off = (offset[0] + self.border + txt.offset[0],
                   offset[1] + self.border + txt.offset[1])
            draw_.text(text=txt.content, xy=off, font=font(txt.fontsize), fill=txt.fill)

    def region_size(self) -> Tuple[int, int]:
        x0, y0, x1, y1 = self.region_coor((0, 0))
        return (x1 - x0, y1 - y0)

    def region_coor(self, offset) -> Tuple[int, int, int, int]:
        max_x_size = 0
        max_y_size = 0
        for i in range(len(self.widgets) // self.cstride):
            x_size = 0
            y_size = 0
            for j in range(self.cstride):
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


class TensorDrawer(Widget):
    class CellConfig:
        def __init__(self, width: int, height: int, fill=colors.SANDYBROWN, border=1, outline=colors.SEAGREEN4):
            self.width = width
            self.height = height
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

    def __int__(self, shape: List[int], order: List[int], data: List[int] = [], cell_config=CellConfig(20, 20)):
        assert len(shape) <= 3, "Tensor with more than 3 dimensions is not visualized yet."
        assert len(shape) == len(order), "Shape and order dimension are not match"
        self.cell_config = cell_config
        self.shape = shape
        self.order = order
        self.data = data if data else [i for i in range(math.prod(self.shape))]

    def draw(self, draw_: ImageDraw, offset=(0, 0), fill=None, border=0):
        for dim in range(len(self.shape)):  # from innermost to outermost
            stride = 1
            for i, ord in enumerate(self.order[:dim]):
                stride *= self.shape[ord]
            data = [self.data[idx] for idx in range(0, len(self.data), stride)]
            cells = [Rectangle(**self.cell_config) for i in range(data)]

        stack = Stack(self.shape[self.order[0]])
        if len(self.shape) == 1:
            cell = Rectangle(**self.cell_config.dict_)
            cells.append(cell)


if __name__ == '__main__':
    draw, canvas = create_canvas(size=(1200, 1200))

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

    canvas.show('demo')

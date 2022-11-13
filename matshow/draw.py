__all__ = [
    "Widget",
    "Rectangle",
    "Stack",
    "Matrix",
    "HStack",
    "VStack",
    "LabeledWidget",
    "to_animation",
    "create_canvas",
]

import abc
import math
import subprocess
import sys
from collections import OrderedDict, namedtuple
from sys import platform
from typing import *

import imageio
from PIL import Image, ImageDraw, ImageFont

from matshow import colors

try:
    import torch
except:

    class torch:
        class Tensor:
            pass

RESOLUTION = 1

INF = 10000000000


def _font_path() -> str:
    ttf_path = None
    if platform == "linux" or platform == "linux2":
        # choose a random font from the system
        fonts = subprocess.check_output(["fc-list"])
        assert fonts
        fonts = fonts.decode(sys.stdout.encoding)
        one_font = fonts.split("\n")[0]
        ttf_path = one_font.split(":")[0]
    elif platform == "darwin":
        # Not considered yet.
        ttf_path = "Verdana.ttf"
    elif platform == "win32":
        # The arial.ttf should exist in Windows
        ttf_path = "arial.ttf"
    return ttf_path


def font(size: int):
    """
    :param size:
    :return:
    """
    font = ImageFont.truetype(_font_path(), size)
    return font


class Widget(abc.ABC):
    Text = namedtuple("Text", "content, fontsize, container, fill, pos")

    def __init__(self):
        self.texts: List[Widget.Text] = []
        self.fill = None
        self.border = 0
        self.outline: colors.RGB = Widget.border_colors[0]
        self.fill: colors.RGB = Widget.fill_colors[0]
        self.margin = (0, 0)

        self.pre_draw_callbacks = []
        self.post_draw_callbacks = []

        self._draw_cache: Optional[Tuple[Image.Image,
                                         ImageDraw.ImageDraw]] = None

    def draw(self, draw_: ImageDraw = None, offset: Tuple[int, int] = (0, 0)):
        """Draw with external canvas."""

        if draw_:
            for fn in self.pre_draw_callbacks:
                fn()

            self._draw(draw_, offset)
            self._draw_text(draw_, offset)

            for fn in self.post_draw_callbacks:
                fn()
        else:
            canvas, draw = create_canvas(self.outer_size, fill=colors.WHITE)
            self.draw(canvas, offset)
            self._draw_cache = [canvas, draw]

    def show(self, title: str = ""):
        assert self._draw_cache, "Should call `draw` before"
        self._draw_cache[1].show(title)

    def save(self, filename: str):
        assert self._draw_cache, "Should call `draw` before"
        self._draw_cache[1].save(filename)

    def draw_and_show(self, title=""):
        canvas, im = create_canvas(self.outer_size)
        self.draw(canvas)
        im.show(title=title)

    @abc.abstractmethod
    def _draw(self, draw_: ImageDraw, offset: Tuple[int, int]):
        raise NotImplemented

    @property
    def outer_size(self) -> Tuple[int, int]:
        """
        Get the size with margin considered.
        :return [width, height]
        """
        raise NotImplemented

    @property
    def inner_size(self) -> Tuple[int, int]:
        """
        Get the size of the widget.
        :return [width, height]
        """
        raise NotImplemented

    def text(
            self,
            content: str,
            fontsize: int,
            fill=colors.BLACK,
            pos: Tuple[str, str] = ("mid", "mid"),
    ) -> None:
        """
        Place a text.
        :param poses: one of ('mid', 'left', 'right', 'top', 'bottom)
        """
        VALID_POS = ("mid", "left", "right", "top", "bottom")
        assert pos[0] in VALID_POS and pos[1] in VALID_POS
        the_font = font(fontsize)
        # get the true size with the font
        text_size = the_font.getsize(content)

        text = Widget.Text(content, fontsize, self, fill, pos)
        self.texts.append(text)

    def set_border(self, border: int, outline: colors.RGB):
        '''
        Set the border of the widget.
        '''
        self.border = border
        self.outline = outline

    @abc.abstractmethod
    def get_cell(self, *offs) -> "Widget":
        raise NotImplementedError()

    def add_pre_draw_callback(self, fn):
        self.pre_draw_callbacks.append(fn)

    def add_post_draw_callback(self, fn):
        self.post_draw_callbacks.append(fn)

    @abc.abstractmethod
    def get_cells(self) -> List["Widget"]:
        '''
        Get basic cells.
        '''
        return []

    @staticmethod
    def get_text_actual_size(content: str, fontsize: int):
        the_font = font(fontsize)
        # get the true size with the font
        return the_font.getsize(content)

    def _draw_text(self, draw_: ImageDraw, offset: Tuple[int, int]):
        # draw texts
        for txt in self.texts:
            size = txt.container.outer_size
            text_size = Widget.get_text_actual_size(txt.content, txt.fontsize)
            text_offset = [
                self.__get_text_offset(size, text_size, txt.pos, i) for i in range(2)
            ]

            off = (
                offset[0] + self.border + text_offset[0],
                offset[1] + self.border + text_offset[1],
            )
            draw_.text(text=txt.content, xy=off,
                       font=font(txt.fontsize), fill=txt.fill)

    def __get_text_offset(
            self, container_size: List[int], text_size: List[int], poses: List[str], i: int
    ):
        assert len(container_size) == len(poses)

        pos = poses[i]
        size = container_size[i]
        if pos == "mid":
            return max(size // 2 - text_size[i] // 2, 0)
        elif pos == "left":
            return 0
        elif pos == "right":
            return size - text_size[i]
        elif pos == "top":
            return 0
        elif pos == "bottom":
            return size - text_size[i]
        else:
            assert False, "pos: %s is not supported" % pos

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


ColorTy = Tuple[int, int, int]


class Rectangle(Widget):
    def __init__(
            self,
            width: int,
            height: int,
            fill: ColorTy,
            outline: ColorTy = Widget.border_colors[0],
            border: int = 0,
            margin: Tuple[int, int] = (0, 0),
    ):
        super(Rectangle, self).__init__()
        self.width = width
        self.height = height
        self.fill = fill
        self.outline = outline
        self.border = border
        self.margin = margin

    def __repr__(self):
        return "<Rectangle %s>" % hash(self)

    def _draw(self, draw_: ImageDraw, offset=(0, 0)):
        offset = (offset[0] + self.margin[0], offset[1] + self.margin[1])
        coor = [
            offset[0],  # left
            offset[1],  # top
            offset[0] + self.width,  # right
            offset[1] + self.height,  # bottom
        ]
        draw_.rectangle(coor, fill=self.fill,
                        outline=self.outline, width=self.border)

    @property
    def outer_size(self) -> Tuple[int, int]:
        width = self.width + self.margin[0] * 2
        height = self.height + self.margin[1] * 2
        return width, height

    @property
    def inner_size(self) -> Tuple[int, int]:
        return self.width, self.height

    def get_cell(self, *offs) -> Widget:
        assert len(offs) == 1
        assert offs[0] == 0
        return self

    def get_cells(self) -> List[Widget]:
        return [self]

    @property
    def x(self) -> int:
        return self.offset[0]

    @property
    def y(self) -> int:
        return self.offset[1]


class Stack(Widget):
    def __init__(
            self,
            widgets: List[Widget] = None,
            cstride: int = 1,
            border: int = 0,
            fill: ColorTy = None,
            outline: ColorTy = None,
            margin: Tuple[int, int] = (0, 0),
    ):
        super(Stack, self).__init__()
        self.cstride = cstride
        self.border = border
        self.fill = fill
        self.outline = outline
        self.margin = margin
        self.widgets = [] if not widgets else widgets

    def add(self, widget: Widget) -> None:
        assert widget != self, "recursion found"
        self.widgets.append(widget)

    def insert(self, widget: Widget, pos=0):
        self.widgets.insert(pos, widget)

    def set_label(self, text, fontsize, color=colors.BLACK, fill=colors.WHITE):
        size = self.inner_size
        rec = Rectangle(
            width=size[0] - self.border, height=fontsize * 2, border=0, fill=fill
        )
        rec.text(text, pos=("mid", "mid"), fontsize=fontsize, fill=color)
        self.insert(rec)

    def __repr__(self):
        return "<Stack #%d %s>" % (len(self.widgets), hash(self))

    def get_cells(self) -> List[Widget]:
        return self.widgets

    def set_fill(self, fill: ColorTy):
        self.fill = fill

    def set_outline(self, outline: ColorTy):
        self.outline = outline

    def set_margin(self, margin: Tuple[int, int]):
        self.margin = margin

    @property
    def widget_count(self):
        return len(self.widgets)

    def get_cell(self, *offset) -> Widget:
        assert len(offset) <= 2
        if len(offset) == 1:
            offset = offset[0]
            if type(self.widgets[0]) is Stack:
                stride = self.widgets[0].total_stride
                idx = offset // stride
                return self.widgets[idx].get_cell(offset % stride)
            if offset >= len(self.widgets):
                return None
            return self.widgets[offset]
        elif len(offset) == 2:
            row, col = offset
            abs_offset = row * self.cstride + col
            return self.get_cell(abs_offset)

    @property
    def total_stride(self):
        assert self.widgets
        cls = type(self.widgets[0])
        if cls is Stack:
            if self.cstride == INF:
                return len(self.widgets)
            return self.cstride * self.widgets[0].total_stride
        return self.cstride

    def _draw(self, draw_: ImageDraw, offset=(0, 0)):
        """
        Draw the Stack to canvas.
        """
        coor = self.region_coor(offset)

        if self.border > 0:
            # draw the border
            draw_.rectangle(
                coor, width=self.border, fill=self.fill, outline=self.outline
            )

        offset_y = offset[1] + self.margin[1] + self.border

        nrows = math.ceil(len(self.widgets) / self.cstride)
        for i in range(nrows):
            offset_x = offset[0] + self.border + self.margin[0]
            max_col_size = 0
            for j in range(self.cstride):
                nth = i * self.cstride + j
                if nth >= len(self.widgets):
                    break
                cur = self.widgets[nth]
                assert cur != self
                cur.draw(draw_, (offset_x, offset_y))
                offset_x += cur.outer_size[0]
                max_col_size = max(max_col_size, cur.outer_size[1])
            offset_y += max_col_size  # no overlap

    @property
    def outer_size(self) -> Tuple[int, int]:
        x, y = self.inner_size
        return x + 2 * self.margin[0], y + 2 * self.margin[1]

    @property
    def inner_size(self) -> Tuple[int, int]:
        max_x_size = 0
        max_y_size = 0
        nrows = math.ceil(len(self.widgets) / self.cstride)
        for i in range(nrows):
            x_size = 0
            y_size = 0
            for j in range(self.cstride):
                nth = i * self.cstride + j
                if nth >= len(self.widgets):
                    break
                cur = self.widgets[i * self.cstride + j]
                x_size += cur.outer_size[0]
                y_size = max(y_size, cur.outer_size[1])
            max_x_size = max(max_x_size, x_size)
            max_y_size += y_size
        return max_x_size + 2 * self.border, max_y_size + 2 * self.border

    def region_coor(self, offset: Tuple[int, int]) -> Tuple[int, int, int, int]:
        width, height = self.inner_size
        coor = (
            offset[0] + self.margin[0],  # left
            offset[1] + self.margin[1],  # top
            offset[0] + self.margin[0] + width,  # right
            offset[1] + self.margin[1] + height,  # bottom
        )
        return coor


class HStack(Stack):
    def __init__(
            self,
            widgets: List[Widget] = None,
            border: int = 0,
            fill: ColorTy = None,
            outline: ColorTy = None,
            margin: Tuple[int, int] = (0, 0),
    ):
        super(HStack, self).__init__(
            widgets=widgets,
            cstride=INF,
            border=border,
            fill=fill,
            outline=outline,
            margin=margin,
        )

    def get_cell(self, *offs) -> Widget:
        if len(offs) == 2:
            return Stack.get_cell(self, *offs)
        return self.widgets[offs[0]]


class VStack(Stack):
    def __init__(
            self,
            widgets: List[Widget] = None,
            border: int = 0,
            fill: ColorTy = None,
            outline: ColorTy = None,
            margin: Tuple[int, int] = (0, 0),
    ):
        super(VStack, self).__init__(
            widgets=widgets,
            cstride=1,
            border=border,
            fill=fill,
            outline=outline,
            margin=margin,
        )

    def get_cell(self, *offs) -> Widget:
        if len(offs) == 2:
            return Stack.get_cell(self, *offs)
        return self.widgets[offs[0]]


class Label(Widget):
    """
    A label widget.
    """

    def __init__(
            self,
            content: str,
            width: int,
            height: int,
            fontsize: int,
            fill=colors.BLACK,
            margin: Tuple[int, int] = (0, 0),
            pos: Tuple[str, str] = ("mid", "mid"),
    ):
        super(Label, self).__init__()
        self.content = content
        self.fontsize = fontsize
        self.width = width
        self.margin = margin
        self.height = height
        self.fill = fill
        self.border = 0

        self.text(content, fontsize=fontsize, fill=fill, pos=pos)

    def set_size(self, size: Tuple[int, int]):
        self.width = size[0]
        self.height = size[1]

    def __repr__(self):
        return "<Label: %s>" % hash(self)

    @property
    def outer_size(self) -> Tuple[int, int]:
        self._update_label_size()
        return self.width + self.margin[0] * 2, self.height + self.margin[1] * 2

    @property
    def inner_size(self) -> Tuple[int, int]:
        self._update_label_size()
        return self.width + self.margin[0], self.height + self.margin[1]

    def get_cells(self) -> List[Widget]:
        return [self]

    def _draw(self, draw_: ImageDraw, offset: Tuple[int, int]):
        pass

    def get_cell(self, *offs) -> Widget:
        return self

    def _update_label_size(self):
        label_width, label_height = Widget.get_text_actual_size(
            self.content, self.fontsize
        )
        new_width = max(label_width, self.width)
        new_height = max(label_height, self.height)
        self.width = new_width
        self.height = new_height


class LabeledWidget(Widget):
    """
    Widget with a label.
    """

    def __init__(
            self,
            label: str,
            fontsize: int,
            label_pos: str = "top",
            padding: Tuple[int, int] = (10, 5),
            margin: Tuple[int, int] = (0, 0),
            main_widget: Widget = None,
    ):
        super(LabeledWidget, self).__init__()
        assert label_pos == "top", "Currently only top is supported"
        self.view = VStack()
        self.fontsize = fontsize
        self.main_widget = main_widget
        self.margin: Tuple[int, int] = margin

        self.label_widget = Label(
            label, fontsize=fontsize, width=0, height=0, margin=padding
        )
        self.view.add(self.label_widget)
        if main_widget:
            self.view.add(main_widget)

        # self.add_pre_draw_callback(self._update_label_size)

    def set_main_widget(self, widget: Widget):
        self.main_widget = widget
        self.view.add(self.main_widget)
        assert self.view.widget_count == 2

    @property
    def outer_size(self):
        return self.view.outer_size

    @property
    def inner_size(self):
        return self.view.inner_size

    def get_cells(self) -> List[Widget]:
        return [self.main_widget]

    def get_cell(self, *offs) -> Widget:
        assert len(offs) == 1
        assert offs[0] == 0
        return self.main_widget

    def _draw(self, draw_: ImageDraw, offset=(0, 0)):
        offset = (offset[0] + self.margin[0], offset[1] + self.margin[1])
        self.view.draw(draw_, offset)


class Matrix(Widget):
    class CellConfig:
        def __init__(
                self,
                width: int = 20,
                height: int = None,
                fill: ColorTy = colors.SANDYBROWN,
                border=1,
                outline: ColorTy = colors.SEAGREEN4,
        ):
            self.width = width
            self.height = height if height else width
            self.fill = fill
            self.border = border
            self.outline = outline

        @property
        def dict_(self) -> Dict[str, int]:
            return dict(
                width=self.width,
                height=self.height,
                fill=self.fill,
                border=self.border,
                outline=self.outline,
            )

    def __init__(
            self,
            shape: List[int],
            data: torch.Tensor = None,
            border: int = 0,
            outline: ColorTy = colors.BLACK,
            margin=(0, 0),
            fill: ColorTy = colors.WHITE,
            cell_config: CellConfig = CellConfig(20, 20),
    ):
        super(Matrix, self).__init__()
        assert (
            len(shape) <= 3
        ), "Matrix with more than 3 dimensions is not visualized yet."
        self.border = border
        self.outline = outline
        self.cell_config = cell_config
        self.shape = shape
        self.fill = fill
        self.data = data if data else [i for i in range(math.prod(self.shape))]
        self.stack = self.get_main()
        self.stack.set_margin(margin)

    def _draw(self, draw_: ImageDraw, offset=(0, 0)):
        if self.border > 0:
            width, height = self.inner_size
            coor = [
                offset[0],  # left
                offset[1],  # top
                offset[0] + width,  # right
                offset[1] + height,  # bottom
            ]
            draw_.rectangle(
                coor, width=self.border, fill=self.fill, outline=self.outline
            )

        inner_offset = (offset[0] + self.border, offset[1] + self.border)
        self.stack.draw(draw_, inner_offset)

    @property
    def inner_size(self) -> Tuple[int, int]:
        size = self.stack.outer_size
        size = (size[0] + 2 * self.border, size[1] + 2 * self.border)
        return size

    @property
    def outer_size(self) -> Tuple[int, int]:
        return self.inner_size

    def get_cell(self, *offset) -> Widget:
        return self.stack.get_cell(*offset)

    def get_main(self):
        rank = len(self.shape)
        if rank == 1:
            stack = Stack(
                cstride=self.shape[0], border=2, outline=Widget.border_colors[0]
            )
            for i in range(self.shape[0]):
                cell = Rectangle(**self.cell_config.dict_)
                stack.add(cell)
        elif rank == 2:
            stack = Stack(
                cstride=self.shape[1], border=0, outline=Widget.border_colors[0]
            )
            for i in range(self.shape[0] * self.shape[1]):
                cell = Rectangle(**self.cell_config.dict_)
                stack.add(cell)
        elif rank == 3:
            stack = Stack(
                cstride=self.shape[0], border=2, outline=Widget.border_colors[0]
            )
            for i in range(self.shape[0]):
                row = Stack(
                    cstride=self.shape[1], border=2, fill=Widget.border_colors[1]
                )
                for j in range(self.shape[1] * self.shape[2]):
                    cell = Rectangle(**self.cell_config.dict_)
                    row.add(cell)
                stack.add(row)
        return stack

    def get_cells(self) -> List[Widget]:
        return self.stack.get_cells()


def create_canvas(
        size=(500, 300), fill=colors.GRAY
) -> Tuple[ImageDraw.ImageDraw, Image.Image]:
    im = Image.new("RGB", size, fill)
    draw = ImageDraw.Draw(im)
    return draw, im


def to_animation(image_paths: List[str], gif_path: str, duration: int = 1):
    images = [imageio.imread(path) for path in image_paths]
    imageio.mimsave(gif_path, images, "GIF", duration=duration)


if __name__ == "__main__":
    draw, canvas = create_canvas(size=(2200, 2200))
    """
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
    """

    tensor = Matrix(shape=[16, 16], cell_config=Matrix.CellConfig(width=40))
    tensor.draw(draw)

    canvas.show("demo")

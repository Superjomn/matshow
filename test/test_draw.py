import os

from matshow import draw
from matshow.draw import (HStack, Label, LabeledWidget, Rectangle, Stack,
                          VStack, Widget, colors, create_canvas)


def get_test_img_root():
    return os.environ.get("matshow_img_root", "./")


def test_draw_rectangle():
    rec = Rectangle(400,
                    400,
                    fill=Widget.fill_colors[0],
                    outline=Widget.border_colors[0],
                    border=2)
    rec0 = Rectangle(
        200,
        200,
        fill=Widget.fill_hl_colors[1],
        outline=Widget.border_colors[1],
        border=2,
    )
    rec1 = Rectangle(100,
                     100,
                     fill=Widget.fill_colors[2],
                     outline=Widget.border_colors[2],
                     border=2)

    draw, canvas = create_canvas(rec.outer_size)

    rec.draw(draw)
    rec0.draw(draw, offset=(40, 40))
    rec1.draw(draw, offset=(100, 100))

    canvas.save(os.path.join(get_test_img_root(), "./rec.png"))


def test_stack0():
    rec = Rectangle(80, 80, fill=colors.RED1, outline=colors.WHITE, border=20)
    table0 = Stack([rec], cstride=4, border=6, outline=colors.SGIBEET)
    draw, canvas = create_canvas(table0.outer_size)
    table0.draw(draw)

    canvas.save(os.path.join(get_test_img_root(), "./stack0.png"))

    assert table0.inner_size == (
        rec.outer_size[0] + table0.border * 2,
        rec.outer_size[1] + table0.border * 2,
    )

    assert rec.outer_size == (80, 80)
    assert table0.outer_size == (80 + 6 * 2, 80 + 6 * 2)
    assert canvas.size == table0.outer_size


def test_stack1():
    rec = Rectangle(40,
                    40,
                    fill=Widget.fill_colors[0],
                    outline=Widget.border_colors[0],
                    border=6)
    table0 = Stack([rec, rec, rec, rec, rec, rec],
                   cstride=3,
                   border=6,
                   outline=colors.SGIBEET)
    draw, canvas = create_canvas(table0.outer_size)
    table0.draw(draw)

    assert canvas.size == table0.outer_size

    canvas.save(os.path.join(get_test_img_root(), "./stack1.png"))

    assert table0.inner_size == (
        rec.outer_size[0] * 3 + table0.border * 2,
        rec.outer_size[1] * 2 + table0.border * 2,
    )
    assert table0.inner_size == table0.outer_size


def test_stack_with_margin():
    rec = Rectangle(
        40,
        40,
        fill=Widget.fill_colors[0],
        outline=Widget.border_colors[0],
        border=6,
        margin=(10, 10),
    )
    table0 = Stack([rec],
                   cstride=4,
                   border=40,
                   outline=colors.SGIBEET,
                   fill=colors.WHITE)
    draw, canvas = create_canvas(table0.outer_size)
    table0.draw(draw)

    canvas.save(os.path.join(get_test_img_root(), "./stack_margin.png"))

    assert table0.inner_size == (
        rec.outer_size[0] + table0.border * 2,
        rec.outer_size[1] + table0.border * 2,
    )


def test_HStack():
    rec = Rectangle(40,
                    40,
                    fill=Widget.fill_colors[0],
                    outline=Widget.border_colors[0],
                    border=6)
    view = HStack([rec for i in range(10)])
    assert view.outer_size == (40 * 10, 40)

    draw, canvas = create_canvas(view.outer_size)
    view.draw(draw)

    canvas.save(os.path.join(get_test_img_root(), "./hstack.png"))


def test_VStack():
    rec = Rectangle(40,
                    40,
                    fill=Widget.fill_colors[0],
                    outline=Widget.border_colors[0],
                    border=6)
    view = VStack([rec for i in range(10)])
    assert view.outer_size == (40, 40 * 10)

    draw, canvas = create_canvas(view.outer_size)
    view.draw(draw)

    canvas.save(os.path.join(get_test_img_root(), "./vstack.png"))


def test_text():
    rec = Rectangle(40,
                    40,
                    fill=Widget.fill_colors[0],
                    outline=Widget.border_colors[0],
                    border=2)
    rec.text("1", fontsize=20, fill=colors.RED1, pos=("mid", "mid"))
    recs = [rec for i in range(20)]

    main = Stack(cstride=3)
    table0 = Stack(recs, 4, border=4, outline=colors.SGIBEET)
    table1 = Stack([rec for i in range(20)],
                   border=2,
                   outline=Widget.border_colors[0],
                   cstride=10)

    main.add(table0)
    main.add(table1)
    main.add(table0)
    main.add(table1)
    main.add(table0)
    main.add(table1)

    draw, canvas = create_canvas(main.outer_size)
    main.draw(draw)

    canvas.save(os.path.join(get_test_img_root(), "./text.png"))


def test_Label():
    widget = Label("hello world",
                   0,
                   0,
                   fontsize=20,
                   fill=colors.RED1,
                   margin=(10, 10))
    draw, canvas = create_canvas(widget.outer_size)
    widget.draw(draw)
    canvas.save(os.path.join(get_test_img_root(), "./label.png"))


def test_LabeledWidget():
    rec = Rectangle(40,
                    40,
                    fill=Widget.fill_colors[0],
                    outline=Widget.border_colors[0],
                    border=2,
                    margin=(20, 20))

    view = LabeledWidget("hello world", fontsize=20,
                         main_widget=rec, padding=(20, 10), margin=(10, 10))

    draw, canvas = create_canvas(view.outer_size)
    view.draw(draw)
    canvas.save(os.path.join(get_test_img_root(), "./labeled_widget.png"))


if __name__ == "__main__":
    test_stack0()

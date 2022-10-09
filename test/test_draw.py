from matshow import draw
from matshow.draw import Rectangle, Widget, create_canvas, Stack
from matshow.draw import colors
import os


def get_test_img_root():
    return os.environ.get('matshow_img_root', './')


def test_Ruler():
    ruler = draw.Ruler(width=300, height=400, resolution=10)
    assert ruler.piece == (300 // 10, 400 // 10)


def test_recursive_Ruler():
    ruler0 = draw.Ruler(width=300, height=400, resolution=50)
    ruler1 = draw.Ruler(width=3, height=4, parent=ruler0)
    assert ruler0.piece == (300 // 50, 400 / 50)
    assert ruler1.piece == (ruler0.piece[0] * 3, ruler0.piece[1] * 4)


def test_draw_rectangle():
    rec = Rectangle(400, 400, fill=Widget.fill_colors[0], outline=Widget.border_colors[0], border=2)
    rec0 = Rectangle(200, 200, fill=Widget.fill_hl_colors[1], outline=Widget.border_colors[1], border=2)
    rec1 = Rectangle(100, 100, fill=Widget.fill_colors[2], outline=Widget.border_colors[2], border=2)

    draw, canvas = create_canvas(rec.region_size)

    rec.draw(draw)
    rec0.draw(draw, offset=(40, 40))
    rec1.draw(draw, offset=(100, 100))

    canvas.save(os.path.join(get_test_img_root(), './rec.png'))


def test_stack():
    rec = Rectangle(40, 40, fill=Widget.fill_colors[0], outline=Widget.border_colors[0], border=2)
    rec.text('1', fontsize=20, fill=colors.RED1, pos=('mid', 'mid'))
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

    draw, canvas = create_canvas(main.region_size)
    main.draw(draw)

    canvas.save(os.path.join(get_test_img_root(), "./stack.png"))

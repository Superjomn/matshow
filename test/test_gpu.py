import os

from matshow import *


def get_test_img_root():
    return os.environ.get('matshow_img_root', './')


def test_tensorview():
    warp = TensorView([4, 8])
    draw_, canvas = create_canvas(warp.drawer.outer_size)
    warp.drawer.draw(draw_)
    canvas.save(os.path.join(get_test_img_root(), "./gpu0.png"))

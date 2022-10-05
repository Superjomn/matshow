from matshow import draw


def test_Ruler():
    ruler = draw.Ruler(width=300, height=400, resolution=10)
    assert ruler.piece == (300 // 10, 400 // 10)


def test_recursive_Ruler():
    ruler0 = draw.Ruler(width=300, height=400, resolution=50)
    ruler1 = draw.Ruler(width=3, height=4, parent=ruler0)
    assert ruler0.piece == (300//50, 400/50)
    assert ruler1.piece == (ruler0.piece[0] * 3, ruler0.piece[1] * 4)

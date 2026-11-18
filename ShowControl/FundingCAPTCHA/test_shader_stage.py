"""shader_stage.py: which display the stage goes fullscreen on."""


def test_pick_display_uses_that_displays_own_size():
    from shader_stage import pick_display
    sizes = [(3072, 1920), (1600, 1200)]
    assert pick_display(sizes, 1) == (1, (1600, 1200))
    assert pick_display(sizes, 0) == (0, (3072, 1920))


def test_pick_display_out_of_range_falls_back_to_first():
    from shader_stage import pick_display
    assert pick_display([(1920, 1080)], 2) == (0, (1920, 1080))
    assert pick_display([(1920, 1080)], -1) == (0, (1920, 1080))


def test_display_index_flag_beats_settings():
    from argparse import Namespace
    from shader_stage import display_index
    settings = {"shader_app": {"display": 1}}
    assert display_index(Namespace(display=None), settings) == 1
    assert display_index(Namespace(display=2), settings) == 2
    from settings import with_defaults
    assert display_index(Namespace(display=None), with_defaults({})) == 0

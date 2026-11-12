import unittest
from types import SimpleNamespace
from game_ui.world_rendering.depth_sorter import DepthSorter


class TestDepthSorter(unittest.TestCase):
    def test_sorts_back_to_front_by_axial_row_then_column(self):
        items = ["front", "right", "back"]
        positions = {
            "front": SimpleNamespace(q=0, r=2),
            "right": SimpleNamespace(q=1, r=0),
            "back": SimpleNamespace(q=-1, r=-1),
        }
        self.assertEqual(DepthSorter.sort(items, lambda item: positions[item]),
                         ("back", "right", "front"))

    def test_sort_is_stable_for_equal_depth(self):
        items = ["first", "second"]
        positions = {item: SimpleNamespace(q=0, r=0) for item in items}
        self.assertEqual(DepthSorter.sort(items, lambda item: positions[item]),
                         ("first", "second"))


if __name__ == "__main__":
    unittest.main()

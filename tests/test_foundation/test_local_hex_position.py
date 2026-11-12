import unittest
from core.domain.spatial import HexCoord, LocalHexPosition

class TestLocalHexPosition(unittest.TestCase):
    def test_valid_negative_zero_equality_and_hash(self):
        a=LocalHexPosition(-2,0)
        self.assertEqual(a,LocalHexPosition(-2,0))
        self.assertEqual(hash(a),hash(LocalHexPosition(-2,0)))
        self.assertEqual(LocalHexPosition(0,0),LocalHexPosition(0,0))
    def test_rejects_bool_float_and_string(self):
        for v in (True,False,1.0,"1"):
            with self.subTest(v=v),self.assertRaises(TypeError): LocalHexPosition(v,0)
    def test_immutable(self):
        with self.assertRaises((AttributeError,TypeError)): LocalHexPosition(1,2).q=3
    def test_explicit_hex_coord_conversion(self):
        p=LocalHexPosition.from_hex_coord(HexCoord(-4,7))
        self.assertEqual(p.to_hex_coord(),HexCoord(-4,7))
        with self.assertRaises(TypeError): LocalHexPosition.from_hex_coord((1,2))

if __name__=="__main__": unittest.main()

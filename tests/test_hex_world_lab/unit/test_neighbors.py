from hex_world_lab.geometry import AxialCoord, hex_neighbors, hex_distance

def test_each_cell_has_six_unique_neighbors():
    for q in range(-5,6):
        for r in range(-5,6):
            cell=AxialCoord(q,r); neighbors=hex_neighbors(cell)
            assert len(neighbors)==6
            assert len(set(neighbors))==6
            assert all(hex_distance(cell,n)==1 for n in neighbors)

def test_neighbor_relation_is_symmetric():
    origin=AxialCoord(-3,7)
    for neighbor in hex_neighbors(origin):
        assert origin in hex_neighbors(neighbor)

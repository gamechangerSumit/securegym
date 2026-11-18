from app.services.zone_geometry import bbox_center_normalized, is_outside_storage, point_in_polygon


def test_point_in_polygon():
    polygon = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
    assert point_in_polygon((0.5, 0.5), polygon)
    assert not point_in_polygon((0.95, 0.5), polygon)


def test_bbox_center_and_storage_membership():
    polygon = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
    bbox = (40, 40, 60, 60)
    assert bbox_center_normalized(bbox, 100, 100) == (0.5, 0.5)
    assert is_outside_storage((1, 1, 10, 10), 100, 100, polygon)
    assert not is_outside_storage((40, 40, 60, 60), 100, 100, polygon)

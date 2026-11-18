from collections.abc import Sequence


def point_in_polygon(point: tuple[float, float], polygon: Sequence[Sequence[float]]) -> bool:
    """Ray-casting point-in-polygon for a normalized frame point."""
    x, y = point
    inside = False
    count = len(polygon)
    if count < 3:
        return False

    previous = polygon[-1]
    for current in polygon:
        x1, y1 = float(previous[0]), float(previous[1])
        x2, y2 = float(current[0]), float(current[1])
        crosses = (y1 > y) != (y2 > y)
        if crosses:
            intersection_x = (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-12) + x1
            if x < intersection_x:
                inside = not inside
        previous = current
    return inside


def bbox_center_normalized(
    bbox: tuple[float, float, float, float], frame_width: int, frame_height: int
) -> tuple[float, float]:
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("Frame dimensions must be positive")
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / (2 * frame_width), (y1 + y2) / (2 * frame_height))


def is_outside_storage(
    bbox: tuple[float, float, float, float],
    frame_width: int,
    frame_height: int,
    storage_polygon: Sequence[Sequence[float]],
) -> bool:
    center = bbox_center_normalized(bbox, frame_width, frame_height)
    return not point_in_polygon(center, storage_polygon)

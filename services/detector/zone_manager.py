import structlog

logger = structlog.get_logger()


class ZoneManager:
    """Checks if detection bounding boxes fall within defined zones."""

    def __init__(self):
        self.zones: dict[str, list[dict]] = {}  # camera_id -> list of zones

    def update_zones(self, camera_id: str, zones: list[dict]):
        self.zones[camera_id] = zones

    def check_detection(self, camera_id: str, bbox: dict, frame_width: int, frame_height: int) -> list[dict]:
        """Check if a detection's center point falls within any zone for this camera.
        Returns list of matching zones."""
        camera_zones = self.zones.get(camera_id, [])
        if not camera_zones:
            return []

        # Get center of detection bbox (normalized)
        cx = ((bbox["x1"] + bbox["x2"]) / 2) / frame_width
        cy = ((bbox["y1"] + bbox["y2"]) / 2) / frame_height

        matches = []
        for zone in camera_zones:
            if not zone.get("is_enabled", True):
                continue

            points = zone.get("points", [])
            if not points:
                continue

            if zone.get("zone_type") == "tripwire":
                # Tripwire: check if detection crosses the line
                # Simplified: check proximity to line
                if self._near_line(cx, cy, points, threshold=0.05):
                    matches.append(zone)
            else:
                # ROI/perimeter: point-in-polygon
                if self._point_in_polygon(cx, cy, points):
                    matches.append(zone)

        return matches

    @staticmethod
    def _point_in_polygon(x: float, y: float, polygon: list[dict]) -> bool:
        """Ray casting algorithm for point-in-polygon."""
        n = len(polygon)
        inside = False
        j = n - 1

        for i in range(n):
            xi, yi = polygon[i].get("x", 0), polygon[i].get("y", 0)
            xj, yj = polygon[j].get("x", 0), polygon[j].get("y", 0)

            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i

        return inside

    @staticmethod
    def _near_line(x: float, y: float, points: list[dict], threshold: float = 0.05) -> bool:
        """Check if point is near a line defined by two points."""
        if len(points) < 2:
            return False

        x1, y1 = points[0].get("x", 0), points[0].get("y", 0)
        x2, y2 = points[1].get("x", 0), points[1].get("y", 0)

        # Distance from point to line segment
        dx, dy = x2 - x1, y2 - y1
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5 < threshold

        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / length_sq))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        dist = ((x - proj_x) ** 2 + (y - proj_y) ** 2) ** 0.5

        return dist < threshold

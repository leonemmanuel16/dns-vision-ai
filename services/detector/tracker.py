import time
import structlog
from dataclasses import dataclass, field

logger = structlog.get_logger()


@dataclass
class TrackedObject:
    track_id: int
    label: str
    confidence: float
    bbox: dict
    first_seen: float
    last_seen: float
    event_published: bool = False


class SimpleTracker:
    """Simple IoU-based tracker for deduplicating detections across frames."""

    def __init__(self, iou_threshold: float = 0.3, max_age: float = 5.0):
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.tracks: dict[int, TrackedObject] = {}
        self._next_id = 1

    def update(self, detections: list[dict]) -> list[TrackedObject]:
        now = time.time()
        new_objects = []

        # Remove stale tracks
        stale = [tid for tid, t in self.tracks.items() if now - t.last_seen > self.max_age]
        for tid in stale:
            del self.tracks[tid]

        # Match detections to existing tracks
        matched_tracks = set()
        matched_dets = set()

        for i, det in enumerate(detections):
            best_iou = 0
            best_tid = None

            for tid, track in self.tracks.items():
                if tid in matched_tracks:
                    continue
                if det["label"] != track.label:
                    continue

                iou = self._compute_iou(det["bbox"], track.bbox)
                if iou > best_iou and iou >= self.iou_threshold:
                    best_iou = iou
                    best_tid = tid

            if best_tid is not None:
                # Update existing track
                self.tracks[best_tid].bbox = det["bbox"]
                self.tracks[best_tid].confidence = det["confidence"]
                self.tracks[best_tid].last_seen = now
                matched_tracks.add(best_tid)
                matched_dets.add(i)

        # Create new tracks for unmatched detections
        for i, det in enumerate(detections):
            if i in matched_dets:
                continue

            track = TrackedObject(
                track_id=self._next_id,
                label=det["label"],
                confidence=det["confidence"],
                bbox=det["bbox"],
                first_seen=now,
                last_seen=now,
            )
            self.tracks[self._next_id] = track
            new_objects.append(track)
            self._next_id += 1

        return new_objects

    @staticmethod
    def _compute_iou(box_a: dict, box_b: dict) -> float:
        x1 = max(box_a["x1"], box_b["x1"])
        y1 = max(box_a["y1"], box_b["y1"])
        x2 = min(box_a["x2"], box_b["x2"])
        y2 = min(box_a["y2"], box_b["y2"])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        if intersection == 0:
            return 0.0

        area_a = (box_a["x2"] - box_a["x1"]) * (box_a["y2"] - box_a["y1"])
        area_b = (box_b["x2"] - box_b["x1"]) * (box_b["y2"] - box_b["y1"])
        union = area_a + area_b - intersection

        return intersection / union if union > 0 else 0.0

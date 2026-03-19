import os
import sys
import time
import asyncio
import signal
import cv2
import structlog

from detector import Detector
from frame_grabber import FrameGrabber
from tracker import SimpleTracker
from zone_manager import ZoneManager
from event_publisher import EventPublisher

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()

DETECTION_FPS = int(os.getenv("DETECTION_FPS", "5"))
ZONE_RELOAD_INTERVAL = 60  # Reload zones every 60 seconds
CAMERA_RELOAD_INTERVAL = 30  # Check for new cameras every 30 seconds


class DetectionPipeline:
    def __init__(self):
        self.detector = Detector()
        self.publisher = EventPublisher()
        self.zone_manager = ZoneManager()
        self.grabbers: dict[str, FrameGrabber] = {}
        self.trackers: dict[str, SimpleTracker] = {}
        self._running = True

    async def start(self):
        await self.publisher.connect()
        logger.info("detection_pipeline_started", fps=DETECTION_FPS)

        # Set up signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._shutdown)

        # Main loop
        tasks = [
            asyncio.create_task(self._camera_refresh_loop()),
            asyncio.create_task(self._zone_refresh_loop()),
            asyncio.create_task(self._detection_loop()),
        ]

        await asyncio.gather(*tasks, return_exceptions=True)
        await self.shutdown()

    def _shutdown(self):
        logger.info("shutdown_signal_received")
        self._running = False

    async def shutdown(self):
        for grabber in self.grabbers.values():
            grabber.stop()
        await self.publisher.close()
        logger.info("detection_pipeline_stopped")

    async def _camera_refresh_loop(self):
        """Periodically check for new/removed cameras."""
        while self._running:
            try:
                cameras = await self.publisher.get_active_cameras()
                current_ids = set(self.grabbers.keys())
                new_ids = {c["id"] for c in cameras}

                # Start grabbers for new cameras
                for cam in cameras:
                    if cam["id"] not in current_ids and cam["rtsp_url"]:
                        grabber = FrameGrabber(cam["name"], cam["rtsp_url"], fps=DETECTION_FPS)
                        grabber.start()
                        self.grabbers[cam["id"]] = grabber
                        self.trackers[cam["id"]] = SimpleTracker()
                        logger.info("camera_added_to_pipeline", camera=cam["name"])

                # Stop grabbers for removed cameras
                for cam_id in current_ids - new_ids:
                    self.grabbers[cam_id].stop()
                    del self.grabbers[cam_id]
                    del self.trackers[cam_id]
                    logger.info("camera_removed_from_pipeline", camera_id=cam_id)

            except Exception as e:
                logger.error("camera_refresh_error", error=str(e))

            await asyncio.sleep(CAMERA_RELOAD_INTERVAL)

    async def _zone_refresh_loop(self):
        """Periodically reload zones from database."""
        while self._running:
            try:
                for camera_id in list(self.grabbers.keys()):
                    zones = await self.publisher.load_zones(camera_id)
                    self.zone_manager.update_zones(camera_id, zones)
            except Exception as e:
                logger.error("zone_refresh_error", error=str(e))

            await asyncio.sleep(ZONE_RELOAD_INTERVAL)

    async def _detection_loop(self):
        """Main detection loop - process frames from all cameras."""
        interval = 1.0 / DETECTION_FPS

        # Wait for cameras to be loaded
        await asyncio.sleep(5)

        while self._running:
            start = time.time()

            for camera_id, grabber in list(self.grabbers.items()):
                try:
                    frame, frame_time = grabber.get_frame()
                    if frame is None:
                        continue

                    # Skip if frame is too old
                    if time.time() - frame_time > 2.0:
                        continue

                    # Run detection
                    detections = self.detector.detect(frame)
                    if not detections:
                        continue

                    # Track objects to avoid duplicate events
                    tracker = self.trackers.get(camera_id)
                    if tracker is None:
                        continue

                    new_objects = tracker.update(detections)

                    # Process only new objects
                    for obj in new_objects:
                        event_type = self.detector.get_event_type(obj.label)

                        # Check zones
                        h, w = frame.shape[:2]
                        matching_zones = self.zone_manager.check_detection(camera_id, obj.bbox, w, h)
                        zone_id = matching_zones[0]["id"] if matching_zones else None

                        # Encode snapshot
                        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        snapshot_path = self.publisher.upload_snapshot(jpeg.tobytes(), camera_id)

                        # Publish event
                        await self.publisher.publish_event(
                            camera_id=camera_id,
                            event_type=event_type,
                            label=obj.label,
                            confidence=obj.confidence,
                            bbox=obj.bbox,
                            snapshot_path=snapshot_path,
                            zone_id=zone_id,
                            tracker_id=obj.track_id,
                        )

                except Exception as e:
                    logger.error("detection_error", camera_id=camera_id, error=str(e))

            elapsed = time.time() - start
            sleep_time = interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)


async def main():
    pipeline = DetectionPipeline()
    await pipeline.start()


if __name__ == "__main__":
    asyncio.run(main())

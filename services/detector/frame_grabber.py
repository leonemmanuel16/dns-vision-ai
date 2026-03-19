import os
import cv2
import time
import structlog
import numpy as np
from threading import Thread, Event

logger = structlog.get_logger()

GO2RTC_URL = os.getenv("GO2RTC_URL", "http://localhost:1984")


class FrameGrabber:
    """Pulls frames from go2rtc RTSP streams."""

    def __init__(self, camera_name: str, rtsp_url: str, fps: int = 5):
        self.camera_name = camera_name
        self.rtsp_url = rtsp_url
        self.target_fps = fps
        self.frame: np.ndarray | None = None
        self.frame_time: float = 0
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._cap: cv2.VideoCapture | None = None

    def start(self):
        self._stop_event.clear()
        self._thread = Thread(target=self._grab_loop, daemon=True)
        self._thread.start()
        logger.info("frame_grabber_started", camera=self.camera_name)

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        if self._cap:
            self._cap.release()
        logger.info("frame_grabber_stopped", camera=self.camera_name)

    def get_frame(self) -> tuple[np.ndarray | None, float]:
        return self.frame, self.frame_time

    def _grab_loop(self):
        interval = 1.0 / self.target_fps
        reconnect_delay = 5

        while not self._stop_event.is_set():
            try:
                self._cap = cv2.VideoCapture(self.rtsp_url)
                if not self._cap.isOpened():
                    logger.warning("rtsp_connect_failed", camera=self.camera_name, url=self.rtsp_url)
                    time.sleep(reconnect_delay)
                    continue

                logger.info("rtsp_connected", camera=self.camera_name)

                while not self._stop_event.is_set():
                    start = time.time()
                    ret, frame = self._cap.read()
                    if not ret:
                        logger.warning("frame_read_failed", camera=self.camera_name)
                        break

                    self.frame = frame
                    self.frame_time = time.time()

                    elapsed = time.time() - start
                    sleep_time = interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

            except Exception as e:
                logger.error("grabber_error", camera=self.camera_name, error=str(e))
            finally:
                if self._cap:
                    self._cap.release()

            if not self._stop_event.is_set():
                logger.info("rtsp_reconnecting", camera=self.camera_name)
                time.sleep(reconnect_delay)

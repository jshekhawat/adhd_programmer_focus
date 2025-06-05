import asyncio
import fractions
import time
import av
from defaults import AppConfig
from dataclasses import dataclass

@dataclass
class FrameTiming:
    pts: int
    time_base: fractions.Fraction
    wait_time: float

class Recorder:

    def __init__(self, filename):
        cfg = AppConfig()
        self.VIDEO_PTIME = cfg.VIDEO_PTIME
        self.VIDEO_CLOCK_RATE = cfg.VIDEO_CLOCK_RATE
        self.VIDEO_TIME_BASE = cfg.VIDEO_TIME_BASE
        self.FPS = cfg.FPS
        self._timestamp = None
        self.output = av.open(filename, 'w')
        self.stream = self.output.add_stream("h264", fractions.Fraction(self.FPS))

    def _calculate_frame_timing(self):
        """Calculate timing information for the next frame."""
        current_time = time.time()
        
        if self._timestamp is None:
            self._start = current_time
            self._timestamp = 0
            wait_time = 0
        else:
            self._timestamp += int(self.VIDEO_PTIME * self.VIDEO_CLOCK_RATE)
            wait_time = self._start + (self._timestamp / self.VIDEO_CLOCK_RATE) - current_time

        return FrameTiming(
            pts=self._timestamp,
            time_base=self.VIDEO_TIME_BASE,
            wait_time=wait_time
        )

    async def _wait_for_next_frame(self, wait_time: float):
        """Wait until it's time for the next frame."""
        if wait_time > 0:
            await asyncio.sleep(wait_time)

    def _create_video_frame(self, image, pts, time_base):
        frame = av.video.frame.VideoFrame.from_ndarray(image, format="bgr24")
        frame.pts = pts
        frame.time_base = time_base
        return frame

    

    async def record(self, im):
        timing = self._calculate_frame_timing()
        
        # Wait for correct frame timing
        await self._wait_for_next_frame(timing.wait_time)
        
        # Create and encode frame
        frame = self._create_video_frame(im, timing.pts, timing.time_base)
        packet = self.stream.encode(frame)
        self.output.mux(packet)
    
    def stop(self):
        packet = self.stream.encode(None)
        self.output.mux(packet)
        self.output.close()
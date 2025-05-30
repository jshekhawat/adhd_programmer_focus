import av
import time
from pathlib import Path
import numpy as np
from PIL import Image

class Recorder:
    def __init__(self, output_path, fps=0.5, resolution=(1920, 1080)):
        """
        Initialize the recorder with the given settings.
        
        Args:
            output_path (str): Path where the video file will be saved
            fps (int): Desired frames per second
            resolution (tuple): Video resolution as (width, height)
        """
        self.output_path = Path(output_path)
        self.fps = fps
        self.resolution = resolution
        self.frame_duration = 1.0 / fps
        self.last_frame_time = 0
        
        # Create the container and stream
        self.container = av.open(str(self.output_path), mode='w')
        self.stream = self.container.add_stream('h264', rate=fps)
        self.stream.width = resolution[0]
        self.stream.height = resolution[1]
        self.stream.pix_fmt = 'yuv420p'
        
        # Set some reasonable H.264 encoding parameters
        self.stream.options = {
            'crf': '23',  # Constant Rate Factor (18-28 is a reasonable range)
            'preset': 'medium'  # Encoding speed preset
        }
        
        self.frame_count = 0
    
    def add_frame(self, frame: Image.Image):
        """
        Add a new frame to the video.
        
        Args:
            frame (PIL.Image): The frame to add
        """
        # Ensure we maintain the desired FPS
        current_time = time.time()
        time_since_last = current_time - self.last_frame_time
        
        if time_since_last < self.frame_duration:
            time.sleep(self.frame_duration - time_since_last)
        
        # Ensure the frame matches our desired resolution
        if frame.size != self.resolution:
            frame = frame.resize(self.resolution)
        
        # Convert PIL image to the format needed by PyAV
        frame_array = np.array(frame)
        av_frame = av.VideoFrame.from_ndarray(frame_array, format='bgr24')
        
        # Encode and write the frame
        packet = self.stream.encode(av_frame)
        self.container.mux(packet)
        
        self.last_frame_time = time.time()
        self.frame_count += 1
    
    def stop(self):
        """
        Finish encoding and close the video file.
        """
        # Flush the encoder
        packet = self.stream.encode(None)
        self.container.mux(packet)
        
        # Close the container
        self.container.close()
        
        print(f"Recording stopped. Wrote {self.frame_count} frames to {self.output_path}")

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
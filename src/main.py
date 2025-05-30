from PIL import ImageGrab
import time
import Xlib.display
from pathlib import Path
from datetime import datetime
from app import App


import Xlib.xobject
from recorder import Recorder

def get_window():
    display = Xlib.display.Display()
    window = display.get_input_focus().focus
    if isinstance(window, Xlib.xobject.drawable.Window):
        wmclass = window.get_wm_class()
        if wmclass is None:
            window = window.query_tree().parent
            wmclass = window.get_wm_class()
        if wmclass is None:
            return None
        wmclass = wmclass[1]
        return wmclass
    else:
        return None

def record_screen(duration=60, fps=30, output_dir="recordings"):
    """
    Record the screen for a specified duration.
    
    Args:
        duration (int): Recording duration in seconds
        fps (int): Frames per second
        output_dir (str): Directory to save the recording
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_path / f"recording_{timestamp}.mp4"
    
    print(f"Starting screen recording...")
    print(f"Duration: {duration} seconds")
    print(f"FPS: {fps}")
    print(f"Output: {output_file}")
    
    # Get screen resolution from first capture
    screen = ImageGrab.grab()
    resolution = screen.size
    


    # Initialize recorder
    with Recorder(str(output_file), fps=fps, resolution=resolution) as recorder:
        start_time = time.time()
        frame_count = 0
        
        while (time.time() - start_time) < duration:
            frame = ImageGrab.grab()
            recorder.add_frame(frame)
            frame_count += 1
            
    print(f"\nRecording complete!")
    print(f"Captured {frame_count} frames in {duration} seconds")
    print(f"Saved to: {output_file}")

if __name__ == "__main__":
    app = App()
    app.run()
    #wmclass = get_window()
    #print(wmclass)
    # Record for 10 seconds at 30fps
    #record_screen(duration=10, fps=1)
from PIL import ImageGrab
import time
from datetime import datetime
from pathlib import Path

class ScreenshotTaker:
    def __init__(self, save_dir="screenshots", interval=60):
        self.save_dir = Path(save_dir)
        self.interval = interval
        self.save_dir.mkdir(exist_ok=True)
    
    def take_screenshot(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.save_dir / f"screenshot_{timestamp}.png"
        screenshot = ImageGrab.grab()
        screenshot.save(filename)
        print(f"Screenshot saved: {filename}")
    
    def run(self):
        print(f"Starting screenshot capture every {self.interval} seconds")
        print(f"Saving screenshots to: {self.save_dir.absolute()}")
        try:
            while True:
                self.take_screenshot()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\nStopping screenshot capture")

if __name__ == "__main__":
    # Take a screenshot every minute
    app = ScreenshotTaker(interval=5)
    app.run()
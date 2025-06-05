import os
import json
from recorder import Recorder
import mss
from asyncio import Queue
import numpy as np
import cv2
import asyncio
from defaults import AppConfig

APP_DIR = os.path.join(os.environ["HOME"], ".cache", "afp")
METADATA_FILE = "metadata.json"
CONFIG_FILE = "config.json"
DB_NAME = "afp.db"
RECORDINGS_PATH = "recordings"
# App runs in background and captures a screenshot every two seconds


def dump_metadata(data):
    with open(os.path.join(APP_DIR, METADATA_FILE), "w") as m:
        json.dump(data, m, indent=2)


def dump_config(data):
    with open(os.path.join(APP_DIR, CONFIG_FILE), "w") as c:
        json.dump(data, c, indent=2)


class App:

    def __init__(self):
        if os.path.exists(os.path.join(APP_DIR, METADATA_FILE)):
            with open(os.path.join(APP_DIR, METADATA_FILE), "r") as m:
                metadata = json.load(m)
                self.frame_i = metadata["frame_i"]
                self.rec_num = metadata["rec_num"]
                # print(self.frame_i)
        else:
            if not os.path.exists(APP_DIR):
                os.makedirs(os.path.join(APP_DIR, RECORDINGS_PATH))
            
            dump_metadata({"frame_i": 0, "rec_num": 0})
            self.rec_num = 0
            self.frame_i = 0

        config = AppConfig()
        # create a work queue
        self.work_queue = Queue()
        self.processed = Queue()

        # mss for screenshots
        self.sst = mss.mss()
        self.FPS = config.FPS
        self.SECONDS_PER_REC = config.SECONDS_PER_REC
        self.recorder = Recorder(os.path.join(APP_DIR, "recordings", str(self.rec_num) + ".mp4"))
        

    def run(self):

        print("App is running in the background")
        while True:
            # take a screenshot every two seconds and send to recorder
            im = np.array(self.sst.grab(self.sst.monitors[1]))
            im = im[:, :, :-1]
            im = cv2.resize(im, (1920, 1080))
            # send async to recorder
            asyncio.run(self.recorder.record(im))

            # timestamp the image and queue for text processing
            self.frame_i +=1
            if (self.frame_i % (self.FPS * self.SECONDS_PER_REC)) == 0:
                print(f"Done with Current Recording. [FLUSHING] recording number: {self.rec_num}")
                self.recorder.stop()
                self.rec_num += 1
                self.recorder = Recorder(os.path.join(APP_DIR, "recordings", str(self.rec_num) + ".mp4"))
                dump_metadata({
                    "frame_i": self.frame_i,
                    "rec_num": self.rec_num
                })
    
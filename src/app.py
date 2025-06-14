import os
import json
from recorder import Recorder
import mss
from multiprocessing import Queue
import numpy as np
import cv2
import asyncio
from defaults import AppConfig
import Xlib.display
import multiprocessing
import datetime
import time
from PIL import Image
from tesserocr import PyTessBaseAPI, RIL
import signal


APP_DIR = os.path.join(os.environ["HOME"], ".cache", "afp")
METADATA_FILE = "metadata.json"
CONFIG_FILE = "config.json"
DB_NAME = "afp.db"
RECORDINGS_PATH = "recordings"


def get_active_window():
    display = Xlib.display.Display()
    window = display.get_input_focus().focus
    if isinstance(window, Xlib.xobject.drawable.Window):
        wmclass = window.get_wm_class()
        if wmclass is None:
            window = window.query_tree().parent
            wmclass = window.get_wm_class()
        if wmclass is None:
            return "None"
        winclass = wmclass[1]
        return winclass
    else:
        return "None"


def dump_metadata(data):
    with open(os.path.join(APP_DIR, METADATA_FILE), "w") as m:
        json.dump(data, m, indent=2)


def dump_config(data):
    with open(os.path.join(APP_DIR, CONFIG_FILE), "w") as c:
        json.dump(data, c, indent=2)

def dump_text(data):
    with open(os.path.join(APP_DIR, f"{data["frame_i"]}.json"), "w") as m:
        json.dump(data, m, indent=2)

class OCR:
    def __init__(self, langs="eng", resize_factor=1, conf_threshold=50):
        super().__init__()
        self.langs = langs
        self.rf = resize_factor
        self.conf_threshold = conf_threshold
        self.api = PyTessBaseAPI(psm=11, oem=3)

    def process_image(self, im):
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im = cv2.resize(im, (0, 0), fx=self.rf, fy=self.rf)
        im = Image.fromarray(im)
        self.api.SetImage(im)
        boxes = self.api.GetComponentImages(RIL.TEXTLINE, True)
        results = []
        _bboxes = []
        for i, (im, box, _, _) in enumerate(boxes):
            self.api.SetRectangle(box["x"], box["y"], box["w"], box["h"])

            ocrResult = self.api.GetUTF8Text()
            conf = self.api.MeanTextConf()

            if conf < self.conf_threshold:
                continue

            entry = {
                "x": box["x"] // self.rf,
                "y": box["y"] // self.rf,
                "w": box["w"] // self.rf,
                "h": box["h"] // self.rf,
                "text": ocrResult,
                "conf": conf,
            }

            _bboxes.append([entry["x"], entry["y"], entry["w"], entry["h"]])

            results.append(entry)

        return results


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
        self.recorder = Recorder(
            os.path.join(APP_DIR, "recordings", str(self.rec_num) + ".mp4")
        )

        self.nb_workers = 1 
        self.workers = []
        self.pids = []
        for i in range(self.nb_workers):
            w = multiprocessing.Process(target=self.process_images, args=())
            self.workers.append(w)
            self.pids.append(w.pid)
        for i in range(self.nb_workers):
            self.workers[i].start()
            print("started worker", i)

    def stop_process(self, sig, frame):
        print("STOPPING PROCESS", os.getpid())
        exit()

    def process_images(self):
        ocr = OCR()
        signal.signal(signal.SIGINT, self.stop_process)
        while True:

            data = self.work_queue.get()
            frame_i = data["frame_i"]
            im = data["im"]
            window_title = data["active_window"]
            t = data["time"]

            start = time.time()
            results = ocr.process_image(im)
            print("Processing time :", time.time() - start)
            data = {
                    "frame_i": frame_i,
                    "results": results,
                    "time": t,
                    "window_title": window_title,
                }
            self.processed.put(data)

            dump_text(data)

    def run(self):

        print("App is running in the background")
        monitor = self.sst.monitors[0]
        width = monitor["width"]
        height = monitor["height"]
        print(f"detected width:{width} detected height: {height}")
        prev_im = np.zeros((width, height, 3), dtype=np.uint8)
        while True:
            # take a screenshot every two seconds and send to recorder
            window = get_active_window()
            print(window)
            im = np.array(self.sst.grab(self.sst.monitors[0]))
            im = im[:, :, :-1]
            im = cv2.resize(im, (width, height))
            # send async to recorder
            asyncio.run(self.recorder.record(im))

            t = json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(t)
            try:
                self.work_queue.put(
                    {
                        "im": im,
                        "prev_im": prev_im,
                        "active_window": window,
                        "time": t,
                        "frame_i": self.frame_i,
                    }
                )
            except Exception as e:
                print(f"{e}")
            prev_im = im
            print(self.work_queue.qsize())
            print(self.processed.qsize())



            # timestamp the image and queue for text processing
            self.frame_i += 1
            if (self.frame_i % (self.FPS * self.SECONDS_PER_REC)) == 0:
                print(
                    f"Done with Current Recording. [FLUSHING] recording number: {self.rec_num}"
                )
                self.recorder.stop()
                self.rec_num += 1
                self.recorder = Recorder(
                    os.path.join(APP_DIR, "recordings", str(self.rec_num) + ".mp4")
                )
                dump_metadata({"frame_i": self.frame_i, "rec_num": self.rec_num})

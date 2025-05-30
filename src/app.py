from datetime import datetime
import json
import Xlib.display
import mss
from recorder import Recorder
import multiprocessing
from multiprocessing import Queue
import numpy as np
import cv2
from PIL import Image
from tesserocr import PyTessBaseAPI, RIL
import asyncio
import os
from pathlib import Path


DIR_PATH = os.path.join(os.environ["HOME"], ".cache", "apf")

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

class OCR:
    def __init__(self, langs="eng", rf=1, ct=50):
        self.langs = langs
        self.rf = rf
        self.ct = ct
        self.api = PyTessBaseAPI(psm=11, oem=3)

    def process_image(self, im):
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        im = cv2.resize(im, (0, 0), fx=self.rf, fy=self.rf)
        im = Image.fromarray(im)
        self.api.SetImage(im)
        boxes = self.api.GetComponentImages(RIL.TEXTLINE, True)
        results = []

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

            results.append(entry)

        return results



class App:

    def __init__(self):
        output_dir = "recordings"
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
    
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"recording_{timestamp}.mp4"
        print(output_file)
        self.recorder = Recorder(output_path=str(output_file))
        self.is_running = True
        self.sct = mss.mss()
        self.frame_i = 0
        # create two queues one to offload the text extraction work to the tesseract helpper
        # another to process the results back from the extracted text.
        
        self.images_queue = Queue()
        self.processed_images = Queue()
        self.num_workers = 1
        self.workers = []
        self.pids = []

        for i in range(self.num_workers):
            #offload work
            w = multiprocessing.Process(target=self.process_image, args = ())
            self.workers.append(w)
        for i in range(self.num_workers):
            self.workers[i].start()


    def process_image(self):
        ocr = OCR()

        while True:
            img = self.images_queue.get()
            results = ocr.process_image(img)
            self.processed_frames.put({
                "results": results
            })
        
    def run(self):
        #count = 0
        prev_img = np.zeros(
            (2560,1080, 3), dtype=np.uint8
        )
        while self.is_running:
            #print(self.sct.monitors)
            current_app = get_window()
            sc = self.sct.grab(self.sct.monitors[1])
            n_sc = np.array(sc)[:, :, :-1]
            n_sc = cv2.resize(n_sc, (2560, 1080))
            asyncio.run(self.recorder.add_frame(n_sc))

            time_stamp = json.dumps(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            self.images_queue.put({
                "img": n_sc,
                "prev_img": prev_img,
                "current_app": current_app,
                "timestamp": time_stamp,
                "frame_id":self.frame_i
            })

            self.frame_i += 1
            # print(n_sc)
            # count = count + 1
            #print(self.processed_frames.get(0))

            




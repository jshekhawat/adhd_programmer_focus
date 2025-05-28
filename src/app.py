import Xlib.display
import mss
from recorder import Recorder
from multiprocessing import Queue
import numpy as np
import cv2
from PIL import Image
from tesserocr import PyTessBaseAPI, RIL

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
        
        #self.recorder = Recorder()
        self.is_running = True
        self.sct = mss.mss()
        # create two queues one to offload the text extraction work to the tesseract helpper
        # another to process the results back from the extracted text.
        
        self.frames_queue = Queue()
        self.processed_frames = Queue()
        self.num_workers = 1
        self.workers = []
        self.pids = []

        for i in range(self.num_workers):
            #offload work
            w = multiprocessing.Process(target=self.)



    def process_image(self):
        ocr = OCR()

        while True:
            frame = self.frames_queue

        
    def run(self):
        #count = 0
        while self.is_running:
            print(self.sct.monitors)
            sc = self.sct.grab(self.sct.monitors[1])
            n_sc = np.array(sc)[:, :, :-1]
            n_sc = cv2.resize(n_sc, (2560, 1080))
            print(n_sc)
            #count = count + 1

            




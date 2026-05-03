"""
🎯 AI Detection PRO MAX
Object Detection + Tracking + Face Analysis (Age + Emotion)
Optimized for smooth FPS (async processing)
"""

# ================= AUTO INSTALL =================
import sys, subprocess, importlib

def install(pkg, name=None):
    try:
        importlib.import_module(name if name else pkg)
    except:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install("ultralytics")
install("opencv-python", "cv2")
install("numpy")
install("Pillow", "PIL")
install("deepface")

# ================= IMPORTS =================
import tkinter as tk
from tkinter import filedialog
import threading, queue
import cv2, time, random
import numpy as np
from PIL import Image, ImageTk
from ultralytics import YOLO
from deepface import DeepFace

# ================= COLORS =================
def get_color(cls):
    random.seed(hash(cls) % 1000)
    return (random.randint(50,255), random.randint(50,255), random.randint(50,255))

# ================= TRACKER =================
class Tracker:
    def __init__(self):
        self.objects = {}
        self.id_count = 0

    def update(self, detections):
        updated = {}
        output = []

        for det in detections:
            x1,y1,x2,y2,cls,conf = det
            cx,cy = (x1+x2)//2,(y1+y2)//2

            matched = False
            for oid,(ox,oy) in self.objects.items():
                if ((cx-ox)**2+(cy-oy)**2)**0.5 < 50:
                    updated[oid]=(cx,cy)
                    output.append(det+[oid])
                    matched=True
                    break

            if not matched:
                updated[self.id_count]=(cx,cy)
                output.append(det+[self.id_count])
                self.id_count+=1

        self.objects=updated
        return output

# ================= FACE ANALYZER (ASYNC) =================
class FaceAnalyzer(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.queue = queue.Queue()
        self.results = {}
        self.running = True

    def run(self):
        while self.running:
            if not self.queue.empty():
                oid, face_img = self.queue.get()

                try:
                    analysis = DeepFace.analyze(
                        face_img,
                        actions=['age', 'emotion'],
                        enforce_detection=False
                    )[0]

                    age = analysis['age']
                    emotion = max(analysis['emotion'], key=analysis['emotion'].get)

                    self.results[oid] = (age, emotion)
                except:
                    pass

    def stop(self):
        self.running = False

# ================= APP =================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 AI Detection PRO MAX")
        self.root.geometry("1100x700")

        self.canvas = tk.Label(root)
        self.canvas.pack()

        panel = tk.Frame(root)
        panel.pack()

        tk.Button(panel,text="Webcam",command=self.webcam).grid(row=0,column=0)
        tk.Button(panel,text="Video",command=self.open_video).grid(row=0,column=1)
        tk.Button(panel,text="Stop",command=self.stop).grid(row=0,column=2)
        tk.Button(panel,text="Save",command=self.save_toggle).grid(row=0,column=3)

        self.stats = tk.Label(root, text="Stats", font=("Arial",12))
        self.stats.pack()

        self.running=False
        self.cap=None
        self.save=False
        self.writer=None

        self.model=YOLO("yolov8n.pt")
        self.tracker=Tracker()

        self.face_analyzer = FaceAnalyzer()
        self.face_analyzer.start()

        self.last_face_update = {}
        self.counted_ids=set()

    def webcam(self):
        self.cap=cv2.VideoCapture(0)
        self.start()

    def open_video(self):
        path=filedialog.askopenfilename()
        if path:
            self.cap=cv2.VideoCapture(path)
            self.start()

    def start(self):
        if self.running: return
        self.running=True
        threading.Thread(target=self.loop,daemon=True).start()

    def stop(self):
        self.running=False
        if self.cap: self.cap.release()
        if self.writer:
            self.writer.release()
            self.writer=None
        self.face_analyzer.stop()

    def save_toggle(self):
        self.save=not self.save

    def loop(self):
        prev=time.time()
        frame_count = 0

        while self.running:
            frame_count += 1

            ret,frame=self.cap.read()
            if not ret: break

            small=cv2.resize(frame,(640,384))
            results=self.model(small,verbose=False)[0]

            detections=[]
            for box in results.boxes:
                x1,y1,x2,y2=map(int,box.xyxy[0])
                cls=self.model.names[int(box.cls[0])]
                conf=float(box.conf[0])

                h_ratio=frame.shape[0]/384
                w_ratio=frame.shape[1]/640

                x1=int(x1*w_ratio); x2=int(x2*w_ratio)
                y1=int(y1*h_ratio); y2=int(y2*h_ratio)

                detections.append([x1,y1,x2,y2,cls,conf])

            tracked=self.tracker.update(detections)

            class_count={}

            for det in tracked:
                x1,y1,x2,y2,cls,conf,oid=det
                color=get_color(cls)

                cv2.rectangle(frame,(x1,y1),(x2,y2),color,2)

                label = f"{cls} #{oid}"

                # FACE ANALYSIS ONLY FOR PERSON
                if cls == "person":
                    face_crop = frame[y1:y2, x1:x2]

                    if oid not in self.last_face_update or frame_count - self.last_face_update.get(oid,0) > 20:
                        if face_crop.size > 0:
                            self.face_analyzer.queue.put((oid, face_crop))
                            self.last_face_update[oid] = frame_count

                    if oid in self.face_analyzer.results:
                        age, emotion = self.face_analyzer.results[oid]
                        label += f" | Age:{age} | {emotion}"

                cv2.putText(frame,label,(x1,y1-10),0,0.6,color,2)

                class_count[cls]=class_count.get(cls,0)+1
                self.counted_ids.add(oid)

            # FPS
            now=time.time()
            fps=1/(now-prev)
            prev=now
            cv2.putText(frame,f"FPS:{int(fps)}",(10,30),0,1,(0,255,0),2)

            # SAVE VIDEO
            if self.save:
                if self.writer is None:
                    self.writer=cv2.VideoWriter(
                        "output.avi",
                        cv2.VideoWriter_fourcc(*'XVID'),
                        20,
                        (frame.shape[1],frame.shape[0])
                    )
                self.writer.write(frame)

            # TKINTER DISPLAY
            rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            img=Image.fromarray(rgb)
            imgtk=ImageTk.PhotoImage(img)

            self.canvas.imgtk=imgtk
            self.canvas.config(image=imgtk)

            # STATS PANEL
            text=f"Objects Seen: {len(self.counted_ids)}\n"
            for k,v in class_count.items():
                text+=f"{k}: {v}\n"

            self.stats.config(text=text)

        self.stop()


# ================= RUN =================
if __name__=="__main__":
    root=tk.Tk()
    App(root)
    root.mainloop()

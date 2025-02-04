import cv2
import threading
import numpy as np
from collections import defaultdict
from ultralytics import YOLO
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance


class MobileCamera:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
        self.frame = None
        self.running = True
        self.frame_skip = 0
        self.photo_count = 0
        self.total_price = 0
        self.detected_objects = defaultdict(lambda: {'count': 0, 'total': 0})
        self.show_price_window = False
        self.prices = {
            "apple": 1,
            "banana": 2,
            "orange": 3,
            "bottle": 4,
            "mouse": 5,
            "carrot": 6,
            "chair": 20
        }

    def getVideo(self, camera):
        cap = cv2.VideoCapture(camera)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        def capture_frames():
            while self.running and cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self.frame = frame
                else:
                    break

        thread = threading.Thread(target=capture_frames, daemon=True)
        thread.start()

        cv2.namedWindow("Mobile Cam - Object Detection")
        cv2.setMouseCallback("Mobile Cam - Object Detection", self.mouse_callback)

        while self.running:
            if self.frame is not None:
                if self.frame_skip % 2 == 0:
                    frame_copy = self.frame.copy()
                    self.process_frame(frame_copy)
                    self.draw_buttons(frame_copy)
                    cv2.imshow("Mobile Cam - Object Detection", frame_copy)

                self.frame_skip += 1

            key = cv2.waitKey(1)
            if key in [ord('c'), ord('e'), ord('q')]:
                self.handle_key_press(key)
                if key == ord('q'):
                    break

        cap.release()
        cv2.destroyAllWindows()

    def process_frame(self, frame):
        self.detected_objects.clear()
        self.total_price = 0

        results = self.model(frame)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                if conf > 0.5:
                    class_name = self.model.names[cls]
                    price = self.prices.get(class_name.lower())

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                    if price is not None:
                        self.detected_objects[class_name]['count'] += 1
                        self.detected_objects[class_name]['total'] = self.detected_objects[class_name]['count'] * price
                        cv2.putText(frame, f"{class_name}: ${price}", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    else:
                        cv2.putText(frame, f"{class_name}: undefined", (x1, y1 - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        self.total_price = sum(item['total'] for item in self.detected_objects.values())

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if 30 <= x <= 150 and 30 <= y <= 80:
                self.capture_photo()
            elif 180 <= x <= 300 and 30 <= y <= 80:
                self.retry_action()
            elif 330 <= x <= 450 and 30 <= y <= 80:
                self.quit_action()

    def handle_key_press(self, key):
        actions = {
            ord('c'): self.capture_photo,
            ord('e'): self.retry_action,
            ord('q'): self.quit_action
        }
        if key in actions:
            actions[key]()

    def draw_buttons(self, frame):
        buttons = [
            ("Scan", (30, 30), (150, 80)),
            ("Retry", (180, 30), (300, 80)),
            ("Quit", (330, 30), (450, 80))
        ]
        for text, (x1, y1), (x2, y2) in buttons:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (200, 200, 200), -1)
            cv2.putText(frame, text, (x1 + 20, y1 + 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    def capture_photo(self):
        if self.frame is not None:
            photo_name = f"detected_photo_{self.photo_count}.jpg"
            cv2.imwrite(photo_name, self.frame)
            self.display_price_window()
            self.photo_count += 1

    def retry_action(self):
        if hasattr(self, 'tk_window') and self.tk_window.winfo_exists():
            self.tk_window.destroy()
        self.show_price_window = False

    def quit_action(self):
        self.running = False
        if hasattr(self, 'tk_window') and self.tk_window.winfo_exists():
            self.tk_window.destroy()

    def load_image(self, path, size=(250, 200)):
        try:
            img = Image.open(path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img), img
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None, None

    def display_price_window(self):
        self.tk_window = tk.Tk()
        self.tk_window.title("Cashier Checkout")
        self.setup_price_window()
        self.tk_window.mainloop()

    def setup_price_window(self):
        self.tk_window.attributes("-fullscreen", True)
        self.tk_window.configure(bg="#F8F9F0")

        self.create_title()
        self.create_item_list()
        self.create_buttons()

    def create_title(self):
        title = tk.Label(self.tk_window, text="Cashier Checkout",
                         font=("Helvetica", 40, "bold"), bg="#F8F9F0", fg="#333333")
        title.pack(pady=20)

    def create_item_list(self):
        frame = tk.Frame(self.tk_window, bg="#FFFFFF", bd=2, relief="raised")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        columns = ("Item", "Price", "Quantity", "Total")
        item_list = ttk.Treeview(frame, columns=columns, show='headings', height=10)

        for col in columns:
            item_list.heading(col, text=col)
            item_list.column(col, width=200, anchor="center")

        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 18), rowheight=40)
        style.configure("Treeview.Heading", font=("Helvetica", 24, "bold"))

        for item_name, data in self.detected_objects.items():
            price = self.prices.get(item_name.lower(), 0)
            item_list.insert("", "end", values=(
                item_name.capitalize(),
                f"{price:.2f}",
                data['count'],
                f"{data['total']:.2f}"
            ))

        item_list.pack(fill="both", expand=True)

        total_label = tk.Label(frame, text=f"Total Price: ${self.total_price:.2f}",
                               font=("Helvetica", 28, "bold"), bg="#FFFFFF", fg="#D9534F")
        total_label.pack(pady=20)

    def create_buttons(self):
        button_frame = tk.Frame(self.tk_window, bg="#F8F9F0")
        button_frame.pack(pady=20)

        style = ttk.Style()
        style.configure("Accent.TButton", font=("Helvetica", 18, "bold"), padding=10)

        buttons = [
            ("Retry", self.retry_action),
            ("Quit", self.quit_action),
            ("Checkout", self.checkout_action)
        ]

        for i, (text, command) in enumerate(buttons):
            ttk.Button(button_frame, text=text, command=command,
                       style="Accent.TButton").grid(row=0, column=i, padx=20)


if __name__ == "__main__":
    cam = MobileCamera()
    cam.getVideo(0)
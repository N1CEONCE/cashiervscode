import cv2
import threading
import numpy as np

class MobileCamera:
    def __init__(self):
        # Load the pre-trained Haar Cascade classifier for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.frame = None
        self.running = True
        self.frame_skip = 0  # Initialize frame skip
        self.photo_count = 0  # To count the saved photos
        self.price = 10  # Example price for each detected face (numerical value)
        self.total_price = 0  # To accumulate the total price
        self.detected_faces = 0  # To track the number of detected faces
        self.name = "Human"  # Example item name for display

    def get_video(self, camera):
        self.camera = camera
        cap = cv2.VideoCapture(self.camera)

        # Reduce resolution to 960x720
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        def capture_frames():
            while self.running:
                ret, frame = cap.read()
                if ret:
                    self.frame = frame

        thread = threading.Thread(target=capture_frames)
        thread.start()

        while self.running:
            if self.frame is not None:
                if self.frame_skip % 2 == 0:
                    gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                    self.detected_faces = len(faces)
                    self.total_price = self.detected_faces * self.price

                    for (x, y, w, h) in faces:
                        cv2.rectangle(self.frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        cv2.putText(self.frame, f"Price: ${self.price}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                    cv2.imshow("Mobile Cam - Face Detection", self.frame)
                self.frame_skip += 1

            key = cv2.waitKey(1)
            if key == ord('c') and self.frame is not None:
                self.capture_photo()
            elif key == ord('q'):
                self.running = False
                break

        cap.release()
        thread.join()
        cv2.destroyAllWindows()

    def capture_photo(self):
        photo_name = f"detected_photo_{self.photo_count}.jpg"
        cv2.imwrite(photo_name, self.frame)
        print(f"Photo saved: {photo_name}")

        captured_image = cv2.imread(photo_name)
        if captured_image is not None:
            cv2.imshow("Captured Photo", captured_image)
        else:
            print("Error: Could not load the captured photo.")

        white_image = np.ones((600, 800, 3), dtype=np.uint8) * 255
        amount_text = f"Price: ${self.price} x {self.detected_faces} (amount of objects)"
        total_text = f"Total: ${self.total_price}"
        cv2.putText(white_image, f"Name: {self.name}", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 5)
        cv2.putText(white_image, amount_text, (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 5)
        cv2.putText(white_image, total_text, (100, 350), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 5)
        cv2.imshow("Price & Name Display", white_image)

        self.photo_count += 1

# Create an instance of MobileCamera and start video capture
cam = MobileCamera()
cam.get_video(0)

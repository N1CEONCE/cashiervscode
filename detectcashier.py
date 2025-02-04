import cv2
import threading
import numpy as np
from collections import defaultdict
from ultralytics import YOLO
import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from PIL import Image, ImageTk, ImageEnhance  # Added ImageEnhance for brightness adjustments

class MobileCamera:
    def __init__(self):
        # Load YOLOv8 model for object detection
        self.model = YOLO('yolov8n.pt')  # Use 'yolov8n.pt' or any desired model
        self.frame = None
        self.running = True
        self.frame_skip = 0  # Initialize frame skip
        self.photo_count = 0  # To count the saved photos
        self.total_price = 0  # To accumulate the total price
        self.detected_objects = defaultdict(lambda: {'count': 0, 'total': 0})  # Track each object and its total cost
        self.show_price_window = False  # Flag to control the display of the price window



        # Dictionary to store prices for specific object classes
        self.prices = {
            "apple": 1,  # Price of an apple is $1
            "banana": 2,  # Price of a banana is $2
            "orange": 3,
            "bottle": 4,
            "mouse": 5,
            "carrot": 6,
            "chair": 20,



        }

        # Calculate total price
        self.total_price = sum(data['total'] for data in self.detected_objects.values())

        # Load the QR code and Cash images (to be done in separate methods)
        self.qr_code_image = None
        self.cash_image = None
        self.original_qr_image = None
        self.original_cash_image = None

    def getVideo(self, camera):
        self.camera = camera
        cap = cv2.VideoCapture(self.camera)

        # Reduce resolution to 640x480
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 960)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Function to capture frames in a separate thread
        def capture_frames():
            while self.running:
                ret, frame = cap.read()
                if ret:
                    self.frame = frame

        # Start a thread to capture frames
        thread = threading.Thread(target=capture_frames)
        thread.start()

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                # Check if the "Scan" button was clicked
                if 30 < x < 150 and 30 < y < 80:
                    self.capture_photo()  # Call the function to handle 'c'

                # Check if the "Retry" button was clicked
                if 180 < x < 300 and 30 < y < 80:
                    self.retry_action()  # Call the function to handle 'e'

                # Check if the "Quit" button was clicked
                if 330 < x < 450 and 30 < y < 80:
                    self.quit_action()  # Call the function to handle 'q'

        # Set the mouse callback function for the window
        cv2.namedWindow("Mobile Cam - Object Detection")
        cv2.setMouseCallback("Mobile Cam - Object Detection", mouse_callback)

        while True:
            if self.frame is not None:
                # Skip every 2nd frame to reduce processing load
                if self.frame_skip % 2 == 0:
                    # Detect objects using YOLOv8 model
                    results = self.model(self.frame)

                    # Reset detected objects and total price for this frame
                    self.detected_objects.clear()
                    self.total_price = 0

                    # Loop over detected objects
                    # Loop over detected objects
                    for result in results:
                        boxes = result.boxes
                        for box in boxes:
                            # Extract bounding box and confidence score
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = box.conf[0]
                            cls = int(box.cls[0])

                            # Only show results with high confidence
                            if conf > 0.5:  # Threshold for confidence
                                # Draw rectangle for detected object
                                cv2.rectangle(self.frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                                # Get object class name from YOLO
                                class_name = self.model.names[cls]

                                # Get price from the price dictionary
                                if class_name.lower() in self.prices:
                                    price_tag = self.prices[class_name.lower()]
                                    # Add the object, increment count and calculate total for each type
                                    self.detected_objects[class_name]['count'] += 1
                                    self.detected_objects[class_name]['total'] = self.detected_objects[class_name][
                                                                                     'count'] * price_tag
                                else:
                                    price_tag = "undefined value"  # Set to "undefined" if not in the price dictionary

                                # Display class name and price tag on the video frame
                                if price_tag != "undefined value":
                                    cv2.putText(self.frame, f"{class_name}: ${price_tag}",
                                                (x1, y1 - 10),
                                                cv2.FONT_HERSHEY_SIMPLEX,
                                                1,  # Larger font scale for price display
                                                (0, 255, 0),
                                                2)  # Thicker font for better readability
                                else:
                                    cv2.putText(self.frame, f"{class_name}: {price_tag}",
                                                (x1, y1 - 10),
                                                cv2.FONT_HERSHEY_SIMPLEX,
                                                1,
                                                (0, 0, 255),  # Red color for undefined prices
                                                2)

                    # Calculate the cumulative total price for all detected items, excluding undefined ones
                    self.total_price = sum(item['total'] for item in self.detected_objects.values() if
                                           isinstance(item['total'], (int, float)))

                    # Calculate the cumulative total price for all detected items
                    self.total_price = sum(item['total'] for item in self.detected_objects.values())

                    # Draw buttons for "Scan", "Retry", and "Quit"
                    self.draw_buttons(self.frame)

                    # Display the frame with object detection
                    cv2.imshow("Mobile Cam - Object Detection", self.frame)

                self.frame_skip += 1

            # Capture keyboard input for 'c', 'e', and 'q'
            key = cv2.waitKey(1)
            if key == ord('c'):  # Scan (same as clicking "Scan")
                self.capture_photo()
            elif key == ord('e'):  # Retry (same as clicking "Retry")
                self.retry_action()
            elif key == ord('q'):  # Quit (same as clicking "Quit")
                self.quit_action()
                break

        cap.release()
        thread.join()
        cv2.destroyAllWindows()

    def draw_buttons(self, frame):
        # Draw "Scan" button
        cv2.rectangle(frame, (30, 30), (150, 80), (200, 200, 200), -1)
        cv2.putText(frame, "Scan", (50, 65), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # Draw "Retry" button
        cv2.rectangle(frame, (180, 30), (300, 80), (200, 200, 200), -1)
        cv2.putText(frame, "Retry", (200, 65), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

        # Draw "Quit" button
        cv2.rectangle(frame, (330, 30), (450, 80), (200, 200, 200), -1)
        cv2.putText(frame, "Quit", (350, 65), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    def capture_photo(self):
        # Save the current frame as an image
        if self.frame is not None:
            photo_name = f"detected_photo_{self.photo_count}.jpg"
            cv2.imwrite(photo_name, self.frame)
            print(f"Photo saved: {photo_name}")

            # Show the captured photo in a new window
            captured_image = cv2.imread(photo_name)
            if captured_image is not None:
                cv2.imshow("Captured Photo", captured_image)
                self.display_price_window()  # Show the price window after capturing the photo

                cv2.waitKey(1000)  # Optional: Wait 1 second before closing the window
                cv2.destroyWindow("Captured Photo")  # Close the captured photo window
            else:
                print("Error: Could not load the captured photo.")
            self.photo_count += 1

    def retry_action(self):
        # Close both the price window and the captured photo window
        if hasattr(self, 'tk_window') and self.tk_window.winfo_exists():
            self.tk_window.destroy()
        if cv2.getWindowProperty("Captured Photo", cv2.WND_PROP_VISIBLE) >= 1:
            cv2.destroyWindow("Captured Photo")
        self.show_price_window = False  # Reset flag

    def quit_action(self):
        self.running = False  # Stop the camera feed
        if hasattr(self, 'tk_window') and self.tk_window.winfo_exists():
            self.tk_window.destroy()
        if cv2.getWindowProperty("Captured Photo", cv2.WND_PROP_VISIBLE) >= 1:
            cv2.destroyWindow("Captured Photo")
        cv2.destroyAllWindows()  # Close all OpenCV windows

    def load_qr_code_image(self):
        try:
            img = Image.open("qrcode.jpg")  # Adjust the path if necessary
            img = img.resize((250, 200), Image.Resampling.LANCZOS)  # Resize the image to fit the frame
            self.qr_code_image = ImageTk.PhotoImage(img)
            self.original_qr_image = img  # Store the original image
        except Exception as e:
            print(f"Error loading QR code image: {e}")

    def load_cash_image(self):
        try:
            img = Image.open("cash.jpg")  # Adjust the path if necessary
            img = img.resize((250, 200), Image.Resampling.LANCZOS)  # Resize the image to fit the frame
            self.cash_image = ImageTk.PhotoImage(img)
            self.original_cash_image = img  # Store the original image
        except Exception as e:
            print(f"Error loading cash image: {e}")

    def load_buymeacoffee_image(self):
        try:
            img = Image.open("buymeacoffee.jpg")
            img = img.resize((400, 400), Image.Resampling.LANCZOS)
            self.buymeacoffee_image = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading buymeacoffee image: {e}")

    def darken_qr_image(self):
        enhancer = ImageEnhance.Brightness(self.original_qr_image)
        darkened_img = enhancer.enhance(0.5)  # Darken the image
        self.qr_code_image = ImageTk.PhotoImage(darkened_img)
        return self.qr_code_image

    def restore_qr_image(self):
        self.qr_code_image = ImageTk.PhotoImage(self.original_qr_image)
        return self.qr_code_image

    def darken_cash_image(self):
        enhancer = ImageEnhance.Brightness(self.original_cash_image)
        darkened_img = enhancer.enhance(0.5)  # Darken the image
        self.cash_image = ImageTk.PhotoImage(darkened_img)
        return self.cash_image

    def restore_cash_image(self):
        self.cash_image = ImageTk.PhotoImage(self.original_cash_image)
        return self.cash_image

    def display_price_window(self):
        self.tk_window = tk.Tk()
        self.tk_window.title("Cashier Checkout")
        self.tk_window.attributes("-fullscreen", True)
        self.tk_window.configure(bg="#F8F9F0")  # Light gray background

        title_label = tk.Label(self.tk_window, text="Cashier Checkout", font=("Helvetica", 40, "bold"), bg="#F8F9F0", fg="#333333")
        title_label.pack(pady=20)

        frame = tk.Frame(self.tk_window, bg="#FFFFFF", bd=2, relief="raised")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        separator = ttk.Separator(self.tk_window, orient="horizontal")
        separator.pack(fill="x", padx=20)

        # Load the images
        self.load_qr_code_image()
        self.load_cash_image()

        columns = ("Item", "Price", "Quantity", "Total")
        item_list = ttk.Treeview(frame, columns=columns, show='headings', height=10)

        item_list.heading("Item", text="Item")
        item_list.heading("Price", text="Price ($)")
        item_list.heading("Quantity", text="Quantity")
        item_list.heading("Total", text="Total ($)")

        item_list.column("Item", width=300, anchor="center")
        item_list.column("Price", width=200, anchor="center")
        item_list.column("Quantity", width=200, anchor="center")
        item_list.column("Total", width=200, anchor="center")

        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 18), rowheight=40)
        style.configure("Treeview.Heading", font=("Helvetica", 24, "bold"))

        for item_name, data in self.detected_objects.items():
            price = self.prices.get(item_name.lower(), 0)
            count = data['count']
            total_for_item = data['total']
            item_list.insert("", "end", values=(item_name.capitalize(), f"{price:.2f}", count, f"{total_for_item:.2f}"))

        item_list.pack(fill="both", expand=True)

        total_price_text = f"Total Price: ${self.total_price:.2f}"
        total_price_label = tk.Label(frame, text=total_price_text, font=("Helvetica", 28, "bold"), bg="#FFFFFF", fg="#D9534F")
        total_price_label.pack(pady=20)

        button_frame = tk.Frame(self.tk_window, bg="#F8F9F0")
        button_frame.pack(pady=20)

        retry_button = ttk.Button(button_frame, text="Retry", command=self.retry_action, style="Accent.TButton")
        retry_button.grid(row=0, column=0, padx=20, pady=10)

        quit_button = ttk.Button(button_frame, text="Quit", command=self.close_cashier_checkout, style="Accent.TButton")
        quit_button.grid(row=0, column=1, padx=20, pady=10)

        checkout_button = ttk.Button(button_frame, text="Checkout", command=self.checkout_action, style="Accent.TButton")
        checkout_button.grid(row=0, column=2, padx=20, pady=10)

        style.configure("Accent.TButton", font=("Helvetica", 18, "bold"), padding=10)
        style.map("Accent.TButton", foreground=[('active', '#FFFFFF')], background=[('active', '#D9534F')])

        self.tk_window.mainloop()

    def checkout_action(self):
        checkout_window = tk.Toplevel(self.tk_window)
        checkout_window.title("Checkout Confirmation")
        checkout_window.geometry("600x500")

        price_label = tk.Label(checkout_window, text=f"Total Price: ${self.total_price:.2f}", font=("Helvetica", 30, "bold"), fg="#D9534F")
        price_label.pack(pady=20)

        paymentmethod_label = tk.Label(checkout_window, text=f'Select Payment Method', font=("Helvetica", 30, "bold"))
        paymentmethod_label.pack(pady=5)

        boxes_frame = tk.Frame(checkout_window)
        boxes_frame.pack(pady=20)

        qr_label = tk.Label(boxes_frame, text="QR Code", font=("Helvetica", 16, "bold"))
        qr_label.grid(row=0, column=0, padx=10, pady=(0, 10), sticky="s")

        cash_label = tk.Label(boxes_frame, text="Cashout", font=("Helvetica", 16, "bold"))
        cash_label.grid(row=0, column=1, padx=10, pady=(0, 10), sticky="s")

        def on_enter_qr(event):
            qr_image_label.config(image=self.darken_qr_image())  # Change the image to a darker one

        def on_leave_qr(event):
            qr_image_label.config(image=self.restore_qr_image())  # Restore the original image

        def on_enter_cash(event):
            cash_image_label.config(image=self.darken_cash_image())  # Change the image to a darker one

        def on_leave_cash(event):
            cash_image_label.config(image=self.restore_cash_image())  # Restore the original image

        qr_frame = tk.Frame(boxes_frame, width=250, height=200, bd=2, relief="raised", bg="#FFFFFF")
        qr_frame.grid(row=1, column=0, padx=10)

        cash_frame = tk.Frame(boxes_frame, width=250, height=200, bd=2, relief="raised", bg="#FFFFFF")
        cash_frame.grid(row=1, column=1, padx=10)

        if self.qr_code_image:
            qr_image_label = tk.Label(qr_frame, image=self.qr_code_image, bg="#FFFFFF")
            qr_image_label.pack(expand=True)
            qr_image_label.bind("<Enter>", on_enter_qr)
            qr_image_label.bind("<Leave>", on_leave_qr)
            qr_image_label.bind("<Button-1>", self.qr_clicked)  # Add click event for the QR code

        if self.cash_image:
            cash_image_label = tk.Label(cash_frame, image=self.cash_image, bg="#FFFFFF")
            cash_image_label.pack(expand=True)
            cash_image_label.bind("<Enter>", on_enter_cash)
            cash_image_label.bind("<Leave>", on_leave_cash)
            cash_image_label.bind("<Button-1>", self.cash_clicked)  # Add click event for the Cash image


    def qr_clicked(self, event):

        # Create a new window on click
        new_window = tk.Toplevel(self.tk_window)
        new_window.title("QrCode")
        new_window.geometry("600x600")  # Increased window size

        label = tk.Label(new_window, text="Scan the QRCode", font=("Helvetica", 24))
        label.pack(pady=20)

        # Load and display the Buy Me a Coffee image
        self.load_buymeacoffee_image()  # Ensure the image is loaded
        if self.buymeacoffee_image:
            coffee_image_label = tk.Label(new_window, image=self.buymeacoffee_image)
            coffee_image_label.pack(pady=10)

        close_button = ttk.Button(new_window, text="Close", command=new_window.destroy)
        close_button.pack(pady=20)


    def cash_clicked(self, event):
        # Create a new window on click
        new_window = tk.Toplevel(self.tk_window)
        new_window.title("Cashout")
        new_window.geometry("500x300")

        label = tk.Label(new_window, text="Thank you for shopping with us", font=("Helvetica", 24))
        label.pack(pady=50)

        close_button = ttk.Button(new_window, text="Close", command=new_window.destroy)
        close_button.pack(pady=20)

    def retry_action(self):
        if hasattr(self, 'tk_window') and self.tk_window.winfo_exists():
            self.tk_window.destroy()

    def close_cashier_checkout(self):
        if hasattr(self, 'tk_window') and self.tk_window.winfo_exists():
            self.tk_window.destroy()


        self.tk_window.mainloop()


# Initialize and run the camera object
cam = MobileCamera()
cap = cv2.VideoCapture(0) #The number could be change depends on the network




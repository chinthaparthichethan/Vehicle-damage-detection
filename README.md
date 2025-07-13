

#  Automated Vehicle Damage Detection & Cost Estimator 

This project uses **YOLOv8**, a state-of-the-art deep learning model, to automate the detection of vehicle damage (scratches, dents, broken parts, etc.) and estimate the cost of repairs. It aims to help **insurance companies** speed up claims, reduce human error, and improve customer satisfaction.

---

##  Technologies Used

-  Object Detection: [YOLOv8](https://github.com/ultralytics/ultralytics)
-  Backend: Python + Flask / Django
- Image Processing: OpenCV, PIL
-  Deep Learning: PyTorch
-  Database: SQLite / MySQL
-  Cost Mapping: Dictionary-based part-pricing
-  Packaging: `requirements.txt`, `model.pt` (YOLOv8)

---

## Features

- Detects vehicle damages:  scratches, broken parts, broken lights
- Supports **2-wheelers, 4-wheelers, and 6-wheelers**
- Trained using a **custom damage dataset**
- Automatically estimates repair cost using predefined part-price database
- Clean user interface with login/register & result preview
- Real-time predictions and output image with bounding boxes

---

##  Project Structure


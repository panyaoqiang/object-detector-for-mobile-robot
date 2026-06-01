# Onboard Detector

`onboard_detector` is a ROS2 package for real-time dynamic obstacle detection, tracking, and velocity estimation on mobile robots. This package operates using an RGB-D camera and vehicle odometry, utilizing both vision-based deep learning and geometry-based point cloud processing algorithms.

## Features

* **Vision-based Object Detection (YOLO)**: A Python-based node running YOLO for robust 2D object detection. Supports PyTorch models (`.pt`) and TensorRT engines (`.engine`) for fast inference on hardware like Nvidia Jetson. Includes pose/keypoint estimation capabilities.
* **3D Obstacle Extraction & Clustering**: Processes depth images using U-V depth map projection and DBSCAN clustering from Point Cloud Data (PCL) to generate 3D bounding box proposals.
* **Tracking & Data Association**: Tracks 3D objects over time using a Kalman Filter to predict and update states across consecutive frames.
* **Dynamic & Static Classification**: Estimates velocity by analyzing frame-to-frame point cloud consistency and velocity vectors to classify objects as dynamic (moving) or static.
* **ROS2 Service Interface**: Provides a custom service (`GetDynamicObstacles.srv`) for other nodes to easily query dynamic obstacles within a specific radius.

## System Architecture

The package contains two main ROS2 nodes:
1. **`yolo_detector_node` (Python)**: Subscribes to the RGB image and outputs 2D bounding boxes and optional keypoints.
2. **`dynamic_detector_node` (C++)**: Subscribes to depth images, RGB images, and vehicle odometry/pose. It handles clustering, 3D bounding box generation, 3D tracking (Kalman Filter), and dynamic classification. 

## Dependencies

* ROS2 (Tested on foxy/humble)
* OpenCV (`cv_bridge`)
* PCL (Point Cloud Library) and `pcl_conversions`
* PyTorch / torchvision (For Python YOLO node)
* TensorRT (Optional, if using `.engine` Nano models)

Ensure standard ROS2 geometry, sensor, and vision message packages are installed:
```bash
sudo apt install ros-<ros2-distro>-vision-msgs ros-<ros2-distro>-sensor-msgs ros-<ros2-distro>-pcl-conversions

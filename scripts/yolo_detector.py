#!/usr/bin/env python3

from rclpy.node import Node
import cv2
import torch
import os
import std_msgs
from sensor_msgs.msg import CompressedImage
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray
from vision_msgs.msg import Detection2D
from cv_bridge import CvBridge
from std_msgs.msg import Float64, Float32MultiArray
from ament_index_python.packages import get_package_share_directory
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

from ultralytics import YOLO

target_classes = ["trunk"]

path_curr = os.path.dirname(__file__)

class yolo_detector(Node):
    def __init__(self):
        super().__init__('yolo_detector_node')
        self.get_logger().info("[onboardDetector]: YOLO detector init...")

        self.img_received = False
        self.img_detected = False

        # using ament to find the package's share directory where weights are installed
        pkg_share_path = get_package_share_directory('onboard_detector')
        
        self.declare_parameter('weights_path', '~/weights')
        weights_dir = self.get_parameter('weights_path').value
        weights_dir = os.path.expanduser(weights_dir)
        
        self.declare_parameter('use_pose_model', False)
        self.use_pose = self.get_parameter('use_pose_model').value
        
        self.declare_parameter('use_nano', True)
        self.use_nano = self.get_parameter('use_nano').value
        
        model_dir = 'pos' if self.use_pose else 'det'
        
        if self.use_nano:
            weight_path = os.path.join(weights_dir, model_dir, 'best.engine')
        else:
            weight_path = os.path.join(weights_dir, model_dir, 'best.pt')

        self.get_logger().info(f"Loading YOLO model from: {weight_path}")
        if self.use_pose:
            self.model = YOLO(weight_path, task='pose')
        else:
            self.model = YOLO(weight_path, task='detect')

        # subscriber
        self.br = CvBridge()
        self.declare_parameter('color_image_topic', '/camera/color/image_raw/compressed')
        img_topic = self.get_parameter('color_image_topic').get_parameter_value().string_value
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        self.img_sub = self.create_subscription(CompressedImage, img_topic, self.image_callback, qos_profile)
        self.get_logger().info(f"[onboardDetector]: YOLO color image topic name: {img_topic}.")

        # publisher
        self.img_pub = self.create_publisher(Image, "/yolo_detector/detected_image", 10)
        self.bbox_pub = self.create_publisher(Detection2DArray, "/yolo_detector/detected_bounding_boxes", 10)
        self.time_pub = self.create_publisher(std_msgs.msg.Float64, "/yolo_detector/yolo_time", 10)
        if self.use_pose:
            self.kpt_pub = self.create_publisher(Float32MultiArray, "/yolo_detector/detected_keypoints", 10)

        # timer
        self.declare_parameter('detect_timer_period', 0.020)
        time_step = self.get_parameter('detect_timer_period').value
        self.detect_timer = self.create_timer(time_step, self.detect_callback)
        self.get_logger().info(f"[onboardDetector]: Time step is set to: {time_step}s")
        self.bbox_timer = self.create_timer(time_step, self.bbox_callback)

        self.declare_parameter('debug_visualization', False)
        debug_vis = self.get_parameter('debug_visualization').value
        if (debug_vis):
            self.vis_timer = self.create_timer(time_step, self.vis_callback)
        self.get_logger().info(f"[onboardDetector]: Debug visualization is set to: {debug_vis}.")

    def image_callback(self, msg):
        self.img = self.br.compressed_imgmsg_to_cv2(msg, "bgr8")
        self.img_received = True

    def detect_callback(self):
        import time
        t1 = time.time()
        
        # Define confidence threshold here so it matches the inference parameters and filter
        conf_threshold = 0.30 #0.75
        
        if (self.img_received == True):
            # run YOLOv8 inference
            results = self.model.predict(source=self.img, conf=conf_threshold, verbose=False) 
            result = results[0] # taking the first (and only) result
            
            self.detected_bboxes = []
            self.detected_keypoints = []
            
            # extract bounding boxes, confidence, and class names
            for i in range(len(result.boxes)):
                box = result.boxes[i]
                conf = float(box.conf[0])
                
                # Filter results by confidence threshold
                if conf < conf_threshold:
                    continue
                    
                # get coordinates
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cls = int(box.cls[0])
                class_name = result.names.get(cls, "trunk")
                
                self.detected_bboxes.append([x1, y1, x2, y2, class_name, conf])
                
                if self.use_pose and hasattr(result, 'keypoints') and result.keypoints is not None and len(result.keypoints) > 0:
                    kpts = result.keypoints.xy[i].tolist() # List of [x, y]
                    self.detected_keypoints.append(kpts)
                
            # result.plot() typically returns a BGR image array. 
            # We convert BGR to RGB so it is displayed correctly by downstream ROS tools subscribing via our bgr8 or rgb8 formats.
            self.detected_img = cv2.cvtColor(result.plot(), cv2.COLOR_BGR2RGB)
            
            # Manually draw keypoints if use_pose
            if self.use_pose and hasattr(self, 'detected_keypoints'):
                for kpts in self.detected_keypoints:
                    for idx, kpt in enumerate(kpts):
                        x, y = int(kpt[0]), int(kpt[1])
                        if x == 0 and y == 0: 
                            continue # Skip unconfident or missing keypoints
                        cv2.circle(self.detected_img, (x, y), 5, (0, 255, 0), -1) # Green circle
                        cv2.putText(self.detected_img, str(idx), (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2) # Red text
                        
            self.img_detected = True

        
        t2 = time.time()
        
        # Calculate the duration in seconds
        duration_in_seconds = t2 - t1

        # Create a Float64 message and publish the duration
        duration_msg = Float64()
        duration_msg.data = duration_in_seconds
        self.time_pub.publish(duration_msg)
        
        
        import sys
        if not hasattr(self, 'last_print_time'):
            self.last_print_time = time.time()
        
        now = time.time()
        if now - self.last_print_time >= 1.0:
            if hasattr(self, 'detected_bboxes'):
                self.get_logger().info(f"[Timing] YOLO Inference took: {duration_in_seconds * 1000.0:.2f} ms")
                self.get_logger().info(f"[Detection] Found {len(self.detected_bboxes)} targets in the image.")
            self.last_print_time = now
        
    def vis_callback(self):
        if (self.img_detected == True):
            if self.img_pub.get_subscription_count() > 0:
                self.img_pub.publish(self.br.cv2_to_imgmsg(self.detected_img, "bgr8"))

    def bbox_callback(self):
        if (self.img_detected == True):
            bboxes_msg = Detection2DArray()
            for detected_box in self.detected_bboxes:
                category = detected_box[4]
                if (category in target_classes):
                    bbox_msg = Detection2D()
                    
                    x1, y1, x2, y2 = detected_box[0:4]
                    
                    # Note: Although this field says "center", the downstream dynamicDetector.cpp 
                    # actually expects the TOP-LEFT corner coordinates to be passed here.
                    bbox_msg.bbox.center.position.x = float(x1)
                    bbox_msg.bbox.center.position.y = float(y1)
                    
                    # Compute sizes: width = x2 - x1, height = y2 - y1
                    bbox_msg.bbox.size_x = float(abs(x2 - x1)) 
                    bbox_msg.bbox.size_y = float(abs(y2 - y1))

                    bboxes_msg.detections.append(bbox_msg)
            bboxes_msg.header.stamp = self.get_clock().now().to_msg()
            self.bbox_pub.publish(bboxes_msg)

            if self.use_pose and hasattr(self, 'detected_keypoints'):
                # Publish keypoints as Float32MultiArray
                # Format: [num_detections, 
                #          obj1_class_id, obj1_conf, obj1_x1, obj1_y1, obj1_x2, obj1_y2, obj1_num_kpts, kpt1_x, kpt1_y, kpt2_x, kpt2_y...,
                #          obj2_class_id, ...]
                kpt_msg = Float32MultiArray()
                data = [float(len(self.detected_bboxes))]
                for i in range(len(self.detected_bboxes)):
                    x1, y1, x2, y2, class_name, conf = self.detected_bboxes[i]
                    cls_id = 0.0 # You can map class_name to ID if needed
                    data.extend([cls_id, conf, float(x1), float(y1), float(x2), float(y2)])
                    
                    if i < len(self.detected_keypoints):
                        kpts = self.detected_keypoints[i]
                        data.append(float(len(kpts))) # num_kpts
                        for kpt in kpts:
                            data.extend([float(kpt[0]), float(kpt[1])])
                    else:
                        data.append(0.0) # 0 keypoints
                
                kpt_msg.data = data
                self.kpt_pub.publish(kpt_msg)

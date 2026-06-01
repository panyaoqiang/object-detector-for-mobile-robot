#!/usr/bin/env python3
"""
Utility script to export a YOLOv8 PyTorch model (.pt) to a TensorRT engine (.engine).
Optimized for NVIDIA Jetson Orin Nano.

NOTE: This script MUST be executed directly on the Orin Nano hardware, 
because TensorRT engines are highly specific to the GPU architecture and TensorRT version.
"""

import os
from ultralytics import YOLO

def main():
    # Define paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pt_path = os.path.join(script_dir, "best.pt")

    if not os.path.exists(pt_path):
        print(f"[Error] Weights file not found: {pt_path}")
        print("Please ensure 'best.pt' is placed in this directory.")
        return

    print(f"[Info] Loading PyTorch model from: {pt_path}")
    model = YOLO(pt_path)

    print("\n=======================================================")
    print("[Info] Starting TensorRT Export for Jetson Orin Nano...")
    print("[Info] Please be patient! Building the TRT engine may take 5 - 20 minutes.")
    print("=======================================================\n")

    # Export to TensorRT (.engine)
    # Recommended settings for Orin Nano:
    #   - format='engine': Targets TensorRT.
    #   - device=0: Uses the primary GPU.
    #   - half=True: Uses FP16 precision. The Orin Nano has hardware acceleration for FP16, resulting in huge speedups with negligible accuracy loss.
    #   - simplify=True: Simplifies the model graph before conversion.
    #   - workspace=4: Limits the TRT build workspace to 4GB to prevent Out-Of-Memory (OOM) crashes on Orin Nano (which has shared RAM).
    #   - imgsz=640: Locks the image size to 640x640 (standard YOLOv8).
    
    model.export(
        format='engine',
        device=0,
        half=True,
        simplify=True,
        imgsz=640,
        workspace=4
    )

    print("\n=======================================================")
    print("[Success] Export finished!")
    print("A new 'best.engine' file should now be available in the directory.")
    print("Update your code to load 'best.engine' instead of 'best.pt' for maximum performance.")
    print("=======================================================\n")

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
Created on Thu Jul 17 08:23:24 2025

@author: HP
"""
import cv2
import numpy as np
from tqdm import tqdm
import time

def circle_det(file):
    img = cv2.imread(file, cv2.IMREAD_GRAYSCALE)
    img_blur = cv2.medianBlur(img, 5) # reduce noise
    # Detect circles using HoughCircles
    circles = cv2.HoughCircles(
        img_blur,                    # Input image (grayscale)
        cv2.HOUGH_GRADIENT,          # Detection method
        dp=1.2,                      # Inverse ratio of accumulator resolution to image resolution
        minDist=250,                  # Minimum distance between detected circle centers
        param1=100,                  # Higher threshold for Canny edge detection (lower is half)
        param2=50,                   # Accumulator threshold for circle detection (smaller = more false circles)
        minRadius=20,                # Minimum radius to detect
        maxRadius=30                 # Maximum radius to detect
    )
    # Draw detected circles
    output = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
 
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for c in tqdm(circles[0, :]):
            # Draw outer circle
            cv2.circle(output, (c[0], c[1]), c[2], (0, 255, 0), 2)
            # Draw center point
            cv2.circle(output, (c[0], c[1]), 2, (0, 0, 255), 3)
    cv2.imwrite('test'+str(int(time.time()))+'.png', output)
    return circles


capture = cv2.VideoCapture('rtsp://10.58.12.246/0')
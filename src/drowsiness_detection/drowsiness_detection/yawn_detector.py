#!/usr/bin/env python3
import numpy as np
from scipy.spatial import distance as dist


class YawnDetector:
    def __init__(self, calibration_frames=70, k_threshold=4, moving_avg_window=20,):
        self.calibration_frames = calibration_frames 
        self.k_threshold = k_threshold  
        self.moving_avg_window = moving_avg_window
        self.mar_values = [] 
        self.calibrated = False      
        self.baseline_mean = 0       
        self.baseline_std = 0   
        self.mar_moving = []
        self.threshold = 0
        self.status = "Normal"

    def detect(self, landmarks):
        A = dist.euclidean(landmarks[50], landmarks[58]) 
        B = dist.euclidean(landmarks[52], landmarks[56])  
        C = dist.euclidean(landmarks[48], landmarks[54])  
        mar = (A + B) / (2.0 * C)

        self.mar_moving.append(mar)
        if len(self.mar_moving) > self.moving_avg_window:
            self.mar_moving.pop(0)

        mar_avg = np.mean(self.mar_moving)
        return mar_avg

    def calibrate_mouth(self, mar_avg):
        if len(self.mar_values) < self.calibration_frames:
            self.mar_values.append(mar_avg)
            self.status = "Calibrating..."
        else:
            if not self.calibrated:
                self.baseline_mean = np.mean(self.mar_values)
                self.baseline_std = np.std(self.mar_values)
                self.threshold = self.baseline_mean + self.k_threshold * self.baseline_std
                self.calibrated = True
                print(f"outh Calibration done:  Baseline Mean = {self.baseline_mean:.3f}, Baseline Std = {self.baseline_std:.3f}, Threshold = {self.threshold:.3f}")
                self.status = "Normal"
                
        return self.baseline_mean, self.baseline_std, self.threshold
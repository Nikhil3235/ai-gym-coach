import os
import cv2
import av
import time
import numpy as np
import mediapipe as mp
import threading
from collections import deque
from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from detectors.squat import SquatDetector
from detectors.pushup import PushUpDetector
from detectors.biceps_curl import BicepsCurlDetector
from detectors.shoulder_press import ShoulderPressDetector
from detectors.lunges import LungesDetector
from services.config.workout_config import POSE_CONNECTIONS


class VideoProcessorClass(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "Squats"

        # Trajectory & Tempo state
        self._path_history = deque(maxlen=40)
        self._concentric_duration = 0.0
        self._eccentric_duration = 0.0
        self._last_stage = None
        self._stage_changed_at = None

        model_path = os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task")
        base_option = python.BaseOptions(model_asset_path=model_path)

        options = vision.PoseLandmarkerOptions(
            base_options=base_option,
            running_mode=vision.RunningMode.VIDEO,
            min_pose_detection_confidence=0.7,
            min_pose_presence_confidence=0.7,
            min_tracking_confidence=0.7,
            output_segmentation_masks=False
        )

        self._landmarker = vision.PoseLandmarker.create_from_options(options)

        self._detectors = {
            "Squats": SquatDetector(),
            "Push-ups": PushUpDetector(),
            "Biceps Curls (Dumbbell)": BicepsCurlDetector(),
            "Shoulder Press": ShoulderPressDetector(),
            "Lunges": LungesDetector(),
        }

        self._frame_timestamps_ms = 0
    
    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()
        
    def set_exercise(self, exercise_type):
        with self._lock:
            if self._exercise_type != exercise_type:
                self._exercise_type = exercise_type
                self._path_history.clear()
                self._concentric_duration = 0.0
                self._eccentric_duration = 0.0
                self._last_stage = None
                self._stage_changed_at = None

    def get_exercise(self):
        with self._lock:
            return self._exercise_type

    def _get_connection_color(self, start_idx, end_idx, metrics, ex_type):
        # Neon palette (BGR format for OpenCV)
        default_color = (80, 255, 80)    # Green
        warning_color = (0, 165, 255)    # Amber/Orange
        danger_color = (0, 0, 255)       # Red

        if not metrics:
            return default_color

        if ex_type == "Squats":
            # Knee valgus caving alert
            if start_idx in [23, 24, 25, 26] and end_idx in [25, 26, 27, 28]:
                if metrics.get("valgus_status") == "CAVING":
                    return danger_color
                if metrics.get("depth_status") == "TOO HIGH":
                    return warning_color
            # Back angle leaning alert
            if start_idx in [11, 12, 23, 24] and end_idx in [11, 12, 23, 24]:
                if metrics.get("back_angle", 180) < 130:
                    return danger_color

        elif ex_type == "Push-ups":
            # Hip sagittal alignment alert
            if start_idx in [11, 12, 23, 24] and end_idx in [11, 12, 23, 24]:
                if metrics.get("hip_status") in ["SAGGING", "PIKED UP"]:
                    return danger_color
                if metrics.get("body_alignment") == "Poor Form":
                    return danger_color
                if metrics.get("body_alignment") == "Slight Bend":
                    return warning_color

        elif ex_type == "Biceps Curls (Dumbbell)":
            # Elbow drift alert
            if start_idx in [11, 12, 13, 14] and end_idx in [13, 14, 15, 16]:
                if metrics.get("shoulder_status") == "ELBOW DRIFTING":
                    return danger_color
            # Torso swing alert
            if start_idx in [11, 12, 23, 24] and end_idx in [11, 12, 23, 24]:
                if metrics.get("swing_status") == "SWINGING":
                    return danger_color

        elif ex_type == "Shoulder Press":
            # Back arch alert
            if start_idx in [11, 12, 23, 24] and end_idx in [11, 12, 23, 24]:
                if metrics.get("back_arch_status") == "Excessive Arch":
                    return danger_color
                if metrics.get("back_arch_status") == "Slight Arch":
                    return warning_color

        elif ex_type == "Lunges":
            # Balance alert on legs
            if start_idx in [23, 24, 25, 26] and end_idx in [25, 26, 27, 28]:
                if metrics.get("balance_status") == "OFF BALANCE":
                    return danger_color

        return default_color
        
    def _draw_skeleton(self, img, landmarks, metrics, ex_type):
        h, w = img.shape[:2]

        # Draw connecting lines with dynamic heatmap colors
        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]

            if p1.visibility > 0.7 and p2.visibility > 0.7:
                color = self._get_connection_color(start_idx, end_idx, metrics, ex_type)
                cv2.line(
                    img,
                    (int(p1.x * w), int(p1.y * h)),
                    (int(p2.x * w), int(p2.y * h)),
                    color,
                    8
                )
        
        # Draw joint coordinates
        for lm_idx, lm in enumerate(landmarks):
            if lm.visibility > 0.7:
                color = (255, 255, 0) # Cyan-blue default
                radius = 8
                
                # Check for joint specific alerts
                if metrics:
                    if ex_type == "Squats" and lm_idx in [25, 26] and metrics.get("valgus_status") == "CAVING":
                        color = (0, 0, 255)
                        radius = 12
                    elif ex_type == "Push-ups" and lm_idx in [23, 24] and metrics.get("hip_status") in ["SAGGING", "PIKED UP"]:
                        color = (0, 0, 255)
                        radius = 12
                    elif ex_type == "Biceps Curls (Dumbbell)" and lm_idx in [13, 14] and metrics.get("shoulder_status") == "ELBOW DRIFTING":
                        color = (0, 0, 255)
                        radius = 12

                cv2.circle(
                    img, 
                    (int(lm.x * w), int(lm.y * h)),
                    radius,
                    color,
                    -1
                )
            
    def _draw_no_pose_warnings(self, img):
        cv2.putText(
            img,
            "NO POSE DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            img,
            "PLEASE FACE THE CAMERA",
            (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

    def _draw_hud(self, img, metrics, ex_type):
        h, w = img.shape[:2]
        
        # 1. Semi-transparent panel overlay
        overlay = img.copy()
        cv2.rectangle(overlay, (15, 15), (380, 220), (10, 10, 15), -1)
        cv2.addWeighted(overlay, 0.75, img, 0.25, 0, img)
        
        # 2. Border
        cv2.rectangle(img, (15, 15), (380, 220), (245, 166, 35), 2)
        
        # 3. Header
        cv2.putText(img, f"COACH HUD | {ex_type.upper()}", (30, 42), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 212, 255), 2, cv2.LINE_AA)
        cv2.line(img, (25, 52), (370, 52), (255, 255, 255), 1)
        
        # 4. Reps
        reps = metrics.get("reps", 0)
        cv2.putText(img, f"REPS: {reps}", (30, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                    
        # 5. Form Alerts
        alert_text = "FORM: EXCELLENT"
        alert_color = (80, 255, 80)
        
        if ex_type == "Squats":
            depth = metrics.get("depth_status", "")
            valgus = metrics.get("valgus_status", "")
            back = metrics.get("back_angle", 180)
            if valgus == "CAVING":
                alert_text = "ALERT: KNEES CAVING!"
                alert_color = (0, 0, 255)
            elif back < 130:
                alert_text = "ALERT: LEANING FORWARD!"
                alert_color = (0, 0, 255)
            elif depth == "TOO HIGH":
                alert_text = "INFO: SQUAT DEEPER"
                alert_color = (0, 165, 255)
                
        elif ex_type == "Push-ups":
            hip = metrics.get("hip_status", "")
            align = metrics.get("body_alignment", "")
            if hip == "SAGGING":
                alert_text = "ALERT: HIPS SAGGING!"
                alert_color = (0, 0, 255)
            elif hip == "PIKED UP":
                alert_text = "ALERT: HIPS TOO HIGH!"
                alert_color = (0, 0, 255)
            elif align == "Poor Form":
                alert_text = "ALERT: POOR BODY LINE!"
                alert_color = (0, 0, 255)
            elif align == "Slight Bend":
                alert_text = "INFO: KEEP BODY STRAIGHT"
                alert_color = (0, 165, 255)
                
        elif ex_type == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")
            if swing == "SWINGING":
                alert_text = "ALERT: STOP SWINGING!"
                alert_color = (0, 0, 255)
            elif shoulder == "ELBOW DRIFTING":
                alert_text = "ALERT: KEEP ELBOW STABLE!"
                alert_color = (0, 0, 255)
                
        elif ex_type == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")
            if back_arch == "Excessive Arch":
                alert_text = "ALERT: ARCH EXCESSIVE!"
                alert_color = (0, 0, 255)
            elif back_arch == "Slight Arch":
                alert_text = "INFO: BRACE YOUR CORE"
                alert_color = (0, 165, 255)
                
        elif ex_type == "Lunges":
            balance = metrics.get("balance_status", "")
            if balance == "OFF BALANCE":
                alert_text = "ALERT: FIX BALANCE!"
                alert_color = (0, 0, 255)
                
        cv2.putText(img, alert_text, (30, 115), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, alert_color, 2, cv2.LINE_AA)
        
        # 6. Tempo
        concentric_str = f"{self._concentric_duration:.1f}s" if self._concentric_duration > 0 else "0.0s"
        eccentric_str = f"{self._eccentric_duration:.1f}s" if self._eccentric_duration > 0 else "0.0s"
        cv2.putText(img, f"TEMPO: Up: {concentric_str} | Down: {eccentric_str}", (30, 145), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)
        
        # 7. Core Angles / Joint values
        if ex_type == "Squats":
            cv2.putText(img, f"Knee Angle: {metrics.get('knee_angle', 0)}d", (30, 175), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(img, f"Back Angle: {metrics.get('back_angle', 0)}d", (30, 200), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        elif ex_type == "Push-ups":
            cv2.putText(img, f"Elbow Angle: {metrics.get('elbow_angle', 0)}d", (30, 175), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(img, f"Alignment: {metrics.get('body_alignment', 'N/A')}", (30, 200), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        elif ex_type == "Biceps Curls (Dumbbell)":
            cv2.putText(img, f"Elbow Angle: {metrics.get('elbow_angle', 0)}d", (30, 175), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(img, f"Stability: {metrics.get('shoulder_status', 'N/A')}", (30, 200), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        elif ex_type == "Shoulder Press":
            cv2.putText(img, f"Elbow Angle: {metrics.get('elbow_angle', 0)}d", (30, 175), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(img, f"Lockout: {metrics.get('extension_status', 'N/A')}", (30, 200), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        elif ex_type == "Lunges":
            cv2.putText(img, f"Front Knee: {metrics.get('front_knee_angle', 0)}d", (30, 175), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(img, f"Torso: {metrics.get('torso_angle', 0)}d", (30, 200), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

    def _draw_bar_path(self, img):
        if len(self._path_history) < 2:
            return
        
        points = list(self._path_history)
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            thickness = int(6 * (i / len(points))) + 1
            # Dynamic shade: older coordinates are darker, newer are neon yellow/cyan
            color_shade = (255, int(120 + 135 * (i / len(points))), 0)
            cv2.line(img, p1, p2, color_shade, thickness)
            
        cv2.circle(img, points[-1], 6, (0, 255, 255), -1)

    def recv(self, frame):
        image = np.asarray(
            cv2.flip(frame.to_ndarray(format="bgr24"), 1),
            dtype=np.uint8
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        )

        self._frame_timestamps_ms += 30
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamps_ms)

        ex_type = self.get_exercise()
        detector = self._detectors.get(ex_type)
        metrics = None

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]
            h, w = image.shape[:2]

            # 1. Calculate active pose metrics first
            if detector:
                metrics = detector.process(landmarks)
                metrics["pose_detected"] = True
                
                # 2. Dynamic Bar Path / Wrist Trajectory Tracking
                track_idx = None
                if ex_type in ["Biceps Curls (Dumbbell)", "Shoulder Press"]:
                    left_vis = landmarks[15].visibility
                    right_vis = landmarks[16].visibility
                    track_idx = 15 if left_vis >= right_vis else 16
                elif ex_type == "Squats":
                    track_idx = 11
                elif ex_type == "Push-ups":
                    track_idx = 11
                elif ex_type == "Lunges":
                    track_idx = 23

                if track_idx is not None and landmarks[track_idx].visibility > 0.7:
                    pt = landmarks[track_idx]
                    self._path_history.append((int(pt.x * w), int(pt.y * h)))

                # 3. Tempo Tracking
                current_stage = detector.stage
                now = time.time()
                if current_stage != self._last_stage:
                    if self._stage_changed_at is not None:
                        duration = now - self._stage_changed_at
                        if self._last_stage == "down" and current_stage == "up":
                            self._eccentric_duration = duration
                        elif self._last_stage == "up" and current_stage == "down":
                            self._concentric_duration = duration
                    self._stage_changed_at = now
                    self._last_stage = current_stage

                # Add tempo to session metrics
                metrics["concentric_duration"] = self._concentric_duration
                metrics["eccentric_duration"] = self._eccentric_duration
                self.set_latest_metrics(metrics)

            # 4. Render Dynamic Joint Heatmap & Skeleton
            self._draw_skeleton(image, landmarks, metrics, ex_type)
            
            # 5. Render Neon Bar Path Trail
            self._draw_bar_path(image)
            
            # 6. Render Glassmorphic Stats HUD
            if metrics:
                self._draw_hud(image, metrics, ex_type)

        else:
            self._draw_no_pose_warnings(image)
            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"] = False
                else:
                    self._latest_metrics = {"pose_detected": False}

        return av.VideoFrame.from_ndarray(image, format="bgr24")
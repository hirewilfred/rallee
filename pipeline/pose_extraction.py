"""Step 1 of the pipeline: pose extraction.

Runs MediaPipe Pose over every frame of a clip and returns the raw
landmark sequence. Nothing here is scale- or angle-invariant yet --
that's normalization.py's job.
"""

from __future__ import annotations

import cv2
import mediapipe as mp

from datatypes import PoseFrame, PoseSequence

_mp_pose = mp.solutions.pose

# MediaPipe Pose landmark indices we care about (of the full 33).
# https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
LANDMARK = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
}


def extract_pose_sequence(video_path: str, min_visibility: float = 0.5) -> PoseSequence:
    """Extract a PoseSequence from a video file.

    Frames where MediaPipe fails to detect a pose are dropped rather than
    padded -- the caller (contact-frame detection) works on whatever frames
    it's given and shouldn't have to special-case gaps.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames: list[PoseFrame] = []

    with _mp_pose.Pose(
        static_image_mode=False,
        model_complexity=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        frame_index = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result.pose_landmarks is not None:
                landmarks = {
                    i: (lm.x, lm.y, lm.z, lm.visibility)
                    for i, lm in enumerate(result.pose_landmarks.landmark)
                }
                visible = [landmarks[i] for i in LANDMARK.values() if i in landmarks]
                if visible and min(v[3] for v in visible) >= min_visibility:
                    frames.append(
                        PoseFrame(
                            frame_index=frame_index,
                            timestamp_s=frame_index / fps,
                            landmarks=landmarks,
                        )
                    )

            frame_index += 1

    cap.release()

    if not frames:
        raise ValueError(
            f"No reliable pose detected in {video_path} -- "
            "reject at capture, don't pass this downstream."
        )

    return PoseSequence(frames=frames, fps=fps, source_path=video_path)

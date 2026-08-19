"""Step 2 of the pipeline: normalization.

The hard part and the real IP, per the build plan. Converts raw pose
landmarks into scale- and angle-invariant features: joint angles, ratios
of body-relative distances, and swing timing. A 5'2" and 6'4" player
hitting the same shot should produce near-identical feature vectors.
"""

from __future__ import annotations

import numpy as np

from datatypes import FeatureVector, PoseSequence
from pose_extraction import LANDMARK


def _xy(landmarks: dict[int, tuple[float, float, float, float]], idx: int) -> np.ndarray:
    x, y, *_ = landmarks[idx]
    return np.array([x, y])


def _angle_deg(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at vertex b, formed by rays b->a and b->c, in degrees."""
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_angle)))


def _shoulder_width(landmarks: dict[int, tuple[float, float, float, float]]) -> float:
    l = _xy(landmarks, LANDMARK["left_shoulder"])
    r = _xy(landmarks, LANDMARK["right_shoulder"])
    return float(np.linalg.norm(l - r))


def _hip_height(landmarks: dict[int, tuple[float, float, float, float]]) -> float:
    """Vertical distance from ankle midpoint to hip midpoint -- a scale
    reference that's stable across the swing (unlike shoulder width,
    which can foreshorten as the torso rotates)."""
    hip_mid = (_xy(landmarks, LANDMARK["left_hip"]) + _xy(landmarks, LANDMARK["right_hip"])) / 2
    ankle_mid = (
        _xy(landmarks, LANDMARK["left_ankle"]) + _xy(landmarks, LANDMARK["right_ankle"])
    ) / 2
    return float(abs(hip_mid[1] - ankle_mid[1]))


def _wrist_speed_series(sequence: PoseSequence, paddle_side: str) -> list[float]:
    wrist_idx = LANDMARK[f"{paddle_side}_wrist"]
    speeds = [0.0]
    for i in range(1, len(sequence.frames)):
        prev, curr = sequence.frames[i - 1], sequence.frames[i]
        if wrist_idx not in prev.landmarks or wrist_idx not in curr.landmarks:
            speeds.append(0.0)
            continue
        dt = curr.timestamp_s - prev.timestamp_s
        if dt <= 0:
            speeds.append(0.0)
            continue
        d = np.linalg.norm(_xy(curr.landmarks, wrist_idx) - _xy(prev.landmarks, wrist_idx))
        speeds.append(float(d / dt))
    return speeds


def _find_takeback_frame(speeds: list[float], contact_idx: int) -> int:
    """Walk backward from contact to the local speed minimum that marks
    the start of the forward swing (end of the backswing pause)."""
    i = contact_idx
    while i > 0 and speeds[i - 1] <= speeds[i]:
        i -= 1
    return i


def _find_weight_shift_onset(sequence: PoseSequence, contact_idx: int, paddle_side: str) -> int:
    """Approximate weight-shift onset as the frame where the lead ankle
    (opposite the paddle hand) starts moving laterally toward the shot,
    walking backward from contact. Simplified heuristic -- validate
    against labelled clips before trusting this as a coaching signal."""
    lead_side = "left" if paddle_side == "right" else "right"
    ankle_idx = LANDMARK[f"{lead_side}_ankle"]

    i = contact_idx
    while i > 0:
        if ankle_idx not in sequence.frames[i].landmarks or ankle_idx not in sequence.frames[i - 1].landmarks:
            break
        dx = abs(
            _xy(sequence.frames[i].landmarks, ankle_idx)[0]
            - _xy(sequence.frames[i - 1].landmarks, ankle_idx)[0]
        )
        if dx < 1e-3:
            break
        i -= 1
    return i


def compute_feature_vector(
    sequence: PoseSequence, contact_idx: int, paddle_side: str = "right"
) -> FeatureVector:
    contact_landmarks = sequence.frames[contact_idx].landmarks
    shoulder = LANDMARK["left_shoulder"] if paddle_side == "right" else LANDMARK["right_shoulder"]
    elbow = LANDMARK[f"{paddle_side}_elbow"]
    wrist = LANDMARK[f"{paddle_side}_wrist"]
    hip = LANDMARK[f"{paddle_side}_hip"]
    knee = LANDMARK[f"{paddle_side}_knee"]
    ankle = LANDMARK[f"{paddle_side}_ankle"]
    opp_shoulder = LANDMARK["right_shoulder"] if paddle_side == "right" else LANDMARK["left_shoulder"]

    elbow_angle = _angle_deg(
        _xy(contact_landmarks, shoulder), _xy(contact_landmarks, elbow), _xy(contact_landmarks, wrist)
    )
    shoulder_angle = _angle_deg(
        _xy(contact_landmarks, opp_shoulder), _xy(contact_landmarks, shoulder), _xy(contact_landmarks, elbow)
    )
    knee_angle = _angle_deg(
        _xy(contact_landmarks, hip), _xy(contact_landmarks, knee), _xy(contact_landmarks, ankle)
    )
    hip_angle = _angle_deg(
        _xy(contact_landmarks, knee), _xy(contact_landmarks, hip), _xy(contact_landmarks, shoulder)
    )

    hip_h = _hip_height(contact_landmarks)
    shoulder_w = _shoulder_width(contact_landmarks)

    contact_height = float(1.0 - _xy(contact_landmarks, wrist)[1])  # image y grows downward
    contact_height_ratio = contact_height / hip_h if hip_h else 0.0

    lead_ankle = LANDMARK["left_ankle"] if paddle_side == "right" else LANDMARK["right_ankle"]
    stride = float(
        np.linalg.norm(_xy(contact_landmarks, ankle) - _xy(contact_landmarks, lead_ankle))
    )
    stride_ratio = stride / shoulder_w if shoulder_w else 0.0

    speeds = _wrist_speed_series(sequence, paddle_side)
    takeback_idx = _find_takeback_frame(speeds, contact_idx)
    weight_shift_idx = _find_weight_shift_onset(sequence, contact_idx, paddle_side)

    return FeatureVector(
        contact_frame_index=contact_idx,
        elbow_angle=elbow_angle,
        shoulder_angle=shoulder_angle,
        knee_angle=knee_angle,
        hip_angle=hip_angle,
        contact_height_over_hip_height=contact_height_ratio,
        stride_over_shoulder_width=stride_ratio,
        takeback_to_contact_frames=contact_idx - takeback_idx,
        weight_shift_onset_frame=contact_idx - weight_shift_idx,
    )

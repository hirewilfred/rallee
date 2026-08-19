"""Step 3 of the pipeline: contact-frame detection.

Highest-risk piece of the pipeline per the build plan: "identify the
contact frame reliably or every measurement is noise." This is a first
pass heuristic, not the final answer -- it needs validation against
hand-labelled reference clips before anything downstream is trusted
(see Phase 1b gate at week 12).

Heuristic: the paddle-side wrist reaches peak forward speed at contact,
then decelerates sharply as the paddle meets the ball. We track wrist
speed (finite difference of position, normalized by shoulder width to
stay scale-invariant) and take the peak within the swing window.
"""

from __future__ import annotations

import numpy as np

from datatypes import PoseSequence
from pose_extraction import LANDMARK


def _shoulder_width(frame_landmarks: dict[int, tuple[float, float, float, float]]) -> float:
    lx, ly, *_ = frame_landmarks[LANDMARK["left_shoulder"]]
    rx, ry, *_ = frame_landmarks[LANDMARK["right_shoulder"]]
    return float(np.hypot(lx - rx, ly - ry))


def detect_contact_frame(sequence: PoseSequence, paddle_side: str = "right") -> int:
    """Return the index into sequence.frames (not the original video frame
    index) of the estimated contact frame.

    paddle_side: "right" or "left" -- which wrist holds the paddle.
    """
    wrist_idx = LANDMARK[f"{paddle_side}_wrist"]

    positions = []
    scales = []
    for f in sequence.frames:
        if wrist_idx not in f.landmarks:
            positions.append(None)
            scales.append(None)
            continue
        x, y, *_ = f.landmarks[wrist_idx]
        positions.append((x, y))
        scales.append(_shoulder_width(f.landmarks))

    speeds = [0.0] * len(positions)
    for i in range(1, len(positions)):
        if positions[i] is None or positions[i - 1] is None or not scales[i]:
            continue
        dx = positions[i][0] - positions[i - 1][0]
        dy = positions[i][1] - positions[i - 1][1]
        dt = sequence.frames[i].timestamp_s - sequence.frames[i - 1].timestamp_s
        if dt <= 0:
            continue
        # Normalize by shoulder width so the speed is scale-invariant.
        speeds[i] = float(np.hypot(dx, dy) / scales[i] / dt)

    if not any(speeds):
        raise ValueError(
            "Could not track paddle wrist through the clip -- "
            "reject this clip rather than guessing a contact frame."
        )

    contact_idx = int(np.argmax(speeds))
    return contact_idx

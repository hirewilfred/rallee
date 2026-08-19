"""Shared data types for the DinkIQ analysis pipeline.

clip -> pose extraction -> normalization -> feature vector
                                                 |
                                pgvector nearest-neighbour vs. corpus
                                                 |
                                      deviation deltas -> Claude -> coaching
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PoseFrame:
    """One frame of MediaPipe Pose landmarks.

    landmarks maps MediaPipe's 33 landmark indices to (x, y, z, visibility),
    in normalized image coordinates (0-1) as returned by the Pose model.
    """

    frame_index: int
    timestamp_s: float
    landmarks: dict[int, tuple[float, float, float, float]]


@dataclass
class PoseSequence:
    frames: list[PoseFrame]
    fps: float
    source_path: str


@dataclass
class FeatureVector:
    """Scale- and angle-invariant features measured at the contact frame.

    Every distance is expressed as a ratio (unit = shoulder width or hip
    height), and every angle is in degrees, so a 5'2" and 6'4" player with
    an identical shot produce the same vector.
    """

    contact_frame_index: int

    # Joint angles at contact (degrees)
    elbow_angle: float
    shoulder_angle: float
    knee_angle: float
    hip_angle: float

    # Scale-invariant ratios
    contact_height_over_hip_height: float
    stride_over_shoulder_width: float

    # Timing (frames, at source fps -- convert to seconds for cross-fps comparison)
    takeback_to_contact_frames: int
    weight_shift_onset_frame: int

    def as_vector(self) -> list[float]:
        """Flatten to the fixed-order embedding stored in pgvector."""
        return [
            self.elbow_angle,
            self.shoulder_angle,
            self.knee_angle,
            self.hip_angle,
            self.contact_height_over_hip_height,
            self.stride_over_shoulder_width,
            float(self.takeback_to_contact_frames),
            float(self.weight_shift_onset_frame),
        ]


FEATURE_NAMES = [
    "elbow_angle",
    "shoulder_angle",
    "knee_angle",
    "hip_angle",
    "contact_height_over_hip_height",
    "stride_over_shoulder_width",
    "takeback_to_contact_frames",
    "weight_shift_onset_frame",
]


@dataclass
class NeighbourMatch:
    reference_clip_id: str
    player_level: str
    distance: float
    vector: list[float]


@dataclass
class FeatureDelta:
    feature_name: str
    amateur_value: float
    corpus_mean: float
    delta: float
    delta_pct: float


@dataclass
class CoachingFault:
    feature_name: str
    severity: float  # normalized 0-1, larger = further from corpus
    explanation: str


@dataclass
class CoachingResult:
    faults: list[CoachingFault] = field(default_factory=list)
    drill: str = ""
    summary: str = ""
    raw_response: str = ""

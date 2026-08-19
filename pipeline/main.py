"""Orchestrates one clip through the full pipeline:

clip -> pose extraction -> normalization -> feature vector
                                                 |
                                pgvector nearest-neighbour vs. corpus
                                                 |
                                      deviation deltas -> Claude -> coaching

Usage:
    python main.py path/to/clip.mp4 --shot-type third_shot_drop --paddle-side right
"""

from __future__ import annotations

import argparse
import os

from comparison import compute_deltas, find_nearest_neighbours
from contact_frame import detect_contact_frame
from coaching import generate_coaching
from normalization import compute_feature_vector
from pose_extraction import extract_pose_sequence


def analyze_clip(video_path: str, shot_type: str, paddle_side: str = "right") -> None:
    print(f"[1/5] Extracting pose from {video_path}...")
    sequence = extract_pose_sequence(video_path)
    print(f"      {len(sequence.frames)} frames with reliable pose detected")

    print("[2/5] Detecting contact frame...")
    contact_idx = detect_contact_frame(sequence, paddle_side=paddle_side)
    print(f"      Contact at frame {contact_idx} ({sequence.frames[contact_idx].timestamp_s:.2f}s)")

    print("[3/5] Computing feature vector...")
    feature_vector = compute_feature_vector(sequence, contact_idx, paddle_side=paddle_side)

    print("[4/5] Querying reference corpus...")
    neighbours = find_nearest_neighbours(feature_vector, shot_type, paddle_side)
    if not neighbours:
        print("      No reference shots found for this shot_type/paddle_side -- "
              "corpus not seeded yet, or filters too narrow.")
        return
    deltas = compute_deltas(feature_vector, neighbours)

    print("[5/5] Generating coaching...")
    result = generate_coaching(deltas)

    print("\n--- Coaching result ---")
    print(f"Summary: {result.summary}")
    for fault in result.faults:
        print(f"  - [{fault.severity:.2f}] {fault.feature_name}: {fault.explanation}")
    if result.drill:
        print(f"Drill: {result.drill}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run one clip through the DinkIQ pipeline")
    parser.add_argument("video_path")
    parser.add_argument("--shot-type", default="third_shot_drop")
    parser.add_argument("--paddle-side", default="right", choices=["left", "right"])
    args = parser.parse_args()

    if "SUPABASE_DB_URL" not in os.environ:
        raise SystemExit("Set SUPABASE_DB_URL (postgres connection string) before running.")
    if "ANTHROPIC_API_KEY" not in os.environ:
        raise SystemExit("Set ANTHROPIC_API_KEY before running.")

    analyze_clip(args.video_path, args.shot_type, args.paddle_side)

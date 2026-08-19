"""Step 5 of the pipeline: nearest-neighbour comparison against the corpus.

Queries pgvector for the k reference shots closest to the amateur's
feature vector, then expresses the amateur's deviation from those
neighbours as a per-feature delta. The deltas -- not the raw vector --
are what get handed to the coaching layer.
"""

from __future__ import annotations

import os

import psycopg
from pgvector.psycopg import register_vector

from datatypes import FEATURE_NAMES, FeatureDelta, FeatureVector, NeighbourMatch


def _connect() -> psycopg.Connection:
    dsn = os.environ["SUPABASE_DB_URL"]  # postgres connection string, ca-central-1
    conn = psycopg.connect(dsn, autocommit=True)
    register_vector(conn)
    return conn


def find_nearest_neighbours(
    feature_vector: FeatureVector,
    shot_type: str,
    paddle_side: str,
    k: int = 8,
    conn: psycopg.Connection | None = None,
) -> list[NeighbourMatch]:
    owns_conn = conn is None
    conn = conn or _connect()
    try:
        rows = conn.execute(
            """
            select id, player_level, embedding, embedding <-> %s as distance
            from reference_shots
            where shot_type = %s and paddle_side = %s
            order by embedding <-> %s
            limit %s
            """,
            (feature_vector.as_vector(), shot_type, paddle_side, feature_vector.as_vector(), k),
        ).fetchall()
    finally:
        if owns_conn:
            conn.close()

    return [
        NeighbourMatch(
            reference_clip_id=str(row[0]),
            player_level=row[1],
            distance=float(row[3]),
            vector=list(row[2]),
        )
        for row in rows
    ]


def compute_deltas(
    feature_vector: FeatureVector, neighbours: list[NeighbourMatch]
) -> list[FeatureDelta]:
    if not neighbours:
        raise ValueError("Need at least one corpus neighbour to compute deltas")

    amateur = feature_vector.as_vector()
    corpus_means = [
        sum(n.vector[i] for n in neighbours) / len(neighbours) for i in range(len(amateur))
    ]

    deltas = []
    for i, name in enumerate(FEATURE_NAMES):
        amateur_value = amateur[i]
        corpus_mean = corpus_means[i]
        delta = amateur_value - corpus_mean
        delta_pct = (delta / corpus_mean * 100) if corpus_mean else 0.0
        deltas.append(
            FeatureDelta(
                feature_name=name,
                amateur_value=amateur_value,
                corpus_mean=corpus_mean,
                delta=delta,
                delta_pct=delta_pct,
            )
        )
    return deltas

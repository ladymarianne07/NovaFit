"""Seed utilities for workout/exercise reference data."""

from __future__ import annotations

import json
from collections.abc import Sequence
from sqlalchemy.engine import Connection
from sqlalchemy import inspect, text


EXERCISE_ACTIVITY_SEED_DATA: list[dict] = [
    {
        "activity_key": "caminar",
        "category": "cardio",
        "label_es": "Caminar",
        "met_low": 2.8,
        "met_medium": 3.5,
        "met_high": 4.3,
    },
    {
        "activity_key": "trote",
        "category": "cardio",
        "label_es": "Trote",
        "met_low": 6.0,
        "met_medium": 7.0,
        "met_high": 8.3,
    },
    {
        "activity_key": "correr",
        "category": "cardio",
        "label_es": "Correr",
        "met_low": 8.0,
        "met_medium": 9.8,
        "met_high": 11.8,
    },
    {
        "activity_key": "ciclismo",
        "category": "cardio",
        "label_es": "Ciclismo",
        "met_low": 4.0,
        "met_medium": 6.8,
        "met_high": 10.0,
    },
    {
        "activity_key": "spinning",
        "category": "cardio",
        "label_es": "Spinning",
        "met_low": 7.0,
        "met_medium": 8.8,
        "met_high": 11.0,
    },
    {
        "activity_key": "saltar_cuerda",
        "category": "cardio",
        "label_es": "Saltar cuerda",
        "met_low": 8.8,
        "met_medium": 10.5,
        "met_high": 12.3,
    },
    {
        "activity_key": "fuerza_general",
        "category": "fuerza",
        "label_es": "Entrenamiento de fuerza general",
        "met_low": 3.5,
        "met_medium": 5.0,
        "met_high": 6.0,
    },
    {
        "activity_key": "pesas_intenso",
        "category": "fuerza",
        "label_es": "Pesas intenso",
        "met_low": 5.0,
        "met_medium": 6.0,
        "met_high": 7.0,
    },
    {
        "activity_key": "crossfit",
        "category": "fuerza",
        "label_es": "CrossFit",
        "met_low": 7.0,
        "met_medium": 9.0,
        "met_high": 12.0,
    },
    {
        "activity_key": "hiit",
        "category": "mixto",
        "label_es": "HIIT",
        "met_low": 8.0,
        "met_medium": 10.0,
        "met_high": 12.0,
    },
    {
        "activity_key": "yoga",
        "category": "flexibilidad",
        "label_es": "Yoga",
        "met_low": 2.0,
        "met_medium": 2.8,
        "met_high": 3.5,
    },
    {
        "activity_key": "pilates",
        "category": "flexibilidad",
        "label_es": "Pilates",
        "met_low": 3.0,
        "met_medium": 3.8,
        "met_high": 4.5,
    },
    {
        "activity_key": "natacion",
        "category": "cardio",
        "label_es": "Natación",
        "met_low": 6.0,
        "met_medium": 8.0,
        "met_high": 10.3,
    },
    {
        "activity_key": "remo",
        "category": "cardio",
        "label_es": "Remo ergómetro",
        "met_low": 5.0,
        "met_medium": 7.0,
        "met_high": 8.5,
    },
    {
        "activity_key": "eliptica",
        "category": "cardio",
        "label_es": "Elíptica",
        "met_low": 4.5,
        "met_medium": 5.8,
        "met_high": 7.0,
    },
]


def seed_exercise_activities(connection: Connection) -> dict[str, int]:
    """Insert/update default MET activities in an idempotent way."""
    if not inspect(connection).has_table("exercise_activities"):
        return {"inserted": 0, "updated": 0}

    existing_rows: Sequence = connection.execute(
        text("SELECT activity_key FROM exercise_activities")
    ).fetchall()
    existing_keys = {row[0] for row in existing_rows}

    inserted = 0
    updated = 0

    for activity in EXERCISE_ACTIVITY_SEED_DATA:
        params = {
            "activity_key": activity["activity_key"],
            "category": activity["category"],
            "label_es": activity["label_es"],
            "met_low": activity["met_low"],
            "met_medium": activity["met_medium"],
            "met_high": activity["met_high"],
            "source_refs": json.dumps({"source": "seed_v1"}),
            "is_active": True,
        }

        if activity["activity_key"] in existing_keys:
            connection.execute(
                text(
                    """
                    UPDATE exercise_activities
                    SET category = :category,
                        label_es = :label_es,
                        met_low = :met_low,
                        met_medium = :met_medium,
                        met_high = :met_high,
                        source_refs = :source_refs,
                        is_active = :is_active,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE activity_key = :activity_key
                    """
                ),
                params,
            )
            updated += 1
            continue

        connection.execute(
            text(
                """
                INSERT INTO exercise_activities (
                    activity_key,
                    category,
                    label_es,
                    met_low,
                    met_medium,
                    met_high,
                    source_refs,
                    is_active,
                    created_at,
                    updated_at
                ) VALUES (
                    :activity_key,
                    :category,
                    :label_es,
                    :met_low,
                    :met_medium,
                    :met_high,
                    :source_refs,
                    :is_active,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
                """
            ),
            params,
        )
        inserted += 1

    return {"inserted": inserted, "updated": updated}

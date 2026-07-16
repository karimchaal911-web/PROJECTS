"""Reusable data-cleaning helpers."""

import re


def clean_column_names(columns):
    """Return normalized snake_case column names and reject collisions."""
    cleaned = [
        re.sub(
            r"_+",
            "_",
            re.sub(r"[^\w\s]", "_", str(column).strip().lower()).replace(" ", "_"),
        ).strip("_")
        for column in columns
    ]
    if len(cleaned) != len(set(cleaned)):
        raise ValueError("Column cleaning produced duplicate names.")
    return cleaned

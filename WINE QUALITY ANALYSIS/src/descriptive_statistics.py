"""Reusable descriptive-statistics helpers."""


def descriptive_summary(df):
    """Return standard summary measures plus variance, skewness, and kurtosis."""
    summary = df.describe().T
    summary["variance"] = df.var()
    summary["skewness"] = df.skew()
    summary["excess_kurtosis"] = df.kurt()
    return summary[
        [
            "count", "mean", "std", "variance", "min", "25%", "50%",
            "75%", "max", "skewness", "excess_kurtosis",
        ]
    ]

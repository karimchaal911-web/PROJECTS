def descriptive_summary(df):
    """Return descriptive measures for the numeric columns in ``df``."""
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        raise ValueError("descriptive_summary requires at least one numeric column.")

    summary = numeric_df.describe().T
    summary["variance"] = numeric_df.var()
    summary["skewness"] = numeric_df.skew()
    summary["excess_kurtosis"] = numeric_df.kurt()
    return summary[
        [
            "count", "mean", "std", "variance", "min", "25%", "50%",
            "75%", "max", "skewness", "excess_kurtosis",
        ]
    ]
    


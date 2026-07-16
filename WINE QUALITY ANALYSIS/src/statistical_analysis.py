"""Reusable inferential-statistics helpers."""

import numpy as np
import pandas as pd
from scipy import stats


def holm_adjust(p_values):
    """Adjust a collection of p-values using Holm's step-down procedure."""
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p)
    adjusted_sorted = np.maximum.accumulate((len(p) - np.arange(len(p))) * p[order])
    adjusted = np.empty_like(adjusted_sorted)
    adjusted[order] = np.minimum(adjusted_sorted, 1.0)
    return adjusted


def spearman_table(df, feature_columns, target="quality"):
    """Calculate feature-to-target Spearman associations with Holm adjustment."""
    rows = []
    for feature in feature_columns:
        result = stats.perasonr(df[feature], df[target])
    
        rows.append(
            {
                "feature": feature,
                "spearman_rho": result.statistic,
                "p_value": result.pvalue,
            }
        )
    result = pd.DataFrame(rows)
    result["holm_p_value"] = holm_adjust(result["p_value"])
    return result.sort_values(
        "spearman_rho", key=abs, ascending=False
    ).reset_index(drop=True)


def welch_comparison(low, high, confidence=0.95):
    """Return a Welch comparison, confidence interval, and Hedges' g."""
    low, high = np.asarray(low, dtype=float), np.asarray(high, dtype=float)
    n1, n2 = len(low), len(high)
    mean_difference = low.mean() - high.mean()
    v1, v2 = low.var(ddof=1), high.var(ddof=1)
    standard_error = np.sqrt(v1 / n1 + v2 / n2)
    df = (v1 / n1 + v2 / n2) ** 2 / (
        (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    )
    critical = stats.t.ppf(1 - (1 - confidence) / 2, df)
    test = stats.ttest_ind(low, high, equal_var=False)
    pooled_sd = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    cohen_d = mean_difference / pooled_sd
    correction = 1 - 3 / (4 * (n1 + n2) - 9)
    return {
        "n_low": n1,
        "n_high": n2,
        "low_mean": low.mean(),
        "high_mean": high.mean(),
        "mean_difference_low_minus_high": mean_difference,
        "ci_95_low": mean_difference - critical * standard_error,
        "ci_95_high": mean_difference + critical * standard_error,
        "hedges_g": correction * cohen_d,
        "welch_t": test.statistic,
        "p_value": test.pvalue,
    }

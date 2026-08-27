"""Regenerate the report's data/feature figures from the canonical handoff."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "processed" / "MAP_Dryer_Canonical_5s.csv"
ALIGNED = ROOT / "data" / "processed" / "MAP_Dryer_Lab_Aligned_16.csv"
OUTPUT = ROOT / "final_report" / "figures" / "plots"

PROCESS = [
    "Dryer Air Temperature",
    "Cooler Air Temperature",
    "Air Flow Rate",
    "Wet Product Feed Rate",
    "Product Inlet Temperature",
    "Residence Time",
    "Vacuum",
    "Steam Pressure",
    "Fan Speed",
]
QUALITY = ["Product Density", "Final Product Temp", "Final Moisture (%H2O)"]


def read_plot_samples() -> tuple[pd.DataFrame, pd.DataFrame]:
    process_parts: list[pd.DataFrame] = []
    laboratory_parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(SOURCE, usecols=PROCESS + QUALITY, chunksize=100_000):
        process_parts.append(chunk[PROCESS].iloc[::25].copy())
        laboratory_parts.append(chunk.dropna(subset=QUALITY, how="all"))
    return pd.concat(process_parts, ignore_index=True), pd.concat(laboratory_parts, ignore_index=True)


def distributions(process: pd.DataFrame, laboratory: pd.DataFrame) -> None:
    values = {name: process[name] for name in PROCESS}
    values.update({name: laboratory[name].dropna() for name in QUALITY})
    fig, axes = plt.subplots(3, 4, figsize=(14, 8.5))
    for axis, (name, series) in zip(axes.flat, values.items(), strict=True):
        axis.hist(series, bins=35, color="#0B6E4F", alpha=0.86, edgecolor="white")
        axis.set_title(name, fontsize=9)
        axis.grid(axis="y", alpha=0.18)
    fig.suptitle("Canonical 92-day source: sampled process distributions and all laboratory values", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUTPUT / "data_distributions.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def boxplots(process: pd.DataFrame, laboratory: pd.DataFrame) -> None:
    values = {name: process[name] for name in PROCESS}
    values.update({name: laboratory[name].dropna() for name in QUALITY})
    fig, axes = plt.subplots(3, 4, figsize=(14, 8.5))
    for axis, (name, series) in zip(axes.flat, values.items(), strict=True):
        axis.boxplot(
            series,
            orientation="vertical",
            patch_artist=True,
            boxprops={"facecolor": "#D8EFE7", "edgecolor": "#0B6E4F"},
            medianprops={"color": "#C13F2B", "linewidth": 1.5},
            flierprops={"markersize": 1.5, "alpha": 0.25},
        )
        axis.set_title(name, fontsize=9)
        axis.set_xticks([])
        axis.grid(axis="y", alpha=0.18)
    fig.suptitle("Canonical 92-day source: process and laboratory ranges", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUTPUT / "feature_boxplots.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def correlations(laboratory: pd.DataFrame) -> None:
    columns = PROCESS + QUALITY
    corr = laboratory[columns].corr()
    fig, axis = plt.subplots(figsize=(11, 9))
    image = axis.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    axis.set_xticks(np.arange(len(columns)), labels=columns, rotation=55, ha="right", fontsize=8)
    axis.set_yticks(np.arange(len(columns)), labels=columns, fontsize=8)
    for row in range(len(columns)):
        for col in range(len(columns)):
            value = corr.iloc[row, col]
            axis.text(col, row, f"{value:.2f}", ha="center", va="center", fontsize=6.5,
                      color="white" if abs(value) > 0.55 else "#20252B")
    fig.colorbar(image, ax=axis, shrink=0.78, label="Pearson correlation")
    axis.set_title("Canonical variables at the 1,104 laboratory timestamps")
    fig.tight_layout()
    fig.savefig(OUTPUT / "correlation_matrix.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def engineered_relationships() -> None:
    aligned = pd.read_csv(ALIGNED)
    target = "Final Moisture (%H2O)"
    features = [
        "temperature_drop",
        "air_product_delta",
        "air_per_feed",
        "steam_temp_interaction",
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for axis, feature in zip(axes.flat, features, strict=True):
        axis.scatter(aligned[feature], aligned[target], s=11, alpha=0.42, color="#135D8C")
        slope, intercept = np.polyfit(aligned[feature], aligned[target], 1)
        xline = np.linspace(aligned[feature].min(), aligned[feature].max(), 100)
        axis.plot(xline, slope * xline + intercept, color="#C13F2B", linewidth=1.5)
        axis.set_xlabel(feature, fontsize=8)
        axis.set_ylabel("Final Moisture (%H2O)", fontsize=8)
        axis.grid(alpha=0.18)
    fig.suptitle("Notebook 02 aligned 16-feature handoff (1,103 laboratory targets)", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUTPUT / "engineered_features_vs_moisture.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    process, laboratory = read_plot_samples()
    distributions(process, laboratory)
    boxplots(process, laboratory)
    correlations(laboratory)
    engineered_relationships()
    print(f"Updated four report figures from {len(process):,} sampled process rows and {len(laboratory):,} lab rows.")


if __name__ == "__main__":
    main()

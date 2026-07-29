"""Visualization utilities for football rarity analysis."""
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path


def save_figure(filename, figures_dir=None, dpi=300, bbox_inches='tight'):
    """
    Save current matplotlib figure to file.
    
    Args:
        filename: Name of file to save (with extension)
        figures_dir: Directory to save to. If None, saves to current directory
        dpi: Resolution for saved figure (default 300 for publication quality)
        bbox_inches: 'tight' to remove excess whitespace
    """
    if figures_dir:
        figures_dir = Path(figures_dir)
        figures_dir.mkdir(parents=True, exist_ok=True)
        filepath = figures_dir / filename
    else:
        filepath = Path(filename)
    
    plt.savefig(filepath, dpi=dpi, bbox_inches=bbox_inches)
    print(f"✓ Saved figure to: {filepath}")
    return filepath


def plot_distribution_with_player(attackers, player_value, player_name, season=None, metric_name="G+A per 90", figures_dir=None, save_name=None):
    """
    Plot distribution histogram with player's performance marked.
    
    Args:
        attackers: Series of all attacker values
        player_value: The player's metric value
        player_name: Player name
        season: Optional season information
        metric_name: Name of the metric being plotted
    """
    plt.figure(figsize=(10, 6))
    
    plt.hist(attackers, bins=60, density=True, alpha=0.7)
    
    label = f"{player_name}"
    if season:
        label += f" {season}"
    label += f": {player_value:.2f} {metric_name}"
    
    plt.axvline(player_value, linestyle="--", linewidth=2, label=label)
    plt.xlabel(metric_name)
    plt.ylabel("Density")
    plt.title(f"Distribution of {metric_name}, 2005–2026")
    plt.legend()
    
    if save_name and figures_dir:
        save_figure(save_name, figures_dir)
    plt.show()


def plot_comparison_distribution(attackers, player_data, metric_name="G+A per 90", title_suffix="", figures_dir=None, save_name=None):
    """
    Plot distribution with multiple elite players marked.
    
    Args:
        attackers: Series of all attacker values
        player_data: List of tuples (value, name, season/period)
        metric_name: Name of the metric
        title_suffix: Additional text for title
        figures_dir: Directory to save figure to
        save_name: Filename to save as
    """
    plt.figure(figsize=(12, 6))
    
    plt.hist(attackers, bins=60, density=True, alpha=0.7)
    
    for value, name, period in player_data:
        label = f"{name} {period}: {value:.2f}"
        plt.axvline(value, linestyle="--", linewidth=2, label=label)
    
    plt.xlabel(metric_name)
    plt.ylabel("Density")
    plt.title(f"{metric_name} Compared to All Attackers, 2005–2026 {title_suffix}".strip())
    plt.legend()
    
    if save_name and figures_dir:
        save_figure(save_name, figures_dir)
    plt.show()


def plot_bar_chart(df, x_col, y_col, title="", xlabel="", ylabel="", rotation=45, figures_dir=None, save_name=None):
    """
    Create a bar chart from dataframe.
    
    Args:
        df: Dataframe containing data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        rotation: X-axis label rotation
        figures_dir: Directory to save figure to
        save_name: Filename to save as
    """
    plt.figure(figsize=(10, 6))
    
    plt.bar(df[x_col], df[y_col])
    
    plt.xticks(rotation=rotation, ha="right")
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    if title:
        plt.title(title)
    
    plt.tight_layout()
    
    if save_name and figures_dir:
        save_figure(save_name, figures_dir)
    plt.show()

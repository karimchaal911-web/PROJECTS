"""Statistical utilities for calculating rarity metrics."""
from scipy.stats import norm


def calculate_rarity_metrics(player_value, comparison_values):
    """
    Calculate statistical rarity metrics for a player value.
    
    Args:
        player_value: The player's performance metric (e.g., G+A per 90)
        comparison_values: Series of comparison values from the dataset
        
    Returns:
        dict: Dictionary with z-score, normal probability, and empirical probability
    """
    mu = comparison_values.mean()
    sd = comparison_values.std()
    
    z = (player_value - mu) / sd
    normal_prob = 1 - norm.cdf(z)
    empirical_prob = (comparison_values >= player_value).mean()
    
    return {
        "mean": mu,
        "std": sd,
        "z_score": z,
        "normal_probability": normal_prob,
        "empirical_probability": empirical_prob,
        "normal_rarity": f"1 in {1 / normal_prob:,.0f}" if normal_prob > 0 else "N/A",
        "empirical_rarity": f"1 in {1 / empirical_prob:,.0f}" if empirical_prob > 0 else "N/A"
    }


def print_rarity_report(player_info, rarity_metrics, analysis_type="Single Season"):
    """
    Print a formatted rarity report.
    
    Args:
        player_info: Dictionary with player details
        rarity_metrics: Dictionary from calculate_rarity_metrics()
        analysis_type: String describing the analysis type
    """
    print(f"\n================ RARITY RESULT ({analysis_type}) ================")
    
    for key, value in player_info.items():
        if isinstance(value, float) and value == int(value):
            print(f"{key.replace('_', ' ').title()}: {int(value)}")
        elif isinstance(value, float):
            print(f"{key.replace('_', ' ').title()}: {value:.3f}" if value > 0.1 else f"{key.replace('_', ' ').title()}: {value:.2f}")
        else:
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    print(f"\nDataset mean = {rarity_metrics['mean']:.3f}")
    print(f"Dataset standard deviation = {rarity_metrics['std']:.3f}")
    print(f"z-score = {rarity_metrics['z_score']:.2f}σ above average")
    print()
    print(f"Normal probability = {rarity_metrics['normal_probability']:.10f}")
    print(f"Normal rarity ≈ {rarity_metrics['normal_rarity']}")
    print()
    print(f"Empirical probability = {rarity_metrics['empirical_probability']:.10f}")
    print(f"Empirical rarity ≈ {rarity_metrics['empirical_rarity']}")

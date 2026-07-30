"""Football Rarity Analysis utilities."""

from .data_cleaning import (
    save_processed_data,
    load_raw_data,
    handle_missing_values,
    remove_duplicates,
    remove_outliers,
    standardize_dtypes,
    clean_text_column,
    remove_columns,
    rename_columns,
    validate_data_quality,
    clean_numeric_column,
    filter_by_condition,
    consolidate_pipeline
)

from .data_processing import (
    merge_appearances_with_games,
    merge_with_players,
    filter_seasons,
    create_ga_column,
    aggregate_by_season,
    aggregate_by_career,
    filter_attackers,
    find_player_seasons
)

from .statistics import (
    calculate_rarity_metrics,
    print_rarity_report
)

from .visualization import (
    save_figure,
    plot_distribution_with_player,
    plot_comparison_distribution,
    plot_bar_chart
)

__all__ = [
    # data_cleaning
    'save_processed_data',
    'load_raw_data',
    'handle_missing_values',
    'remove_duplicates',
    'remove_outliers',
    'standardize_dtypes',
    'clean_text_column',
    'remove_columns',
    'rename_columns',
    'validate_data_quality',
    'clean_numeric_column',
    'filter_by_condition',
    'consolidate_pipeline',
    # data_processing
    'merge_appearances_with_games',
    'merge_with_players',
    'filter_seasons',
    'create_ga_column',
    'aggregate_by_season',
    'aggregate_by_career',
    'filter_attackers',
    'find_player_seasons',
    # statistics
    'calculate_rarity_metrics',
    'print_rarity_report',
    # visualization
    'save_figure',
    'plot_distribution_with_player',
    'plot_comparison_distribution',
    'plot_bar_chart',
]

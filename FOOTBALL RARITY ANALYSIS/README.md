# Football Rarity Analysis

Statistical analysis of football player performance to quantify the rarity and uniqueness of elite attacking players' achievements.

## Objective

This project analyzes football player performance using appearances, games, players, and competition datasets to:
- Identify rare and exceptional attacking performances
- Calculate statistical rarity metrics (z-scores, percentiles, empirical probability)
- Compare elite players across different time periods and contexts
- Determine how statistically rare specific performance levels are

## Dataset

The project uses the following files:

- **appearances.csv** - Player appearance records with goals and assists
- **players.csv** - Player information including position and demographics
- **games.csv** - Game details including season and competition
- **competitions.csv** - Competition metadata

All raw data is preserved in `data/raw/` and never modified.

## Project Structure

```
Football Rarity Analysis/
│
├── data/
│   ├── raw/                          # Raw data files (never modified)
│   │   ├── appearances.csv
│   │   ├── players.csv
│   │   ├── games.csv
│   │   └── competitions.csv
│   │
│   └── processed/                    # Cleaned and aggregated datasets
│       ├── appearances_cleaned.csv
│       ├── players_cleaned.csv
│       ├── games_cleaned.csv
│       ├── competitions_cleaned.csv
│       ├── merged_data_cleaned.csv
│       ├── season_stats_cleaned.csv
│       └── career_stats_cleaned.csv
│
├── notebooks/
│   └── analysis.ipynb                # Main analysis notebook
│
├── src/                              # Reusable Python utilities
│   ├── __init__.py
│   ├── data_cleaning.py              # Data cleaning functions
│   ├── data_processing.py            # Data aggregation and filtering
│   ├── statistics.py                 # Statistical calculations
│   └── visualization.py              # Plotting utilities
│
├── reports/
│   └── figures/                      # Generated visualizations
│
└── README.md                         # This file
```

## Main Questions

- Which players have rare goal and assist profiles?
- How do appearances relate to goals and assists?
- Which competitions show stronger performance patterns?
- How do Messi and Ronaldo compare based on selected metrics?
- What percentage of players achieve specific performance levels?

## Methods

### Data Preparation
- **Data Cleaning**: Handle missing values, remove duplicates, standardize formats
- **Data Integration**: Merge appearances with game and player metadata
- **Feature Engineering**: Create Goals+Assists metric, calculate per-90 statistics

### Analysis Approaches

1. **Best Single Season Analysis**
   - Identifies each player's peak performance year
   - Calculates statistical rarity relative to all seasons

2. **Career-Long Analysis**
   - Aggregates statistics across entire player careers
   - Measures sustained excellence

3. **Comparative Analysis**
   - Compares elite players directly
   - Visualizes performance distributions

### Statistical Techniques
- **Z-score calculation**: Measure deviation from mean in standard deviations
- **Normal distribution probability**: Theoretical rarity based on normal distribution
- **Empirical probability**: Actual percentage of players exceeding performance level
- **Interquartile Range (IQR)**: Outlier detection and removal
- **Percentile analysis**: Rank performance within dataset

## Tools Used

### Core Libraries
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computations
- **scipy** - Statistical functions

### Visualization
- **matplotlib** - Statistical plots and distributions
- **seaborn** (optional) - Enhanced statistical visualizations

### Development
- **Python 3.8+** - Programming language
- **Jupyter Notebook** - Interactive analysis environment

## Reusable Utilities (`src/`)

### `data_cleaning.py`
Domain-agnostic data cleaning functions:
- `handle_missing_values()` - 7 strategies for missing data
- `remove_duplicates()` - Identify and remove duplicate rows
- `remove_outliers()` - IQR and z-score methods
- `clean_text_column()` - Text normalization
- `validate_data_quality()` - Generate quality reports
- `save_processed_data()` - Safe saving to processed folder
- `load_raw_data()` - Format-agnostic data loading

### `data_processing.py`
Domain-specific football data processing:
- `merge_appearances_with_games()` - Combine game and appearance data
- `merge_with_players()` - Add player metadata
- `aggregate_by_season()` - Season-level statistics
- `aggregate_by_career()` - Career-level statistics
- `filter_attackers()` - Extract attacking players

### `statistics.py`
Statistical analysis utilities:
- `calculate_rarity_metrics()` - Compute z-scores and probabilities
- `print_rarity_report()` - Format statistical summaries

### `visualization.py`
Plotting utilities:
- `plot_distribution_with_player()` - Mark player on distribution
- `plot_comparison_distribution()` - Compare multiple players
- `plot_bar_chart()` - Generic bar chart helper

## Quick Start

### 1. Load Data
```python
from src.data_processing import *
from src.data_cleaning import *

# Load raw data
appearances = pd.read_csv("data/raw/appearances.csv")
players = pd.read_csv("data/raw/players.csv")
games = pd.read_csv("data/raw/games.csv")
competitions = pd.read_csv("data/raw/competitions.csv")
```

### 2. Prepare Data
```python
# Merge and filter
df = merge_appearances_with_games(appearances, games)
df = merge_with_players(df, players)
df = filter_seasons(df, min_season=2005, max_season=2026)
df = create_ga_column(df)
```

### 3. Aggregate Statistics
```python
# By season
season_stats = aggregate_by_season(df)
attackers_season = filter_attackers(season_stats)

# By career
career_stats = aggregate_by_career(df)
attackers_career = filter_attackers(career_stats)
```

### 4. Calculate Rarity
```python
from src.statistics import calculate_rarity_metrics, print_rarity_report

player_value = 1.7  # Goals+Assists per 90
rarity = calculate_rarity_metrics(player_value, attackers_season["GA_per90"])
print_rarity_report({"Player": "Messi"}, rarity)
```

### 5. Visualize
```python
from src.visualization import plot_distribution_with_player

plot_distribution_with_player(
    attackers_season["GA_per90"], 
    player_value, 
    "Messi",
    season=2012
)
```

## Data Integrity Best Practices

✅ **Always followed in this project:**
- Raw data in `data/raw/` is **never modified**
- Processed datasets saved to `data/processed/` with `_cleaned` suffix
- Naming convention clearly indicates processing status
- All transformations are traceable and reproducible
- Utilities are domain-agnostic and reusable

## Running the Analysis

1. Open `notebooks/analysis.ipynb` in Jupyter
2. Run all cells sequentially
3. Processed datasets automatically save to `data/processed/`
4. Visualizations generate inline in notebook
5. Quality reports print to console

## Results Summary

The analysis reveals:
- **Peak Performance**: Messi's 2012 season (1.70 G+A per 90) was 1 in 4,532 players
- **Elite Comparison**: Top attackers (Messi, Ronaldo, Haaland, Mbappé, Lewandowski) show remarkably rare performance levels
- **Distribution**: Most attackers produce 0.3-0.7 G+A per 90; elite players exceed 1.5
- **Career vs. Season**: Career averages are more stable; single seasons show greater variance

## Future Enhancements

- Add defensive metrics (tackles, interceptions)
- Include player age and experience factors
- Analyze performance trends over time
- Compare across different leagues/competitions
- Implement machine learning classification
- Create interactive dashboard

## License

This project is for educational and analytical purposes.

---

**Last Updated**: 2026-07-08  
**Author**: Football Rarity Analysis Team

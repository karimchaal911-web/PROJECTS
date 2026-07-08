"""Data processing utilities for football rarity analysis."""
import pandas as pd


def merge_appearances_with_games(appearances, games):
    """Merge appearances with game information."""
    return appearances.merge(
        games[["game_id", "season", "competition_id"]],
        on="game_id",
        how="left"
    )


def merge_with_players(df, players):
    """Merge dataframe with player information."""
    return df.merge(
        players[["player_id", "name", "position"]],
        on="player_id",
        how="left"
    )


def filter_seasons(df, min_season=2005, max_season=2026):
    """Filter data to specified season range."""
    return df[(df["season"] >= min_season) & (df["season"] <= max_season)].copy()


def create_ga_column(df):
    """Create Goals + Assists column."""
    df = df.copy()
    df["GA"] = df["goals"] + df["assists"]
    return df


def aggregate_by_season(df):
    """Aggregate statistics by player and season."""
    season_stats = df.groupby(
        ["player_id", "name", "position", "season"],
        as_index=False
    ).agg({
        "goals": "sum",
        "assists": "sum",
        "GA": "sum",
        "minutes_played": "sum",
        "game_id": "count"
    })
    
    season_stats = season_stats.rename(columns={"game_id": "appearances"})
    season_stats = season_stats[season_stats["minutes_played"] >= 900]
    
    season_stats["ninety_minutes"] = season_stats["minutes_played"] / 90
    season_stats["GA_per90"] = season_stats["GA"] / season_stats["ninety_minutes"]
    
    return season_stats


def aggregate_by_career(df):
    """Aggregate statistics across entire player career."""
    career_stats = df.groupby(
        ["player_id", "name", "position"],
        as_index=False
    ).agg({
        "goals": "sum",
        "assists": "sum",
        "GA": "sum",
        "minutes_played": "sum",
        "game_id": "count",
        "season": ["min", "max", "nunique"]
    })
    
    career_stats.columns = [
        "player_id", "name", "position", "goals", "assists", "GA",
        "minutes_played", "appearances", "first_season", "last_season", "active_seasons"
    ]
    
    career_stats = career_stats[career_stats["minutes_played"] >= 3000]
    career_stats["ninety_minutes"] = career_stats["minutes_played"] / 90
    career_stats["GA_per90"] = career_stats["GA"] / career_stats["ninety_minutes"]
    
    return career_stats


def filter_attackers(stats_df):
    """Filter to attacking players only."""
    return stats_df[
        stats_df["position"].str.contains(
            "Attack|Forward|Centre-Forward|Winger|Second Striker|Left Winger|Right Winger",
            case=False,
            na=False
        )
    ].copy()


def find_player_seasons(attackers, player_name):
    """Find all seasons for a specific player."""
    return attackers[
        attackers["name"].str.contains(player_name, case=False, na=False)
    ].sort_values("GA_per90", ascending=False)

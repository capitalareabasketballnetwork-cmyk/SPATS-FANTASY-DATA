"""Create player-versus-defense fantasy records and defense/position summaries.

Inputs: data/processed/player_week_YYYY.parquet
Outputs:
  data/matchups/player_vs_defense.parquet
  data/matchups/defense_position_by_season.parquet
  data/matchups/defense_position_all_time.parquet

The per-player-game dataset retains zero-point appearances from the source.
Summaries include all player-week appearances, not just starters; totals are
the points allowed to the whole position group in each defense game.
"""
from pathlib import Path
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
MATCHUPS = ROOT / "data" / "matchups"
SCORING = ("fantasy_standard", "fantasy_half_ppr", "fantasy_ppr")
KEYS = ("season", "week", "opponent_team", "position")
POSITIONS = ("QB", "RB", "WR", "TE")

def make_matchups(frame: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    required = {"player_id", "season", "week", "team", "opponent_team", "position", *SCORING}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required player data columns: {sorted(missing)}")

    name_col = "player_name" if "player_name" in frame.columns else ("player_display_name" if "player_display_name" in frame.columns else None)
    columns = ["player_id"] + ([name_col] if name_col else []) + ["position", "team", "opponent_team", "season", "week", *SCORING]
    games = (
        frame.select(columns)
        .filter(pl.col("opponent_team").is_not_null() & pl.col("position").is_in(POSITIONS))
        .unique(subset=["player_id", "season", "week"], keep="first")
        .sort(["season", "week", "opponent_team", "position", "player_id"])
    )
    # Sum all fantasy points at each position against the defense in that week.
    defense_games = (
        games.group_by(list(KEYS))
        .agg(
            pl.len().alias("players_recorded"),
            *(pl.col(s).sum().round(2).alias(s + "_allowed") for s in SCORING),
        )
    )
    by_season = (
        defense_games.group_by(["season", "opponent_team", "position"])
        .agg(
            pl.len().alias("games_recorded"),
            pl.col("players_recorded").sum().alias("player_appearances"),
            *(pl.col(s + "_allowed").sum().round(2).alias(s + "_total_allowed") for s in SCORING),
            *(pl.col(s + "_allowed").mean().round(2).alias(s + "_per_game_allowed") for s in SCORING),
        )
        .sort(["season", "opponent_team", "position"])
    )
    all_time = (
        defense_games.group_by(["opponent_team", "position"])
        .agg(
            pl.len().alias("games_recorded"),
            pl.col("players_recorded").sum().alias("player_appearances"),
            *(pl.col(s + "_allowed").mean().round(2).alias(s + "_per_game_allowed") for s in SCORING),
        )
        .sort(["opponent_team", "position"])
    )
    return games, by_season, all_time

def run() -> None:
    paths = sorted(PROCESSED.glob("player_week_*.parquet"))
    if not paths:
        raise FileNotFoundError("No processed player-week Parquet files found")
    frame = pl.concat([pl.read_parquet(p) for p in paths], how="diagonal_relaxed")
    games, by_season, all_time = make_matchups(frame)
    MATCHUPS.mkdir(parents=True, exist_ok=True)
    games.write_parquet(MATCHUPS / "player_vs_defense.parquet")
    by_season.write_parquet(MATCHUPS / "defense_position_by_season.parquet")
    all_time.write_parquet(MATCHUPS / "defense_position_all_time.parquet")
    print(f"Matchups: {games.height} player-week rows, {by_season.height} season/defense/position summaries")

if __name__ == "__main__":
    run()

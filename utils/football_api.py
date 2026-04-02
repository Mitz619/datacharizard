"""
utils/football_api.py  —  Premier League & Championship data
Uses the free football-data.org API (10 req/min on free tier).

Free API key: https://www.football-data.org/client/register

Data used in lessons to make Spark SQL / PySpark / Python examples
feel real and exciting rather than boring sample tables.
"""
import requests, time, json
from functools import lru_cache
from config import FOOTBALL_API_KEY, FOOTBALL_LEAGUES, FOOTBALL_SEASON

BASE_URL = "https://api.football-data.org/v4"

HEADERS = {
    "X-Auth-Token": FOOTBALL_API_KEY,
    "Accept": "application/json",
}


def _get(endpoint: str) -> dict | None:
    """Raw API call with simple error handling."""
    if not FOOTBALL_API_KEY:
        print("  ⚠️  No FOOTBALL_API_KEY set — using fallback sample data.")
        return None
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=8)
        if resp.status_code == 429:
            print("  ⏳ Rate limited, waiting 12s...")
            time.sleep(12)
            resp = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  Football API error ({endpoint}): {e}")
        return None


# ── Top-level data fetchers ───────────────────────────────────────────────────

def get_standings(league_code: str = "PL") -> list[dict]:
    """Return league table as a list of flat dicts (great for DataFrames)."""
    data = _get(f"/competitions/{league_code}/standings?season={FOOTBALL_SEASON}")
    if not data:
        return _fallback_standings()
    rows = []
    for entry in data["standings"][0]["table"]:
        rows.append({
            "position":      entry["position"],
            "team":          entry["team"]["name"],
            "short_name":    entry["team"]["shortName"],
            "played":        entry["playedGames"],
            "won":           entry["won"],
            "drawn":         entry["draw"],
            "lost":          entry["lost"],
            "goals_for":     entry["goalsFor"],
            "goals_against": entry["goalsAgainst"],
            "goal_diff":     entry["goalDifference"],
            "points":        entry["points"],
        })
    return rows


def get_top_scorers(league_code: str = "PL", limit: int = 20) -> list[dict]:
    """Return top scorers list."""
    data = _get(f"/competitions/{league_code}/scorers?season={FOOTBALL_SEASON}&limit={limit}")
    if not data:
        return _fallback_scorers()
    rows = []
    for entry in data.get("scorers", []):
        p = entry["player"]
        t = entry.get("team", {})
        rows.append({
            "player":       p["name"],
            "nationality":  p.get("nationality", ""),
            "team":         t.get("name", ""),
            "goals":        entry.get("goals", 0),
            "assists":      entry.get("assists", 0),
            "penalties":    entry.get("penalties", 0),
            "played":       entry.get("playedMatches", 0),
        })
    return rows


def get_recent_matches(league_code: str = "PL", limit: int = 20) -> list[dict]:
    """Return recent completed matches."""
    data = _get(f"/competitions/{league_code}/matches?season={FOOTBALL_SEASON}&status=FINISHED")
    if not data:
        return _fallback_matches()
    rows = []
    for m in data.get("matches", [])[-limit:]:
        score = m.get("score", {}).get("fullTime", {})
        rows.append({
            "date":       m.get("utcDate", "")[:10],
            "home_team":  m["homeTeam"]["name"],
            "away_team":  m["awayTeam"]["name"],
            "home_goals": score.get("home", 0),
            "away_goals": score.get("away", 0),
            "matchday":   m.get("matchday", 0),
            "result":     ("HOME" if (score.get("home") or 0) > (score.get("away") or 0)
                           else "AWAY" if (score.get("away") or 0) > (score.get("home") or 0)
                           else "DRAW"),
        })
    return rows


# ── Lesson data builders (Claude-ready context strings) ───────────────────────

def get_lesson_dataset(topic: str) -> str:
    """
    Returns a string describing a football dataset for use in Claude prompts.
    Claude uses this as the real-world data context for lessons.
    """
    standings = get_standings("PL")[:6]  # top 6 for brevity
    scorers   = get_top_scorers("PL", 5)

    standings_str = "| Pos | Team | P | W | D | L | GF | GA | Pts |\n|-----|------|---|---|---|---|----|----|-----|\n"
    for r in standings:
        standings_str += (f"| {r['position']} | {r['team']} | {r['played']} | "
                          f"{r['won']} | {r['drawn']} | {r['lost']} | "
                          f"{r['goals_for']} | {r['goals_against']} | {r['points']} |\n")

    scorers_str = "| Player | Team | Goals | Assists | Penalties |\n|--------|------|-------|---------|----------|\n"
    for s in scorers:
        scorers_str += (f"| {s['player']} | {s['team']} | {s['goals']} | "
                        f"{s['assists']} | {s['penalties']} |\n")

    return f"""
REAL PREMIER LEAGUE DATA (use this as the dataset in your lesson):

**League standings (top 6):**
{standings_str}

**Top scorers:**
{scorers_str}

Table names to use in code examples:
- `pl_standings`   → columns: position, team, played, won, drawn, lost, goals_for, goals_against, points
- `pl_scorers`     → columns: player, nationality, team, goals, assists, penalties, played
- `pl_matches`     → columns: date, home_team, away_team, home_goals, away_goals, matchday, result
"""


# ── Fallback sample data (if no API key yet) ──────────────────────────────────

def _fallback_standings() -> list[dict]:
    return [
        {"position":1,"team":"Liverpool","short_name":"LIV","played":34,"won":24,"drawn":7,"lost":3,"goals_for":78,"goals_against":32,"goal_diff":46,"points":79},
        {"position":2,"team":"Arsenal","short_name":"ARS","played":34,"won":23,"drawn":5,"lost":6,"goals_for":74,"goals_against":38,"goal_diff":36,"points":74},
        {"position":3,"team":"Manchester City","short_name":"MCI","played":34,"won":20,"drawn":7,"lost":7,"goals_for":68,"goals_against":41,"goal_diff":27,"points":67},
        {"position":4,"team":"Chelsea","short_name":"CHE","played":34,"won":18,"drawn":8,"lost":8,"goals_for":65,"goals_against":47,"goal_diff":18,"points":62},
        {"position":5,"team":"Aston Villa","short_name":"AVL","played":34,"won":18,"drawn":6,"lost":10,"goals_for":72,"goals_against":54,"goal_diff":18,"points":60},
        {"position":6,"team":"Tottenham","short_name":"TOT","played":34,"won":16,"drawn":7,"lost":11,"goals_for":59,"goals_against":53,"goal_diff":6,"points":55},
    ]

def _fallback_scorers() -> list[dict]:
    return [
        {"player":"Mohamed Salah","nationality":"Egypt","team":"Liverpool","goals":26,"assists":15,"penalties":5,"played":33},
        {"player":"Erling Haaland","nationality":"Norway","team":"Manchester City","goals":22,"assists":6,"penalties":7,"played":28},
        {"player":"Cole Palmer","nationality":"England","team":"Chelsea","goals":20,"assists":14,"penalties":6,"played":34},
        {"player":"Alexander Isak","nationality":"Sweden","team":"Newcastle","goals":19,"assists":5,"penalties":2,"played":30},
        {"player":"Ollie Watkins","nationality":"England","team":"Aston Villa","goals":17,"assists":10,"penalties":1,"played":34},
    ]

def _fallback_matches() -> list[dict]:
    return [
        {"date":"2025-03-01","home_team":"Arsenal","away_team":"Liverpool","home_goals":2,"away_goals":2,"matchday":28,"result":"DRAW"},
        {"date":"2025-03-08","home_team":"Manchester City","away_team":"Chelsea","home_goals":3,"away_goals":1,"matchday":29,"result":"HOME"},
        {"date":"2025-03-15","home_team":"Liverpool","away_team":"Aston Villa","home_goals":2,"away_goals":0,"matchday":30,"result":"HOME"},
        {"date":"2025-03-22","home_team":"Tottenham","away_team":"Arsenal","home_goals":1,"away_goals":2,"matchday":31,"result":"AWAY"},
    ]

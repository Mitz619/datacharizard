"""
tasks/coach.py  —  Task 2: DataCharizard Learning Coach
Interactive CLI coach for Spark SQL, PySpark, Python + sports analytics.
Includes gamification: XP, levels, streaks, real-world problems.
"""
import json, textwrap, re
from utils.claude_client import ask, chat
from utils.db import (get_total_xp, get_level, add_progress,
                      add_quiz_result, init_db)
from tasks.obsidian_writer import save_note
from config import XP_PER_LESSON, XP_PER_CORRECT, XP_PER_STREAK, LEVELS


# ── Curriculum ─────────────────────────────────────────────────────────────────
CURRICULUM = {
    "spark_sql": [
        "SELECT, FROM, WHERE basics in Spark SQL on Databricks",
        "GROUP BY, HAVING, and aggregate functions",
        "JOINs in Spark SQL — inner, left, anti",
        "Window functions: ROW_NUMBER, RANK, LAG, LEAD",
        "CTEs and subqueries in Spark SQL",
        "Working with Databricks Delta tables",
        "Spark SQL on Snowflake — key differences",
        "Optimising Spark SQL: partitioning and caching",
    ],
    "pyspark": [
        "DataFrames vs RDDs — when to use which",
        "Reading CSV, JSON, Parquet with PySpark",
        "Transformations: select, filter, withColumn, drop",
        "Aggregations and groupBy in PySpark",
        "Joins in PySpark — broadcast vs shuffle",
        "UDFs — when and how (and when NOT to use them)",
        "PySpark with Delta Lake — MERGE and UPSERT",
        "Writing production PySpark pipelines",
    ],
    "python": [
        "List comprehensions and generators",
        "Functions: args, kwargs, decorators",
        "Error handling: try/except/finally",
        "Working with pandas DataFrames",
        "APIs with requests library",
        "Object-oriented Python — classes and inheritance",
        "Python for sports analytics — tracking stats",
        "Testing your code with pytest",
    ],
}


COACH_SYSTEM = """You are DataCharizard, a fun and engaging data engineering coach. 
You teach Spark SQL, PySpark, and Python with:
- Super simple real-world examples (always use sports/footy/cricket stats as examples when possible)
- Short code snippets with clear comments
- Analogies that make complex things click instantly
- An encouraging, enthusiastic tone (but not cringe)

Format lessons like this:
1. Quick concept explanation (3-4 sentences max)
2. Real-world example (always relatable — sports data, Netflix, Uber, etc.)
3. Code snippet with comments
4. One "try this yourself" mini challenge
5. A fun fact about why this matters in industry

Keep lessons to ~300 words. Use emoji sparingly for key points."""


QUIZ_SYSTEM = """You are a quiz master for data engineering. 
Generate ONE multiple-choice question testing the given concept.

RETURN ONLY valid JSON in this exact format (no markdown, no extra text):
{
  "question": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "answer": "A",
  "explanation": "Brief explanation of why the answer is correct"
}"""


PROBLEM_SYSTEM = """You are a senior data engineer giving a real-world problem.
Create a realistic scenario (use Australian sports, streaming data, or e-commerce).
Give:
1. The problem statement (2-3 sentences)  
2. Sample data (a small table or JSON snippet)
3. The task (what the student needs to write)
4. Hints (2 hints, hidden by default — student asks to reveal)
Keep it achievable in 15-30 minutes."""


def show_xp_bar(xp: int):
    """Print a fun XP progress bar."""
    level = get_level(xp)
    thresholds = sorted(LEVELS.keys())
    # find next threshold
    next_t = next((t for t in thresholds if t > xp), thresholds[-1])
    prev_t = max((t for t in thresholds if t <= xp), default=0)
    if next_t == prev_t:
        pct = 100
    else:
        pct = int((xp - prev_t) / (next_t - prev_t) * 100)
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
    print(f"\n  {level}  |  XP: {xp}  [{bar}] {pct}% to next level\n")


def pick_topic() -> str:
    print("\n  What do you want to learn today?")
    print("  1. Spark SQL (Databricks + Snowflake)")
    print("  2. PySpark for data engineering")
    print("  3. Python + sports analytics")
    choice = input("\n  Enter 1, 2, or 3: ").strip()
    return {"1": "spark_sql", "2": "pyspark", "3": "python"}.get(choice, "spark_sql")


def pick_lesson(topic: str) -> tuple[int, str]:
    lessons = CURRICULUM[topic]
    print(f"\n  📚 {topic.upper()} curriculum:")
    for i, l in enumerate(lessons, 1):
        print(f"     {i}. {l}")
    try:
        num = int(input("\n  Pick lesson number (or press Enter for next): ").strip() or "1")
    except ValueError:
        num = 1
    num = max(1, min(num, len(lessons)))
    return num, lessons[num - 1]


def run_lesson(topic: str, lesson_num: int, lesson_title: str):
    print(f"\n  🔥 Lesson {lesson_num}: {lesson_title}\n")
    print("  " + "─" * 55)

    # Inject real Premier League data as the lesson dataset
    try:
        from utils.football_api import get_lesson_dataset
        football_ctx = get_lesson_dataset(topic)
        prompt = (f"Teach me lesson: '{lesson_title}'\n\n"
                  f"Use this REAL Premier League data in ALL your code examples:\n"
                  f"{football_ctx}")
    except Exception:
        prompt = f"Teach me lesson: '{lesson_title}'"

    content = ask(COACH_SYSTEM, prompt)
    print(textwrap.fill(content, width=70, initial_indent="  ",
                        subsequent_indent="  "))
    print()

    # Save to Obsidian
    save_note(topic, lesson_num, lesson_title, content)

    # Award XP
    add_progress(topic, lesson_num, XP_PER_LESSON)
    xp = get_total_xp()
    print(f"\n  +{XP_PER_LESSON} XP earned! 🎉")
    show_xp_bar(xp)
    return content


def run_quiz(topic: str, lesson_title: str):
    print("\n  ── Quick quiz time! ──────────────────────────────────")
    streak = 0
    total_xp = 0

    for q_num in range(1, 4):   # 3 questions per lesson
        raw = ask(QUIZ_SYSTEM, f"Concept: {lesson_title} ({topic})")
        # strip markdown fences if present
        raw = re.sub(r"```json|```", "", raw).strip()
        try:
            q = json.loads(raw)
        except json.JSONDecodeError:
            print("  (Quiz generation hiccup, skipping...)")
            continue

        print(f"\n  Q{q_num}: {q['question']}")
        for k, v in q["options"].items():
            print(f"       {k}) {v}")

        answer = input("\n  Your answer (A/B/C/D): ").strip().upper()
        correct = (answer == q["answer"])

        if correct:
            streak += 1
            xp = XP_PER_CORRECT + (XP_PER_STREAK if streak >= 3 else 0)
            emoji = "🔥" if streak >= 3 else "✅"
            print(f"  {emoji} Correct! +{xp} XP   (streak: {streak})")
        else:
            streak = 0
            xp = 0
            print(f"  ❌ Not quite. Correct: {q['answer']}")

        print(f"  💡 {q['explanation']}")
        add_quiz_result(topic, q["question"], correct, xp)
        total_xp += xp

    print(f"\n  Quiz done! You earned {total_xp} XP this session.")
    show_xp_bar(get_total_xp())


def run_real_world_problem(topic: str, lesson_title: str):
    print("\n  ── Real-world challenge 🏆 ────────────────────────────")
    problem = ask(PROBLEM_SYSTEM,
                  f"Create a real-world {topic} problem based on: {lesson_title}")
    print(textwrap.fill(problem, width=70, initial_indent="  ",
                        subsequent_indent="  "))

    while True:
        cmd = input("\n  Type 'hint', 'solution', 'skip', or 'done': ").strip().lower()
        if cmd == "hint":
            hint = ask(COACH_SYSTEM, f"Give me ONE hint for this problem: {problem}")
            print(f"\n  💡 Hint: {hint}\n")
        elif cmd == "solution":
            sol = ask(COACH_SYSTEM,
                      f"Show the solution with explanation for: {problem}")
            print(textwrap.fill(sol, width=70, initial_indent="\n  ",
                                subsequent_indent="  "))
            break
        elif cmd in ("skip", "done"):
            break


def run():
    """Entry point — interactive CLI learning session."""
    print("\n" + "═" * 60)
    print("  🔥 DATACHARIZARD COACH — Let's level up!")
    print("═" * 60)
    init_db()

    xp = get_total_xp()
    show_xp_bar(xp)

    topic = pick_topic()
    lesson_num, lesson_title = pick_lesson(topic)

    lesson_content = run_lesson(topic, lesson_num, lesson_title)

    again = input("\n  Ready for a quiz? (y/n): ").strip().lower()
    if again == "y":
        run_quiz(topic, lesson_title)

    challenge = input("\n  Try a real-world problem? (y/n): ").strip().lower()
    if challenge == "y":
        run_real_world_problem(topic, lesson_title)

    print("\n  Great session! Your notes are saved in Obsidian. 📓")
    print("  See you tomorrow — keep that streak going! 🔥\n")


if __name__ == "__main__":
    run()

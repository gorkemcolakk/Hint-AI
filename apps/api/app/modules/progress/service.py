"""Ebeveyn özeti: dönem içindeki sorular, ipucu kullanımı, konular ve güvenlik uyarıları.

Gizlilik (Bölüm 10.4): ebeveyn varsayılan olarak ÖZET görür (konu, sayı, bağımsızlık,
güvenlik uyarıları). Soru metni yalnızca `privacy_level = full_transcript` iken gösterilir.
İstismar bildirimleri ebeveyne hiç gösterilmez (bkz. safety.models.GUARDIAN_HIDDEN_CATEGORIES).
"""

import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth_consent.models import ChildProfile
from app.modules.problems.models import HiddenSolution, Problem
from app.modules.safety.models import GUARDIAN_HIDDEN_CATEGORIES, ModerationEvent
from app.modules.tutoring.models import Attempt, Hint

RECENT_LIMIT = 10
UNKNOWN_TOPIC = "Konu belirlenemedi"

ALERT_TEXTS = {
    "self_harm": (
        "Kendine zarar verme ile ilgili bir ifade",
        "Uygulama ipucu akışını durdurdu, sakin bir destek mesajı gösterdi ve 112 ile ALO 183 "
        "hatlarını önerdi. Çocuğunuzla sakin ve yargılamadan konuşmanızı, gerekirse bir uzmandan "
        "destek almanızı öneririz.",
    ),
}
FLAG_LABELS = {
    "violence": "Şiddet içeren ifade",
    "bullying": "Zorbalık anlatımı",
    "sexual_content": "Uygunsuz içerik",
}


class TopicStat(BaseModel):
    topic: str
    problems: int
    solved: int


class RecentProblem(BaseModel):
    id: uuid.UUID
    topic: str
    text: str | None
    solved: bool
    hints_used: int
    attempts: int
    created_at: datetime


class SafetyAlert(BaseModel):
    title: str
    guidance: str
    created_at: datetime


class ChildSummary(BaseModel):
    period_days: int
    since: datetime
    problems_started: int
    problems_solved: int
    solved_without_hints: int
    # Çözülen soru başına ortalama ipucu sayısı (düşükse daha bağımsız; Bölüm 6.4).
    avg_hints_per_solved: float | None
    hints_total: int
    attempts_total: int
    topics: list[TopicStat]
    recent: list[RecentProblem]
    shows_problem_text: bool
    alerts: list[SafetyAlert]
    # Ebeveyne gösterilen diğer güvenlik işaretleri: etiket → sayı.
    flags: dict[str, int]
    answer_requests: int


async def build_summary(db: AsyncSession, child: ChildProfile, days: int) -> ChildSummary:
    since = datetime.now(UTC) - timedelta(days=days)
    rows = (
        await db.execute(
            select(Problem, HiddenSolution.topic)
            .outerjoin(HiddenSolution, HiddenSolution.id == Problem.solution_id)
            .where(Problem.child_id == child.id, Problem.created_at >= since)
            .order_by(Problem.created_at.desc())
        )
    ).all()
    problem_ids = [problem.id for problem, _ in rows]

    hint_counts: dict[uuid.UUID, int] = {}
    attempt_counts: dict[uuid.UUID, int] = {}
    if problem_ids:
        hint_counts = {
            pid: int(n)
            for pid, n in await db.execute(
                select(Hint.problem_id, func.count(Hint.id))
                .where(Hint.problem_id.in_(problem_ids))
                .group_by(Hint.problem_id)
            )
        }
        attempt_counts = {
            pid: int(n)
            for pid, n in await db.execute(
                select(Attempt.problem_id, func.count(Attempt.id))
                .where(Attempt.problem_id.in_(problem_ids))
                .group_by(Attempt.problem_id)
            )
        }

    solved = [p for p, _ in rows if p.state == "solved"]
    solved_hints = [hint_counts.get(p.id, 0) for p in solved]
    topic_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for problem, topic in rows:
        stat = topic_stats[topic or UNKNOWN_TOPIC]
        stat[0] += 1
        stat[1] += problem.state == "solved"

    shows_text = child.privacy_level == "full_transcript"
    recent = [
        RecentProblem(
            id=problem.id,
            topic=topic or UNKNOWN_TOPIC,
            text=problem.masked_text if shows_text else None,
            solved=problem.state == "solved",
            hints_used=hint_counts.get(problem.id, 0),
            attempts=attempt_counts.get(problem.id, 0),
            created_at=problem.created_at,
        )
        for problem, topic in rows[:RECENT_LIMIT]
    ]

    events = (
        await db.scalars(
            select(ModerationEvent)
            .where(
                ModerationEvent.child_id == child.id,
                ModerationEvent.created_at >= since,
                ModerationEvent.category.not_in(GUARDIAN_HIDDEN_CATEGORIES),
            )
            .order_by(ModerationEvent.created_at.desc())
        )
    ).all()
    alerts = [
        SafetyAlert(
            title=ALERT_TEXTS[e.category][0],
            guidance=ALERT_TEXTS[e.category][1],
            created_at=e.created_at,
        )
        for e in events
        if e.notify_guardian and e.category in ALERT_TEXTS
    ]
    flags: dict[str, int] = defaultdict(int)
    for event in events:
        if event.stage == "input" and event.category in FLAG_LABELS:
            flags[FLAG_LABELS[event.category]] += 1

    return ChildSummary(
        period_days=days,
        since=since,
        problems_started=len(rows),
        problems_solved=len(solved),
        solved_without_hints=sum(1 for n in solved_hints if n == 0),
        avg_hints_per_solved=round(sum(solved_hints) / len(solved), 1) if solved else None,
        hints_total=sum(hint_counts.values()),
        attempts_total=sum(attempt_counts.values()),
        topics=sorted(
            (TopicStat(topic=t, problems=s[0], solved=s[1]) for t, s in topic_stats.items()),
            key=lambda stat: (-stat.problems, stat.topic),
        ),
        recent=recent,
        shows_problem_text=shows_text,
        alerts=alerts,
        flags=dict(flags),
        answer_requests=sum(1 for e in events if e.category == "prompt_injection"),
    )

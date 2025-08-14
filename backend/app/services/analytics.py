from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from app.core.db import get_db
async def log_event(evt_type: str, user_id: str | None, payload: Dict[str, Any] | None = None):
    db = get_db()
    await db.events.insert_one({
        "type": evt_type,
        "user_id": user_id,
        "payload": payload or {},
        "created_at": datetime.now(timezone.utc),
    })
async def summary(days: int = 7):
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(days=days)
    total_users = await db.users.count_documents({})
    uploads = await db.events.count_documents({"type": "document_uploaded", "created_at": {"$gte": since}})
    questions = await db.events.count_documents({"type": "question_asked", "created_at": {"$gte": since}})
    pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "events": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    per_day = []
    async for row in db.events.aggregate(pipeline):
        per_day.append({"date": row["_id"], "events": row["events"]})
    return {"since": since.isoformat(), "totals": {"users": total_users, "uploads": uploads, "questions": questions}, "per_day": per_day}

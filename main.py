import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Post, Event, Notification

app = FastAPI(title="Community App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility to convert ObjectId to string recursively

def serialize_doc(doc: dict):
    if not doc:
        return doc
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, list):
            out[k] = [serialize_doc(i) if isinstance(i, dict) else (str(i) if isinstance(i, ObjectId) else i) for i in v]
        elif isinstance(v, dict):
            out[k] = serialize_doc(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out

@app.get("/")
def read_root():
    return {"message": "Community API is running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Simple list endpoints

@app.get("/api/posts")
def list_posts(tag: Optional[str] = None, limit: int = Query(50, le=100)):
    filt = {"tags": tag} if tag else {}
    docs = get_documents("post", filt, limit)
    return [serialize_doc(d) for d in docs]

@app.post("/api/posts")
def create_post(payload: Post):
    post_id = create_document("post", payload)
    # Create broadcast notification about new post
    notif = Notification(user=None, type="post", message=f"New post: {payload.title}", related_id=str(post_id))
    create_document("notification", notif)
    return {"id": post_id}

@app.get("/api/events")
def list_events(upcoming: bool = True, limit: int = Query(50, le=100)):
    filt = {}
    if upcoming:
        filt = {"start_time": {"$gte": datetime.utcnow()}}
    docs = get_documents("event", filt, limit)
    return [serialize_doc(d) for d in docs]

@app.post("/api/events")
def create_event(payload: Event):
    event_id = create_document("event", payload)
    # Create broadcast notification about new event
    notif = Notification(user=None, type="event", message=f"New event: {payload.title}", related_id=str(event_id))
    create_document("notification", notif)
    return {"id": event_id}

@app.get("/api/notifications")
def list_notifications(user: Optional[str] = None, unread_only: bool = False, limit: int = Query(50, le=200)):
    filt = {}
    if user:
        filt["$or"] = [{"user": user}, {"user": None}]
    if unread_only:
        filt["is_read"] = False
    docs = get_documents("notification", filt, limit)
    return [serialize_doc(d) for d in docs]

class MarkReadPayload(BaseModel):
    id: str

@app.post("/api/notifications/read")
def mark_notification_read(payload: MarkReadPayload):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        oid = ObjectId(payload.id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")
    res = db["notification"].update_one({"_id": oid}, {"$set": {"is_read": True, "updated_at": datetime.utcnow()}})
    if res.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok"}

# Users minimal endpoints (create + list)
@app.get("/api/users")
def list_users(limit: int = Query(50, le=200)):
    docs = get_documents("user", {}, limit)
    return [serialize_doc(d) for d in docs]

@app.post("/api/users")
def create_user(payload: User):
    user_id = create_document("user", payload)
    return {"id": user_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

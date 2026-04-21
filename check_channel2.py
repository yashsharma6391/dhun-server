# save as check_channels2.py
from app.database import SessionLocal
from app.models.channel import Channel
from app.models.user import User

db = SessionLocal()

print("=== ALL CHANNELS ===")
channels = db.query(Channel).all()
for ch in channels:
    print(f"  Name: {ch.name}")
    print(f"  ID: {ch.id}")
    print(f"  Owner: {ch.owner_id}")
    print(f"  Public: {ch.is_public}")
    print(f"  Followers: {ch.follower_count}")
    print()

print("=== ALL USERS ===")
users = db.query(User).all()
for u in users:
    print(f"  {u.email} | id:{u.id}")

db.close()
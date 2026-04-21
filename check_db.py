# save as check_db.py in dhun-server folder
from app.database import SessionLocal
from app.models.channel import Channel
from app.models.user import User

db = SessionLocal()

print("=== USERS ===")
users = db.query(User).all()
for u in users:
    print(f"  {u.email} | id:{u.id}")

print("\n=== CHANNELS ===")
channels = db.query(Channel).all()
for ch in channels:
    print(f"  {ch.name} | id:{ch.id} | owner:{ch.owner_id}")

db.close()
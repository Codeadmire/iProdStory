import sys
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from auth import hash_password

db = SessionLocal()
user = db.query(models.User).filter(models.User.email == "s.tamilmani21@gmail.com").first()
if user:
    user.hashed_password = hash_password("Test@123")
    db.commit()
    print("Password updated successfully!")
else:
    print("User not found!")

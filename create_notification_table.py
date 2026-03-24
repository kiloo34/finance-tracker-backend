import asyncio
import sys
from app.database import engine, Base
from app.models import Notification

def setup_db():
    print("Creating newly added schema elements...")
    Base.metadata.create_all(bind=engine)
    print("Finished.")

if __name__ == "__main__":
    setup_db()

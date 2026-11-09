from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from app.core.security import create_user_access_token
from app.db.session import SessionLocal
from app.models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Issue a short-lived local demo access token for an existing user")
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == args.email.lower()))
        if user is None:
            raise RuntimeError("No account found for that email; run scripts/seed_demo.py first")
        if user.status.value != "ACTIVE":
            raise RuntimeError("Cannot issue token to a disabled account")
        print(create_user_access_token(user.user_id))
        print(f"# subject={user.email} role={user.role.value}", file=sys.stderr)
    finally:
        db.close()


if __name__ == "__main__":
    main()

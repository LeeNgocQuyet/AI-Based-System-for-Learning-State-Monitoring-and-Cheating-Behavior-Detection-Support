"""Create or update a pre-provisioned INSTRUCTOR account for the demo.

Required environment variables:
  DATABASE_URL
  INSTRUCTOR_EMAIL
  INSTRUCTOR_FULL_NAME
  INSTRUCTOR_PASSWORD

Dependencies: pip install 'psycopg[binary]' argon2-cffi
Never put the instructor password in source control or a committed .env file.
"""

from __future__ import annotations

import os
import re
import sys

import psycopg
from argon2 import PasswordHasher
from argon2.low_level import Type


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    database_url = required_env("DATABASE_URL")
    email = required_env("INSTRUCTOR_EMAIL").lower()
    full_name = required_env("INSTRUCTOR_FULL_NAME")
    password = required_env("INSTRUCTOR_PASSWORD")

    if len(password) < 10 or len(password) > 128:
        raise RuntimeError("INSTRUCTOR_PASSWORD must contain 10 to 128 characters")
    if len(full_name) > 120:
        raise RuntimeError("INSTRUCTOR_FULL_NAME must be at most 120 characters")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise RuntimeError("INSTRUCTOR_EMAIL must be a valid email address")

    hasher = PasswordHasher(
        time_cost=3,
        memory_cost=65536,
        parallelism=2,
        hash_len=32,
        salt_len=16,
        type=Type.ID,
    )
    password_hash = hasher.hash(password)

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, role FROM users WHERE LOWER(email) = %s FOR UPDATE",
                (email,),
            )
            existing = cur.fetchone()

            if existing is None:
                cur.execute(
                    """
                    INSERT INTO users (email, full_name, password_hash, role, status)
                    VALUES (%s, %s, %s, 'INSTRUCTOR', 'ACTIVE')
                    RETURNING user_id
                    """,
                    (email, full_name, password_hash),
                )
                user_id = cur.fetchone()[0]
                action = "created"
            else:
                user_id, role = existing
                if role != "INSTRUCTOR":
                    raise RuntimeError(
                        "This email already belongs to a non-instructor account; "
                        "refusing to elevate its role. Use a dedicated instructor email."
                    )
                cur.execute(
                    """
                    UPDATE users
                    SET full_name = %s,
                        password_hash = %s,
                        status = 'ACTIVE'
                    WHERE user_id = %s
                    """,
                    (full_name, password_hash, user_id),
                )
                action = "updated"

    print(f"Instructor account {action}: {email} (user_id={user_id})")
    print("No password or password hash was printed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed; do not dump secrets
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

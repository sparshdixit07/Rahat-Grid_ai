#!/usr/bin/env python
"""
RAHAT GRID AI — Demo bootstrap.

Creates the SQLite DB if missing, the users table, and demo accounts:
  Admin     : demo_admin       / DemoAdmin!2025
  Responder : demo_responder   / DemoResp!2025
  Citizen   : demo_citizen     / DemoCit!2025

Safe to run repeatedly. Will NOT overwrite existing accounts.
Provide --admin-user/--admin-email/--admin-password for custom first-admin.
Use --no-demo-responder / --no-demo-citizen to skip demo accounts.

DEMO CREDENTIALS ONLY — change or delete before any real deployment.
"""
import argparse
import hashlib
import secrets
import sqlite3
from datetime import datetime

DB_PATH = "rahat_grid_ai.db"
PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return digest.hex(), salt.hex()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_users_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL COLLATE NOCASE,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Citizen','Responder','Admin')),
            display_name TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            last_login_at TEXT
        )"""
    )
    conn.commit()


def find_user(conn, username=None, email=None):
    if username:
        return conn.execute(
            "SELECT * FROM users WHERE LOWER(username)=LOWER(?)", (username,)
        ).fetchone()
    if email:
        return conn.execute(
            "SELECT * FROM users WHERE LOWER(email)=LOWER(?)", (email,)
        ).fetchone()
    return None


def any_active_admin(conn) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM users WHERE role='Admin' AND is_active=1 LIMIT 1"
        ).fetchone()
        is not None
    )


def create_user(conn, username, email, password, role, display_name=None) -> None:
    h, s = hash_password(password)
    conn.execute(
        "INSERT INTO users (username, email, password_hash, password_salt, "
        "role, display_name, is_active, created_at) VALUES (?,?,?,?,?,?,1,?)",
        (
            username.lower(),
            email.lower(),
            h,
            s,
            role,
            display_name or username,
            now_iso(),
        ),
    )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="RAHAT GRID AI — Demo bootstrap")
    parser.add_argument("--admin-user", default="demo_admin")
    parser.add_argument("--admin-email", default="demo_admin@example.local")
    parser.add_argument("--admin-password", default="DemoAdmin!2025")
    parser.add_argument("--no-demo-responder", action="store_true")
    parser.add_argument("--no-demo-citizen", action="store_true")
    args = parser.parse_args()

    print("=== RAHAT GRID AI · Bootstrap ===\n")
    conn = sqlite3.connect(DB_PATH)
    ensure_users_table(conn)

    # ---- Admin ----
    if any_active_admin(conn):
        print("[i] An active Admin already exists — skipping admin creation.")
    else:
        if find_user(conn, username=args.admin_user) or find_user(
            conn, email=args.admin_email
        ):
            print(
                f"[!] Username/email {args.admin_user!r} / {args.admin_email!r} "
                "already exists but is not an Admin. Choose different values."
            )
            conn.close()
            return 1
        create_user(
            conn,
            args.admin_user,
            args.admin_email,
            args.admin_password,
            "Admin",
            "Demo Admin",
        )
        print(f"[+] Created Admin: {args.admin_user!r} ({args.admin_email!r})")

    # ---- Responder ----
    if not args.no_demo_responder:
        if find_user(conn, username="demo_responder"):
            print("[i] demo_responder exists — skipped.")
        else:
            create_user(
                conn,
                "demo_responder",
                "demo_responder@example.local",
                "DemoResp!2025",
                "Responder",
                "Demo Responder",
            )
            print("[+] Created Responder: 'demo_responder'")

    # ---- Citizen ----
    if not args.no_demo_citizen:
        if find_user(conn, username="demo_citizen"):
            print("[i] demo_citizen exists — skipped.")
        else:
            create_user(
                conn,
                "demo_citizen",
                "demo_citizen@example.local",
                "DemoCit!2025",
                "Citizen",
                "Demo Citizen",
            )
            print("[+] Created Citizen: 'demo_citizen'")

    print("\n=== DEMO CREDENTIALS (LOCAL ONLY) ===")
    print(f"Admin     : {args.admin_user} / {args.admin_password}")
    if not args.no_demo_responder:
        print("Responder : demo_responder / DemoResp!2025")
    if not args.no_demo_citizen:
        print("Citizen   : demo_citizen / DemoCit!2025")
    print("\n[!] Change or delete these before any real deployment.")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
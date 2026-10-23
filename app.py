# """
# RAHAT GRID AI — Explainable Disaster Triage & Resource Coordination System
# with Role-Based Access Control (Citizen · Responder · Admin)

# Local prototype. Deterministic rule-based triage. Fictional demo data only.
# """

# import hashlib
# import hmac
# import json
# import re
# import secrets
# import sqlite3
# import uuid
# from datetime import datetime
# from difflib import SequenceMatcher

# import pandas as pd
# import streamlit as st

# # ============================================================================
# # CONFIG & CONSTANTS
# # ============================================================================
# DB_PATH = "rahat_grid_ai.db"
# PBKDF2_ITERATIONS = 200_000

# ROLES = ["Citizen", "Responder", "Admin"]
# HAZARDS = ["Flood", "Medical", "Food", "Water", "Other"]
# STATUSES = [
#     "Under Review",
#     "Awaiting Verification",
#     "Assigned for Follow-up",
#     "Resolved / Closed",
# ]
# PRIORITIES = ["Urgent Review", "High", "Moderate", "Routine Review"]
# VERIFY_STATUSES = ["Unverified", "Verified by reviewer", "Cannot verify"]

# PRIORITY_COLORS = {
#     "Urgent Review": "#dc2626",
#     "High": "#ea580c",
#     "Moderate": "#d97706",
#     "Routine Review": "#16a34a",
# }
# ROLE_COLORS = {"Citizen": "#0891b2", "Responder": "#7c3aed", "Admin": "#dc2626"}

# ROLE_PERMISSIONS = {
#     "Citizen": {
#         "submit_report": True,
#         "view_own_reports": True,
#         "view_all_reports": False,
#         "review_incidents": False,
#         "review_duplicates": False,
#         "view_inventory": False,
#         "manage_inventory": False,
#         "create_relief_request": False,
#         "review_relief_requests": False,
#         "fulfill_relief_request": False,
#         "manage_users": False,
#         "view_audit_log": False,
#         "reset_demo": False,
#         "view_admin_dashboard": False,
#     },
#     "Responder": {
#         "submit_report": False,
#         "view_own_reports": False,
#         "view_all_reports": True,
#         "review_incidents": True,
#         "review_duplicates": True,
#         "view_inventory": True,
#         "manage_inventory": False,
#         "create_relief_request": True,
#         "review_relief_requests": False,
#         "fulfill_relief_request": False,
#         "manage_users": False,
#         "view_audit_log": False,
#         "reset_demo": False,
#         "view_admin_dashboard": False,
#     },
#     "Admin": {k: True for k in [
#         "submit_report", "view_own_reports", "view_all_reports", "review_incidents",
#         "review_duplicates", "view_inventory", "manage_inventory",
#         "create_relief_request", "review_relief_requests", "fulfill_relief_request",
#         "manage_users", "view_audit_log", "reset_demo", "view_admin_dashboard",
#     ]},
# }

# st.set_page_config(
#     page_title="RAHAT GRID AI",
#     page_icon="◈",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ============================================================================
# # CSS
# # ============================================================================
# def inject_css():
#     st.markdown(
#         """
#         <style>
#         :root {
#             --navy: #0b1e35; --navy-light: #13294a; --accent: #2563eb;
#             --bg: #f4f6f9; --border: #e2e8f0;
#         }
#         .stApp { background: var(--bg); }
#         section[data-testid="stSidebar"] {
#             background: linear-gradient(180deg, #0b1e35 0%, #0e2444 100%);
#             border-right: 1px solid #1a2f52;
#         }
#         section[data-testid="stSidebar"] * { color: #e6eef7; }
#         section[data-testid="stSidebar"] .stRadio > label {
#             color: #cbd5e1 !important; font-weight: 600;
#         }
#         section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
#             color: #cbd5e1 !important; padding: 6px 10px; border-radius: 8px;
#         }
#         section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
#             background: rgba(37, 99, 235, 0.18);
#         }
#         section[data-testid="stSidebar"] hr { border-color: #1a2f52; }

#         .rahat-header {
#             background: linear-gradient(135deg, #0b1e35 0%, #1e3a5f 100%);
#             padding: 22px 28px; border-radius: 12px; margin-bottom: 18px;
#             border: 1px solid #1a2f52;
#             box-shadow: 0 4px 20px rgba(15, 23, 42, 0.18);
#         }
#         .rahat-header h1 {
#             color: #ffffff; font-size: 26px; font-weight: 800;
#             letter-spacing: 1px; margin: 0;
#         }
#         .rahat-header .sub {
#             color: #93b4d6; font-size: 13px; margin-top: 4px;
#         }
#         .sim-banner {
#             display: inline-block; background: rgba(220, 38, 38, 0.20);
#             color: #fecaca; border: 1px solid rgba(248, 113, 113, 0.45);
#             padding: 4px 12px; border-radius: 6px; font-size: 11px;
#             font-weight: 700; letter-spacing: 1.2px; margin-top: 12px;
#         }
#         .stTabs [data-baseweb="tab-list"] {
#             gap: 4px; border-bottom: 1px solid var(--border);
#         }
#         .stTabs [data-baseweb="tab"] {
#             background: transparent; color: #64748b; font-weight: 600;
#             padding: 8px 16px; border-radius: 8px 8px 0 0;
#         }
#         .stTabs [aria-selected="true"] {
#             color: var(--accent) !important; background: white !important;
#             border-bottom: 2px solid var(--accent);
#         }
#         .stButton > button { border-radius: 8px; font-weight: 600; }
#         .badge {
#             display: inline-block; padding: 2px 10px; border-radius: 999px;
#             font-size: 11px; font-weight: 700; letter-spacing: 0.3px;
#         }
#         #MainMenu { visibility: hidden; }
#         footer { visibility: hidden; }
#         </style>
#         """,
#         unsafe_allow_html=True,
#     )

# # ============================================================================
# # SMALL HELPERS
# # ============================================================================
# def now_iso() -> str:
#     return datetime.now().isoformat(timespec="seconds")


# def new_report_code() -> str:
#     return "INC-" + datetime.now().strftime("%y%m%d") + "-" + uuid.uuid4().hex[:5].upper()


# def priority_badge(p: str) -> str:
#     color = PRIORITY_COLORS.get(p, "#64748b")
#     return (
#         f'<span class="badge" style="background:{color}1a; color:{color}; '
#         f'border:1px solid {color}55;">{p}</span>'
#     )


# def role_badge(role: str) -> str:
#     color = ROLE_COLORS.get(role, "#64748b")
#     return (
#         f'<span class="badge" style="background:{color}22; color:{color}; '
#         f'border:1px solid {color}66;">{role}</span>'
#     )


# def current_priority(i) -> str:
#     return i["human_priority"] or i["suggested_priority"]


# def _row_get(row, key, default=None):
#     try:
#         v = row[key]
#         return v if v is not None else default
#     except (KeyError, IndexError):
#         return default

# # ============================================================================
# # DATABASE
# # ============================================================================
# def get_conn() -> sqlite3.Connection:
#     conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#     conn.row_factory = sqlite3.Row
#     return conn


# def _table_columns(conn, table: str) -> set:
#     return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


# def migrate_schema(conn: sqlite3.Connection) -> None:
#     conn.execute(
#         """CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT UNIQUE NOT NULL COLLATE NOCASE,
#             email TEXT UNIQUE NOT NULL COLLATE NOCASE,
#             password_hash TEXT NOT NULL,
#             password_salt TEXT NOT NULL,
#             role TEXT NOT NULL CHECK(role IN ('Citizen','Responder','Admin')),
#             display_name TEXT,
#             is_active INTEGER NOT NULL DEFAULT 1,
#             created_at TEXT NOT NULL,
#             last_login_at TEXT
#         )"""
#     )
#     ddl_list = [
#         "ALTER TABLE incidents ADD COLUMN owner_user_id INTEGER",
#         "ALTER TABLE incidents ADD COLUMN reviewer_user_id INTEGER",
#         "ALTER TABLE incidents ADD COLUMN public_note TEXT",
#         "ALTER TABLE activity_log ADD COLUMN actor_user_id INTEGER",
#         "ALTER TABLE activity_log ADD COLUMN actor_role TEXT",
#         "ALTER TABLE relief_requests ADD COLUMN requested_by_user_id INTEGER",
#     ]
#     for ddl in ddl_list:
#         try:
#             conn.execute(ddl)
#         except sqlite3.OperationalError:
#             pass
#     conn.commit()


# def init_db() -> None:
#     conn = get_conn()
#     c = conn.cursor()
#     c.execute(
#         """CREATE TABLE IF NOT EXISTS incidents (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             report_code TEXT UNIQUE NOT NULL,
#             title TEXT NOT NULL,
#             description TEXT NOT NULL,
#             location TEXT,
#             hazard_type TEXT,
#             affected_count INTEGER DEFAULT 0,
#             danger_trapped INTEGER DEFAULT 0,
#             danger_rising_water INTEGER DEFAULT 0,
#             danger_injury INTEGER DEFAULT 0,
#             danger_other INTEGER DEFAULT 0,
#             reporter TEXT,
#             created_at TEXT NOT NULL,
#             status TEXT DEFAULT 'Under Review',
#             suggested_priority TEXT,
#             priority_reasons TEXT,
#             verify_flags TEXT,
#             recommended_action TEXT,
#             human_decision TEXT DEFAULT 'Pending',
#             human_priority TEXT,
#             reviewer_notes TEXT,
#             verified_status TEXT DEFAULT 'Unverified'
#         )"""
#     )
#     c.execute(
#         """CREATE TABLE IF NOT EXISTS inventory (
#             item_id TEXT PRIMARY KEY,
#             item_name TEXT NOT NULL,
#             category TEXT,
#             quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
#             unit TEXT,
#             location TEXT,
#             last_updated TEXT,
#             notes TEXT
#         )"""
#     )
#     c.execute(
#         """CREATE TABLE IF NOT EXISTS relief_requests (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             incident_code TEXT,
#             item_id TEXT,
#             quantity_requested INTEGER NOT NULL CHECK(quantity_requested >= 0),
#             notes TEXT,
#             status TEXT DEFAULT 'Pending Review',
#             matched_qty INTEGER DEFAULT 0,
#             shortfall INTEGER DEFAULT 0,
#             storage_location TEXT,
#             explanation TEXT,
#             created_at TEXT,
#             reviewed_at TEXT
#         )"""
#     )
#     c.execute(
#         """CREATE TABLE IF NOT EXISTS duplicate_reviews (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             report_a TEXT NOT NULL,
#             report_b TEXT NOT NULL,
#             decision TEXT NOT NULL,
#             reviewed_at TEXT,
#             UNIQUE(report_a, report_b)
#         )"""
#     )
#     c.execute(
#         """CREATE TABLE IF NOT EXISTS activity_log (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             timestamp TEXT NOT NULL,
#             entity_type TEXT,
#             entity_id TEXT,
#             action TEXT,
#             details TEXT
#         )"""
#     )
#     conn.commit()
#     migrate_schema(conn)
#     seed_demo_data(conn)
#     conn.close()


# def seed_demo_data(conn: sqlite3.Connection) -> None:
#     c = conn.cursor()
#     c.execute("SELECT COUNT(*) FROM incidents")
#     if c.fetchone()[0] > 0:
#         return

#     demo = [
#         dict(title="Floodwater reportedly rising in Maple Lane residential area",
#              description=("Residents report water level rising quickly along Maple Lane. "
#                           "Some households are unsure whether to evacuate. Fictional scenario."),
#              location="Sector 4 – Maple Lane (fictional ward)", hazard_type="Flood",
#              affected_count=18, danger_trapped=0, danger_rising_water=1,
#              danger_injury=0, danger_other=0, reporter="Demo Resident A"),
#         dict(title="People reportedly trapped on roof – Maple Lane",
#              description=("Report of three people stranded on a rooftop after floodwater rose quickly. "
#                           "Cannot confirm from field. Fictional scenario."),
#              location="Maple Lane, Sector 4 (fictional ward)", hazard_type="Flood",
#              affected_count=3, danger_trapped=1, danger_rising_water=1,
#              danger_injury=0, danger_other=0, reporter="Demo Neighbor B"),
#         dict(title="First-aid needed after reported injury",
#              description=("A volunteer reports a minor cut that may need first-aid kits at a "
#                           "temporary shelter. Fictional scenario."),
#              location="Shelter 3, Sector 2 (fictional)", hazard_type="Medical",
#              affected_count=1, danger_trapped=0, danger_rising_water=0,
#              danger_injury=1, danger_other=0, reporter="Demo Volunteer C"),
#         dict(title="Drinking water shortage at temporary shelter",
#              description=("Shelter coordinator reports drinking water will run out within hours. "
#                           "No immediate danger reported. Fictional scenario."),
#              location="Shelter 7, Sector 2 (fictional)", hazard_type="Water",
#              affected_count=60, danger_trapped=0, danger_rising_water=0,
#              danger_injury=0, danger_other=0, reporter="Demo Coordinator D"),
#         dict(title="Food packs requested for flooded neighbourhood",
#              description=("Community members request food packs for families in a flooded "
#                           "neighbourhood. No immediate danger reported. Fictional scenario."),
#              location="Sector 9 – Riverside (fictional)", hazard_type="Food",
#              affected_count=45, danger_trapped=0, danger_rising_water=0,
#              danger_injury=0, danger_other=0, reporter="Demo Community E"),
#         dict(title="Rapidly rising water in Riverside Lane",
#              description=("Water reportedly rising fast in Riverside Lane. Residents requesting "
#                           "guidance. Fictional scenario."),
#              location="Sector 9 – Riverside Lane (fictional)", hazard_type="Flood",
#              affected_count=20, danger_trapped=0, danger_rising_water=1,
#              danger_injury=0, danger_other=0, reporter="Demo Resident F"),
#         dict(title="Floodwater rising near Riverside Lane homes",
#              description=("Several homes near Riverside Lane report floodwater rising quickly. "
#                           "Fictional scenario."),
#              location="Riverside Lane, Sector 9 (fictional)", hazard_type="Flood",
#              affected_count=15, danger_trapped=0, danger_rising_water=1,
#              danger_injury=0, danger_other=0, reporter="Demo Resident G"),
#     ]

#     ts = now_iso()
#     for d in demo:
#         code = new_report_code()
#         tr = evaluate_triage(d)
#         c.execute(
#             """INSERT INTO incidents (
#                 report_code, title, description, location, hazard_type, affected_count,
#                 danger_trapped, danger_rising_water, danger_injury, danger_other,
#                 reporter, created_at, status, suggested_priority, priority_reasons,
#                 verify_flags, recommended_action, human_decision, human_priority,
#                 reviewer_notes, verified_status, owner_user_id
#             ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)""",
#             (code, d["title"], d["description"], d["location"], d["hazard_type"],
#              d["affected_count"], d["danger_trapped"], d["danger_rising_water"],
#              d["danger_injury"], d["danger_other"], d["reporter"], ts,
#              "Under Review", tr["priority"], json.dumps(tr["reasons"]),
#              json.dumps(tr["flags"]), tr["action"], "Pending", tr["priority"],
#              "", "Unverified"),
#         )

#     inventory_seed = [
#         ("WTR-001", "Drinking water", "Water", 500, "litres",
#          "Depot A – North Fictional Yard", ts, "Bottled and bulk supply"),
#         ("FOOD-001", "Food packs", "Food", 120, "packs",
#          "Depot A – North Fictional Yard", ts, "Family-sized, ready to eat"),
#         ("MED-001", "First-aid kits", "Medical", 40, "kits",
#          "Depot B – Central Fictional Yard", ts, "Basic dressings"),
#         ("BLK-001", "Blankets", "Shelter", 200, "units",
#          "Depot B – Central Fictional Yard", ts, "Thermal"),
#         ("HYG-001", "Basic hygiene kits", "Hygiene", 80, "kits",
#          "Depot C – South Fictional Yard", ts, "Family hygiene"),
#     ]
#     for row in inventory_seed:
#         c.execute("INSERT OR IGNORE INTO inventory VALUES (?,?,?,?,?,?,?,?)", row)

#     c.execute(
#         "INSERT INTO activity_log (timestamp, entity_type, entity_id, action, details, "
#         "actor_user_id, actor_role) VALUES (?,?,?,?,?,NULL,'system')",
#         (ts, "system", "seed", "Demo data seeded",
#          "Fictional demonstration dataset loaded."),
#     )
#     conn.commit()


# def log_activity(entity_type: str, entity_id: str, action: str, details: str,
#                  actor_user_id=None, actor_role=None) -> None:
#     conn = get_conn()
#     try:
#         conn.execute(
#             "INSERT INTO activity_log (timestamp, entity_type, entity_id, action, details, "
#             "actor_user_id, actor_role) VALUES (?,?,?,?,?,?,?)",
#             (now_iso(), entity_type, entity_id, action, details, actor_user_id, actor_role),
#         )
#         conn.commit()
#     finally:
#         conn.close()


# def log_action(entity_type: str, entity_id: str, action: str, details: str) -> None:
#     user = get_current_user()
#     log_activity(
#         entity_type, entity_id, action, details,
#         actor_user_id=user["id"] if user else None,
#         actor_role=user["role"] if user else "system",
#     )

# # ============================================================================
# # AUTH
# # ============================================================================
# def hash_password(password: str):
#     salt = secrets.token_bytes(16)
#     digest = hashlib.pbkdf2_hmac(
#         "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
#     )
#     return digest.hex(), salt.hex()


# def verify_password(password: str, stored_hash_hex: str, stored_salt_hex: str) -> bool:
#     try:
#         salt = bytes.fromhex(stored_salt_hex)
#     except (ValueError, TypeError):
#         return False
#     digest = hashlib.pbkdf2_hmac(
#         "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
#     )
#     return hmac.compare_digest(digest.hex(), stored_hash_hex or "")


# def validate_registration(username, email, password):
#     if not username or len(username) < 3:
#         return "Username must be at least 3 characters."
#     if not re.match(r"^[A-Za-z0-9_.-]{3,40}$", username):
#         return "Username may only contain letters, digits, dot, dash, underscore (3–40 chars)."
#     if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
#         return "Please enter a valid email address."
#     if not password or len(password) < 8:
#         return "Password must be at least 8 characters."
#     return None


# def register_user(username, email, password, display_name=None,
#                   role="Citizen", actor=None):
#     if role not in ROLES:
#         return False, "Invalid role."
#     if role in ("Responder", "Admin"):
#         if not actor or actor.get("role") != "Admin":
#             return False, "Only an Admin can create Responder or Admin accounts."
#     err = validate_registration(username, email, password)
#     if err:
#         return False, err
#     conn = get_conn()
#     try:
#         exists = conn.execute(
#             "SELECT 1 FROM users WHERE LOWER(username)=LOWER(?) OR LOWER(email)=LOWER(?)",
#             (username, email),
#         ).fetchone()
#         if exists:
#             return False, "Username or email already in use."
#         h, s = hash_password(password)
#         cur = conn.execute(
#             "INSERT INTO users (username, email, password_hash, password_salt, "
#             "role, display_name, is_active, created_at) VALUES (?,?,?,?,?,?,1,?)",
#             (username, email, h, s, role, display_name or username, now_iso()),
#         )
#         conn.commit()
#         uid = cur.lastrowid
#     finally:
#         conn.close()
#     log_action("user", str(uid), "User created", f"username={username} role={role}")
#     return True, uid


# def authenticate(identifier: str, password: str):
#     conn = get_conn()
#     try:
#         row = conn.execute(
#             "SELECT * FROM users WHERE LOWER(username)=LOWER(?) OR LOWER(email)=LOWER(?)",
#             (identifier, identifier),
#         ).fetchone()
#         if not row:
#             log_activity("auth", identifier, "Login failed",
#                          "Unknown username/email", actor_role="anon")
#             return None, "Invalid credentials."
#         user = dict(row)
#         if not user["is_active"]:
#             log_activity("auth", str(user["id"]), "Login failed",
#                          "Account deactivated", actor_role="anon")
#             return None, "Account is deactivated. Contact an administrator."
#         if not verify_password(password, user["password_hash"], user["password_salt"]):
#             log_activity("auth", str(user["id"]), "Login failed",
#                          "Incorrect password", actor_role="anon")
#             return None, "Invalid credentials."
#         conn.execute("UPDATE users SET last_login_at=? WHERE id=?",
#                      (now_iso(), user["id"]))
#         conn.commit()
#     finally:
#         conn.close()
#     log_activity("auth", str(user["id"]), "Login success",
#                  f"role={user['role']}",
#                  actor_user_id=user["id"], actor_role=user["role"])
#     return user, None


# def get_current_user():
#     uid = st.session_state.get("auth_user_id")
#     if not uid:
#         return None
#     conn = get_conn()
#     try:
#         row = conn.execute(
#             "SELECT * FROM users WHERE id=? AND is_active=1", (uid,)
#         ).fetchone()
#     finally:
#         conn.close()
#     if not row:
#         st.session_state.pop("auth_user_id", None)
#         return None
#     return dict(row)


# def can(user, action: str) -> bool:
#     if not user:
#         return False
#     return ROLE_PERMISSIONS.get(user["role"], {}).get(action, False)


# def change_own_password(user_id, old_password, new_password):
#     conn = get_conn()
#     try:
#         row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
#         if not row:
#             return False, "User not found."
#         if not verify_password(old_password, row["password_hash"], row["password_salt"]):
#             return False, "Current password is incorrect."
#         if len(new_password or "") < 8:
#             return False, "New password must be at least 8 characters."
#         h, s = hash_password(new_password)
#         conn.execute(
#             "UPDATE users SET password_hash=?, password_salt=? WHERE id=?",
#             (h, s, user_id),
#         )
#         conn.commit()
#     finally:
#         conn.close()
#     log_action("user", str(user_id), "Password changed",
#                "User changed own password.")
#     return True, None

# # ============================================================================
# # TRIAGE ENGINE
# # ============================================================================
# def evaluate_triage(d: dict) -> dict:
#     score = 0
#     reasons, flags = [], []

#     if d.get("danger_trapped"):
#         score += 50
#         reasons.append("Reported people trapped in a dangerous situation.")
#     if d.get("danger_rising_water"):
#         score += 25
#         reasons.append("Reported rapidly rising floodwater.")
#     if d.get("danger_injury"):
#         score += 30
#         reasons.append("Reported serious injury or immediate medical danger.")
#     if d.get("danger_other"):
#         score += 15
#         reasons.append("Other urgent circumstance reported.")

#     danger_count = sum(
#         1 for k in ("danger_trapped", "danger_rising_water",
#                     "danger_injury", "danger_other") if d.get(k)
#     )
#     if danger_count >= 2:
#         score += 10
#         reasons.append(f"Multiple danger indicators reported ({danger_count}).")

#     loc = (d.get("location") or "").strip()
#     desc = (d.get("description") or "").lower()
#     vague = ("somewhere", "unknown", "not sure", "maybe", "possibly", "near")

#     if not loc or len(loc) < 6:
#         flags.append("Location text is missing or very brief — verify before routing.")
#     if loc and any(w in loc.lower() for w in vague):
#         flags.append("Location contains uncertain language — verify.")
#     if desc and any(w in desc for w in vague):
#         flags.append("Description contains uncertain language — verify.")
#     if int(d.get("affected_count", 0) or 0) == 0:
#         flags.append("Reported number of affected people is 0 or unspecified — verify scale.")

#     if not reasons:
#         reasons.append("No immediate-danger indicators reported in the submission.")

#     if score >= 60:
#         priority = "Urgent Review"
#     elif score >= 35:
#         priority = "High"
#     elif score >= 15:
#         priority = "Moderate"
#     else:
#         priority = "Routine Review"

#     action = {
#         "Urgent Review": ("Human reviewer should verify immediately with the reporter "
#                           "and escalate to the on-duty coordinator."),
#         "High": ("Reviewer should verify details and prepare a follow-up plan within the "
#                  "next review cycle."),
#         "Moderate": ("Reviewer should confirm the report and route to the appropriate "
#                      "relief track."),
#         "Routine Review": "Log for routine review; confirm details before routing.",
#     }[priority]

#     if d.get("hazard_type") in ("Food", "Water") and danger_count == 0:
#         reasons.append(
#             "Basic-needs request without immediate-danger indicators — "
#             "route to logistics review; do not disregard."
#         )

#     return {"score": score, "priority": priority, "reasons": reasons,
#             "flags": flags, "action": action}

# # ============================================================================
# # DUPLICATE DETECTION
# # ============================================================================
# def _combined_text(title, description, location):
#     return " ".join(x for x in [title or "", description or "", location or ""]
#                     if x).lower()


# def similarity_score(a: str, b: str) -> float:
#     seq = SequenceMatcher(None, a, b).ratio()
#     ta = set(re.findall(r"\w+", a))
#     tb = set(re.findall(r"\w+", b))
#     overlap = (len(ta & tb) / len(ta | tb)) if (ta and tb) else 0.0
#     return 0.5 * seq + 0.5 * overlap


# def find_duplicate_pairs(threshold: float = 0.6):
#     conn = get_conn()
#     try:
#         incidents = conn.execute(
#             "SELECT report_code, title, description, location FROM incidents"
#         ).fetchall()
#         reviewed = conn.execute(
#             "SELECT report_a, report_b FROM duplicate_reviews"
#         ).fetchall()
#     finally:
#         conn.close()

#     reviewed_set = {tuple(sorted((r["report_a"], r["report_b"]))) for r in reviewed}
#     pairs = []
#     n = len(incidents)
#     for i in range(n):
#         for j in range(i + 1, n):
#             a, b = incidents[i], incidents[j]
#             key = tuple(sorted((a["report_code"], b["report_code"])))
#             if key in reviewed_set:
#                 continue
#             ta = _combined_text(a["title"], a["description"], a["location"])
#             tb = _combined_text(b["title"], b["description"], b["location"])
#             s = similarity_score(ta, tb)
#             if s >= threshold:
#                 pairs.append({
#                     "a": a["report_code"], "b": b["report_code"],
#                     "a_title": a["title"], "b_title": b["title"],
#                     "a_desc": a["description"], "b_desc": b["description"],
#                     "location": a["location"] or b["location"],
#                     "score": round(s, 3),
#                 })
#     pairs.sort(key=lambda x: -x["score"])
#     return pairs


# def record_duplicate_review(a: str, b: str, decision: str):
#     user = get_current_user()
#     if not user or not can(user, "review_duplicates"):
#         return False, "Not authorized."
#     a, b = sorted((a, b))
#     conn = get_conn()
#     try:
#         conn.execute(
#             "INSERT OR REPLACE INTO duplicate_reviews (report_a, report_b, decision, reviewed_at) "
#             "VALUES (?,?,?,?)", (a, b, decision, now_iso()),
#         )
#         conn.commit()
#     finally:
#         conn.close()
#     log_action("duplicate_review", f"{a}|{b}", decision,
#                f"Pair reviewed: {a} ↔ {b} — {decision}.")
#     return True, None

# # ============================================================================
# # RESOURCE MATCHING
# # ============================================================================
# def compute_match(item_id: str, qty: int):
#     conn = get_conn()
#     try:
#         item = conn.execute("SELECT * FROM inventory WHERE item_id=?", (item_id,)).fetchone()
#     finally:
#         conn.close()
#     if not item:
#         return None
#     available = int(item["quantity"])
#     return {
#         "available": available,
#         "matchable": min(available, qty),
#         "shortfall": max(0, qty - available),
#         "location": item["location"],
#         "unit": item["unit"],
#         "item_name": item["item_name"],
#     }


# def create_relief_request(incident_code, item_id, qty, notes):
#     user = get_current_user()
#     if not user or not can(user, "create_relief_request"):
#         return False, "Not authorized to create relief requests.", None
#     if qty <= 0:
#         return False, "Requested quantity must be positive.", None
#     match = compute_match(item_id, int(qty))
#     if match is None:
#         return False, "Item not found in inventory.", None
#     explanation = (
#         f"Requested {qty} {match['unit']} of {match['item_name']}. "
#         f"Available at {match['location'] or 'unspecified location'}: "
#         f"{match['available']} {match['unit']}. "
#         f"Potentially matchable: {match['matchable']} {match['unit']}. "
#         f"Shortfall: {match['shortfall']} {match['unit']}. "
#         f"Stock is NOT deducted until an Admin marks this request as Fulfilled."
#     )
#     conn = get_conn()
#     try:
#         cur = conn.execute(
#             """INSERT INTO relief_requests
#                (incident_code, item_id, quantity_requested, notes, status,
#                 matched_qty, shortfall, storage_location, explanation,
#                 created_at, reviewed_at, requested_by_user_id)
#                VALUES (?,?,?,?,?,?,?,?,?,?,NULL,?)""",
#             (incident_code or "", item_id, int(qty), notes.strip(), "Pending Review",
#              match["matchable"], match["shortfall"], match["location"],
#              explanation, now_iso(), user["id"]),
#         )
#         req_id = cur.lastrowid
#         conn.commit()
#     finally:
#         conn.close()
#     log_action("relief_request", str(req_id), "Request created",
#                f"Requested {qty} {match['unit']} of {item_id}. "
#                f"Matchable: {match['matchable']}. Shortfall: {match['shortfall']}.")
#     return True, None, {"id": req_id, **match, "qty": qty}


# def set_request_status(req_id: int, new_status: str):
#     user = get_current_user()
#     if not user or not can(user, "review_relief_requests"):
#         return False, "Not authorized."
#     if new_status not in ("Approved", "Rejected"):
#         return False, "Invalid status change."
#     conn = get_conn()
#     try:
#         conn.execute(
#             "UPDATE relief_requests SET status=?, reviewed_at=? WHERE id=?",
#             (new_status, now_iso(), req_id),
#         )
#         conn.commit()
#     finally:
#         conn.close()
#     log_action("relief_request", str(req_id), new_status,
#                f"Request marked {new_status} (no stock deducted).")
#     return True, None


# def fulfill_request(req_id: int):
#     user = get_current_user()
#     if not user or not can(user, "fulfill_relief_request"):
#         return False, "Not authorized."
#     conn = get_conn()
#     try:
#         req = conn.execute(
#             "SELECT * FROM relief_requests WHERE id=?", (req_id,)
#         ).fetchone()
#         if not req:
#             return False, "Request not found."
#         if req["status"] == "Fulfilled":
#             return False, "Request already fulfilled."
#         item = conn.execute(
#             "SELECT * FROM inventory WHERE item_id=?", (req["item_id"],)
#         ).fetchone()
#         if not item:
#             return False, "Inventory item not found."
#         deduct = min(int(req["matched_qty"]), int(item["quantity"]))
#         if deduct <= 0:
#             return False, "No stock available to deduct."
#         new_qty = int(item["quantity"]) - deduct
#         conn.execute(
#             "UPDATE inventory SET quantity=?, last_updated=? WHERE item_id=?",
#             (new_qty, now_iso(), req["item_id"]),
#         )
#         conn.execute(
#             "UPDATE relief_requests SET status='Fulfilled', reviewed_at=? WHERE id=?",
#             (now_iso(), req_id),
#         )
#         conn.commit()
#     except sqlite3.IntegrityError as exc:
#         conn.rollback()
#         return False, f"Deduction failed: {exc}"
#     finally:
#         conn.close()
#     log_action("relief_request", str(req_id), "Fulfilled",
#                f"Deducted {deduct} {item['unit']} of {item['item_name']} "
#                f"from inventory {req['item_id']}. Remaining: {new_qty}.")
#     return True, f"Deducted {deduct} {item['unit']}. Remaining: {new_qty}."

# # ============================================================================
# # UI COMPONENTS
# # ============================================================================
# def render_header(user=None):
#     badge = ""
#     if user:
#         badge = (
#             f"<div style='margin-top:10px; font-size:12px; color:#93b4d6;'>"
#             f"Signed in as <b style='color:#fff;'>{user['username']}</b> "
#             f"{role_badge(user['role'])}</div>"
#         )
#     st.markdown(
#         f"""
#         <div class="rahat-header">
#             <h1>RAHAT GRID AI</h1>
#             <div class="sub">Explainable Disaster Triage &amp; Resource Coordination</div>
#             <span class="sim-banner">SIMULATION MODE · FICTIONAL DATA · NOT A LIVE EMERGENCY SERVICE</span>
#             {badge}
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# def metric_card(label, value, hint=None, color="#2563eb"):
#     hint_html = (
#         f"<div style='font-size:11px; color:#94a3b8; margin-top:4px;'>{hint}</div>"
#         if hint else ""
#     )
#     return (
#         f"<div style='background:white; border-radius:10px; padding:16px 18px; "
#         f"border:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(15,23,42,0.06); height:100%;'>"
#         f"<div style='font-size:11px; text-transform:uppercase; letter-spacing:0.8px; "
#         f"color:#64748b; font-weight:600;'>{label}</div>"
#         f"<div style='font-size:28px; font-weight:700; color:{color}; margin-top:6px;'>{value}</div>"
#         f"{hint_html}</div>"
#     )


# def bar_chart_html(counts, keys, colors=None, accent="#2563eb"):
#     total = max(sum(counts.get(k, 0) for k in keys), 1)
#     html = ""
#     for k in keys:
#         n = counts.get(k, 0)
#         pct = n / total * 100
#         color = (colors or {}).get(k, accent)
#         html += (
#             f"<div style='margin-bottom:10px;'>"
#             f"<div style='display:flex; justify-content:space-between; font-size:12px; "
#             f"color:#475569; margin-bottom:4px;'><span>{k}</span><span>{n}</span></div>"
#             f"<div style='background:#e2e8f0; border-radius:6px; height:10px; overflow:hidden;'>"
#             f"<div style='width:{pct:.1f}%; background:{color}; height:100%;'></div>"
#             f"</div></div>"
#         )
#     return html


# def render_incident_detail(i, internal=True):
#     col1, col2 = st.columns([2, 1])
#     with col1:
#         st.markdown(f"**Description:** {i['description']}")
#         st.markdown(f"**Location:** {i['location'] or '—'}")
#         st.markdown(f"**Hazard type:** {i['hazard_type']}")
#         st.markdown(f"**Reported affected people:** {i['affected_count']}")
#         if internal:
#             st.markdown(f"**Reporter (reported):** {i['reporter'] or '—'}")
#             st.markdown(f"**Created:** {i['created_at']}")
#     with col2:
#         st.markdown(f"**Status:** {i['status']}")
#         st.markdown(f"**Verified:** {i['verified_status']}")
#         st.markdown(f"**Human decision:** {i['human_decision']}")

#     st.markdown("---")
#     suggested_html = priority_badge(i["suggested_priority"])
#     final_html = (
#         priority_badge(i["human_priority"])
#         if i["human_priority"] and i["human_priority"] != i["suggested_priority"]
#         else ""
#     )
#     st.markdown(
#         "**Suggested priority:** " + suggested_html
#         + (" · **Human final:** " + final_html if final_html else ""),
#         unsafe_allow_html=True,
#     )

#     reasons = json.loads(i["priority_reasons"] or "[]")
#     st.markdown("**Why this was flagged:**")
#     for r in reasons:
#         st.markdown(f"- {r}")

#     flags = json.loads(i["verify_flags"] or "[]")
#     if flags and internal:
#         st.markdown("**Information to verify:**")
#         for f in flags:
#             st.markdown(f"- {f}")

#     if internal:
#         st.markdown(f"**Recommended next step:** {i['recommended_action']}")
#         if i["reviewer_notes"]:
#             st.markdown(f"**Reviewer notes (internal):** {i['reviewer_notes']}")

#     if _row_get(i, "public_note"):
#         st.markdown(f"**Public status note for reporter:** {i['public_note']}")

# # ============================================================================
# # AUTH PAGE
# # ============================================================================
# def page_bootstrap_needed():
#     st.markdown(
#         "### System setup required\n\n"
#         "No Admin account exists yet. This application does **not** auto-promote "
#         "the first person who registers. To create the first Admin, run the "
#         "bootstrap script once from the project folder:\n\n"
#         "```powershell\n"
#         "python bootstrap_demo.py\n"
#         "```\n\n"
#         "Or provide custom credentials:\n\n"
#         "```powershell\n"
#         "python bootstrap_demo.py --admin-user myname --admin-email me@x.com --admin-password \"MyStr0ng!pw\"\n"
#         "```\n\n"
#         "Then refresh this page and sign in."
#     )
#     if st.button("I've run the bootstrap — reload"):
#         st.rerun()


# def page_auth():
#     tab_login, tab_register = st.tabs(["Sign In", "Register (Citizen)"])

#     with tab_login:
#         with st.form("login_form"):
#             ident = st.text_input("Username or email")
#             pw = st.text_input("Password", type="password")
#             submit = st.form_submit_button("Sign In")
#         if submit:
#             if not ident or not pw:
#                 st.error("Enter both username/email and password.")
#             else:
#                 user, err = authenticate(ident.strip(), pw)
#                 if err:
#                     st.error(err)
#                 else:
#                     st.session_state["auth_user_id"] = user["id"]
#                     st.rerun()

#     with tab_register:
#         st.caption(
#             "Self-registration creates a **Citizen** account only. Responders and "
#             "Admins are provisioned by an existing Admin."
#         )
#         with st.form("register_form"):
#             u = st.text_input("Username (3–40 chars; letters, digits, . _ -)")
#             e = st.text_input("Email")
#             d = st.text_input("Display name (optional)")
#             p1 = st.text_input("Password (min 8 chars)", type="password")
#             p2 = st.text_input("Confirm password", type="password")
#             submit = st.form_submit_button("Create Account")
#         if submit:
#             if p1 != p2:
#                 st.error("Passwords do not match.")
#             else:
#                 ok, res = register_user(u.strip(), e.strip(), p1,
#                                         d.strip() or None, role="Citizen")
#                 if ok:
#                     st.success("Account created. You may now sign in.")
#                 else:
#                     st.error(res)


# def check_no_admin() -> bool:
#     conn = get_conn()
#     try:
#         n = conn.execute(
#             "SELECT COUNT(*) FROM users WHERE role='Admin' AND is_active=1"
#         ).fetchone()[0]
#     finally:
#         conn.close()
#     return n == 0

# # ============================================================================
# # CITIZEN DASHBOARD
# # ============================================================================
# def page_my_reports(user):
#     st.subheader("My Reports")
#     st.caption("You can only see reports you submitted. Statuses are updated by responders/admins.")

#     tab_new, tab_mine = st.tabs(["Submit New Report", "My Submitted Reports"])

#     with tab_new:
#         with st.form("citizen_submit_report"):
#             col1, col2 = st.columns(2)
#             with col1:
#                 title = st.text_input("Report title *")
#                 location = st.text_input("Fictional ward / sector or location text")
#                 hazard = st.selectbox("Hazard type", HAZARDS)
#                 affected = st.number_input("Number of people reported affected",
#                                            min_value=0, step=1, value=0)
#             with col2:
#                 description = st.text_area("Detailed description *", height=140)
#                 reporter_alias = st.text_input("Reporter name or alias (optional)")
#             st.markdown("**Immediate-danger indicators (as reported):**")
#             dc1, dc2, dc3, dc4 = st.columns(4)
#             with dc1:
#                 d_trapped = st.checkbox("People reported trapped")
#             with dc2:
#                 d_water = st.checkbox("Rapidly rising water")
#             with dc3:
#                 d_injury = st.checkbox("Reported injury / medical danger")
#             with dc4:
#                 d_other = st.checkbox("Other urgent circumstance")
#             submitted = st.form_submit_button("Submit Report")

#         if submitted:
#             title = (title or "").strip()
#             description = (description or "").strip()
#             if not title:
#                 st.error("Title is required.")
#             elif not description:
#                 st.error("Description is required.")
#             elif affected < 0:
#                 st.error("Affected count cannot be negative.")
#             else:
#                 payload = dict(title=title, description=description,
#                                location=(location or "").strip(),
#                                hazard_type=hazard, affected_count=int(affected),
#                                danger_trapped=int(d_trapped),
#                                danger_rising_water=int(d_water),
#                                danger_injury=int(d_injury),
#                                danger_other=int(d_other))
#                 tr = evaluate_triage(payload)
#                 code = new_report_code()
#                 conn = get_conn()
#                 try:
#                     conn.execute(
#                         """INSERT INTO incidents (
#                             report_code, title, description, location, hazard_type,
#                             affected_count, danger_trapped, danger_rising_water,
#                             danger_injury, danger_other, reporter, created_at, status,
#                             suggested_priority, priority_reasons, verify_flags,
#                             recommended_action, human_decision, human_priority,
#                             reviewer_notes, verified_status, owner_user_id
#                         ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
#                         (code, title, description, payload["location"], hazard,
#                          int(affected), int(d_trapped), int(d_water), int(d_injury),
#                          int(d_other), (reporter_alias or "").strip(), now_iso(),
#                          "Under Review", tr["priority"], json.dumps(tr["reasons"]),
#                          json.dumps(tr["flags"]), tr["action"], "Pending",
#                          tr["priority"], "", "Unverified", user["id"]),
#                     )
#                     conn.commit()
#                 finally:
#                     conn.close()
#                 log_action("incident", code, "Report submitted",
#                            f"title={title} hazard={hazard} suggested={tr['priority']}")
#                 st.success(
#                     f"Report submitted. Generated report ID: **{code}** · "
#                     f"Suggested priority: **{tr['priority']}** (pending human review)."
#                 )

#     with tab_mine:
#         conn = get_conn()
#         try:
#             rows = conn.execute(
#                 "SELECT * FROM incidents WHERE owner_user_id=? ORDER BY created_at DESC",
#                 (user["id"],),
#             ).fetchall()
#         finally:
#             conn.close()

#         if not rows:
#             st.info("You have not submitted any reports yet.")
#             return

#         st.caption(f"You have {len(rows)} report(s).")
#         for i in rows:
#             with st.expander(
#                 f"{i['report_code']} · {i['title']} · {i['status']} · "
#                 f"{current_priority(i)}"
#             ):
#                 render_incident_detail(i, internal=False)

# # ============================================================================
# # SHARED PAGES (Responder + Admin)
# # ============================================================================
# def page_overview(user):
#     st.subheader("Operations Overview")
#     st.caption("All figures computed from the local SQLite database. Fictional demonstration data only.")

#     conn = get_conn()
#     try:
#         incidents = conn.execute("SELECT * FROM incidents").fetchall()
#         inventory = conn.execute("SELECT * FROM inventory").fetchall()
#         activity = conn.execute(
#             "SELECT * FROM activity_log ORDER BY id DESC LIMIT 8"
#         ).fetchall()
#     finally:
#         conn.close()

#     open_inc = [i for i in incidents if i["status"] != "Resolved / Closed"]
#     urgent = [i for i in open_inc if current_priority(i) == "Urgent Review"]
#     pending = [i for i in incidents if i["human_decision"] == "Pending"]
#     dup_pairs = find_duplicate_pairs()
#     total_stock = sum(int(i["quantity"]) for i in inventory)
#     low_stock = [i for i in inventory if int(i["quantity"]) < 20]

#     cols = st.columns(5)
#     cards = [
#         ("Open Incidents", len(open_inc), "Excluding closed cases", "#2563eb"),
#         ("Urgent Review", len(urgent), "Current priority = Urgent", "#dc2626"),
#         ("Awaiting Review", len(pending), "Human decision pending", "#ea580c"),
#         ("Possible Duplicates", len(dup_pairs), "Unresolved candidate pairs", "#d97706"),
#         ("Total Stock Units", total_stock,
#          f"{len(inventory)} items · {len(low_stock)} low", "#16a34a"),
#     ]
#     for c, (label, value, hint, color) in zip(cols, cards):
#         with c:
#             st.markdown(metric_card(label, value, hint, color), unsafe_allow_html=True)

#     st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
#     colA, colB = st.columns(2)
#     with colA:
#         with st.container(border=True):
#             st.markdown("#### Priority Distribution (open cases)")
#             counts = {}
#             for i in open_inc:
#                 p = current_priority(i)
#                 counts[p] = counts.get(p, 0) + 1
#             st.markdown(bar_chart_html(counts, PRIORITIES, PRIORITY_COLORS),
#                         unsafe_allow_html=True)
#     with colB:
#         with st.container(border=True):
#             st.markdown("#### Hazard Mix (open cases)")
#             haz = {}
#             for i in open_inc:
#                 haz[i["hazard_type"]] = haz.get(i["hazard_type"], 0) + 1
#             st.markdown(bar_chart_html(haz, HAZARDS), unsafe_allow_html=True)

#     with st.container(border=True):
#         st.markdown("#### Recent Incidents")
#         if incidents:
#             df = pd.DataFrame([{
#                 "Report": i["report_code"],
#                 "Title": (i["title"][:64] + "…") if len(i["title"]) > 64 else i["title"],
#                 "Hazard": i["hazard_type"],
#                 "Priority": current_priority(i),
#                 "Status": i["status"],
#                 "Created": i["created_at"],
#             } for i in incidents[:10]])
#             st.dataframe(df, use_container_width=True, hide_index=True)
#         else:
#             st.info("No incidents recorded yet.")

#     with st.container(border=True):
#         st.markdown("#### Recent Activity")
#         if activity:
#             for a in activity:
#                 st.markdown(
#                     f"<div style='padding:8px 0; border-bottom:1px solid #eef2f7; "
#                     f"font-size:13px;'><span style='color:#64748b;'>{a['timestamp']}</span>"
#                     f" · <b>{a['action']}</b> · "
#                     f"<span style='color:#475569;'>{a['details']}</span></div>",
#                     unsafe_allow_html=True,
#                 )
#         else:
#             st.info("No activity logged yet.")


# def page_incidents(user):
#     st.subheader("Incident Reports")
#     tabs = st.tabs(["Browse Reports", "Possible Duplicates"])
#     with tabs[0]:
#         browse_reports(user)
#     with tabs[1]:
#         duplicates_tab()


# def browse_reports(user):
#     st.markdown("##### Browse and filter reports")
#     conn = get_conn()
#     try:
#         incidents = conn.execute(
#             "SELECT * FROM incidents ORDER BY created_at DESC"
#         ).fetchall()
#     finally:
#         conn.close()

#     c1, c2, c3, c4 = st.columns(4)
#     with c1:
#         f_hazard = st.selectbox("Hazard", ["All"] + HAZARDS)
#     with c2:
#         f_status = st.selectbox("Status", ["All"] + STATUSES)
#     with c3:
#         f_priority = st.selectbox("Current priority", ["All"] + PRIORITIES)
#     with c4:
#         f_search = st.text_input("Search title or location")

#     rows = []
#     for i in incidents:
#         if f_hazard != "All" and i["hazard_type"] != f_hazard:
#             continue
#         if f_status != "All" and i["status"] != f_status:
#             continue
#         if f_priority != "All" and current_priority(i) != f_priority:
#             continue
#         if f_search and f_search.lower() not in (
#             (i["title"] + " " + (i["location"] or "")).lower()
#         ):
#             continue
#         rows.append(i)

#     st.caption(f"{len(rows)} of {len(incidents)} reports match the current filters.")
#     if not rows:
#         st.info("No reports match these filters.")
#         return

#     for i in rows:
#         label = (f"{i['report_code']} · {i['title']} — "
#                  f"{current_priority(i)} · {i['status']}")
#         with st.expander(label):
#             render_incident_detail(i, internal=True)


# def duplicates_tab():
#     st.markdown("##### Possible duplicate reports")
#     st.caption(
#         "Similar wording alone does not prove two reports describe the same event. "
#         "Reviewers decide. Confirmed pairs are not shown again."
#     )
#     threshold = st.slider("Similarity threshold", 0.4, 0.95, 0.6, 0.05)
#     st.caption(
#         f"Score = 0.5 × character-sequence similarity + 0.5 × token overlap. "
#         f"Pairs with score ≥ {threshold:.2f} are flagged."
#     )
#     pairs = find_duplicate_pairs(threshold=threshold)
#     if not pairs:
#         st.success("No unresolved candidate pairs above the threshold.")
#         return

#     for idx, p in enumerate(pairs):
#         with st.container(border=True):
#             st.markdown(f"**Combined score: {p['score']:.2f}** · "
#                         f"`{p['a']}` ↔ `{p['b']}`")
#             c1, c2 = st.columns(2)
#             with c1:
#                 st.markdown(f"**{p['a']} — {p['a_title']}**")
#                 st.write(p["a_desc"])
#             with c2:
#                 st.markdown(f"**{p['b']} — {p['b_title']}**")
#                 st.write(p["b_desc"])
#             st.markdown(f"**Location:** {p['location'] or '—'}")
#             b1, b2 = st.columns(2)
#             with b1:
#                 if st.button("Mark as Duplicate", key=f"dup_yes_{idx}"):
#                     ok, err = record_duplicate_review(p["a"], p["b"],
#                                                      "Reviewed — Duplicate")
#                     if ok:
#                         st.success("Marked as duplicate.")
#                     else:
#                         st.error(err)
#             with b2:
#                 if st.button("Mark as Separate Reports", key=f"dup_no_{idx}"):
#                     ok, err = record_duplicate_review(
#                         p["a"], p["b"], "Reviewed — Separate Reports")
#                     if ok:
#                         st.success("Marked as separate.")
#                     else:
#                         st.error(err)


# def page_triage_review(user):
#     st.subheader("Triage Review")
#     st.caption(
#         "Deterministic rule-based triage. Final decisions remain with trained human responders."
#     )
#     conn = get_conn()
#     try:
#         pending = conn.execute(
#             "SELECT * FROM incidents WHERE human_decision='Pending' "
#             "ORDER BY created_at ASC"
#         ).fetchall()
#     finally:
#         conn.close()

#     if not pending:
#         st.success("No reports pending human review.")
#         return

#     st.markdown(f"**{len(pending)} report(s) awaiting human review.**")
#     for i in pending:
#         with st.expander(f"{i['report_code']} · {i['title']} · {current_priority(i)}"):
#             render_incident_detail(i, internal=True)
#             st.markdown("---")
#             with st.form(f"review_form_{i['report_code']}"):
#                 new_priority = st.selectbox(
#                     "Final priority decision", PRIORITIES,
#                     index=PRIORITIES.index(current_priority(i)),
#                     key=f"pr_{i['report_code']}",
#                 )
#                 new_status = st.selectbox(
#                     "Case status", STATUSES,
#                     index=STATUSES.index(i["status"]),
#                     key=f"st_{i['report_code']}",
#                 )
#                 v_index = (VERIFY_STATUSES.index(i["verified_status"])
#                            if i["verified_status"] in VERIFY_STATUSES else 0)
#                 new_verified = st.selectbox(
#                     "Field verification", VERIFY_STATUSES, index=v_index,
#                     key=f"vf_{i['report_code']}",
#                 )
#                 notes = st.text_area(
#                     "Reviewer notes (internal, required)",
#                     key=f"notes_{i['report_code']}",
#                 )
#                 public_note = st.text_area(
#                     "Public status note for reporter (optional)",
#                     key=f"pnote_{i['report_code']}",
#                 )
#                 submitted = st.form_submit_button("Record Review Decision")

#             if submitted:
#                 if not (notes or "").strip():
#                     st.error("Reviewer notes are required to record a decision.")
#                 else:
#                     decision = ("Confirmed"
#                                 if new_priority == i["suggested_priority"]
#                                 else "Changed by reviewer")
#                     conn = get_conn()
#                     try:
#                         conn.execute(
#                             """UPDATE incidents
#                                SET human_decision=?, human_priority=?, status=?,
#                                    reviewer_notes=?, verified_status=?, public_note=?,
#                                    reviewer_user_id=?
#                                WHERE report_code=?""",
#                             (decision, new_priority, new_status, notes.strip(),
#                              new_verified, (public_note or "").strip(),
#                              user["id"], i["report_code"]),
#                         )
#                         conn.commit()
#                     finally:
#                         conn.close()
#                     log_action("incident", i["report_code"], "Human review recorded",
#                                f"decision={decision} priority={new_priority} "
#                                f"status={new_status} verification={new_verified}")
#                     st.success("Review decision saved.")


# def page_inventory(user):
#     st.subheader("Resource Inventory & Matching")
#     st.caption(
#         "Stock figures are local fictional demo quantities. A match is a suggestion; "
#         "stock is deducted only after an Admin explicitly confirms fulfilment."
#     )

#     is_admin = user["role"] == "Admin"
#     if is_admin:
#         tabs = st.tabs(["Inventory", "All Relief Requests", "New Request"])
#         with tabs[0]:
#             inventory_tab(user, editable=True)
#         with tabs[1]:
#             all_requests_tab(user)
#         with tabs[2]:
#             new_request_tab(user)
#     else:
#         tabs = st.tabs(["Inventory", "My Requests", "New Request"])
#         with tabs[0]:
#             inventory_tab(user, editable=False)
#         with tabs[1]:
#             my_requests_tab(user)
#         with tabs[2]:
#             new_request_tab(user)


# def inventory_tab(user, editable: bool):
#     conn = get_conn()
#     try:
#         items = conn.execute("SELECT * FROM inventory ORDER BY item_id").fetchall()
#     finally:
#         conn.close()

#     if items:
#         df = pd.DataFrame([dict(x) for x in items])
#         st.dataframe(df, use_container_width=True, hide_index=True)
#     else:
#         st.info("No inventory items yet.")

#     if not editable:
#         return

#     with st.expander("Adjust stock quantity"):
#         if not items:
#             st.info("Add an item first.")
#             return
#         ids = [x["item_id"] for x in items]
#         sel = st.selectbox("Select item", ids, key="inv_edit_sel")
#         current = next((x for x in items if x["item_id"] == sel), None)
#         new_qty = st.number_input("New quantity", min_value=0,
#                                   value=int(current["quantity"]), step=1,
#                                   key="inv_edit_qty")
#         note = st.text_input("Reason / note (optional)", key="inv_edit_note")
#         if st.button("Update Quantity", key="inv_update_btn"):
#             if not can(user, "manage_inventory"):
#                 st.error("Not authorized.")
#                 return
#             conn = get_conn()
#             try:
#                 merged_notes = current["notes"] or ""
#                 if note.strip():
#                     merged_notes = (merged_notes + " | " + note.strip()).strip(" |")
#                 conn.execute(
#                     "UPDATE inventory SET quantity=?, last_updated=?, notes=? "
#                     "WHERE item_id=?",
#                     (int(new_qty), now_iso(), merged_notes, sel),
#                 )
#                 conn.commit()
#             except sqlite3.IntegrityError as exc:
#                 st.error(f"Update failed: {exc}")
#                 return
#             finally:
#                 conn.close()
#             log_action("inventory", sel, "Quantity updated",
#                        f"{current['quantity']} → {new_qty}. Note: {note or 'n/a'}.")
#             st.success("Inventory updated.")

#     with st.expander("Add new inventory item"):
#         with st.form("add_inventory_item"):
#             iid = st.text_input("Item ID (must be unique)")
#             name = st.text_input("Item name")
#             cat = st.selectbox("Category",
#                                ["Water", "Food", "Medical", "Shelter",
#                                 "Hygiene", "Other"])
#             qty = st.number_input("Quantity", min_value=0, step=1, value=0)
#             unit = st.text_input("Unit", value="units")
#             loc = st.text_input("Fictional storage location")
#             notes = st.text_input("Notes (optional)")
#             add = st.form_submit_button("Add Item")
#         if add:
#             if not can(user, "manage_inventory"):
#                 st.error("Not authorized.")
#                 return
#             if not iid.strip() or not name.strip():
#                 st.error("Item ID and name are required.")
#                 return
#             conn = get_conn()
#             try:
#                 conn.execute(
#                     "INSERT INTO inventory VALUES (?,?,?,?,?,?,?,?)",
#                     (iid.strip(), name.strip(), cat, int(qty), unit, loc,
#                      now_iso(), notes.strip()),
#                 )
#                 conn.commit()
#             except sqlite3.IntegrityError:
#                 st.error("An item with that ID already exists.")
#                 return
#             finally:
#                 conn.close()
#             log_action("inventory", iid.strip(), "Item added",
#                        f"{name} ({qty} {unit}).")
#             st.success(f"Item {iid} added.")


# def _render_request_row(r, show_actions: bool):
#     label = (f"#{r['id']} · {r['item_id']} · requested {r['quantity_requested']} "
#              f"· {r['status']}")
#     with st.expander(label):
#         c1, c2 = st.columns(2)
#         with c1:
#             st.markdown(f"**Incident:** {r['incident_code'] or '—'}")
#             st.markdown(f"**Item:** {r['item_id']}")
#             st.markdown(f"**Requested:** {r['quantity_requested']}")
#             st.markdown(f"**Matchable:** {r['matched_qty']}")
#             st.markdown(f"**Shortfall:** {r['shortfall']}")
#             st.markdown(f"**Suggested location:** {r['storage_location'] or '—'}")
#         with c2:
#             st.markdown(f"**Status:** {r['status']}")
#             st.markdown(f"**Created:** {r['created_at']}")
#             st.markdown(f"**Reviewed:** {r['reviewed_at'] or '—'}")
#             st.markdown(f"**Notes:** {r['notes'] or '—'}")
#         st.markdown(f"**Explanation:** {r['explanation'] or '—'}")

#         if not show_actions:
#             return
#         if r["status"] in ("Pending Review", "Approved"):
#             c1, c2, c3 = st.columns(3)
#             with c1:
#                 if st.button("Approve", key=f"req_appr_{r['id']}"):
#                     ok, err = set_request_status(r["id"], "Approved")
#                     if ok:
#                         st.success("Approved (no stock deducted).")
#                     else:
#                         st.error(err)
#             with c2:
#                 if st.button("Reject", key=f"req_rej_{r['id']}"):
#                     ok, err = set_request_status(r["id"], "Rejected")
#                     if ok:
#                         st.success("Rejected.")
#                     else:
#                         st.error(err)
#             with c3:
#                 if st.button("Mark Fulfilled (deducts stock)",
#                              key=f"req_ful_{r['id']}"):
#                     ok, msg = fulfill_request(r["id"])
#                     if ok:
#                         st.success(msg)
#                     else:
#                         st.error(msg)


# def all_requests_tab(user):
#     if not can(user, "review_relief_requests"):
#         st.error("Access denied.")
#         return
#     conn = get_conn()
#     try:
#         reqs = conn.execute("SELECT * FROM relief_requests ORDER BY id DESC").fetchall()
#     finally:
#         conn.close()
#     if not reqs:
#         st.info("No relief requests yet.")
#         return
#     st.caption("Approving does NOT dispatch resources. Fulfilment deducts stock after confirmation.")
#     for r in reqs:
#         _render_request_row(r, show_actions=True)


# def my_requests_tab(user):
#     conn = get_conn()
#     try:
#         reqs = conn.execute(
#             "SELECT * FROM relief_requests WHERE requested_by_user_id=? ORDER BY id DESC",
#             (user["id"],),
#         ).fetchall()
#     finally:
#         conn.close()
#     if not reqs:
#         st.info("You have not created any relief requests yet.")
#         return
#     st.caption("You can track status here. Only an Admin can approve, reject, or fulfil.")
#     for r in reqs:
#         _render_request_row(r, show_actions=False)


# def new_request_tab(user):
#     if not can(user, "create_relief_request"):
#         st.error("Access denied.")
#         return
#     st.markdown("##### Recommend a resource match (creates a request)")
#     conn = get_conn()
#     try:
#         incidents = conn.execute(
#             "SELECT report_code, title FROM incidents ORDER BY created_at DESC"
#         ).fetchall()
#         items = conn.execute(
#             "SELECT item_id, item_name, unit, quantity FROM inventory ORDER BY item_id"
#         ).fetchall()
#     finally:
#         conn.close()

#     if not items:
#         st.warning("Add an inventory item before creating a request.")
#         return

#     incident_options = ["(none)"] + [
#         f"{x['report_code']} — {x['title']}" for x in incidents
#     ]
#     item_options = [
#         f"{x['item_id']} — {x['item_name']} ({x['quantity']} {x['unit']})"
#         for x in items
#     ]

#     with st.form("new_relief_request"):
#         incident_sel = st.selectbox("Related incident (optional)", incident_options)
#         item_sel = st.selectbox("Requested item", item_options)
#         qty = st.number_input("Requested quantity", min_value=1, step=1, value=1)
#         notes = st.text_area("Request notes (optional)", height=80)
#         submitted = st.form_submit_button("Create Request & Match")

#     if not submitted:
#         return
#     item_id = item_sel.split(" — ")[0].strip()
#     incident_code = ("" if incident_sel == "(none)"
#                      else incident_sel.split(" — ")[0].strip())
#     ok, err, info = create_relief_request(incident_code, item_id, int(qty), notes)
#     if not ok:
#         st.error(err)
#         return
#     st.success(f"Request #{info['id']} created.")
#     st.markdown("**Match calculation:**")
#     st.markdown(
#         f"- Requested: **{info['qty']} {info['unit']}**\n"
#         f"- Available: **{info['available']} {info['unit']}**\n"
#         f"- Potentially matchable: **{info['matchable']} {info['unit']}**\n"
#         f"- Shortfall: **{info['shortfall']} {info['unit']}**\n"
#         f"- Suggested storage location: **{info['location'] or '—'}**\n"
#         f"- Stock is **not** deducted until an Admin marks this request Fulfilled."
#     )

# # ============================================================================
# # ADMIN-ONLY PAGES
# # ============================================================================
# def page_user_management(user):
#     if not can(user, "manage_users"):
#         st.error("Access denied.")
#         return
#     st.subheader("User Management")
#     st.caption("Only Admins can create, deactivate, change role, or reset passwords.")

#     conn = get_conn()
#     try:
#         users = conn.execute("SELECT * FROM users ORDER BY role, username").fetchall()
#     finally:
#         conn.close()

#     st.markdown("#### All users")
#     df = pd.DataFrame([{
#         "ID": u["id"], "Username": u["username"], "Email": u["email"],
#         "Role": u["role"], "Active": "Yes" if u["is_active"] else "No",
#         "Created": u["created_at"], "Last login": u["last_login_at"] or "—",
#     } for u in users])
#     st.dataframe(df, use_container_width=True, hide_index=True)

#     st.markdown("#### Create a new user")
#     with st.form("admin_create_user"):
#         c1, c2 = st.columns(2)
#         with c1:
#             nu = st.text_input("Username")
#             ne = st.text_input("Email")
#             nd = st.text_input("Display name (optional)")
#         with c2:
#             np1 = st.text_input("Password (min 8)", type="password")
#             np2 = st.text_input("Confirm password", type="password")
#             nr = st.selectbox("Role", ["Citizen", "Responder", "Admin"])
#         created = st.form_submit_button("Create User")
#     if created:
#         if np1 != np2:
#             st.error("Passwords do not match.")
#         else:
#             ok, res = register_user(nu.strip(), ne.strip(), np1,
#                                     nd.strip() or None, role=nr, actor=user)
#             if ok:
#                 st.success(f"User created (id={res}).")
#             else:
#                 st.error(res)

#     st.markdown("#### Manage an existing user")
#     if not users:
#         st.info("No users yet.")
#         return
#     target_username = st.selectbox(
#         "Select user", [u["username"] for u in users],
#         key="um_target_username"
#     )
#     target = next(u for u in users if u["username"] == target_username)

#     st.markdown(f"Editing **{target['username']}** "
#                 f"(role: {target['role']}, "
#                 f"active: {'yes' if target['is_active'] else 'no'})")

#     c1, c2, c3 = st.columns(3)
#     with c1:
#         new_role = st.selectbox("New role", ROLES,
#                                 index=ROLES.index(target["role"]),
#                                 key="um_new_role")
#         if st.button("Change Role", key="um_change_role_btn"):
#             conn = get_conn()
#             try:
#                 admin_count = conn.execute(
#                     "SELECT COUNT(*) FROM users WHERE role='Admin' AND is_active=1"
#                 ).fetchone()[0]
#             finally:
#                 conn.close()
#             if (target["role"] == "Admin" and new_role != "Admin"
#                     and admin_count <= 1 and target["is_active"]):
#                 st.error("Cannot demote the last active Admin.")
#             elif new_role == target["role"]:
#                 st.info("Role unchanged.")
#             else:
#                 conn = get_conn()
#                 try:
#                     conn.execute("UPDATE users SET role=? WHERE id=?",
#                                  (new_role, target["id"]))
#                     conn.commit()
#                 finally:
#                     conn.close()
#                 log_action("user", str(target["id"]), "Role changed",
#                            f"{target['username']}: {target['role']} → {new_role}")
#                 st.success(f"Role changed to {new_role}.")
#                 st.rerun()
#     with c2:
#         if target["is_active"]:
#             if st.button("Deactivate User", key="um_deactivate_btn"):
#                 if target["id"] == user["id"]:
#                     st.error("You cannot deactivate your own account.")
#                 else:
#                     conn = get_conn()
#                     try:
#                         admin_count = conn.execute(
#                             "SELECT COUNT(*) FROM users WHERE role='Admin' AND is_active=1"
#                         ).fetchone()[0]
#                         if target["role"] == "Admin" and admin_count <= 1:
#                             st.error("Cannot deactivate the last active Admin.")
#                         else:
#                             conn.execute("UPDATE users SET is_active=0 WHERE id=?",
#                                          (target["id"],))
#                             conn.commit()
#                             log_action("user", str(target["id"]), "User deactivated",
#                                        f"{target['username']} deactivated.")
#                             st.success("User deactivated.")
#                             st.rerun()
#                     finally:
#                         conn.close()
#         else:
#             if st.button("Reactivate User", key="um_reactivate_btn"):
#                 conn = get_conn()
#                 try:
#                     conn.execute("UPDATE users SET is_active=1 WHERE id=?",
#                                  (target["id"],))
#                     conn.commit()
#                 finally:
#                     conn.close()
#                 log_action("user", str(target["id"]), "User reactivated",
#                            f"{target['username']} reactivated.")
#                 st.success("User reactivated.")
#                 st.rerun()
#     with c3:
#         with st.form("um_reset_pw"):
#             new_pw = st.text_input("New password (min 8)", type="password",
#                                    key="um_reset_pw_field")
#             if st.form_submit_button("Reset Password"):
#                 if len(new_pw) < 8:
#                     st.error("Password must be at least 8 characters.")
#                 else:
#                     h, s = hash_password(new_pw)
#                     conn = get_conn()
#                     try:
#                         conn.execute(
#                             "UPDATE users SET password_hash=?, password_salt=? WHERE id=?",
#                             (h, s, target["id"]),
#                         )
#                         conn.commit()
#                     finally:
#                         conn.close()
#                     log_action("user", str(target["id"]), "Password reset by admin",
#                                f"{target['username']} password reset.")
#                     st.success("Password reset.")


# def page_audit_log(user):
#     if not can(user, "view_audit_log"):
#         st.error("Access denied.")
#         return
#     st.subheader("Activity & Audit Log")
#     st.caption("Append-only log. Actor is recorded where available.")
#     conn = get_conn()
#     try:
#         logs = conn.execute(
#             """SELECT al.*, u.username AS actor_username
#                FROM activity_log al
#                LEFT JOIN users u ON al.actor_user_id = u.id
#                ORDER BY al.id DESC"""
#         ).fetchall()
#     finally:
#         conn.close()
#     if not logs:
#         st.info("No activity yet.")
#         return
#     df = pd.DataFrame([{
#         "Time": x["timestamp"],
#         "Actor": x["actor_username"] or (x["actor_role"] or "system"),
#         "Entity": x["entity_type"],
#         "ID": x["entity_id"],
#         "Action": x["action"],
#         "Details": x["details"],
#     } for x in logs])
#     st.dataframe(df, use_container_width=True, hide_index=True)

# # ============================================================================
# # ABOUT / SAFETY
# # ============================================================================
# def page_about(user):
#     st.subheader("About & Safety")
#     st.markdown(
#         "**RAHAT GRID AI** is a *local demonstration prototype* for explainable "
#         "disaster triage and resource coordination. It is **not** a live emergency "
#         "service.\n\n"
#         "- All preloaded incidents, people, locations, inventory quantities and "
#         "metrics are **FICTIONAL DEMO DATA**.\n"
#         "- Triage is **deterministic rule-based logic**, not a trained AI model.\n"
#         "- Duplicate flags are **candidates for human review**, not proof.\n"
#         "- Resource matches do **not** mean resources were dispatched or delivered. "
#         "Inventory is deducted only when an Admin explicitly marks a request as "
#         "**Fulfilled**.\n"
#         "- There is **no** live government, emergency-service, GPS, SMS or helpline "
#         "integration. No external API is called.\n"
#         "- Human responders retain full responsibility for real emergency decisions.\n"
#         "- This application is **not a substitute** for official emergency services "
#         "or field assessment."
#     )

#     st.markdown("---")
#     st.markdown("### Roles")
#     st.markdown(
#         "- **Citizen** — Submit reports, track status of their own reports only.\n"
#         "- **Responder** — Review incidents, record triage/duplicate decisions, "
#         "recommend resource matches (no approval, no user management, no audit log).\n"
#         "- **Admin** — Full administrative access: all incidents, inventory editing, "
#         "relief request approval/fulfilment, user management, audit log, demo reset."
#     )

#     st.markdown("---")
#     st.markdown("### Change my password")
#     with st.form("self_pw_change"):
#         cur = st.text_input("Current password", type="password", key="self_pw_cur")
#         new1 = st.text_input("New password (min 8)", type="password", key="self_pw_new1")
#         new2 = st.text_input("Confirm new password", type="password", key="self_pw_new2")
#         sub = st.form_submit_button("Update Password")
#     if sub:
#         if new1 != new2:
#             st.error("New passwords do not match.")
#         else:
#             ok, err = change_own_password(user["id"], cur, new1)
#             if ok:
#                 st.success("Password updated.")
#             else:
#                 st.error(err or "Failed.")

#     if not can(user, "reset_demo"):
#         return

#     st.markdown("---")
#     st.markdown("### Reset demo data (Admin only)")
#     st.warning(
#         "Deletes ALL incidents, inventory, relief requests, duplicate reviews, and "
#         "activity log entries — then reloads the fictional demo dataset. "
#         "**Users are preserved.** This cannot be undone."
#     )
#     confirm = st.checkbox("I understand that this will reset the local demo database.")
#     if st.button("Reset Demo Data", disabled=not confirm):
#         conn = get_conn()
#         try:
#             c = conn.cursor()
#             c.execute("DELETE FROM incidents")
#             c.execute("DELETE FROM inventory")
#             c.execute("DELETE FROM relief_requests")
#             c.execute("DELETE FROM duplicate_reviews")
#             c.execute("DELETE FROM activity_log")
#             conn.commit()
#         finally:
#             conn.close()
#         conn2 = get_conn()
#         try:
#             seed_demo_data(conn2)
#         finally:
#             conn2.close()
#         log_action("system", "reset", "Demo data reset",
#                    "Admin reset the demo dataset (users preserved).")
#         st.success("Demo data reset. Fresh fictional records have been seeded.")

# # ============================================================================
# # SIDEBAR / MAIN
# # ============================================================================
# def sidebar(user):
#     st.sidebar.markdown(
#         """
#         <div style='padding: 20px 16px 10px 16px;'>
#             <div style='font-size:22px; font-weight:800; letter-spacing:1px;
#                         color:#ffffff;'>RAHAT GRID AI</div>
#             <div style='font-size:11px; color:#9fb3c8; margin-top:4px;
#                         line-height:1.4;'>
#                 Explainable Disaster Triage &amp;<br/>Resource Coordination
#             </div>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )
#     st.sidebar.markdown(
#         """
#         <div style='background:rgba(220,38,38,0.22); color:#fecaca;
#                     border:1px solid rgba(248,113,113,0.4);
#                     padding:8px 10px; border-radius:6px; font-size:10px;
#                     margin:0 12px 16px 12px; letter-spacing:0.5px;
#                     line-height:1.4;'>
#             SIMULATION MODE<br/>FICTIONAL DATA<br/>NOT A LIVE EMERGENCY SERVICE
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )

#     st.sidebar.markdown(
#         f"<div style='margin:0 12px 10px 12px; font-size:12px; color:#cbd5e1;'>"
#         f"Signed in: <b style='color:#fff;'>{user['username']}</b><br>"
#         f"{role_badge(user['role'])}</div>",
#         unsafe_allow_html=True,
#     )
#     st.sidebar.markdown("---")

#     if user["role"] == "Citizen":
#         options = ["My Reports", "About & Safety"]
#     elif user["role"] == "Responder":
#         options = ["Operations Overview", "Incident Reports", "Triage Review",
#                    "Resource Inventory", "About & Safety"]
#     else:
#         options = ["Operations Overview", "Incident Reports", "Triage Review",
#                    "Resource Inventory", "User Management", "Activity & Audit Log",
#                    "About & Safety"]

#     page = st.sidebar.radio("Navigation", options, label_visibility="collapsed")

#     st.sidebar.markdown("---")
#     if st.sidebar.button("Log Out", use_container_width=True):
#         st.session_state.pop("auth_user_id", None)
#         st.rerun()
#     return page


# def main():
#     inject_css()
#     init_db()

#     if check_no_admin():
#         render_header()
#         page_bootstrap_needed()
#         return

#     user = get_current_user()
#     if not user:
#         render_header()
#         page_auth()
#         return

#     page = sidebar(user)
#     render_header(user)

#     if user["role"] == "Citizen":
#         if page == "My Reports":
#             page_my_reports(user)
#         elif page == "About & Safety":
#             page_about(user)
#     elif user["role"] == "Responder":
#         if page == "Operations Overview":
#             page_overview(user)
#         elif page == "Incident Reports":
#             page_incidents(user)
#         elif page == "Triage Review":
#             page_triage_review(user)
#         elif page == "Resource Inventory":
#             page_inventory(user)
#         elif page == "About & Safety":
#             page_about(user)
#     else:
#         if page == "Operations Overview":
#             page_overview(user)
#         elif page == "Incident Reports":
#             page_incidents(user)
#         elif page == "Triage Review":
#             page_triage_review(user)
#         elif page == "Resource Inventory":
#             page_inventory(user)
#         elif page == "User Management":
#             page_user_management(user)
#         elif page == "Activity & Audit Log":
#             page_audit_log(user)
#         elif page == "About & Safety":
#             page_about(user)


# if __name__ == "__main__":
#     main()





"""
RAHAT GRID AI — Explainable Disaster Triage & Resource Coordination
with RBAC (Citizen · Responder · Admin) and interactive UI.

Local prototype. Deterministic rule-based triage. Fictional demo data only.
"""

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import uuid
from datetime import datetime
from difflib import SequenceMatcher

import pandas as pd
import streamlit as st

try:
    import altair as alt
    HAS_ALTAIR = True
except ImportError:
    HAS_ALTAIR = False

# ============================================================================
# CONFIG
# ============================================================================
DB_PATH = "rahat_grid_ai.db"
PBKDF2_ITERATIONS = 200_000

ROLES = ["Citizen", "Responder", "Admin"]
HAZARDS = ["Flood", "Medical", "Food", "Water", "Other"]
STATUSES = ["Under Review", "Awaiting Verification",
            "Assigned for Follow-up", "Resolved / Closed"]
PRIORITIES = ["Urgent Review", "High", "Moderate", "Routine Review"]
VERIFY_STATUSES = ["Unverified", "Verified by reviewer", "Cannot verify"]

PRIORITY_COLORS = {
    "Urgent Review": "#dc2626", "High": "#ea580c",
    "Moderate": "#d97706", "Routine Review": "#16a34a",
}
ROLE_COLORS = {"Citizen": "#0891b2", "Responder": "#7c3aed", "Admin": "#dc2626"}
HAZARD_COLORS = {
    "Flood": "#2563eb", "Medical": "#dc2626", "Food": "#d97706",
    "Water": "#0891b2", "Other": "#64748b",
}

ROLE_PERMISSIONS = {
    "Citizen": {"submit_report": True, "view_own_reports": True,
                "view_all_reports": False, "review_incidents": False,
                "review_duplicates": False, "view_inventory": False,
                "manage_inventory": False, "create_relief_request": False,
                "review_relief_requests": False, "fulfill_relief_request": False,
                "manage_users": False, "view_audit_log": False,
                "reset_demo": False, "view_admin_dashboard": False},
    "Responder": {"submit_report": False, "view_own_reports": False,
                  "view_all_reports": True, "review_incidents": True,
                  "review_duplicates": True, "view_inventory": True,
                  "manage_inventory": False, "create_relief_request": True,
                  "review_relief_requests": False, "fulfill_relief_request": False,
                  "manage_users": False, "view_audit_log": False,
                  "reset_demo": False, "view_admin_dashboard": False},
    "Admin": {k: True for k in [
        "submit_report", "view_own_reports", "view_all_reports",
        "review_incidents", "review_duplicates", "view_inventory",
        "manage_inventory", "create_relief_request", "review_relief_requests",
        "fulfill_relief_request", "manage_users", "view_audit_log",
        "reset_demo", "view_admin_dashboard"]},
}

st.set_page_config(
    page_title="RAHAT GRID AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# CSS
# ============================================================================
def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --navy: #0b1e35; --navy-2: #0e2444; --accent: #2563eb;
            --bg: #f4f6f9; --border: #e2e8f0;
            --success: #16a34a; --warn: #d97706; --danger: #dc2626;
        }
        .stApp { background: var(--bg); }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1e35 0%, #0e2444 100%);
            border-right: 1px solid #1a2f52;
        }
        section[data-testid="stSidebar"] * { color: #e6eef7; }
        section[data-testid="stSidebar"] .stRadio > label {
            color: #cbd5e1 !important; font-weight: 600;
        }
        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
            color: #cbd5e1 !important; padding: 8px 12px; border-radius: 8px;
            transition: all 0.18s ease;
        }
        section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
            background: rgba(37, 99, 235, 0.22); transform: translateX(2px);
        }
        section[data-testid="stSidebar"] hr { border-color: #1a2f52; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.35; }
        }
        @keyframes glow {
            0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.5); }
            50% { box-shadow: 0 0 0 8px rgba(220, 38, 38, 0); }
        }

        .rahat-header {
            background: linear-gradient(135deg, #0b1e35 0%, #1e3a5f 100%);
            padding: 22px 28px; border-radius: 14px; margin-bottom: 18px;
            border: 1px solid #1a2f52;
            box-shadow: 0 6px 24px rgba(15, 23, 42, 0.22);
            animation: fadeIn 0.35s ease-out;
        }
        .rahat-header h1 {
            color: #ffffff; font-size: 26px; font-weight: 800;
            letter-spacing: 1px; margin: 0;
        }
        .rahat-header .sub {
            color: #93b4d6; font-size: 13px; margin-top: 4px;
        }
        .sim-banner {
            display: inline-block; background: rgba(220, 38, 38, 0.20);
            color: #fecaca; border: 1px solid rgba(248, 113, 113, 0.45);
            padding: 4px 12px; border-radius: 6px; font-size: 11px;
            font-weight: 700; letter-spacing: 1.2px; margin-top: 12px;
        }
        .live-dot {
            display: inline-block; width: 8px; height: 8px;
            background: #22c55e; border-radius: 50%;
            margin-right: 6px; animation: pulse 1.8s infinite;
        }

        .metric-card {
            background: white; border-radius: 12px; padding: 16px 18px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(15,23,42,0.06);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            animation: fadeIn 0.4s ease-out;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(15,23,42,0.12);
        }
        .metric-card .mc-label {
            font-size: 11px; text-transform: uppercase;
            letter-spacing: 0.8px; color: #64748b; font-weight: 600;
        }
        .metric-card .mc-value {
            font-size: 30px; font-weight: 800; margin-top: 6px; line-height: 1;
        }
        .metric-card .mc-hint {
            font-size: 11px; color: #94a3b8; margin-top: 6px;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 4px; border-bottom: 1px solid var(--border);
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent; color: #64748b; font-weight: 600;
            padding: 8px 16px; border-radius: 8px 8px 0 0;
            transition: all 0.15s;
        }
        .stTabs [data-baseweb="tab"]:hover { background: rgba(37,99,235,0.06); }
        .stTabs [aria-selected="true"] {
            color: var(--accent) !important; background: white !important;
            border-bottom: 2px solid var(--accent);
        }

        .stButton > button {
            border-radius: 8px; font-weight: 600;
            transition: transform 0.1s ease, box-shadow 0.15s ease;
        }
        .stButton > button:hover { transform: translateY(-1px);
            box-shadow: 0 3px 8px rgba(15,23,42,0.12); }

        .badge {
            display: inline-block; padding: 3px 10px; border-radius: 999px;
            font-size: 11px; font-weight: 700; letter-spacing: 0.3px;
        }
        .status-pill {
            display: inline-block; padding: 3px 10px; border-radius: 6px;
            font-size: 11px; font-weight: 700; letter-spacing: 0.2px;
            background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0;
        }
        .stock-bar-wrap {
            background: #e2e8f0; border-radius: 6px; height: 8px;
            overflow: hidden; margin-top: 4px;
        }
        .stock-bar-fill {
            height: 100%; border-radius: 6px; transition: width 0.4s ease;
        }

        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ============================================================================
# SMALL HELPERS
# ============================================================================
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_report_code() -> str:
    return "INC-" + datetime.now().strftime("%y%m%d") + "-" + uuid.uuid4().hex[:5].upper()


def priority_badge(p: str) -> str:
    color = PRIORITY_COLORS.get(p, "#64748b")
    return (f'<span class="badge" style="background:{color}1a; color:{color}; '
            f'border:1px solid {color}55;">{p}</span>')


def role_badge(role: str) -> str:
    color = ROLE_COLORS.get(role, "#64748b")
    return (f'<span class="badge" style="background:{color}22; color:{color}; '
            f'border:1px solid {color}66;">{role}</span>')


def status_pill(status: str) -> str:
    color = {
        "Under Review": "#2563eb",
        "Awaiting Verification": "#d97706",
        "Assigned for Follow-up": "#7c3aed",
        "Resolved / Closed": "#16a34a",
    }.get(status, "#64748b")
    return (f'<span class="status-pill" style="color:{color}; '
            f'border-color:{color}55; background:{color}1a;">{status}</span>')


def current_priority(i) -> str:
    return i["human_priority"] or i["suggested_priority"]


def _row_get(row, key, default=None):
    try:
        v = row[key]
        return v if v is not None else default
    except (KeyError, IndexError):
        return default


def toast_success(msg: str):
    st.toast(msg, icon="✅")


def toast_error(msg: str):
    st.toast(msg, icon="❌")


def toast_info(msg: str):
    st.toast(msg, icon="ℹ️")


def altair_hbar(counts: dict, keys: list, colors: dict, title="", height=None):
    """Horizontal bar chart with interactive hover. Falls back to CSS bars."""
    total = sum(counts.get(k, 0) for k in keys)
    if total == 0:
        st.info("No data yet.")
        return
    if HAS_ALTAIR:
        df = pd.DataFrame([{"Category": k, "Count": counts.get(k, 0)}
                           for k in keys])
        h = height or max(160, len(keys) * 40)
        chart = alt.Chart(df).mark_bar(
            cornerRadiusTopRight=6, cornerRadiusBottomRight=6
        ).encode(
            x=alt.X("Count:Q", title="Count"),
            y=alt.Y("Category:N", sort=keys, title=""),
            color=alt.Color(
                "Category:N",
                scale=alt.Scale(domain=keys,
                                range=[colors.get(k, "#2563eb") for k in keys]),
                legend=None,
            ),
            tooltip=[alt.Tooltip("Category:N", title=title or "Category"),
                     alt.Tooltip("Count:Q", title="Count")],
        ).properties(height=h)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.markdown(bar_chart_html(counts, keys, colors), unsafe_allow_html=True)


def bar_chart_html(counts, keys, colors=None, accent="#2563eb"):
    total = max(sum(counts.get(k, 0) for k in keys), 1)
    html = ""
    for k in keys:
        n = counts.get(k, 0)
        pct = n / total * 100
        color = (colors or {}).get(k, accent)
        html += (
            f"<div style='margin-bottom:10px;'>"
            f"<div style='display:flex; justify-content:space-between; font-size:12px; "
            f"color:#475569; margin-bottom:4px;'><span>{k}</span><span>{n}</span></div>"
            f"<div style='background:#e2e8f0; border-radius:6px; height:10px; overflow:hidden;'>"
            f"<div style='width:{pct:.1f}%; background:{color}; height:100%;'></div>"
            f"</div></div>"
        )
    return html

# ============================================================================
# DATABASE (unchanged logic; same schema)
# ============================================================================
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def migrate_schema(conn: sqlite3.Connection) -> None:
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
    for ddl in [
        "ALTER TABLE incidents ADD COLUMN owner_user_id INTEGER",
        "ALTER TABLE incidents ADD COLUMN reviewer_user_id INTEGER",
        "ALTER TABLE incidents ADD COLUMN public_note TEXT",
        "ALTER TABLE activity_log ADD COLUMN actor_user_id INTEGER",
        "ALTER TABLE activity_log ADD COLUMN actor_role TEXT",
        "ALTER TABLE relief_requests ADD COLUMN requested_by_user_id INTEGER",
    ]:
        try:
            conn.execute(ddl)
        except sqlite3.OperationalError:
            pass
    conn.commit()


def init_db() -> None:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT, hazard_type TEXT,
            affected_count INTEGER DEFAULT 0,
            danger_trapped INTEGER DEFAULT 0,
            danger_rising_water INTEGER DEFAULT 0,
            danger_injury INTEGER DEFAULT 0,
            danger_other INTEGER DEFAULT 0,
            reporter TEXT, created_at TEXT NOT NULL,
            status TEXT DEFAULT 'Under Review',
            suggested_priority TEXT, priority_reasons TEXT,
            verify_flags TEXT, recommended_action TEXT,
            human_decision TEXT DEFAULT 'Pending',
            human_priority TEXT, reviewer_notes TEXT,
            verified_status TEXT DEFAULT 'Unverified'
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS inventory (
            item_id TEXT PRIMARY KEY, item_name TEXT NOT NULL,
            category TEXT,
            quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            unit TEXT, location TEXT, last_updated TEXT, notes TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS relief_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_code TEXT, item_id TEXT,
            quantity_requested INTEGER NOT NULL CHECK(quantity_requested >= 0),
            notes TEXT, status TEXT DEFAULT 'Pending Review',
            matched_qty INTEGER DEFAULT 0, shortfall INTEGER DEFAULT 0,
            storage_location TEXT, explanation TEXT,
            created_at TEXT, reviewed_at TEXT
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS duplicate_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_a TEXT NOT NULL, report_b TEXT NOT NULL,
            decision TEXT NOT NULL, reviewed_at TEXT,
            UNIQUE(report_a, report_b)
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL, entity_type TEXT, entity_id TEXT,
            action TEXT, details TEXT
        )"""
    )
    conn.commit()
    migrate_schema(conn)
    seed_demo_data(conn)
    conn.close()


def seed_demo_data(conn: sqlite3.Connection) -> None:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM incidents")
    if c.fetchone()[0] > 0:
        return
    demo = [
        dict(title="Floodwater reportedly rising in Maple Lane residential area",
             description=("Residents report water level rising quickly along Maple Lane. "
                          "Some households are unsure whether to evacuate. Fictional scenario."),
             location="Sector 4 – Maple Lane (fictional ward)", hazard_type="Flood",
             affected_count=18, danger_trapped=0, danger_rising_water=1,
             danger_injury=0, danger_other=0, reporter="Demo Resident A"),
        dict(title="People reportedly trapped on roof – Maple Lane",
             description=("Report of three people stranded on a rooftop after floodwater "
                          "rose quickly. Cannot confirm from field. Fictional scenario."),
             location="Maple Lane, Sector 4 (fictional ward)", hazard_type="Flood",
             affected_count=3, danger_trapped=1, danger_rising_water=1,
             danger_injury=0, danger_other=0, reporter="Demo Neighbor B"),
        dict(title="First-aid needed after reported injury",
             description=("A volunteer reports a minor cut that may need first-aid kits "
                          "at a temporary shelter. Fictional scenario."),
             location="Shelter 3, Sector 2 (fictional)", hazard_type="Medical",
             affected_count=1, danger_trapped=0, danger_rising_water=0,
             danger_injury=1, danger_other=0, reporter="Demo Volunteer C"),
        dict(title="Drinking water shortage at temporary shelter",
             description=("Shelter coordinator reports drinking water will run out within "
                          "hours. No immediate danger reported. Fictional scenario."),
             location="Shelter 7, Sector 2 (fictional)", hazard_type="Water",
             affected_count=60, danger_trapped=0, danger_rising_water=0,
             danger_injury=0, danger_other=0, reporter="Demo Coordinator D"),
        dict(title="Food packs requested for flooded neighbourhood",
             description=("Community members request food packs for families in a flooded "
                          "neighbourhood. No immediate danger reported. Fictional scenario."),
             location="Sector 9 – Riverside (fictional)", hazard_type="Food",
             affected_count=45, danger_trapped=0, danger_rising_water=0,
             danger_injury=0, danger_other=0, reporter="Demo Community E"),
        dict(title="Rapidly rising water in Riverside Lane",
             description=("Water reportedly rising fast in Riverside Lane. Residents "
                          "requesting guidance. Fictional scenario."),
             location="Sector 9 – Riverside Lane (fictional)", hazard_type="Flood",
             affected_count=20, danger_trapped=0, danger_rising_water=1,
             danger_injury=0, danger_other=0, reporter="Demo Resident F"),
        dict(title="Floodwater rising near Riverside Lane homes",
             description=("Several homes near Riverside Lane report floodwater rising "
                          "quickly. Fictional scenario."),
             location="Riverside Lane, Sector 9 (fictional)", hazard_type="Flood",
             affected_count=15, danger_trapped=0, danger_rising_water=1,
             danger_injury=0, danger_other=0, reporter="Demo Resident G"),
    ]
    ts = now_iso()
    for d in demo:
        code = new_report_code()
        tr = evaluate_triage(d)
        c.execute(
            """INSERT INTO incidents (
                report_code, title, description, location, hazard_type, affected_count,
                danger_trapped, danger_rising_water, danger_injury, danger_other,
                reporter, created_at, status, suggested_priority, priority_reasons,
                verify_flags, recommended_action, human_decision, human_priority,
                reviewer_notes, verified_status, owner_user_id
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)""",
            (code, d["title"], d["description"], d["location"], d["hazard_type"],
             d["affected_count"], d["danger_trapped"], d["danger_rising_water"],
             d["danger_injury"], d["danger_other"], d["reporter"], ts,
             "Under Review", tr["priority"], json.dumps(tr["reasons"]),
             json.dumps(tr["flags"]), tr["action"], "Pending", tr["priority"],
             "", "Unverified"),
        )
    inventory_seed = [
        ("WTR-001", "Drinking water", "Water", 500, "litres",
         "Depot A – North Fictional Yard", ts, "Bottled and bulk supply"),
        ("FOOD-001", "Food packs", "Food", 120, "packs",
         "Depot A – North Fictional Yard", ts, "Family-sized, ready to eat"),
        ("MED-001", "First-aid kits", "Medical", 40, "kits",
         "Depot B – Central Fictional Yard", ts, "Basic dressings"),
        ("BLK-001", "Blankets", "Shelter", 200, "units",
         "Depot B – Central Fictional Yard", ts, "Thermal"),
        ("HYG-001", "Basic hygiene kits", "Hygiene", 80, "kits",
         "Depot C – South Fictional Yard", ts, "Family hygiene"),
    ]
    for row in inventory_seed:
        c.execute("INSERT OR IGNORE INTO inventory VALUES (?,?,?,?,?,?,?,?)", row)
    c.execute(
        "INSERT INTO activity_log (timestamp, entity_type, entity_id, action, details, "
        "actor_user_id, actor_role) VALUES (?,?,?,?,?,NULL,'system')",
        (ts, "system", "seed", "Demo data seeded",
         "Fictional demonstration dataset loaded."),
    )
    conn.commit()


def log_activity(entity_type, entity_id, action, details,
                 actor_user_id=None, actor_role=None):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO activity_log (timestamp, entity_type, entity_id, action, "
            "details, actor_user_id, actor_role) VALUES (?,?,?,?,?,?,?)",
            (now_iso(), entity_type, entity_id, action, details,
             actor_user_id, actor_role),
        )
        conn.commit()
    finally:
        conn.close()


def log_action(entity_type, entity_id, action, details):
    user = get_current_user()
    log_activity(entity_type, entity_id, action, details,
                 actor_user_id=user["id"] if user else None,
                 actor_role=user["role"] if user else "system")

# ============================================================================
# AUTH (unchanged logic)
# ============================================================================
def hash_password(password: str):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return digest.hex(), salt.hex()


def verify_password(password, stored_hash_hex, stored_salt_hex):
    try:
        salt = bytes.fromhex(stored_salt_hex)
    except (ValueError, TypeError):
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return hmac.compare_digest(digest.hex(), stored_hash_hex or "")


def validate_registration(username, email, password):
    if not username or len(username) < 3:
        return "Username must be at least 3 characters."
    if not re.match(r"^[A-Za-z0-9_.-]{3,40}$", username):
        return "Username may only contain letters, digits, dot, dash, underscore (3–40 chars)."
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return "Please enter a valid email address."
    if not password or len(password) < 8:
        return "Password must be at least 8 characters."
    return None


def register_user(username, email, password, display_name=None,
                  role="Citizen", actor=None):
    if role not in ROLES:
        return False, "Invalid role."
    if role in ("Responder", "Admin"):
        if not actor or actor.get("role") != "Admin":
            return False, "Only an Admin can create Responder or Admin accounts."
    err = validate_registration(username, email, password)
    if err:
        return False, err
    conn = get_conn()
    try:
        if conn.execute(
            "SELECT 1 FROM users WHERE LOWER(username)=LOWER(?) OR LOWER(email)=LOWER(?)",
            (username, email),
        ).fetchone():
            return False, "Username or email already in use."
        h, s = hash_password(password)
        cur = conn.execute(
            "INSERT INTO users (username, email, password_hash, password_salt, "
            "role, display_name, is_active, created_at) VALUES (?,?,?,?,?,?,1,?)",
            (username, email, h, s, role, display_name or username, now_iso()),
        )
        conn.commit()
        uid = cur.lastrowid
    finally:
        conn.close()
    log_action("user", str(uid), "User created", f"username={username} role={role}")
    return True, uid


def authenticate(identifier, password):
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(username)=LOWER(?) OR LOWER(email)=LOWER(?)",
            (identifier, identifier),
        ).fetchone()
        if not row:
            log_activity("auth", identifier, "Login failed",
                         "Unknown username/email", actor_role="anon")
            return None, "Invalid credentials."
        user = dict(row)
        if not user["is_active"]:
            log_activity("auth", str(user["id"]), "Login failed",
                         "Account deactivated", actor_role="anon")
            return None, "Account is deactivated. Contact an administrator."
        if not verify_password(password, user["password_hash"], user["password_salt"]):
            log_activity("auth", str(user["id"]), "Login failed",
                         "Incorrect password", actor_role="anon")
            return None, "Invalid credentials."
        conn.execute("UPDATE users SET last_login_at=? WHERE id=?",
                     (now_iso(), user["id"]))
        conn.commit()
    finally:
        conn.close()
    log_activity("auth", str(user["id"]), "Login success", f"role={user['role']}",
                 actor_user_id=user["id"], actor_role=user["role"])
    return user, None


def get_current_user():
    uid = st.session_state.get("auth_user_id")
    if not uid:
        return None
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id=? AND is_active=1", (uid,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        st.session_state.pop("auth_user_id", None)
        return None
    return dict(row)


def can(user, action):
    if not user:
        return False
    return ROLE_PERMISSIONS.get(user["role"], {}).get(action, False)


def change_own_password(user_id, old_password, new_password):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            return False, "User not found."
        if not verify_password(old_password, row["password_hash"], row["password_salt"]):
            return False, "Current password is incorrect."
        if len(new_password or "") < 8:
            return False, "New password must be at least 8 characters."
        h, s = hash_password(new_password)
        conn.execute(
            "UPDATE users SET password_hash=?, password_salt=? WHERE id=?",
            (h, s, user_id),
        )
        conn.commit()
    finally:
        conn.close()
    log_action("user", str(user_id), "Password changed",
               "User changed own password.")
    return True, None

# ============================================================================
# TRIAGE ENGINE (unchanged)
# ============================================================================
def evaluate_triage(d):
    score, reasons, flags = 0, [], []
    if d.get("danger_trapped"):
        score += 50
        reasons.append("Reported people trapped in a dangerous situation.")
    if d.get("danger_rising_water"):
        score += 25
        reasons.append("Reported rapidly rising floodwater.")
    if d.get("danger_injury"):
        score += 30
        reasons.append("Reported serious injury or immediate medical danger.")
    if d.get("danger_other"):
        score += 15
        reasons.append("Other urgent circumstance reported.")

    danger_count = sum(1 for k in ("danger_trapped", "danger_rising_water",
                                   "danger_injury", "danger_other") if d.get(k))
    if danger_count >= 2:
        score += 10
        reasons.append(f"Multiple danger indicators reported ({danger_count}).")

    loc = (d.get("location") or "").strip()
    desc = (d.get("description") or "").lower()
    vague = ("somewhere", "unknown", "not sure", "maybe", "possibly", "near")
    if not loc or len(loc) < 6:
        flags.append("Location text is missing or very brief — verify before routing.")
    if loc and any(w in loc.lower() for w in vague):
        flags.append("Location contains uncertain language — verify.")
    if desc and any(w in desc for w in vague):
        flags.append("Description contains uncertain language — verify.")
    if int(d.get("affected_count", 0) or 0) == 0:
        flags.append("Reported number of affected people is 0 or unspecified — verify scale.")
    if not reasons:
        reasons.append("No immediate-danger indicators reported in the submission.")

    if score >= 60:
        priority = "Urgent Review"
    elif score >= 35:
        priority = "High"
    elif score >= 15:
        priority = "Moderate"
    else:
        priority = "Routine Review"

    action = {
        "Urgent Review": ("Human reviewer should verify immediately with the reporter "
                          "and escalate to the on-duty coordinator."),
        "High": ("Reviewer should verify details and prepare a follow-up plan within "
                 "the next review cycle."),
        "Moderate": ("Reviewer should confirm the report and route to the appropriate "
                     "relief track."),
        "Routine Review": "Log for routine review; confirm details before routing.",
    }[priority]

    if d.get("hazard_type") in ("Food", "Water") and danger_count == 0:
        reasons.append("Basic-needs request without immediate-danger indicators — "
                       "route to logistics review; do not disregard.")

    return {"score": score, "priority": priority, "reasons": reasons,
            "flags": flags, "action": action}

# ============================================================================
# DUPLICATE DETECTION (unchanged)
# ============================================================================
def _combined_text(t, d, l):
    return " ".join(x for x in [t or "", d or "", l or ""] if x).lower()


def similarity_score(a, b):
    seq = SequenceMatcher(None, a, b).ratio()
    ta = set(re.findall(r"\w+", a))
    tb = set(re.findall(r"\w+", b))
    overlap = (len(ta & tb) / len(ta | tb)) if (ta and tb) else 0.0
    return 0.5 * seq + 0.5 * overlap


def find_duplicate_pairs(threshold=0.6):
    conn = get_conn()
    try:
        incidents = conn.execute(
            "SELECT report_code, title, description, location FROM incidents"
        ).fetchall()
        reviewed = conn.execute("SELECT report_a, report_b FROM duplicate_reviews").fetchall()
    finally:
        conn.close()
    reviewed_set = {tuple(sorted((r["report_a"], r["report_b"]))) for r in reviewed}
    pairs = []
    for i in range(len(incidents)):
        for j in range(i + 1, len(incidents)):
            a, b = incidents[i], incidents[j]
            key = tuple(sorted((a["report_code"], b["report_code"])))
            if key in reviewed_set:
                continue
            s = similarity_score(
                _combined_text(a["title"], a["description"], a["location"]),
                _combined_text(b["title"], b["description"], b["location"]),
            )
            if s >= threshold:
                pairs.append({
                    "a": a["report_code"], "b": b["report_code"],
                    "a_title": a["title"], "b_title": b["title"],
                    "a_desc": a["description"], "b_desc": b["description"],
                    "location": a["location"] or b["location"],
                    "score": round(s, 3),
                })
    pairs.sort(key=lambda x: -x["score"])
    return pairs


def record_duplicate_review(a, b, decision):
    user = get_current_user()
    if not user or not can(user, "review_duplicates"):
        return False, "Not authorized."
    a, b = sorted((a, b))
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO duplicate_reviews (report_a, report_b, "
            "decision, reviewed_at) VALUES (?,?,?,?)",
            (a, b, decision, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()
    log_action("duplicate_review", f"{a}|{b}", decision,
               f"Pair reviewed: {a} ↔ {b} — {decision}.")
    return True, None

# ============================================================================
# RESOURCE MATCHING (unchanged logic)
# ============================================================================
def compute_match(item_id, qty):
    conn = get_conn()
    try:
        item = conn.execute("SELECT * FROM inventory WHERE item_id=?", (item_id,)).fetchone()
    finally:
        conn.close()
    if not item:
        return None
    available = int(item["quantity"])
    return {"available": available, "matchable": min(available, qty),
            "shortfall": max(0, qty - available), "location": item["location"],
            "unit": item["unit"], "item_name": item["item_name"]}


def create_relief_request(incident_code, item_id, qty, notes):
    user = get_current_user()
    if not user or not can(user, "create_relief_request"):
        return False, "Not authorized to create relief requests.", None
    if qty <= 0:
        return False, "Requested quantity must be positive.", None
    match = compute_match(item_id, int(qty))
    if match is None:
        return False, "Item not found in inventory.", None
    explanation = (
        f"Requested {qty} {match['unit']} of {match['item_name']}. "
        f"Available at {match['location'] or 'unspecified location'}: "
        f"{match['available']} {match['unit']}. "
        f"Potentially matchable: {match['matchable']} {match['unit']}. "
        f"Shortfall: {match['shortfall']} {match['unit']}. "
        f"Stock is NOT deducted until an Admin marks this request as Fulfilled."
    )
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO relief_requests
               (incident_code, item_id, quantity_requested, notes, status,
                matched_qty, shortfall, storage_location, explanation,
                created_at, reviewed_at, requested_by_user_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,NULL,?)""",
            (incident_code or "", item_id, int(qty), notes.strip(),
             "Pending Review", match["matchable"], match["shortfall"],
             match["location"], explanation, now_iso(), user["id"]),
        )
        req_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    log_action("relief_request", str(req_id), "Request created",
               f"Requested {qty} {match['unit']} of {item_id}. "
               f"Matchable: {match['matchable']}. Shortfall: {match['shortfall']}.")
    return True, None, {"id": req_id, **match, "qty": qty}


def set_request_status(req_id, new_status):
    user = get_current_user()
    if not user or not can(user, "review_relief_requests"):
        return False, "Not authorized."
    if new_status not in ("Approved", "Rejected"):
        return False, "Invalid status change."
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE relief_requests SET status=?, reviewed_at=? WHERE id=?",
            (new_status, now_iso(), req_id),
        )
        conn.commit()
    finally:
        conn.close()
    log_action("relief_request", str(req_id), new_status,
               f"Request marked {new_status} (no stock deducted).")
    return True, None


def fulfill_request(req_id):
    user = get_current_user()
    if not user or not can(user, "fulfill_relief_request"):
        return False, "Not authorized."
    conn = get_conn()
    try:
        req = conn.execute(
            "SELECT * FROM relief_requests WHERE id=?", (req_id,)
        ).fetchone()
        if not req:
            return False, "Request not found."
        if req["status"] == "Fulfilled":
            return False, "Request already fulfilled."
        item = conn.execute(
            "SELECT * FROM inventory WHERE item_id=?", (req["item_id"],)
        ).fetchone()
        if not item:
            return False, "Inventory item not found."
        deduct = min(int(req["matched_qty"]), int(item["quantity"]))
        if deduct <= 0:
            return False, "No stock available to deduct."
        new_qty = int(item["quantity"]) - deduct
        conn.execute(
            "UPDATE inventory SET quantity=?, last_updated=? WHERE item_id=?",
            (new_qty, now_iso(), req["item_id"]),
        )
        conn.execute(
            "UPDATE relief_requests SET status='Fulfilled', reviewed_at=? WHERE id=?",
            (now_iso(), req_id),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        return False, f"Deduction failed: {exc}"
    finally:
        conn.close()
    log_action("relief_request", str(req_id), "Fulfilled",
               f"Deducted {deduct} {item['unit']} of {item['item_name']} "
               f"from inventory {req['item_id']}. Remaining: {new_qty}.")
    return True, f"Deducted {deduct} {item['unit']}. Remaining: {new_qty}."

# ============================================================================
# UI COMPONENTS (enhanced)
# ============================================================================
def render_header(user=None):
    clock = datetime.now().strftime("%H:%M:%S")
    badge = ""
    if user:
        badge = (
            f"<div style='margin-top:12px; display:flex; gap:12px; "
            f"align-items:center; flex-wrap:wrap;'>"
            f"<span style='font-size:12px; color:#93b4d6;'>"
            f"<span class='live-dot'></span>Signed in as "
            f"<b style='color:#fff;'>{user['username']}</b></span>"
            f"{role_badge(user['role'])}"
            f"<span style='font-size:11px; color:#64748b;'>"
            f"Local time {clock}</span></div>"
        )
    st.markdown(
        f"""
        <div class="rahat-header">
            <h1>RAHAT GRID AI</h1>
            <div class="sub">Explainable Disaster Triage &amp; Resource Coordination</div>
            <span class="sim-banner">SIMULATION MODE · FICTIONAL DATA · NOT A LIVE EMERGENCY SERVICE</span>
            {badge}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, hint=None, color="#2563eb", icon="◈"):
    hint_html = (f"<div class='mc-hint'>{hint}</div>" if hint else "")
    st.markdown(
        f"""
        <div class="metric-card">
            <div style="display:flex; justify-content:space-between;
                        align-items:flex-start;">
                <div class="mc-label">{label}</div>
                <span style="font-size:16px; opacity:0.5;">{icon}</span>
            </div>
            <div class="mc-value" style="color:{color};">{value}</div>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_incident_detail(i, internal=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Description:** {i['description']}")
        st.markdown(f"**Location:** {i['location'] or '—'}")
        st.markdown(f"**Hazard type:** {i['hazard_type']}")
        st.markdown(f"**Reported affected people:** {i['affected_count']}")
        if internal:
            st.markdown(f"**Reporter (reported):** {i['reporter'] or '—'}")
            st.markdown(f"**Created:** {i['created_at']}")
    with col2:
        st.markdown("**Status:** " + status_pill(i["status"]), unsafe_allow_html=True)
        st.markdown(f"**Verified:** {i['verified_status']}")
        st.markdown(f"**Human decision:** {i['human_decision']}")

    st.markdown("---")
    suggested_html = priority_badge(i["suggested_priority"])
    final_html = (priority_badge(i["human_priority"])
                  if i["human_priority"] and i["human_priority"] != i["suggested_priority"]
                  else "")
    st.markdown("**Suggested priority:** " + suggested_html +
                (" · **Human final:** " + final_html if final_html else ""),
                unsafe_allow_html=True)

    reasons = json.loads(i["priority_reasons"] or "[]")
    st.markdown("**Why this was flagged:**")
    for r in reasons:
        st.markdown(f"- {r}")

    flags = json.loads(i["verify_flags"] or "[]")
    if flags and internal:
        st.markdown("**Information to verify:**")
        for f in flags:
            st.markdown(f"- {f}")

    if internal:
        st.markdown(f"**Recommended next step:** {i['recommended_action']}")
        if i["reviewer_notes"]:
            st.markdown(f"**Reviewer notes (internal):** {i['reviewer_notes']}")

    if _row_get(i, "public_note"):
        st.markdown(f"**Public status note for reporter:** {i['public_note']}")

# ============================================================================
# AUTH PAGE
# ============================================================================
def page_bootstrap_needed():
    st.markdown(
        "### ⚙️ System setup required\n\n"
        "No Admin account exists yet. This application does **not** auto-promote "
        "the first person who registers. To create the first Admin, run the "
        "bootstrap script once from the project folder:\n\n"
        "```powershell\npython bootstrap_demo.py\n```\n\n"
        "Or provide custom credentials:\n\n"
        "```powershell\n"
        "python bootstrap_demo.py --admin-user myname --admin-email me@x.com "
        "--admin-password \"MyStr0ng!pw\"\n```\n\n"
        "Then refresh this page and sign in."
    )
    if st.button("🔄 I've run the bootstrap — reload"):
        st.rerun()


def page_auth():
    tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Register (Citizen)"])

    with tab_login:
        with st.form("login_form"):
            ident = st.text_input("Username or email",
                                  placeholder="demo_admin or demo_admin@example.local")
            pw = st.text_input("Password", type="password",
                               placeholder="Enter your password")
            submit = st.form_submit_button("Sign In", use_container_width=True)
        if submit:
            if not ident or not pw:
                toast_error("Enter both username/email and password.")
            else:
                user, err = authenticate(ident.strip(), pw)
                if err:
                    toast_error(err)
                else:
                    st.session_state["auth_user_id"] = user["id"]
                    toast_success(f"Welcome, {user['username']}!")
                    st.rerun()

    with tab_register:
        st.info(
            "Self-registration creates a **Citizen** account only. Responders and "
            "Admins are provisioned by an existing Admin."
        )
        with st.form("register_form"):
            c1, c2 = st.columns(2)
            with c1:
                u = st.text_input("Username", placeholder="3–40 chars: letters, digits, . _ -",
                                  help="Letters, digits, dot, dash, underscore only.")
                e = st.text_input("Email")
            with c2:
                d = st.text_input("Display name (optional)")
                p1 = st.text_input("Password (min 8 chars)", type="password")
            p2 = st.text_input("Confirm password", type="password")
            submit = st.form_submit_button("Create Account", use_container_width=True)
        if submit:
            if p1 != p2:
                toast_error("Passwords do not match.")
            else:
                ok, res = register_user(u.strip(), e.strip(), p1,
                                        d.strip() or None, role="Citizen")
                if ok:
                    toast_success("Account created. You may now sign in.")
                else:
                    toast_error(res)


def check_no_admin():
    conn = get_conn()
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role='Admin' AND is_active=1"
        ).fetchone()[0]
    finally:
        conn.close()
    return n == 0

# ============================================================================
# CITIZEN DASHBOARD
# ============================================================================
def page_my_reports(user):
    st.subheader("📋 My Reports")
    st.caption("You can only see reports you submitted. Status updates come from responders/admins.")

    conn = get_conn()
    try:
        my_reports = conn.execute(
            "SELECT * FROM incidents WHERE owner_user_id=? ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()
    finally:
        conn.close()

    total = len(my_reports)
    pending = sum(1 for r in my_reports if r["human_decision"] == "Pending")
    resolved = sum(1 for r in my_reports if r["status"] == "Resolved / Closed")

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("My Reports", total, "Submitted by you", "#2563eb", "📋")
    with c2:
        metric_card("Awaiting Review", pending, "Not yet reviewed", "#ea580c", "⏳")
    with c3:
        metric_card("Resolved", resolved, "Closed cases", "#16a34a", "✅")

    st.markdown("---")
    tab_new, tab_mine = st.tabs(["➕ Submit New Report", "📂 My Submitted Reports"])

    with tab_new:
        with st.form("citizen_submit_report"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Report title *", placeholder="Short, clear title")
                location = st.text_input("Fictional ward / sector or location text")
                hazard = st.selectbox("Hazard type", HAZARDS)
                affected = st.number_input("Number of people reported affected",
                                           min_value=0, step=1, value=0)
            with col2:
                description = st.text_area("Detailed description *", height=140,
                                           placeholder="What happened? What do you see?")
                reporter_alias = st.text_input("Reporter name or alias (optional)")
            st.markdown("**Immediate-danger indicators (as reported):**")
            dc1, dc2, dc3, dc4 = st.columns(4)
            with dc1:
                d_trapped = st.checkbox("People reported trapped")
            with dc2:
                d_water = st.checkbox("Rapidly rising water")
            with dc3:
                d_injury = st.checkbox("Reported injury / medical danger")
            with dc4:
                d_other = st.checkbox("Other urgent circumstance")
            submitted = st.form_submit_button("🚨 Submit Report",
                                              use_container_width=True, type="primary")

        if submitted:
            title = (title or "").strip()
            description = (description or "").strip()
            if not title:
                toast_error("Title is required.")
            elif not description:
                toast_error("Description is required.")
            elif affected < 0:
                toast_error("Affected count cannot be negative.")
            else:
                payload = dict(title=title, description=description,
                               location=(location or "").strip(),
                               hazard_type=hazard, affected_count=int(affected),
                               danger_trapped=int(d_trapped),
                               danger_rising_water=int(d_water),
                               danger_injury=int(d_injury),
                               danger_other=int(d_other))
                tr = evaluate_triage(payload)
                code = new_report_code()
                conn = get_conn()
                try:
                    conn.execute(
                        """INSERT INTO incidents (
                            report_code, title, description, location, hazard_type,
                            affected_count, danger_trapped, danger_rising_water,
                            danger_injury, danger_other, reporter, created_at, status,
                            suggested_priority, priority_reasons, verify_flags,
                            recommended_action, human_decision, human_priority,
                            reviewer_notes, verified_status, owner_user_id
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (code, title, description, payload["location"], hazard,
                         int(affected), int(d_trapped), int(d_water), int(d_injury),
                         int(d_other), (reporter_alias or "").strip(), now_iso(),
                         "Under Review", tr["priority"], json.dumps(tr["reasons"]),
                         json.dumps(tr["flags"]), tr["action"], "Pending",
                         tr["priority"], "", "Unverified", user["id"]),
                    )
                    conn.commit()
                finally:
                    conn.close()
                log_action("incident", code, "Report submitted",
                           f"title={title} hazard={hazard} suggested={tr['priority']}")
                toast_success(f"Report {code} submitted · Suggested: {tr['priority']}")
                st.success(
                    f"✅ Report submitted. Report ID: **{code}** · "
                    f"Suggested priority: **{tr['priority']}** (pending human review)."
                )

    with tab_mine:
        if not my_reports:
            st.info("You have not submitted any reports yet.")
            return
        for i in my_reports:
            with st.expander(
                f"{i['report_code']} · {i['title']} · "
                f"{current_priority(i)} · {i['status']}"
            ):
                render_incident_detail(i, internal=False)

# ============================================================================
# SHARED PAGES
# ============================================================================
def page_overview(user):
    st.subheader("📊 Operations Overview")
    top1, top2 = st.columns([3, 1])
    with top2:
        if st.button("🔄 Refresh data", use_container_width=True):
            st.session_state["last_refresh"] = now_iso()
            st.rerun()
        st.caption(f"Last refreshed: {st.session_state.get('last_refresh', now_iso())}")

    conn = get_conn()
    try:
        incidents = conn.execute("SELECT * FROM incidents").fetchall()
        inventory = conn.execute("SELECT * FROM inventory").fetchall()
        activity = conn.execute(
            "SELECT * FROM activity_log ORDER BY id DESC LIMIT 10"
        ).fetchall()
    finally:
        conn.close()

    open_inc = [i for i in incidents if i["status"] != "Resolved / Closed"]
    urgent = [i for i in open_inc if current_priority(i) == "Urgent Review"]
    pending = [i for i in incidents if i["human_decision"] == "Pending"]
    dup_pairs = find_duplicate_pairs()
    total_stock = sum(int(i["quantity"]) for i in inventory)
    low_stock = [i for i in inventory if int(i["quantity"]) < 20]

    cols = st.columns(5)
    cards = [
        ("Open Incidents", len(open_inc), "Excluding closed", "#2563eb", "🎯"),
        ("Urgent Review", len(urgent), "Current = Urgent", "#dc2626", "🚨"),
        ("Awaiting Review", len(pending), "Human decision pending", "#ea580c", "⏳"),
        ("Possible Duplicates", len(dup_pairs), "Unresolved pairs", "#d97706", "🔍"),
        ("Total Stock Units", total_stock,
         f"{len(inventory)} items · {len(low_stock)} low", "#16a34a", "📦"),
    ]
    for c, (label, value, hint, color, icon) in zip(cols, cards):
        with c:
            metric_card(label, value, hint, color, icon)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    colA, colB = st.columns(2)
    with colA:
        with st.container(border=True):
            st.markdown("#### Priority Distribution")
            counts = {}
            for i in open_inc:
                p = current_priority(i)
                counts[p] = counts.get(p, 0) + 1
            altair_hbar(counts, PRIORITIES, PRIORITY_COLORS, "Priority")
    with colB:
        with st.container(border=True):
            st.markdown("#### Hazard Mix")
            haz = {}
            for i in open_inc:
                haz[i["hazard_type"]] = haz.get(i["hazard_type"], 0) + 1
            altair_hbar(haz, HAZARDS, HAZARD_COLORS, "Hazard")

    with st.container(border=True):
        st.markdown("#### Recent Incidents")
        if incidents:
            df = pd.DataFrame([{
                "Report": i["report_code"],
                "Title": (i["title"][:64] + "…") if len(i["title"]) > 64 else i["title"],
                "Hazard": i["hazard_type"],
                "Priority": current_priority(i),
                "Status": i["status"],
                "Created": i["created_at"],
            } for i in incidents[:10]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No incidents recorded yet.")

    with st.container(border=True):
        st.markdown("#### Recent Activity")
        if activity:
            for a in activity:
                st.markdown(
                    f"<div style='padding:8px 0; border-bottom:1px solid #eef2f7; "
                    f"font-size:13px;'><span style='color:#64748b;'>{a['timestamp']}</span>"
                    f" · <b>{a['action']}</b> · "
                    f"<span style='color:#475569;'>{a['details']}</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No activity logged yet.")


def page_incidents(user):
    st.subheader("🚨 Incident Reports")
    tabs = st.tabs(["📋 Browse Reports", "🔍 Possible Duplicates"])
    with tabs[0]:
        browse_reports(user)
    with tabs[1]:
        duplicates_tab()


def browse_reports(user):
    conn = get_conn()
    try:
        incidents = conn.execute(
            "SELECT * FROM incidents ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()

    c1, c2, c3 = st.columns([2, 2, 2])
    with c1:
        f_hazard = st.multiselect("Hazard", HAZARDS, default=[])
    with c2:
        f_status = st.multiselect("Status", STATUSES, default=[])
    with c3:
        f_priority = st.multiselect("Priority", PRIORITIES, default=[])
    f_search = st.text_input("🔎 Search title or location", placeholder="Type to filter...")

    rows = []
    for i in incidents:
        if f_hazard and i["hazard_type"] not in f_hazard:
            continue
        if f_status and i["status"] not in f_status:
            continue
        if f_priority and current_priority(i) not in f_priority:
            continue
        if f_search and f_search.lower() not in (
            (i["title"] + " " + (i["location"] or "")).lower()
        ):
            continue
        rows.append(i)

    st.caption(f"**{len(rows)}** of **{len(incidents)}** reports match the current filters.")
    if not rows:
        st.info("No reports match these filters.")
        return

    for i in rows:
        label = (f"{i['report_code']} · {i['title']} — "
                 f"{current_priority(i)} · {i['status']}")
        with st.expander(label):
            render_incident_detail(i, internal=True)


def duplicates_tab():
    st.markdown("##### Possible duplicate reports")
    st.caption(
        "Similar wording does **not** prove two reports describe the same event. "
        "Reviewers decide. Confirmed pairs are hidden."
    )
    threshold = st.slider("Similarity threshold", 0.4, 0.95, 0.6, 0.05,
                          help="Score = 0.5 × character-sequence + 0.5 × token overlap.")
    pairs = find_duplicate_pairs(threshold=threshold)
    if not pairs:
        st.success("No unresolved candidate pairs above the threshold.")
        return
    st.caption(f"**{len(pairs)}** candidate pair(s) above threshold.")

    for idx, p in enumerate(pairs):
        with st.container(border=True):
            st.markdown(
                f"**Similarity: {p['score']:.2f}** · "
                f"`{p['a']}` ↔ `{p['b']}`"
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**{p['a']}** — {p['a_title']}")
                st.write(p["a_desc"])
            with c2:
                st.markdown(f"**{p['b']}** — {p['b_title']}")
                st.write(p["b_desc"])
            st.markdown(f"**Location:** {p['location'] or '—'}")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("✅ Mark as Duplicate", key=f"dup_yes_{idx}",
                             use_container_width=True):
                    ok, err = record_duplicate_review(p["a"], p["b"],
                                                     "Reviewed — Duplicate")
                    if ok:
                        toast_success("Marked as duplicate.")
                        st.rerun()
                    else:
                        toast_error(err)
            with b2:
                if st.button("🔀 Mark as Separate Reports", key=f"dup_no_{idx}",
                             use_container_width=True):
                    ok, err = record_duplicate_review(
                        p["a"], p["b"], "Reviewed — Separate Reports")
                    if ok:
                        toast_success("Marked as separate.")
                        st.rerun()
                    else:
                        toast_error(err)


def page_triage_review(user):
    st.subheader("🧠 Triage Review")
    st.caption("Deterministic rule-based triage. Final decisions remain with trained human responders.")

    conn = get_conn()
    try:
        pending = conn.execute(
            "SELECT * FROM incidents WHERE human_decision='Pending' ORDER BY created_at ASC"
        ).fetchall()
        total_reviewed = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE human_decision != 'Pending'"
        ).fetchone()[0]
    finally:
        conn.close()

    total = len(pending) + total_reviewed
    if total > 0:
        progress = total_reviewed / total
        st.markdown(
            f"**Progress:** {total_reviewed} of {total} reports reviewed "
            f"({progress*100:.0f}%)"
        )
        st.progress(progress)

    if not pending:
        st.success("✨ No reports pending human review.")
        return

    st.markdown(f"**{len(pending)} report(s) awaiting human review.**")
    for i in pending:
        with st.expander(f"{i['report_code']} · {i['title']} · {current_priority(i)}"):
            render_incident_detail(i, internal=True)
            st.markdown("---")
            with st.form(f"review_form_{i['report_code']}"):
                new_priority = st.selectbox(
                    "Final priority decision", PRIORITIES,
                    index=PRIORITIES.index(current_priority(i)),
                    key=f"pr_{i['report_code']}",
                )
                new_status = st.selectbox(
                    "Case status", STATUSES,
                    index=STATUSES.index(i["status"]),
                    key=f"st_{i['report_code']}",
                )
                v_index = (VERIFY_STATUSES.index(i["verified_status"])
                           if i["verified_status"] in VERIFY_STATUSES else 0)
                new_verified = st.selectbox(
                    "Field verification", VERIFY_STATUSES, index=v_index,
                    key=f"vf_{i['report_code']}",
                )
                notes = st.text_area(
                    "Reviewer notes (internal, required)",
                    key=f"notes_{i['report_code']}",
                )
                public_note = st.text_area(
                    "Public status note for reporter (optional)",
                    key=f"pnote_{i['report_code']}",
                )
                submitted = st.form_submit_button("💾 Record Review Decision",
                                                  use_container_width=True,
                                                  type="primary")

            if submitted:
                if not (notes or "").strip():
                    toast_error("Reviewer notes are required to record a decision.")
                else:
                    decision = ("Confirmed"
                                if new_priority == i["suggested_priority"]
                                else "Changed by reviewer")
                    conn = get_conn()
                    try:
                        conn.execute(
                            """UPDATE incidents
                               SET human_decision=?, human_priority=?, status=?,
                                   reviewer_notes=?, verified_status=?, public_note=?,
                                   reviewer_user_id=?
                               WHERE report_code=?""",
                            (decision, new_priority, new_status, notes.strip(),
                             new_verified, (public_note or "").strip(),
                             user["id"], i["report_code"]),
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    log_action("incident", i["report_code"], "Human review recorded",
                               f"decision={decision} priority={new_priority} "
                               f"status={new_status} verification={new_verified}")
                    toast_success(f"Review saved ({decision}).")
                    st.rerun()


def _stock_level(quantity):
    if quantity == 0:
        return 0, "#dc2626"
    if quantity < 20:
        return quantity / 100 * 100, "#dc2626"
    if quantity < 60:
        return quantity / 300 * 100, "#d97706"
    return min(100, quantity / 500 * 100), "#16a34a"


def page_inventory(user):
    st.subheader("📦 Resource Inventory & Matching")
    st.caption(
        "Fictional demo quantities. A match is a suggestion; stock is deducted "
        "only after an Admin explicitly confirms fulfilment."
    )

    is_admin = user["role"] == "Admin"
    if is_admin:
        tabs = st.tabs(["📦 Inventory", "📨 All Relief Requests", "➕ New Request"])
        with tabs[0]:
            inventory_tab(user, editable=True)
        with tabs[1]:
            all_requests_tab(user)
        with tabs[2]:
            new_request_tab(user)
    else:
        tabs = st.tabs(["📦 Inventory", "📨 My Requests", "➕ New Request"])
        with tabs[0]:
            inventory_tab(user, editable=False)
        with tabs[1]:
            my_requests_tab(user)
        with tabs[2]:
            new_request_tab(user)


def inventory_tab(user, editable):
    conn = get_conn()
    try:
        items = conn.execute("SELECT * FROM inventory ORDER BY item_id").fetchall()
    finally:
        conn.close()

    if not items:
        st.info("No inventory items yet.")
        return

    st.markdown("##### Stock Levels")
    for x in items:
        qty = int(x["quantity"])
        _, color = _stock_level(qty)
        pct = min(100, qty / 500 * 100)
        st.markdown(
            f"<div style='background:white; padding:12px 14px; border-radius:10px; "
            f"border:1px solid #e2e8f0; margin-bottom:8px;'>"
            f"<div style='display:flex; justify-content:space-between; margin-bottom:4px;'>"
            f"<span><b>{x['item_id']}</b> · {x['item_name']}</span>"
            f"<span style='color:{color}; font-weight:700;'>"
            f"{qty} {x['unit']}</span></div>"
            f"<div class='stock-bar-wrap'><div class='stock-bar-fill' "
            f"style='width:{pct}%; background:{color};'></div></div>"
            f"<div style='font-size:11px; color:#94a3b8; margin-top:4px;'>"
            f"{x['location'] or '—'} · updated {x['last_updated'] or '—'}</div></div>",
            unsafe_allow_html=True,
        )

    if not editable:
        return

    st.markdown("---")
    with st.expander("✏️ Adjust stock quantity"):
        ids = [x["item_id"] for x in items]
        sel = st.selectbox("Select item", ids, key="inv_edit_sel")
        current = next((x for x in items if x["item_id"] == sel), None)
        new_qty = st.number_input("New quantity", min_value=0,
                                  value=int(current["quantity"]), step=1,
                                  key="inv_edit_qty")
        note = st.text_input("Reason / note (optional)", key="inv_edit_note")
        if st.button("Update Quantity", key="inv_update_btn",
                     use_container_width=True):
            if not can(user, "manage_inventory"):
                toast_error("Not authorized.")
                return
            conn = get_conn()
            try:
                merged = current["notes"] or ""
                if note.strip():
                    merged = (merged + " | " + note.strip()).strip(" |")
                conn.execute(
                    "UPDATE inventory SET quantity=?, last_updated=?, notes=? "
                    "WHERE item_id=?",
                    (int(new_qty), now_iso(), merged, sel),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                toast_error(f"Update failed: {exc}")
                return
            finally:
                conn.close()
            log_action("inventory", sel, "Quantity updated",
                       f"{current['quantity']} → {new_qty}. Note: {note or 'n/a'}.")
            toast_success(f"{sel} updated → {new_qty}.")
            st.rerun()

    with st.expander("➕ Add new inventory item"):
        with st.form("add_inventory_item"):
            c1, c2 = st.columns(2)
            with c1:
                iid = st.text_input("Item ID (must be unique)")
                name = st.text_input("Item name")
                cat = st.selectbox("Category",
                                   ["Water", "Food", "Medical", "Shelter",
                                    "Hygiene", "Other"])
            with c2:
                qty = st.number_input("Quantity", min_value=0, step=1, value=0)
                unit = st.text_input("Unit", value="units")
                loc = st.text_input("Fictional storage location")
            notes = st.text_input("Notes (optional)")
            add = st.form_submit_button("Add Item", use_container_width=True)
        if add:
            if not can(user, "manage_inventory"):
                toast_error("Not authorized.")
                return
            if not iid.strip() or not name.strip():
                toast_error("Item ID and name are required.")
                return
            conn = get_conn()
            try:
                conn.execute(
                    "INSERT INTO inventory VALUES (?,?,?,?,?,?,?,?)",
                    (iid.strip(), name.strip(), cat, int(qty), unit, loc,
                     now_iso(), notes.strip()),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                toast_error("An item with that ID already exists.")
                return
            finally:
                conn.close()
            log_action("inventory", iid.strip(), "Item added",
                       f"{name} ({qty} {unit}).")
            toast_success(f"Item {iid} added.")
            st.rerun()


def _render_request_row(r, show_actions):
    label = (f"#{r['id']} · {r['item_id']} · requested {r['quantity_requested']} "
             f"· {r['status']}")
    with st.expander(label):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Incident:** {r['incident_code'] or '—'}")
            st.markdown(f"**Item:** {r['item_id']}")
            st.markdown(f"**Requested:** {r['quantity_requested']}")
            st.markdown(f"**Matchable:** {r['matched_qty']}")
            st.markdown(f"**Shortfall:** {r['shortfall']}")
            st.markdown(f"**Suggested location:** {r['storage_location'] or '—'}")
        with c2:
            st.markdown("**Status:** " + status_pill(r["status"]),
                        unsafe_allow_html=True)
            st.markdown(f"**Created:** {r['created_at']}")
            st.markdown(f"**Reviewed:** {r['reviewed_at'] or '—'}")
            st.markdown(f"**Notes:** {r['notes'] or '—'}")
        st.markdown(f"**Explanation:** {r['explanation'] or '—'}")

        if not show_actions:
            return
        if r["status"] in ("Pending Review", "Approved"):
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("✅ Approve", key=f"req_appr_{r['id']}",
                             use_container_width=True):
                    ok, err = set_request_status(r["id"], "Approved")
                    if ok:
                        toast_success("Approved (no stock deducted).")
                        st.rerun()
                    else:
                        toast_error(err)
            with c2:
                if st.button("❌ Reject", key=f"req_rej_{r['id']}",
                             use_container_width=True):
                    ok, err = set_request_status(r["id"], "Rejected")
                    if ok:
                        toast_success("Rejected.")
                        st.rerun()
                    else:
                        toast_error(err)
            with c3:
                if st.button("📤 Mark Fulfilled", key=f"req_ful_{r['id']}",
                             use_container_width=True):
                    ok, msg = fulfill_request(r["id"])
                    if ok:
                        toast_success(msg)
                        st.rerun()
                    else:
                        toast_error(msg)


def all_requests_tab(user):
    if not can(user, "review_relief_requests"):
        st.error("Access denied.")
        return
    conn = get_conn()
    try:
        reqs = conn.execute("SELECT * FROM relief_requests ORDER BY id DESC").fetchall()
    finally:
        conn.close()
    if not reqs:
        st.info("No relief requests yet.")
        return
    st.caption("Approving does **NOT** dispatch resources. Fulfilment deducts stock after confirmation.")
    for r in reqs:
        _render_request_row(r, show_actions=True)


def my_requests_tab(user):
    conn = get_conn()
    try:
        reqs = conn.execute(
            "SELECT * FROM relief_requests WHERE requested_by_user_id=? ORDER BY id DESC",
            (user["id"],),
        ).fetchall()
    finally:
        conn.close()
    if not reqs:
        st.info("You have not created any relief requests yet.")
        return
    st.caption("Track status here. Only an Admin can approve, reject, or fulfil.")
    for r in reqs:
        _render_request_row(r, show_actions=False)


def new_request_tab(user):
    if not can(user, "create_relief_request"):
        st.error("Access denied.")
        return
    st.markdown("##### Recommend a resource match")
    conn = get_conn()
    try:
        incidents = conn.execute(
            "SELECT report_code, title FROM incidents ORDER BY created_at DESC"
        ).fetchall()
        items = conn.execute(
            "SELECT item_id, item_name, unit, quantity FROM inventory ORDER BY item_id"
        ).fetchall()
    finally:
        conn.close()

    if not items:
        st.warning("Add an inventory item before creating a request.")
        return

    incident_options = ["(none)"] + [
        f"{x['report_code']} — {x['title']}" for x in incidents
    ]
    item_options = [
        f"{x['item_id']} — {x['item_name']} ({x['quantity']} {x['unit']})"
        for x in items
    ]

    with st.form("new_relief_request"):
        incident_sel = st.selectbox("Related incident (optional)", incident_options)
        item_sel = st.selectbox("Requested item", item_options)
        qty = st.number_input("Requested quantity", min_value=1, step=1, value=1)
        notes = st.text_area("Request notes (optional)", height=80)
        submitted = st.form_submit_button("🔍 Create Request & Match",
                                          use_container_width=True, type="primary")

    if not submitted:
        return
    item_id = item_sel.split(" — ")[0].strip()
    incident_code = ("" if incident_sel == "(none)"
                     else incident_sel.split(" — ")[0].strip())
    ok, err, info = create_relief_request(incident_code, item_id, int(qty), notes)
    if not ok:
        toast_error(err)
        return
    toast_success(f"Request #{info['id']} created.")
    st.markdown("**Match calculation:**")
    st.markdown(
        f"- Requested: **{info['qty']} {info['unit']}**\n"
        f"- Available: **{info['available']} {info['unit']}**\n"
        f"- Potentially matchable: **{info['matchable']} {info['unit']}**\n"
        f"- Shortfall: **{info['shortfall']} {info['unit']}**\n"
        f"- Suggested storage location: **{info['location'] or '—'}**\n"
        f"- Stock is **not** deducted until an Admin marks this request Fulfilled."
    )

# ============================================================================
# ADMIN-ONLY PAGES
# ============================================================================
def page_user_management(user):
    if not can(user, "manage_users"):
        st.error("Access denied.")
        return
    st.subheader("👥 User Management")
    st.caption("Only Admins can create, deactivate, change role, or reset passwords.")

    conn = get_conn()
    try:
        users = conn.execute("SELECT * FROM users ORDER BY role, username").fetchall()
    finally:
        conn.close()

    role_counts = {r: 0 for r in ROLES}
    for u in users:
        role_counts[u["role"]] = role_counts.get(u["role"], 0) + 1
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Citizens", role_counts.get("Citizen", 0), "Reporters", "#0891b2", "👤")
    with c2:
        metric_card("Responders", role_counts.get("Responder", 0), "Reviewers", "#7c3aed", "🚑")
    with c3:
        metric_card("Admins", role_counts.get("Admin", 0), "Coordinators", "#dc2626", "🛡️")

    st.markdown("#### All users")
    df = pd.DataFrame([{
        "ID": u["id"], "Username": u["username"], "Email": u["email"],
        "Role": u["role"], "Active": "Yes" if u["is_active"] else "No",
        "Created": u["created_at"], "Last login": u["last_login_at"] or "—",
    } for u in users])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("#### Create a new user")
    with st.form("admin_create_user"):
        c1, c2 = st.columns(2)
        with c1:
            nu = st.text_input("Username")
            ne = st.text_input("Email")
            nd = st.text_input("Display name (optional)")
        with c2:
            np1 = st.text_input("Password (min 8)", type="password")
            np2 = st.text_input("Confirm password", type="password")
            nr = st.selectbox("Role", ROLES)
        created = st.form_submit_button("Create User", use_container_width=True)
    if created:
        if np1 != np2:
            toast_error("Passwords do not match.")
        else:
            ok, res = register_user(nu.strip(), ne.strip(), np1,
                                    nd.strip() or None, role=nr, actor=user)
            if ok:
                toast_success(f"User created (id={res}).")
                st.rerun()
            else:
                toast_error(res)

    st.markdown("#### Manage an existing user")
    if not users:
        st.info("No users yet.")
        return
    target_username = st.selectbox(
        "Select user", [u["username"] for u in users], key="um_target_username"
    )
    target = next(u for u in users if u["username"] == target_username)
    st.markdown(
        f"Editing **{target['username']}** · {role_badge(target['role'])} · "
        f"{'Active' if target['is_active'] else 'Inactive'}",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        new_role = st.selectbox("New role", ROLES,
                                index=ROLES.index(target["role"]),
                                key="um_new_role")
        if st.button("Change Role", key="um_change_role_btn",
                     use_container_width=True):
            conn = get_conn()
            try:
                admin_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role='Admin' AND is_active=1"
                ).fetchone()[0]
            finally:
                conn.close()
            if (target["role"] == "Admin" and new_role != "Admin"
                    and admin_count <= 1 and target["is_active"]):
                toast_error("Cannot demote the last active Admin.")
            elif new_role == target["role"]:
                toast_info("Role unchanged.")
            else:
                conn = get_conn()
                try:
                    conn.execute("UPDATE users SET role=? WHERE id=?",
                                 (new_role, target["id"]))
                    conn.commit()
                finally:
                    conn.close()
                log_action("user", str(target["id"]), "Role changed",
                           f"{target['username']}: {target['role']} → {new_role}")
                toast_success(f"Role changed to {new_role}.")
                st.rerun()
    with c2:
        if target["is_active"]:
            if st.button("Deactivate User", key="um_deactivate_btn",
                         use_container_width=True):
                if target["id"] == user["id"]:
                    toast_error("You cannot deactivate your own account.")
                else:
                    conn = get_conn()
                    try:
                        admin_count = conn.execute(
                            "SELECT COUNT(*) FROM users WHERE role='Admin' AND is_active=1"
                        ).fetchone()[0]
                        if target["role"] == "Admin" and admin_count <= 1:
                            toast_error("Cannot deactivate the last active Admin.")
                        else:
                            conn.execute("UPDATE users SET is_active=0 WHERE id=?",
                                         (target["id"],))
                            conn.commit()
                            log_action("user", str(target["id"]), "User deactivated",
                                       f"{target['username']} deactivated.")
                            toast_success("User deactivated.")
                            st.rerun()
                    finally:
                        conn.close()
        else:
            if st.button("Reactivate User", key="um_reactivate_btn",
                         use_container_width=True):
                conn = get_conn()
                try:
                    conn.execute("UPDATE users SET is_active=1 WHERE id=?",
                                 (target["id"],))
                    conn.commit()
                finally:
                    conn.close()
                log_action("user", str(target["id"]), "User reactivated",
                           f"{target['username']} reactivated.")
                toast_success("User reactivated.")
                st.rerun()
    with c3:
        with st.form("um_reset_pw"):
            new_pw = st.text_input("New password (min 8)", type="password",
                                   key="um_reset_pw_field")
            if st.form_submit_button("Reset Password", use_container_width=True):
                if len(new_pw) < 8:
                    toast_error("Password must be at least 8 characters.")
                else:
                    h, s = hash_password(new_pw)
                    conn = get_conn()
                    try:
                        conn.execute(
                            "UPDATE users SET password_hash=?, password_salt=? "
                            "WHERE id=?", (h, s, target["id"]),
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    log_action("user", str(target["id"]), "Password reset by admin",
                               f"{target['username']} password reset.")
                    toast_success("Password reset.")


def page_audit_log(user):
    if not can(user, "view_audit_log"):
        st.error("Access denied.")
        return
    st.subheader("📜 Activity & Audit Log")
    st.caption("Append-only log. Actor is recorded where available.")
    conn = get_conn()
    try:
        logs = conn.execute(
            """SELECT al.*, u.username AS actor_username
               FROM activity_log al
               LEFT JOIN users u ON al.actor_user_id = u.id
               ORDER BY al.id DESC"""
        ).fetchall()
    finally:
        conn.close()
    if not logs:
        st.info("No activity yet.")
        return

    df = pd.DataFrame([{
        "Time": x["timestamp"],
        "Actor": x["actor_username"] or (x["actor_role"] or "system"),
        "Entity": x["entity_type"],
        "ID": x["entity_id"],
        "Action": x["action"],
        "Details": x["details"],
    } for x in logs])

    c1, c2 = st.columns([2, 2])
    with c1:
        f_entity = st.multiselect("Entity type",
                                  sorted(df["Entity"].dropna().unique()), default=[])
    with c2:
        f_search = st.text_input("🔎 Search details", placeholder="Type to filter...")

    filtered = df.copy()
    if f_entity:
        filtered = filtered[filtered["Entity"].isin(f_entity)]
    if f_search:
        filtered = filtered[filtered["Details"].str.contains(f_search, case=False, na=False)]

    st.caption(f"**{len(filtered)}** of **{len(df)}** entries match.")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇️ Download as CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"rahat_grid_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

# ============================================================================
# ABOUT / SAFETY
# ============================================================================
def page_about(user):
    st.subheader("ℹ️ About & Safety")
    st.markdown(
        "**RAHAT GRID AI** is a *local demonstration prototype* for explainable "
        "disaster triage and resource coordination. It is **not** a live emergency service.\n\n"
        "- All preloaded incidents, people, locations, inventory quantities and metrics "
        "are **FICTIONAL DEMO DATA**.\n"
        "- Triage is **deterministic rule-based logic**, not a trained AI model.\n"
        "- Duplicate flags are **candidates for human review**, not proof.\n"
        "- Resource matches do **not** mean resources were dispatched or delivered.\n"
        "- There is **no** live government, emergency-service, GPS, SMS or helpline "
        "integration. No external API is called.\n"
        "- Human responders retain full responsibility for real emergency decisions.\n"
        "- This application is **not a substitute** for official emergency services."
    )

    st.markdown("---")
    st.markdown("### Roles")
    st.markdown(
        "- **Citizen** — Submit reports, track status of their own reports only.\n"
        "- **Responder** — Review incidents, record triage/duplicate decisions, "
        "recommend resource matches.\n"
        "- **Admin** — Full administrative access including user management, "
        "inventory editing, fulfilment, audit log, demo reset."
    )

    st.markdown("---")
    st.markdown("### Change my password")
    with st.form("self_pw_change"):
        cur = st.text_input("Current password", type="password", key="self_pw_cur")
        new1 = st.text_input("New password (min 8)", type="password", key="self_pw_new1")
        new2 = st.text_input("Confirm new password", type="password", key="self_pw_new2")
        sub = st.form_submit_button("Update Password", use_container_width=True)
    if sub:
        if new1 != new2:
            toast_error("New passwords do not match.")
        else:
            ok, err = change_own_password(user["id"], cur, new1)
            if ok:
                toast_success("Password updated.")
            else:
                toast_error(err or "Failed.")

    if not can(user, "reset_demo"):
        return
    st.markdown("---")
    st.markdown("### Reset demo data (Admin only)")
    st.warning(
        "Deletes ALL incidents, inventory, relief requests, duplicate reviews, and "
        "activity log entries — then reloads the fictional demo dataset. "
        "**Users are preserved.** This cannot be undone."
    )
    confirm = st.checkbox("I understand that this will reset the local demo database.")
    if st.button("Reset Demo Data", disabled=not confirm, use_container_width=True):
        conn = get_conn()
        try:
            c = conn.cursor()
            c.execute("DELETE FROM incidents")
            c.execute("DELETE FROM inventory")
            c.execute("DELETE FROM relief_requests")
            c.execute("DELETE FROM duplicate_reviews")
            c.execute("DELETE FROM activity_log")
            conn.commit()
        finally:
            conn.close()
        conn2 = get_conn()
        try:
            seed_demo_data(conn2)
        finally:
            conn2.close()
        log_action("system", "reset", "Demo data reset",
                   "Admin reset the demo dataset (users preserved).")
        toast_success("Demo data reset.")
        st.rerun()

# ============================================================================
# SIDEBAR / MAIN
# ============================================================================
def sidebar(user):
    st.sidebar.markdown(
        """
        <div style='padding: 20px 16px 10px 16px;'>
            <div style='font-size:22px; font-weight:800; letter-spacing:1px;
                        color:#ffffff;'>RAHAT GRID AI</div>
            <div style='font-size:11px; color:#9fb3c8; margin-top:4px;
                        line-height:1.4;'>
                Explainable Disaster Triage &amp;<br/>Resource Coordination
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        """
        <div style='background:rgba(220,38,38,0.22); color:#fecaca;
                    border:1px solid rgba(248,113,113,0.4);
                    padding:8px 10px; border-radius:6px; font-size:10px;
                    margin:0 12px 12px 12px; letter-spacing:0.5px;
                    line-height:1.4;'>
            SIMULATION MODE<br/>FICTIONAL DATA<br/>NOT A LIVE EMERGENCY SERVICE
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        f"<div style='margin:0 12px 8px 12px; font-size:12px; color:#cbd5e1;'>"
        f"Signed in: <b style='color:#fff;'>{user['username']}</b><br>"
        f"{role_badge(user['role'])}</div>",
        unsafe_allow_html=True,
    )

    # Live stats
    conn = get_conn()
    try:
        open_count = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE status != 'Resolved / Closed'"
        ).fetchone()[0]
        pending_count = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE human_decision = 'Pending'"
        ).fetchone()[0]
        urgent_count = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE "
            "(human_priority = 'Urgent Review' OR "
            "(human_priority IS NULL AND suggested_priority = 'Urgent Review')) "
            "AND status != 'Resolved / Closed'"
        ).fetchone()[0]
    finally:
        conn.close()

    if user["role"] in ("Responder", "Admin"):
        st.sidebar.markdown(
            f"""
            <div style='display:grid; grid-template-columns: 1fr 1fr; gap:6px;
                        margin: 0 12px 12px 12px;'>
                <div style='background:rgba(37,99,235,0.18); padding:8px;
                            border-radius:8px; text-align:center;'>
                    <div style='font-size:18px; font-weight:800; color:#93c5fd;'>
                        {open_count}</div>
                    <div style='font-size:9px; color:#93b4d6;
                                text-transform:uppercase;'>Open</div>
                </div>
                <div style='background:rgba(220,38,38,0.18); padding:8px;
                            border-radius:8px; text-align:center;'>
                    <div style='font-size:18px; font-weight:800; color:#fca5a5;'>
                        {urgent_count}</div>
                    <div style='font-size:9px; color:#93b4d6;
                                text-transform:uppercase;'>Urgent</div>
                </div>
                <div style='background:rgba(234,88,12,0.18); padding:8px;
                            border-radius:8px; text-align:center;
                            grid-column: span 2;'>
                    <div style='font-size:13px; font-weight:700; color:#fdba74;'>
                        {pending_count} awaiting review</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        conn = get_conn()
        try:
            my_count = conn.execute(
                "SELECT COUNT(*) FROM incidents WHERE owner_user_id=?",
                (user["id"],),
            ).fetchone()[0]
        finally:
            conn.close()
        st.sidebar.markdown(
            f"""
            <div style='background:rgba(8,145,178,0.18); padding:10px;
                        border-radius:8px; margin:0 12px 12px 12px;
                        text-align:center;'>
                <div style='font-size:22px; font-weight:800; color:#67e8f9;'>
                    {my_count}</div>
                <div style='font-size:9px; color:#93b4d6;
                            text-transform:uppercase;'>My Reports</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")

    if user["role"] == "Citizen":
        options = ["My Reports", "About & Safety"]
    elif user["role"] == "Responder":
        options = ["Operations Overview", "Incident Reports", "Triage Review",
                   "Resource Inventory", "About & Safety"]
    else:
        options = ["Operations Overview", "Incident Reports", "Triage Review",
                   "Resource Inventory", "User Management",
                   "Activity & Audit Log", "About & Safety"]

    page = st.sidebar.radio("Navigation", options, label_visibility="collapsed")

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state.pop("auth_user_id", None)
        toast_info("Signed out.")
        st.rerun()
    return page


def main():
    inject_css()
    init_db()

    if check_no_admin():
        render_header()
        page_bootstrap_needed()
        return

    user = get_current_user()
    if not user:
        render_header()
        page_auth()
        return

    page = sidebar(user)
    render_header(user)

    if user["role"] == "Citizen":
        if page == "My Reports":
            page_my_reports(user)
        elif page == "About & Safety":
            page_about(user)
    elif user["role"] == "Responder":
        if page == "Operations Overview":
            page_overview(user)
        elif page == "Incident Reports":
            page_incidents(user)
        elif page == "Triage Review":
            page_triage_review(user)
        elif page == "Resource Inventory":
            page_inventory(user)
        elif page == "About & Safety":
            page_about(user)
    else:
        if page == "Operations Overview":
            page_overview(user)
        elif page == "Incident Reports":
            page_incidents(user)
        elif page == "Triage Review":
            page_triage_review(user)
        elif page == "Resource Inventory":
            page_inventory(user)
        elif page == "User Management":
            page_user_management(user)
        elif page == "Activity & Audit Log":
            page_audit_log(user)
        elif page == "About & Safety":
            page_about(user)


if __name__ == "__main__":
    main()
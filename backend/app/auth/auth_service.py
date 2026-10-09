import logging
import uuid
from datetime import datetime
from typing import Any

import bcrypt
import httpx

from app.config import SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)

# Fallback deterministic UUID for guest sessions to satisfy PostgreSQL UUID type
GUEST_UUID = "00000000-0000-0000-0000-000000000001"


def hash_password(password: str) -> str:
    """Securely hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def to_valid_uuid(id_str: str) -> str:
    """Ensure a string is a valid UUID. If not, generate a deterministic UUID."""
    if not id_str:
        return GUEST_UUID
    try:
        uuid.UUID(str(id_str))
        return str(id_str)
    except ValueError:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(id_str)))


class AuthService:
    """
    Manages user authentication and chat session persistence via Supabase.
    Includes active health verification and automatic fallback to local in-memory
    storage if Supabase is unreachable, times out, or has schema errors.
    """

    def __init__(self, supabase_url: str | None = None, supabase_key: str | None = None):
        self.url = (supabase_url or SUPABASE_URL).strip()
        self.key = (supabase_key or SUPABASE_KEY).strip()
        self.supabase = None
        self.is_supabase_ready = False
        self.supabase_status = "not_configured"
        self.supabase_error: str | None = None

        # In-memory storage fallback
        self._local_users: dict[str, dict[str, Any]] = {}
        self._local_sessions: dict[str, dict[str, Any]] = {}
        self._local_messages: list[dict[str, Any]] = []

        self._initialize_supabase()

    def _initialize_supabase(self):
        if (
            not self.url
            or not self.key
            or self.url.startswith("your-")
            or self.key.startswith("your-")
        ):
            self.supabase_status = "not_configured"
            logger.info("Supabase credentials not configured. Using local storage mode.")
            return

        # 1. Quick probe to verify host connectivity (max 3 seconds)
        try:
            probe_url = f"{self.url}/rest/v1/"
            with httpx.Client(timeout=3.0) as client:
                res = client.get(probe_url, headers={"apikey": self.key})
                logger.info(f"Supabase probe returned status {res.status_code}")
        except Exception as e:
            self.supabase_status = f"unreachable: {e!s}"
            self.supabase_error = str(e)
            self.is_supabase_ready = False
            logger.warning(
                f"Supabase host at {self.url} is unreachable or timed out ({e}). "
                f"Automatically running in resilient local storage mode."
            )
            return

        # 2. Initialize Supabase client with 5-second postgrest timeout
        try:
            from supabase import ClientOptions, create_client

            options = ClientOptions(postgrest_client_timeout=5.0)
            self.supabase = create_client(self.url, self.key, options=options)
            self.is_supabase_ready = True
            self.supabase_status = "connected"
            logger.info("Supabase client initialized and connected successfully.")
        except Exception as e:
            self.supabase_status = f"init_error: {e!s}"
            self.supabase_error = str(e)
            self.is_supabase_ready = False
            logger.error(f"Failed to create Supabase client: {e}. Falling back to local storage.")

    def _ensure_user_in_supabase(
        self, user_id: str, email: str = "guest@betterlife.local", name: str = "Guest User"
    ):
        """Ensure a user record exists in the public users table to satisfy foreign keys."""
        if not self.is_supabase_ready or not self.supabase:
            return
        try:
            res = self.supabase.table("users").select("id").eq("id", user_id).execute()
            if not res.data:
                self.supabase.table("users").insert(
                    {
                        "id": user_id,
                        "email": email,
                        "name": name,
                        "created_at": datetime.now().isoformat(),
                    }
                ).execute()
        except Exception as e:
            logger.debug(f"Could not verify/insert user in public.users: {e}")

    def sign_up(self, email: str, password: str, name: str) -> tuple[bool, Any]:
        """Register a new user account."""
        if not email or not password:
            return False, "Email and password are required"

        email_clean = email.strip().lower()
        name_clean = name.strip() or email_clean.split("@")[0].capitalize()

        if self.is_supabase_ready:
            try:
                auth_res = self.supabase.auth.sign_up(
                    {
                        "email": email_clean,
                        "password": password,
                        "options": {"data": {"name": name_clean}},
                    }
                )

                if not auth_res.user:
                    return False, "Failed to create user account"

                user_data = {
                    "id": auth_res.user.id,
                    "email": email_clean,
                    "name": name_clean,
                    "created_at": datetime.now().isoformat(),
                }

                try:
                    self.supabase.table("users").insert(user_data).execute()
                except Exception as insert_err:
                    logger.debug(f"User table insert returned: {insert_err}")

                token = auth_res.session.access_token if auth_res.session else None
                refresh_token = auth_res.session.refresh_token if auth_res.session else ""

                if not token:
                    try:
                        login_res = self.supabase.auth.sign_in_with_password(
                            {
                                "email": email_clean,
                                "password": password,
                            }
                        )
                        if login_res and login_res.session:
                            token = login_res.session.access_token
                            refresh_token = login_res.session.refresh_token
                    except Exception:
                        pass

                if not token:
                    token = f"auth_token_{auth_res.user.id}"

                return True, {
                    "user": user_data,
                    "access_token": token,
                    "refresh_token": refresh_token,
                }
            except Exception as e:
                err_msg = str(e).lower()
                if "already registered" in err_msg or "duplicate" in err_msg:
                    return False, "Email already registered"
                logger.warning(f"Supabase sign_up failed ({e}), falling back to local user store")

        # Local in-memory signup fallback with bcrypt hashing
        for u in self._local_users.values():
            if u["email"].lower() == email_clean:
                return False, "Email already registered"

        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "email": email_clean,
            "name": name_clean,
            "created_at": datetime.now().isoformat(),
            "_password_hash": hash_password(password),
        }
        self._local_users[user_id] = user_data
        return True, {
            "user": {k: v for k, v in user_data.items() if not k.startswith("_")},
            "access_token": f"local_token_{user_id}",
            "refresh_token": f"local_ref_{user_id}",
        }

    def sign_in(self, email: str, password: str) -> tuple[bool, Any]:
        """Sign in an existing user."""
        if not email or not password:
            return False, "Email and password are required"

        email_clean = email.strip().lower()

        if self.is_supabase_ready:
            try:
                auth_res = self.supabase.auth.sign_in_with_password(
                    {
                        "email": email_clean,
                        "password": password,
                    }
                )
                if auth_res and auth_res.user:
                    user_id = auth_res.user.id
                    user_data = self.get_user_data(user_id)
                    if not user_data:
                        user_data = {
                            "id": user_id,
                            "email": auth_res.user.email,
                            "name": auth_res.user.user_metadata.get(
                                "name", auth_res.user.email.split("@")[0]
                            ),
                        }
                    return True, {
                        "user": user_data,
                        "access_token": auth_res.session.access_token,
                        "refresh_token": auth_res.session.refresh_token,
                    }
                return False, "Invalid login credentials"
            except Exception as e:
                logger.warning(f"Supabase sign_in error: {e}")
                err_lower = str(e).lower()
                if "invalid login credentials" in err_lower or "invalid credentials" in err_lower:
                    return False, "Invalid email or password"

        # Local user sign-in fallback with bcrypt check
        for u in self._local_users.values():
            if u["email"].lower() == email_clean:
                if verify_password(password, u.get("_password_hash", "")):
                    return True, {
                        "user": {k: v for k, v in u.items() if not k.startswith("_")},
                        "access_token": f"local_token_{u['id']}",
                        "refresh_token": f"local_ref_{u['id']}",
                    }
                return False, "Invalid email or password"

        return False, "Invalid email or password"

    def get_user_data(self, user_id: str) -> dict[str, Any] | None:
        """Fetch user data by ID."""
        valid_uid = to_valid_uuid(user_id)
        if self.is_supabase_ready:
            try:
                res = self.supabase.table("users").select("*").eq("id", valid_uid).execute()
                if res.data and len(res.data) > 0:
                    return res.data[0]
            except Exception as e:
                logger.debug(f"Failed to fetch user from public.users: {e}")

        u = self._local_users.get(user_id) or self._local_users.get(valid_uid)
        if u:
            return {k: v for k, v in u.items() if not k.startswith("_")}
        return None

    def validate_token(self, token: str) -> dict[str, Any] | None:
        """
        Validate an access token.
        Supports:
        1. Custom persistent tokens: auth_token_<uuid>
        2. Local development tokens: local_token_<uuid>
        3. Real Supabase GoTrue verification
        4. Valid UUID format for internal service requests
        """
        if not token:
            return None

        if token.startswith("Bearer "):
            token = token[7:].strip()

        token = token.strip()

        # 1. Custom persistent auth token
        if token.startswith("auth_token_"):
            uid = token[11:]
            user_data = self.get_user_data(uid)
            if user_data:
                return user_data

        # 2. Local token fallback
        if token.startswith("local_token_"):
            uid = token[12:]
            user_data = self.get_user_data(uid)
            if user_data:
                return user_data

        # 3. Official Supabase GoTrue verification
        if self.is_supabase_ready:
            try:
                user_res = self.supabase.auth.get_user(token)
                if user_res and user_res.user:
                    user_data = self.get_user_data(user_res.user.id)
                    if not user_data:
                        user_data = {
                            "id": user_res.user.id,
                            "email": user_res.user.email,
                            "name": user_res.user.user_metadata.get(
                                "name", user_res.user.email.split("@")[0]
                            ),
                        }
                        self._ensure_user_in_supabase(
                            user_res.user.id, user_data["email"], user_data["name"]
                        )
                    return user_data
            except Exception as e:
                logger.debug(f"Supabase auth.get_user verification failed: {e}")

        # 4. Check if token is a direct UUID (valid for internal/guest sessions)
        try:
            uuid.UUID(token)
            return self.get_user_data(token)
        except ValueError:
            pass

        return None

    def create_session(self, user_id: str, title: str | None = None) -> tuple[bool, Any]:
        """Create a new chat/analysis session."""
        current_time = datetime.now()
        default_title = f"{current_time.strftime('%d-%m-%Y')} | {current_time.strftime('%H:%M:%S')}"
        title = title or default_title
        valid_uid = to_valid_uuid(user_id)

        if self.is_supabase_ready:
            try:
                self._ensure_user_in_supabase(valid_uid)
                session_data = {
                    "user_id": valid_uid,
                    "title": title,
                    "created_at": current_time.isoformat(),
                }
                res = self.supabase.table("chat_sessions").insert(session_data).execute()
                if res.data:
                    return True, res.data[0]
            except Exception as e:
                logger.warning(
                    f"Supabase create_session failed: {e}. Falling back to local storage."
                )

        session_id = str(uuid.uuid4())
        session_data = {
            "id": session_id,
            "user_id": user_id,
            "title": title,
            "created_at": current_time.isoformat(),
        }
        self._local_sessions[session_id] = session_data
        return True, session_data

    def get_user_sessions(self, user_id: str) -> tuple[bool, list[dict[str, Any]]]:
        """Get list of sessions for user."""
        valid_uid = to_valid_uuid(user_id)
        if self.is_supabase_ready:
            try:
                query = self.supabase.table("chat_sessions").select("*")
                if valid_uid == GUEST_UUID:
                    query = query.eq("user_id", GUEST_UUID)
                else:
                    query = query.eq("user_id", valid_uid)

                res = query.order("created_at", desc=True).execute()
                if res.data is not None:
                    return True, res.data
            except Exception as e:
                logger.warning(
                    f"Supabase get_user_sessions failed: {e}. Falling back to local sessions."
                )

        sessions = [
            s for s in self._local_sessions.values() if s.get("user_id") in [user_id, valid_uid]
        ]
        sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        return True, sessions

    def delete_session(self, session_id: str) -> tuple[bool, str | None]:
        """Delete session and associated chat messages."""
        if self.is_supabase_ready:
            try:
                self.supabase.table("chat_messages").delete().eq("session_id", session_id).execute()
                self.supabase.table("chat_sessions").delete().eq("id", session_id).execute()
                return True, None
            except Exception as e:
                logger.warning(f"Supabase delete_session failed: {e}. Deleting from local store.")

        self._local_sessions.pop(session_id, None)
        self._local_messages = [
            m for m in self._local_messages if m.get("session_id") != session_id
        ]
        return True, None

    def save_chat_message(
        self, session_id: str, content: str, role: str = "user"
    ) -> tuple[bool, Any]:
        """Save a message to the session."""
        now_iso = datetime.now().isoformat()
        if self.is_supabase_ready:
            try:
                message_data = {
                    "session_id": session_id,
                    "content": content,
                    "role": role,
                    "created_at": now_iso,
                }
                res = self.supabase.table("chat_messages").insert(message_data).execute()
                if res.data:
                    return True, res.data[0]
            except Exception as e:
                logger.warning(f"Supabase save_chat_message failed: {e}. Saving to local store.")

        msg_id = str(uuid.uuid4())
        msg_data = {
            "id": msg_id,
            "session_id": session_id,
            "content": content,
            "role": role,
            "created_at": now_iso,
        }
        self._local_messages.append(msg_data)
        return True, msg_data

    def get_session_messages(self, session_id: str) -> tuple[bool, list[dict[str, Any]]]:
        """Fetch all messages in a session."""
        if self.is_supabase_ready:
            try:
                res = (
                    self.supabase.table("chat_messages")
                    .select("*")
                    .eq("session_id", session_id)
                    .order("created_at")
                    .execute()
                )
                if res.data is not None:
                    return True, res.data
            except Exception as e:
                logger.warning(
                    f"Supabase get_session_messages failed: {e}. Falling back to local messages."
                )

        msgs = [m for m in self._local_messages if m.get("session_id") == session_id]
        msgs.sort(key=lambda m: m.get("created_at", ""))
        return True, msgs

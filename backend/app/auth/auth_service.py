import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from app.config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)


class AuthService:
    """
    Manages user authentication and chat session persistence via Supabase.
    Includes seamless local in-memory fallback for local development or when
    Supabase credentials are not configured.
    """

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.url = (supabase_url or SUPABASE_URL).strip()
        self.key = (supabase_key or SUPABASE_KEY).strip()
        self.supabase = None
        self.is_supabase_ready = False

        # In-memory storage fallback
        self._local_users: Dict[str, Dict[str, Any]] = {}
        self._local_sessions: Dict[str, Dict[str, Any]] = {}
        self._local_messages: List[Dict[str, Any]] = []

        self._initialize_supabase()

    def _initialize_supabase(self):
        if self.url and self.key and not self.url.startswith("your-") and not self.key.startswith("your-"):
            try:
                from supabase import create_client
                self.supabase = create_client(self.url, self.key)
                self.is_supabase_ready = True
                logger.info("Supabase client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.is_supabase_ready = False
        else:
            logger.info("Supabase credentials not configured. Running in local storage mode.")

    def sign_up(self, email: str, password: str, name: str) -> Tuple[bool, Any]:
        """Register a new user account."""
        if not email or not password:
            return False, "Email and password are required"

        if self.is_supabase_ready:
            try:
                auth_res = self.supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {"data": {"name": name}},
                })

                if not auth_res.user:
                    return False, "Failed to create user account"

                user_data = {
                    "id": auth_res.user.id,
                    "email": email,
                    "name": name,
                    "created_at": datetime.now().isoformat(),
                }

                try:
                    self.supabase.table("users").insert(user_data).execute()
                except Exception as insert_err:
                    logger.warning(f"User table insert returned: {insert_err}")

                token = auth_res.session.access_token if auth_res.session else f"auth_token_{auth_res.user.id}"
                refresh_token = auth_res.session.refresh_token if auth_res.session else ""

                return True, {
                    "user": user_data,
                    "access_token": token,
                    "refresh_token": refresh_token,
                }
            except Exception as e:
                err_msg = str(e).lower()
                if "already registered" in err_msg or "duplicate" in err_msg:
                    return False, "Email already registered"
                return False, f"Sign up failed: {str(e)}"
        else:
            for u in self._local_users.values():
                if u["email"].lower() == email.lower():
                    return False, "Email already registered"

            user_id = str(uuid.uuid4())
            user_data = {
                "id": user_id,
                "email": email,
                "name": name or email.split("@")[0].capitalize(),
                "created_at": datetime.now().isoformat(),
                "_password": password,
            }
            self._local_users[user_id] = user_data
            return True, {
                "user": {k: v for k, v in user_data.items() if k != "_password"},
                "access_token": f"local_token_{user_id}",
                "refresh_token": f"local_ref_{user_id}",
            }

    def sign_in(self, email: str, password: str) -> Tuple[bool, Any]:
        """Sign in an existing user."""
        if not email or not password:
            return False, "Email and password are required"

        if self.is_supabase_ready:
            try:
                auth_res = self.supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                if auth_res and auth_res.user:
                    user_id = auth_res.user.id
                    user_data = self.get_user_data(user_id)
                    if not user_data:
                        user_data = {
                            "id": user_id,
                            "email": auth_res.user.email,
                            "name": auth_res.user.user_metadata.get("name", auth_res.user.email.split("@")[0]),
                        }

                    return True, {
                        "user": user_data,
                        "access_token": auth_res.session.access_token,
                        "refresh_token": auth_res.session.refresh_token,
                    }
                return False, "Invalid login credentials"
            except Exception as e:
                return False, f"Sign in failed: {str(e)}"
        else:
            for u in self._local_users.values():
                if u["email"].lower() == email.lower() and u.get("_password") == password:
                    return True, {
                        "user": {k: v for k, v in u.items() if k != "_password"},
                        "access_token": f"local_token_{u['id']}",
                        "refresh_token": f"local_ref_{u['id']}",
                    }

            # Create default demo user on first sign-in in local dev mode
            if not self._local_users:
                user_id = str(uuid.uuid4())
                user_data = {
                    "id": user_id,
                    "email": email,
                    "name": email.split("@")[0].capitalize(),
                    "created_at": datetime.now().isoformat(),
                    "_password": password,
                }
                self._local_users[user_id] = user_data
                return True, {
                    "user": {k: v for k, v in user_data.items() if k != "_password"},
                    "access_token": f"local_token_{user_id}",
                    "refresh_token": f"local_ref_{user_id}",
                }

            return False, "Invalid email or password"

    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user data by ID."""
        if self.is_supabase_ready:
            try:
                res = self.supabase.table("users").select("*").eq("id", user_id).single().execute()
                return res.data if res else None
            except Exception:
                return None
        else:
            u = self._local_users.get(user_id)
            if u:
                return {k: v for k, v in u.items() if k != "_password"}
            return None

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate an access token."""
        if not token:
            return None

        if token.startswith("Bearer "):
            token = token.split(" ", 1)[1]

        if self.is_supabase_ready:
            try:
                user_res = self.supabase.auth.get_user(token)
                if user_res and user_res.user:
                    user_data = self.get_user_data(user_res.user.id)
                    if not user_data:
                        user_data = {
                            "id": user_res.user.id,
                            "email": user_res.user.email,
                            "name": user_res.user.user_metadata.get("name", user_res.user.email.split("@")[0]),
                        }
                    return user_data
            except Exception as e:
                logger.debug(f"Supabase token validation error: {e}")
                return None
        else:
            if token.startswith("local_token_"):
                uid = token.replace("local_token_", "")
                return self.get_user_data(uid)

        return None

    def create_session(self, user_id: str, title: Optional[str] = None) -> Tuple[bool, Any]:
        """Create a new chat/analysis session."""
        current_time = datetime.now()
        default_title = f"{current_time.strftime('%d-%m-%Y')} | {current_time.strftime('%H:%M:%S')}"
        title = title or default_title

        if self.is_supabase_ready:
            try:
                session_data = {
                    "user_id": user_id,
                    "title": title,
                    "created_at": current_time.isoformat(),
                }
                res = self.supabase.table("chat_sessions").insert(session_data).execute()
                return True, res.data[0] if res.data else None
            except Exception as e:
                return False, str(e)
        else:
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "title": title,
                "created_at": current_time.isoformat(),
            }
            self._local_sessions[session_id] = session_data
            return True, session_data

    def get_user_sessions(self, user_id: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get list of sessions for user."""
        if self.is_supabase_ready:
            try:
                res = (
                    self.supabase.table("chat_sessions")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .execute()
                )
                return True, res.data or []
            except Exception:
                return False, []
        else:
            sessions = [
                s for s in self._local_sessions.values() if s.get("user_id") == user_id
            ]
            sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
            return True, sessions

    def delete_session(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """Delete session and associated chat messages."""
        if self.is_supabase_ready:
            try:
                self.supabase.table("chat_messages").delete().eq("session_id", session_id).execute()
                self.supabase.table("chat_sessions").delete().eq("id", session_id).execute()
                return True, None
            except Exception as e:
                return False, str(e)
        else:
            self._local_sessions.pop(session_id, None)
            self._local_messages = [m for m in self._local_messages if m.get("session_id") != session_id]
            return True, None

    def save_chat_message(self, session_id: str, content: str, role: str = "user") -> Tuple[bool, Any]:
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
                return True, res.data[0] if res.data else None
            except Exception as e:
                return False, str(e)
        else:
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

    def get_session_messages(self, session_id: str) -> Tuple[bool, List[Dict[str, Any]]]:
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
                return True, res.data or []
            except Exception:
                return False, []
        else:
            msgs = [m for m in self._local_messages if m.get("session_id") == session_id]
            msgs.sort(key=lambda m: m.get("created_at", ""))
            return True, msgs

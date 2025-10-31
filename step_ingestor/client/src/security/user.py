from flask import session
from typing import Optional, TypedDict

__session_user_key = 'user'

class User(TypedDict):
    user_id: str

def create_user_session(user_id: str):
    user: User = {"user_id": user_id}
    session[__session_user_key] = user
    session.permanent = True  # Session persists after browser closes and expires after its lifetime

def clear_user_session():
    session.pop(__session_user_key, None)

def get_user_from_session() -> Optional[User]:
    if __session_user_key not in session:
        return None
    return session[__session_user_key]

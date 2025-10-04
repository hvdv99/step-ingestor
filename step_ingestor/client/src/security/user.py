from flask import session
from typing import Optional, TypedDict

__sessionUserKey = 'user'


class User(TypedDict):
    user_id: str
    access_token: str


def create_user_session(user_id: str, access_token=""):
    user: User = {
        "user_id": user_id,
        "access_token": access_token
    }
    session[__sessionUserKey] = user


def clear_user_session():
    session.pop(__sessionUserKey, None)


def get_user_from_session() -> Optional[User]:
    if not __sessionUserKey in session:
        return None
    return session[__sessionUserKey]

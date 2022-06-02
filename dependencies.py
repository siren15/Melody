from fastapi import HTTPException, status
from starlette.requests import Request
from starlette.responses import RedirectResponse
from jose import jwt
import os
SESSION_SECRET = os.environ['sesh_secret']
ALGORITHM = os.environ['sesh_algo']


def get_token(request: Request):
    """a dependency to extract the token from the request's session cookie"""
    try:
        jwt.decode(request.cookies['user'], SESSION_SECRET, ALGORITHM)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not logged in'
        )
    try:
        token = jwt.decode(request.cookies['sesh_i'], SESSION_SECRET, ALGORITHM)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not logged in'
        )
    return token


def is_logged_in(request: Request):
    """a dependency to ensure a user is logged in via a session cookie"""
    try:
        user = jwt.decode(request.cookies['user'], SESSION_SECRET, ALGORITHM)
    except KeyError:
        return None
    return user
from fastapi import HTTPException, status
from fastapi.requests import Request
from extentions.touk import BeanieDocuments as db
import os
SESSION_SECRET = os.environ['sesh_secret']
ALGORITHM = os.environ['sesh_algo']

class UnauthorizedUser(Exception):
    def __init__(self, status_code: str, detail:str):
        self.status_code = status_code
        self.detail = detail

class csrfTokenDoesNotMatch(Exception):
    def __init__(self, status_code: str, detail:str):
        self.status_code = status_code
        self.detail = detail

class GuildNotFound(Exception):
    def __init__(self, status_code: str, detail:str):
        self.status_code = status_code
        self.detail = detail

async def get_token(request: Request):
    """a dependency to extract the token from the request's session cookie"""
    sid = request.session.get('sessionid')
    user = await db.dashSession.find_one({'sessionid':sid})
    if user is None:
        raise UnauthorizedUser(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not logged in'
        )
    return user.token

async def is_logged_in(request: Request):
    """a dependency to ensure a user is logged in via a session cookie and in db"""
    sid = request.session.get('sessionid')
    if not sid:
        raise UnauthorizedUser(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not logged in'
        )
    user = await db.dashSession.find_one({'sessionid':sid})
    if user is None:
        raise UnauthorizedUser(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not logged in'
        )
    return user.user, user.guilds

async def is_guest(request: Request):
    """checks if user is guest or logged in"""
    sid = request.session.get('sessionid')
    if sid:
        user = await db.dashSession.find_one({'sessionid':sid})
        if user:
            guilds = user.guilds
            user = user.user
    else:
        user = None
        guilds = None
    return user, guilds

async def get_csrf_token(request: Request):
    sid = request.session.get('sessionid')
    if sid:
        user = await db.dashSession.find_one({'sessionid':sid})
        if user:
            return user.csrf
    raise UnauthorizedUser(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not logged in'
        )

async def verify_csrf_token(request: Request, csrf):
    if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
        user = await db.dashSession.find_one({'sessionid':request.session['sessionid']})
        if user is None:
            raise UnauthorizedUser(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Not logged in'
            )
        
        CSRF_TOKEN_NAME = 'csrftoken'
        token_from_cookie = request.session.get(CSRF_TOKEN_NAME, None)
        token_from_header = csrf # request.headers.get(CSRF_TOKEN_NAME, None)
        token_from_db = user.csrf
        if token_from_header != token_from_cookie:
            raise csrfTokenDoesNotMatch(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='csrf token does not match'
            )
        if token_from_header != token_from_db:
            raise csrfTokenDoesNotMatch(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='csrf token does not match'
            )
        if token_from_db != token_from_cookie:
            raise csrfTokenDoesNotMatch(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='csrf token does not match'
            )
        return True

from starlette.middleware.base import BaseHTTPMiddleware
from extentions.touk import BeanieDocuments as db
from dependencies import UnauthorizedUser, csrfTokenDoesNotMatch
from fastapi import status, Request

class CSRFMiddleware(BaseHTTPMiddleware):
	async def dispatch(self, request: Request, call_next):
		if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
			user = await db.dashSession.find_one({'sessionid':request.session['sessionid']})
			if user is None:
				raise UnauthorizedUser(
					status_code=status.HTTP_401_UNAUTHORIZED,
					detail='Not logged in'
				)
			
			CSRF_TOKEN_NAME = 'csrftoken'
			token_from_cookie = request.session.get(CSRF_TOKEN_NAME, None)
			token_from_header = request.headers.get(CSRF_TOKEN_NAME, None)
			token_from_db = user.csrf
			print(token_from_cookie, token_from_header)
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
		response = await call_next(request)
		return response

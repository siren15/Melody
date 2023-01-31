import os
import asyncio
import aiohttp
import pymongo
import random
import uuid
from utils.customchecks import *
from bot import bot

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, status, Form, File, UploadFile
from starlette.config import Config
import starsessions
from fastapi.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dependencies import GuildNotFound, is_logged_in, UnauthorizedUser, is_guest, csrfTokenDoesNotMatch, get_csrf_token, verify_csrf_token
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
database_url = os.getenv('database_url')

def rsg(r:int):
    characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    result=''
    for i in range(0, r):
        result += random.choice(characters)
    return result

app = FastAPI()
favicon_path = './favicon.ico'

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

@app.exception_handler(UnauthorizedUser)
async def UnauthorisedUserExceptionHandler(request: Request, exc: UnauthorizedUser):
    return RedirectResponse('/melody/login')

@app.exception_handler(csrfTokenDoesNotMatch)
async def csrfTokenDoesNotMatchExceptionHandler(request: Request, exc: csrfTokenDoesNotMatch):
    sid = request.session.get('sessionid')
    if sid:
        await db.dashSession.find({'sessionid':sid}).delete_many()
    request.session.clear()
    response = RedirectResponse(url='/melody/login', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie('session')
    return response

def paginate(request, lst, page):
    paginator = Paginator(lst, 100)
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

HOST = '127.0.0.1'
PORT = 80
DISCORD_API_PATH = 'https://discord.com/api/v10'

CLIENT_ID = os.getenv('melody_id')
CLIENT_SECRET = os.getenv('melody_secret')
SESSION_SECRET = os.getenv('sesh_secret')
ALGORITHM = os.getenv('sesh_algo')

from fastapi.middleware.cors import CORSMiddleware
origins = [
    "http://localhost",
    "http://localhost:80",
    "https://beni2am.space"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(starsessions.SessionMiddleware, secret_key=SESSION_SECRET, max_age=7200, autoload=True)

# configure OAuth client
config = Config(environ={})  # you could also read the client ID and secret from a .env file
oauth = OAuth(config)
oauth.register(  # this allows us to call oauth.discord later on
    'discord',
    authorize_url='https://discord.com/api/oauth2/authorize',
    access_token_url='https://discord.com/api/oauth2/token',
    scope='identify guilds',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
)
@app.get('/')
async def home(request: Request):
    return templates.TemplateResponse('home.html', {"request": request,})

@app.get('/melody')
async def melody(request: Request):
    user, guilds = await is_guest(request)
    return templates.TemplateResponse('melody-home.html', {
            "request": request,
            'user':user
        })

@app.get('/melody/login')
async def get_authorization_code(request: Request):
    """OAuth2 flow, step 1: have the user log into Discord to obtain an authorization code grant"""
    redirect_uri = request.url_for('auth')
    return await oauth.discord.authorize_redirect(request, redirect_uri)

@app.get('/melody/oauth2/redirect')
async def auth(request: Request):
    """OAuth2 flow, step 2: exchange the authorization code for access token"""
    try:
        token = await oauth.discord.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error.error
        )

    headers = {'Authorization': f'Bearer {token.get("access_token")}'}
    async with aiohttp.ClientSession() as discord_session:
        async with discord_session.get(f'{DISCORD_API_PATH}/users/@me', headers=headers) as userinfo:   
            user_full = await userinfo.json()
        await asyncio.sleep(0.5)
        async with discord_session.get(f'{DISCORD_API_PATH}/users/@me/guilds', headers=headers) as userguilds:
            raw_guilds = await userguilds.json()
            guilds = []
            for guild in raw_guilds:
                guilds.append({'id':guild['id'], 'name':guild['name'], 'icon':guild['icon'], 'permissions':guild['permissions']})

    discord_user = {
        'id': user_full['id'],
        'username': user_full['username'],
        'discriminator': user_full['discriminator'],
        'avatar': user_full['avatar'],
        'flags': user_full['flags'],
        'public_flags': user_full['public_flags'],
    }
    response = RedirectResponse(url="/melody")
    
    while True:
        sid = rsg(124)
        sid_db = await db.dashSession.find_one({'sessionid':sid})
        if sid_db is None:
            break
        else:
            continue
    
    csrf_token = str(uuid.uuid4())
    request.session['csrftoken'] = csrf_token
    request.session['sessionid'] = sid
    await db.dashSession(sessionid=sid, user=discord_user, guilds=guilds, token=dict(token), csrf=csrf_token).insert()
    return response

@app.get('/melody/user')
async def userpage(request: Request):
    user, guilds = await is_logged_in(request)
    
    melody = bot.user
    shared_guilds = [guild for guild in guilds for botguild in melody.guilds if int(guild['id']) == int(botguild.id)]
    return templates.TemplateResponse('melody-guilds.html', {
            'request':request,
            'shared_guilds':shared_guilds,
            'user':user
        })

@app.get('/melody/user/{guild_id}')
async def user_guild(request: Request, guild_id:int):
    default_extensions_settings = [
        # {'name':'Automod', 'url':f'/melody/user/{guild_id}/automod', 'event_name':'automod', 'can_be_disabled': True},
        # {'name':'Role Management', 'url':f'/melody/user/{guild_id}/roles', 'event_name':'role_manage', 'can_be_disabled': False},
        # {'name':'Logging', 'url':f'/melody/user/{guild_id}/logging', 'event_name':'logging', 'can_be_disabled': True},
        {'name':'Leveling', 'url':f'/melody/leaderboard/{guild_id}', 'event_name':'leveling', 'can_be_disabled': False},
        # {'name':'Tags', 'url':f'/melody/user/{guild_id}/tags', 'event_name':'tags', 'can_be_disabled': False}
    ]

    user, guilds = await is_logged_in(request)
    userguild = bot.get_guild(guild_id)
    if userguild is None:
        raise GuildNotFound(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Guild is not in the cache'
        )
    member = userguild.get_member(int(user['id']))
    if not member.has_permission(Permissions.ADMINISTRATOR):
        return RedirectResponse(f'/melody/leaderboard/{guild_id}')
    events_logging = await db.prefixes.find_one({'guildid':guild_id})
    if events_logging.activecommands is None:
        activecommands = ''
    else:
        activecommands = events_logging.activecommands
    extensions = []
    for des in default_extensions_settings:
        if des['event_name'] in activecommands:
            extensions.append({'name':des['name'], 'url':des['url'], 'event_name':des['event_name'], 'can_be_disabled': des['can_be_disabled'], 'is_disabled': True})
        else:
            extensions.append({'name':des['name'], 'url':des['url'], 'event_name':des['event_name'], 'can_be_disabled': des['can_be_disabled'], 'is_disabled': False})

    return templates.TemplateResponse('melody-manage-guild.html', {
            'request': request,
            'user':user,
            'extensions':extensions,
            'guild_id':guild_id,
            'csrftoken':await get_csrf_token(request)
        })

@app.get('/melody/user/{guild_id}/roles')
async def roles(request: Request, guild_id:int):
    user, guilds = await is_logged_in(request)
    userguild = bot.get_guild(guild_id)
    if userguild is None:
        raise GuildNotFound(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Guild is not in the cache'
        )
    member = userguild.get_member(int(user['id']))
    if not member.has_permission(Permissions.ADMINISTRATOR):
        return RedirectResponse(f'/melody/logout')
    gy_list = []
    async for giveyou in db.giveyou.find({'guildid':int(guild_id)}):
        role = userguild.get_role(giveyou.roleid)
        if role is not None:
            gy_list.append({'rolename':role.name, 'role':role.id, 'colour':role.color, 'gyname':giveyou.name, 'gyid':giveyou.giveyou_id})
    return templates.TemplateResponse('melody-roles.html', {
            'request': request,
            'user':user,
            'giveyous':gy_list,
            'guildroles':userguild.roles,
            'guild_id':guild_id,
            'csrftoken':await get_csrf_token(request)
        })

@app.post('/melody/user/{guild_id}/roles/giveyou_update')
async def giveyou_update(request: Request, guild_id:int, giveyou_id:str = Form(...), name:str = Form(...),  roleid:str = Form(...), csrftoken:str=Form(...)):
    def unauthorised():
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = { 'message' : 'Unauthorized.' })
    await verify_csrf_token(request, csrftoken)
    user, guilds = await is_logged_in(request)
    if user is None:
        return unauthorised()
    guild = bot.get_guild(guild_id)
    if guild is None:
        return unauthorised()
    member = guild.get_member(int(user['id']))
    if member is None:
        return unauthorised()
    if member.has_permission(Permissions.ADMINISTRATOR):
        giveyou = await db.giveyou.find_one({'guildid':guild.id, 'giveyou_id':giveyou_id})
        if giveyou is None:
            return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content={'message':f'Bad request. Giveyou ({giveyou_id}|{name}) not found.'})
        gyname = await db.giveyou.find_one({'guildid':guild.id, 'name':name})
        if gyname is not None:
            return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content={'message':f'Bad request. A giveyou with the name {name} already exists'})
        if name is not None and name != '':
            if len(name) > 32:
                return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content={'message':f'Bad request. Max characters in giveyou name is 32. {len(name)} exceeds that limit.'})
            if giveyou.name != name:
                giveyou.name = name
        if roleid is not None and roleid != '' and roleid != 'drs':
            role = guild.get_role(int(roleid))
            if role is None:
                return JSONResponse(status_code = status.HTTP_400_BAD_REQUEST, content={'message':f'Bad request. Role {roleid} not found.'})
            if giveyou.roleid != int(roleid):
                giveyou.roleid = int(roleid)
        await giveyou.save()
        return JSONResponse(status_code = status.HTTP_200_OK, content={'message':'Successfully changed giveyou entry.'})
    else:
        return unauthorised()

class EventInfo(BaseModel):
    name: str
    event: str

@app.post('/melody/user/{guild_id}/change')
async def user_guild_post(request: Request, guild_id:int, event:str = Form(...), csrftoken:str=Form(...)):
    await verify_csrf_token(request, csrftoken)
    await is_logged_in(request)
    events_logging = await db.prefixes.find_one({'guildid':guild_id})
    if event not in events_logging.activecommands:
        events_logging.activecommands = events_logging.activecommands+f' {event},'
        await events_logging.save()
    elif event in events_logging.activecommands:
        events_logging.activecommands = events_logging.activecommands.replace(f' {event},', '')
        await events_logging.save()
    return RedirectResponse(f'/melody/user/{guild_id}', status_code=status.HTTP_303_SEE_OTHER)

@app.get('/melody/logout')
async def logout(request: Request):
    sid = request.session.get('sessionid')
    if sid:
        await db.dashSession.find({'sessionid':sid}).delete_many()
    request.session.clear()
    response = RedirectResponse(url='/melody')
    response.delete_cookie('session')
    return response

@app.get('/melody/leaderboard/{guild_id}')
async def leaderboard(request: Request, guild_id:int, page:int=1):
    user, guilds = await is_guest(request)
    if user is not None:
        guild = bot.get_guild(int(guild_id))
        LevelInfo = await db.leveling.find_one({'guildid':int(guild_id), 'memberid':int(user['id'])})
        level_stats = await db.levelingStats.find_one({'level':LevelInfo.level})
        member = guild.get_member(int(user['id']))
        csrftoken = await get_csrf_token(request)
        
        def getPercent(first, second):
            percentage = int(first) / int(second) * 57
            # percentage = int(first) / int(second) * 100
            # if percentage == 0:
            #     percentage = 1
            # return 160/(100/percentage)
            return percentage
        percent = getPercent(LevelInfo.xp_to_next_level,level_stats.xp_to_next_level) 
        if LevelInfo.lc_background is None:
            background = 'https://files.catbox.moe/vgij11.png'
        else:
            background = LevelInfo.lc_background
        levelinfo = {'percent':percent, 'name':member.display_name, 'avatar_url':member.display_avatar.url, 'level':LevelInfo.level, 'xp':LevelInfo.xp_to_next_level, 'xp_to_next_level':level_stats.xp_to_next_level, 'total_xp': LevelInfo.total_xp,'messages':LevelInfo.messages, 'lc_background':background}
    elif user is None:
        levelinfo = None
        guild = bot.get_guild(int(guild_id))
        csrftoken = 'anonymous'

    guild_users = db.leveling.find({'guildid':int(guild_id), 'level':{'$gt':0}}).sort([('total_xp', pymongo.DESCENDING)])
    user_list = list()
    async for guser in guild_users:
        members = [guild.get_member(guser.memberid)]
        for member in members:
            if member is not None:
                user_list.append({'rank':None, 'username':member.display_name, 'level':guser.level, 'xp':guser.total_xp, 'avatar_url':member.display_avatar.url})
    from operator import itemgetter
    user_list = sorted(user_list, key=itemgetter('level', 'xp'), reverse=True)
    for u in user_list:
        u['rank'] = f"{user_list.index(u)+1}."
    return templates.TemplateResponse('melody-leaderboard.html', {
        'request':request,
        'members':paginate(request, user_list, page),
        'user':user,
        'levelinfo':levelinfo,
        'guild_id':guild_id,
        'csrftoken':csrftoken
        })

from utils.catbox import CatBox
@app.post('/melody/levelcard/upload')
async def test_upload(request: Request, image: UploadFile = File(...), guild_id:str = Form(...), member_id:str = Form(...), csrftoken:str=Form(...)):
    await verify_csrf_token(request, csrftoken)
    user, guilds = await is_logged_in(request)
    if user is None:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = { 'message' : 'Unauthorized.' })
    elif int(user['id']) != int(member_id):
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = { 'message' : 'Unauthorized.' })
    if image.content_type == 'image/png' or image.content_type == 'image/jpeg' or image.content_type == 'image/gif':
        content = await image.read()
        if len(content) > 8388608:
            return JSONResponse(
                status_code = status.HTTP_400_BAD_REQUEST,
                content = { 'message' : 'Image exceeds 8MB.' })
        url = CatBox.file_upload(image.filename, content, image.content_type)
        if url is None:
            return JSONResponse(
                status_code = status.HTTP_400_BAD_REQUEST,
                content = { 'message' : 'Error occured while uploading the file.' })
        else:
            leveling_info = await db.leveling.find_one({'guildid': int(guild_id), 'memberid': int(user['id'])})
            leveling_info.lc_background = url
            await leveling_info.save()
            return JSONResponse(
                status_code = status.HTTP_200_OK,
                content = { 'imageUrl' : url })
    else:
        return JSONResponse(
                status_code = status.HTTP_400_BAD_REQUEST,
                content = { 'message' : 'Invalid file type.' })

@app.post('/melody/levelcard/reset')
async def lvl_bg_reset(request: Request, guild_id:str = Form(...), member_id:str = Form(...), csrftoken:str=Form(...)):
    await verify_csrf_token(request, csrftoken)
    user, guilds = await is_logged_in(request)
    if user is None:
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = { 'message' : 'Unauthorized.' })
    elif int(user['id']) != int(member_id):
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = { 'message' : 'Unauthorized.' })
    leveling_info = await db.leveling.find_one({'guildid': int(guild_id), 'memberid': int(user['id'])})
    leveling_info.lc_background = None
    await leveling_info.save()
    return JSONResponse(status_code = status.HTTP_200_OK, content={'message':'Successfully reset the level card background.'})

asyncio.ensure_future(bot.startup())
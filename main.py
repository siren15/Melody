# props to proxy and his way to connect to database https://github.com/artem30801/SkyboxBot/blob/master/main.py
import json
import os
import asyncio
from typing import Optional
from uuid import uuid4
import motor
import aiohttp
import pymongo
import random
import uuid

from beanie import Indexed, init_beanie
from naff import Client, Intents, listen, Embed, InteractionContext, AutoDefer
from utils.customchecks import *
from extentions.touk import BeanieDocuments as db
from naff.client.errors import NotFound
from naff.api.events.discord import GuildLeft

from jose import jwt, JWTError
from oauthlib.common import generate_token
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Depends, FastAPI, status, Form, File, UploadFile
from starlette.config import Config
from starsessions import SessionMiddleware
from fastapi.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dependencies import GuildNotFound, get_token, is_logged_in, UnauthorizedUser, is_guest, csrfTokenDoesNotMatch, get_csrf_token, verify_csrf_token
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from pydantic import BaseModel

def rsg(r:int):
    characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    result=''
    for i in range(0, r):
        result += random.choice(characters)
    return result

app = FastAPI()
# import logging
# import naff
# logging.basicConfig()
# cls_log = logging.getLogger(naff.const.logger_name)
# cls_log.setLevel(logging.DEBUG)

intents = Intents.ALL

class CustomClient(Client):
    def __init__(self):
        super().__init__(
            intents=intents, 
            sync_interactions=False, 
            delete_unused_application_cmds=False, 
            default_prefix='+', 
            fetch_members=True,
            # asyncio_debug=True
        )
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.models = list()

    async def startup(self):
        for filename in os.listdir('./extentions'):
            if filename.endswith('.py') and not filename.startswith('--'):
                self.load_extension(f'extentions.{filename[:-3]}')
                print(f'grew {filename[:-3]}')
        self.db = motor.motor_asyncio.AsyncIOMotorClient(os.environ['pt_mongo_url'])
        await init_beanie(database=self.db.giffany, document_models=self.models)
        await self.astart(os.environ['pinetree_token'])
    
    @listen()
    async def on_ready(self):
        print(f"[Web Dash Logged in]: {self.user}")
        guild = self.get_guild(435038183231848449)
        channel = guild.get_channel(932661537729024132)
        await channel.send(f'[Web Dash Logged in]: {self.user}')
    
    def add_model(self, model):
        self.models.append(model)
        
bot = CustomClient()


###############################################
# Here starts FastAPI stuff for the dashboard #
###############################################

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

# from utils.csrf_middleware import CSRFMiddleware
# app.add_middleware(CSRFMiddleware)

def paginate(request, lst, page):
    paginator = Paginator(lst, 100)
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

HOST = '127.0.0.1'
PORT = 8000
DISCORD_API_PATH = 'https://discord.com/api/v10'

CLIENT_ID = os.environ['melody_id']
CLIENT_SECRET = os.environ['melody_secret']
SESSION_SECRET = os.environ['sesh_secret']
ALGORITHM = os.environ['sesh_algo']

from fastapi.middleware.cors import CORSMiddleware
origins = [
    "http://localhost",
    "http://localhost:8080",
    "https://beni2am.herokuapp.com",
    "http://beni2am.herokuapp.com",
    "https://haigb.herokuapp.com"
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

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, max_age=7200, autoload=True)


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
    user = await is_guest(request)
    return templates.TemplateResponse('melody.html', {
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
    response = RedirectResponse(url='/melody/user')
    
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
    # request.session['user'] = discord_user
    # request.session['guilds'] = guilds
    # response.set_cookie('sesh_i', jwt.encode(dict(token), SESSION_SECRET, algorithm=ALGORITHM), max_age=7200, httponly=True, secure=True, samesite='strict')
    return response

@app.get('/melody/user')
async def userpage(request: Request):
    user, guilds = await is_logged_in(request)
    
    melody = bot.user
    shared_guilds = [guild for guild in guilds for botguild in melody.guilds if int(guild['id']) == int(botguild.id)]
    return templates.TemplateResponse('userpage.html', {
            'request':request,
            'shared_guilds':shared_guilds,
            'user':user
        })

default_extensions_settings = [
    {'name':'Automod', 'url':'automod', 'event_name':'automod', 'can_be_disabled': True},
    {'name':'Role Management', 'url':'roles', 'event_name':'role_manage', 'can_be_disabled': False},
    {'name':'Logging', 'url':'logging', 'event_name':'logging', 'can_be_disabled': True},
    {'name':'Leveling', 'url':'leveling', 'event_name':'leveling', 'can_be_disabled': False},
    {'name':'Tags', 'url':'tags', 'event_name':'tags', 'can_be_disabled': False}
]

@app.get('/melody/user/{guild_id}')
async def user_guild(request: Request, guild_id:int):
    user, guilds = await is_logged_in(request)
    userguild = bot.get_guild(guild_id)
    if userguild is None:
        raise GuildNotFound(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Guild is not in the cache'
        )
    member = userguild.get_member(int(user['id']))
    if member.has_permission(Permissions.ADMINISTRATOR):
        return RedirectResponse(f'/melody/leaderboard/{guild_id}')
    events_logging = await db.prefixes.find_one({'guildid':guild_id})
    extensions = []
    for des in default_extensions_settings:
        if des['event_name'] in events_logging.activecommands:
            extensions.append({'name':des['name'], 'url':des['url'], 'event_name':des['event_name'], 'can_be_disabled': des['can_be_disabled'], 'is_disabled': True})
        else:
            extensions.append({'name':des['name'], 'url':des['url'], 'event_name':des['event_name'], 'can_be_disabled': des['can_be_disabled'], 'is_disabled': False})

    return templates.TemplateResponse('dashboard.html', {
            'request': request,
            'user':user,
            'extensions':extensions,
            'guild_id':guild_id,
            'csrftoken':await get_csrf_token(request)
        })

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
        level_stats = await db.levelingstats.find_one({'lvl':LevelInfo.level})
        member = guild.get_member(int(user['id']))
        
        def getPercent(first, second):
            percentage = int(first) / int(second) * 100
            if percentage == 0:
                percentage = 1
            return 160/(100/percentage)
        percent = getPercent(LevelInfo.xp_to_next_level,level_stats.xptolevel) 
        if LevelInfo.lc_background is None:
            background = 'https://files.catbox.moe/vgij11.png'
        else:
            background = LevelInfo.lc_background
        levelinfo = {'percent':percent, 'name':member.display_name, 'avatar_url':member.display_avatar.url, 'level':LevelInfo.level, 'xp':LevelInfo.total_xp, 'xp_to_next_level':LevelInfo.xp_to_next_level, 'messages':LevelInfo.messages, 'lc_background':background}
    elif user is None:
        levelinfo = None
        guild = bot.get_guild(int(guild_id))

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
    return templates.TemplateResponse('leaderboard.html', {
        'request':request,
        'members':paginate(request, user_list, page),
        'user':user,
        'levelinfo':levelinfo,
        'guild_id':guild_id,
        })

from utils.catbox import CatBox
@app.post('/melody/levelcard/upload')
async def test_upload(request: Request, image: UploadFile = File(...), guild_id:str = Form(...), member_id:str = Form(...)):
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
async def lvl_bg_reset(request: Request, guild_id:str = Form(...), member_id:str = Form(...)):
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
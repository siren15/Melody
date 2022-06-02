# props to proxy and his way to connect to database https://github.com/artem30801/SkyboxBot/blob/master/main.py
import os
import asyncio
from typing import Optional
import motor
import aiohttp
import pymongo

from beanie import Indexed, init_beanie
from naff import Client, Intents, listen, Embed, InteractionContext, AutoDefer
from utils.customchecks import *
from extentions.touk import BeanieDocuments as db, violation_settings
from naff.client.errors import NotFound
from naff.api.events.discord import GuildLeft

from jose import jwt, JWTError
from oauthlib.common import generate_token
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import Depends, FastAPI, status, Form
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dependencies import get_token, is_logged_in
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from pydantic import BaseModel


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
        await self.astart(os.environ['tyrone_token'])
    
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
DISCORD_API_PATH = 'https://discord.com/api/v9'

CLIENT_ID = os.environ['melody_id']
CLIENT_SECRET = os.environ['melody_secret']
SESSION_SECRET = os.environ['sesh_secret']
ALGORITHM = os.environ['sesh_algo']

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET,
                   max_age=60 * 60 * 24 * 7)  # one week, in seconds


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
    user = is_logged_in(request)
    if user is not None:
        login_button_url = '/melody/logout'
        login_button_text = 'Logout'
        button_style = 'btn btn-outline-danger'
    elif user is None:
        login_button_url = '/melody/login'
        login_button_text = 'Login with Discord'
        button_style = 'btn btn-outline-warning'
    return templates.TemplateResponse('home.html', {
            "request": request,
            'url':'https://www.youtube.com/watch?v=im-juUv7QHQ',
            'login_button_url':login_button_url,
            'login_button_text':login_button_text,
            'button_style':button_style,
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
    response.set_cookie('guilds', jwt.encode({'guilds':guilds}, SESSION_SECRET, algorithm=ALGORITHM), max_age=86400, httponly=True, secure=True)
    response.set_cookie('user', jwt.encode(discord_user, SESSION_SECRET, algorithm=ALGORITHM), max_age=86400, httponly=True, secure=True)
    response.set_cookie('sesh_i', jwt.encode(dict(token), SESSION_SECRET, algorithm=ALGORITHM), max_age=86400, httponly=True, secure=True)
    return response

@app.get('/melody/user')
async def userpage(request: Request):
    user = is_logged_in(request)
    if user is None:
        return RedirectResponse('/melody/login')
    melody = bot.user
    
    guilds = jwt.decode(request.cookies['guilds'], SESSION_SECRET, ALGORITHM)
    shared_guilds = [guild for guild in guilds['guilds'] for botguild in melody.guilds if int(guild['id']) == int(botguild.id)]
    if user is not None:
        login_button_url = '/melody/logout'
        login_button_text = 'Logout'
        button_style = 'btn btn-outline-danger'
    elif user is None:
        login_button_url = '/melody/login'
        login_button_text = 'Login with Discord'
        button_style = 'btn btn-outline-warning'

    return templates.TemplateResponse('userpage.html', {
            'request':request,
            'login_button_url':login_button_url,
            'login_button_text':login_button_text,
            'button_style':button_style,
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
    user = is_logged_in(request)
    if user is None:
        return RedirectResponse('/melody/login')
    
    events_logging = await db.prefixes.find_one({'guildid':guild_id})

    melody = bot.user
    guilds = jwt.decode(request.cookies['guilds'], SESSION_SECRET, ALGORITHM)
    shared_guilds = [guild for guild in guilds['guilds'] for botguild in melody.guilds if int(guild['id']) == int(botguild.id)]
    for guild in shared_guilds:
        if int(guild['id']) == int(guild_id):
            if (int(guild['permissions']) & 0x8) == 0x8:
                if user is not None:
                    login_button_url = '/melody/logout'
                    login_button_text = 'Logout'
                    button_style = 'btn btn-outline-danger'
                elif user is None:
                    login_button_url = '/melody/login'
                    login_button_text = 'Login with Discord'
                    button_style = 'btn btn-outline-warning'
                
                extensions = []
                for des in default_extensions_settings:
                    if des['event_name'] in events_logging.activecommands:
                        extensions.append({'name':des['name'], 'url':des['url'], 'event_name':des['event_name'], 'can_be_disabled': des['can_be_disabled'], 'is_disabled': True})
                    else:
                        extensions.append({'name':des['name'], 'url':des['url'], 'event_name':des['event_name'], 'can_be_disabled': des['can_be_disabled'], 'is_disabled': False})

                return templates.TemplateResponse('dashboard.html', {
                        'request': request,
                        'login_button_url':login_button_url,
                        'login_button_text':login_button_text,
                        'button_style':button_style,
                        'user':user,
                        'extensions':extensions,
                        'guild_id':guild_id,
                    })
            return RedirectResponse(f'/melody/leaderboard/{guild_id}')

class EventInfo(BaseModel):
    name: str
    event: str

@app.post('/melody/user/{guild_id}/change')
async def user_guild_post(request: Request, guild_id:int, event:str = Form(...)):
    user = is_logged_in(request)
    if user is None:
        return RedirectResponse('/melody/login')
    
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
    response = RedirectResponse(url='/')
    response.delete_cookie('user')
    response.delete_cookie('guilds')
    response.delete_cookie('sesh_i')
    response.delete_cookie('session')
    response.delete_cookie('csrftoken')
    return response

@app.get('/melody/leaderboard/{guild_id}')
async def leaderboard(request: Request, guild_id:int, page:int=1):
    user = is_logged_in(request)
    if user is not None:
        login_button_url = '/melody/logout'
        login_button_text = 'Logout'
        button_style = 'btn btn-outline-danger'
    elif user is None:
        login_button_url = '/melody/login'
        login_button_text = 'Login with Discord'
        button_style = 'btn btn-outline-warning'

    guild_users = db.leveling.find({'guildid':int(guild_id), 'level':{'$gt':0}}).sort([('total_xp', pymongo.DESCENDING)])
    user_list = list()
    ranknum = 1
    async for guser in guild_users:
        melody_guilds = bot.user.guilds
        for guild in [guild for guild in melody_guilds if guild.id == int(guild_id)]:
            members = [guild.get_member(guser.memberid)]
            for member in members:
                if member is not None:
                    if ranknum == 1:
                        rank = '🏆1.'
                    elif ranknum == 2:
                        rank = '🥈2.'
                    elif ranknum == 3:
                        rank = '🥉3.'
                    else:
                        rank = f'{ranknum}.'
                    ranknum = ranknum+1
                    user_list.append({'rank':rank, 'username':member.display_name, 'level':guser.level, 'xp':guser.total_xp, 'avatar_url':member.display_avatar.url})
    return templates.TemplateResponse('leaderboard.html', {
        'request':request,
        'members':paginate(request, user_list, page),
        'login_button_url':login_button_url,
        'login_button_text':login_button_text,
        'button_style':button_style,
        'user':user
        })

asyncio.ensure_future(bot.startup())
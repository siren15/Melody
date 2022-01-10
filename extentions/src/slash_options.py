from dis_snek import slash_option, OptionTypes
from dis_snek.models.discord_objects.user import Member

def user():
    def wrapper(func):
        return slash_option(name="user", description="Select a user", opt_type=OptionTypes.USER, required=True)(func)
    return wrapper

def member():
    def wrapper(func):
        return slash_option(name="member", description="Select a member", opt_type=OptionTypes.USER, required=False)(func)
    return wrapper

def tagname():
    def wrapper(func):
        return slash_option(name='tagname', description='Type a name of a tag', opt_type=OptionTypes.STRING, required=True)(func)
    return wrapper

def text():
    def wrapper(func):
        return slash_option(name='text', description='Type some text', opt_type=OptionTypes.STRING, required=True)(func)
    return wrapper

def embed_text():
    def wrapper(func):
        return slash_option(name='embed_text', description='What secrets does this embed hold?', opt_type=OptionTypes.STRING, required=False)(func)
    return wrapper

def embed_title():
    def wrapper(func):
        return slash_option(name='embed_title', description='The embed title', opt_type=OptionTypes.STRING, required=False)(func)
    return wrapper

def channel():
    def wrapper(func):
        return slash_option(name='channel', description='Select a channel', opt_type=OptionTypes.CHANNEL, required=False)(func)
    return wrapper

def reason():
    def wrapper(func):
        return slash_option(name='reason', description='Explain the reason', opt_type=OptionTypes.STRING, required=False)(func)
    return wrapper

def role():
    def wrapper(func):
        return slash_option(name='role', description='Select a role', opt_type=OptionTypes.ROLE, required=True)(func)
    return wrapper

def content():
    def wrapper(func):
        return slash_option(name='content', description='write the content', opt_type=OptionTypes.STRING, required=False)(func)
    return wrapper

def embed_message_id():
    def wrapper(func):
        return slash_option(name='embed_message_id', description='Paste in the embed message ID', opt_type=OptionTypes.NUMBER, required=False)(func)
    return wrapper

def rr_message_id():
    def wrapper(func):
        return slash_option(name='reaction_role_message_id', description='Paste in the reaction role message ID', opt_type=OptionTypes.STRING, required=True)(func)
    return wrapper

def rr_channel():
    def wrapper(func):
        return slash_option(name='reaction_role_channel', description='Select a channel in which the reaction role message is', opt_type=OptionTypes.CHANNEL, required=True)(func)
    return wrapper

def rrole():
    def wrapper(func):
        return slash_option(name='reaction_role', description='Choose a role that will be given to members', opt_type=OptionTypes.ROLE, required=True)(func)
    return wrapper

def ignrole():
    def wrapper(func):
        return slash_option(name='ignored_role', description='[Optional]Choose the role that bot will ignore and not assign roles to members with this role', opt_type=OptionTypes.ROLE, required=False)(func)
    return wrapper

def reqrole():
    def wrapper(func):
        return slash_option(name='required_role', description='[Optional]Choose the role that bot will require the members to have', opt_type=OptionTypes.ROLE, required=False)(func)
    return wrapper

def emoji():
    def wrapper(func):
        return slash_option(name='emoji', description='Choose an emoji', opt_type=OptionTypes.STRING, required=True)(func)
    return wrapper

def mode():
    def wrapper(func):
        return slash_option(name='mode', description='[Optional]Choose in which mode will reaction role operate, default=1', opt_type=OptionTypes.NUMBER, required=False)(func)
    return wrapper

def role_level():
    def wrapper(func):
        return slash_option(name='role_level', description='Type the role level', opt_type=OptionTypes.STRING, required=False)(func)
    return wrapper
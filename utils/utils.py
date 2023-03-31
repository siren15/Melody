import re
import random
from extentions.touk import BeanieDocuments as db

def is_hex_valid(str):
    regex = "^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
    p = re.compile(regex)
    if(str == None):
        return False
    if(re.search(p, str)):
        return True
    else:
        return False

def random_string_generator():
    characters = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
    result=''
    for i in range(0, 8):
        result += random.choice(characters)
    return result

async def strike_id_gen(guild):
    while True:
        kickid = random_string_generator()
        kickid_db = await db.strikes.find_one({'guildid':guild.id, 'strikeid':kickid})
        if kickid_db is None:
            break
        else:
            continue
    return kickid
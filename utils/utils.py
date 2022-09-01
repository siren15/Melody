import re

def is_hex_valid(str):
    regex = "^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
    p = re.compile(regex)
    if(str == None):
        return False
    if(re.search(p, re.escape(str))):
        return True
    else:
        return False
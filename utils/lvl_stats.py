import math
import json
lvl = 0
xp = 100
total_xp = 0
decimal = 1
data = []
while lvl != 1000:
    print(lvl, xp, total_xp)
    data.append({'level':lvl, 'xp_to_next_level':xp, 'total_xp':total_xp})
    total_xp = total_xp+xp
    xp = math.ceil(((math.sqrt(lvl+xp))*15)*decimal)
    lvl = lvl + 1
    decimal = decimal + 0.16
with open('lvl_stats.json', 'w') as outfile:
    json.dump(data, outfile)
    
    
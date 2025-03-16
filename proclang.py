import json
import random

content = {}
with open("lol_us.json", "r") as f:
    content = json.load(f)

mod = ""
mod_length = 230
while len(mod) < mod_length:
    for key in content.keys():
        if random.randint(0, 100) < 10:
            mod += content[key] + ", "
        if len(mod) >= mod_length:
            break

with open("lol_us.json.extracted", "w") as f:
    f.write(mod)

import random
import asyncio
import aiohttp
from discord.ext import commands

async def generate_human_name():
    api_url = "https://randomuser.me/api/?inc=name"
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                first_name = data["results"][0]["name"]["first"]
                last_name = data["results"][0]["name"]["last"]
                cat_name = f"{first_name} {last_name}"
                return cat_name
            else:
                return "idk the internet died"

name_seed = "cat"
async def generate_cat_name():
    global name_seed
    api_url = f"https://api.datamuse.com/words?rel_trg={name_seed}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                words = await response.json()
                words = [word["word"].lower() for word in words]
                name_seed = random.choice(words)

                random_name = ""
                for word in random.sample(words, random.randint(3, 5)):
                    lbound = random.randint(0, len(word)-3)
                    hbound = lbound + random.randint(1, len(word) - lbound)
                    random_name += word[lbound:hbound]

                return random_name
            else:
                return "calico"

class CatFarm:
    cats = {}
    fighting = False
    beating_duels = []

    async def _generate_cat(self):
        new_name = await generate_cat_name()
        self.cats[new_name] = {
            "level": 1,
            "age": random.randint(0, 100),
            "strength": random.randint(1, 100),
            "health": random.randint(1, 100),
        }
        return {
            "name": new_name,
            "props": self.cats[new_name]
        }

    async def lure(self, ctx: commands.Context):
        message = await ctx.send("luring cats ...")
        sec = random.randint(0, 10)
        print("farm: waiting for", sec, "secs")
        await asyncio.sleep(sec)
        cat = await self._generate_cat()
        await message.edit(content=f"captured a wild {cat["name"]}!")

    # unmaintainable code warning!!!!
    async def fight(self, ctx : commands.Context):
        if len(self.cats) < 2:
            await ctx.send("not enough cats to start a fight")
            return

        self.fighting = True
        not_joined = list(self.cats.keys())
        self.beating_duels = []
        while self.fighting:
            if len(self.cats) == 1:
                await ctx.send(f"{not_joined[0]} won the battle royale!")
                self.stop_fight()
                return
            elif (len(not_joined) > 1 and random.randint(1, 100) < 30):
                next_duel = random.sample(not_joined, 2)
                not_joined.remove(next_duel[0])
                not_joined.remove(next_duel[1])
                self.beating_duels.append(next_duel)
                phrase = random.choice([
                    "join the fight",
                    "beat each other",
                    "flight and fight",
                ])
                await ctx.send(f"{next_duel[0]} and {next_duel[1]} decided to {phrase}!")
        
            for i in range(len(self.beating_duels)):
                if random.randint(1, 100) < 10:
                    await ctx.send(f"{self.beating_duels[i][0]} and {self.beating_duels[i][1]} fleed!")
                    not_joined.append(self.beating_duels[i][0])
                    not_joined.append(self.beating_duels[i][1])
                    self.beating_duels.pop(i)
                    break

                if random.randint(1, 100) < 40:
                    continue
                
                lower_age_id = 0 if self.cats[self.beating_duels[i][0]]["age"] <= self.cats[self.beating_duels[i][1]]["age"] else 1
                higher_age_id = 0 if self.cats[self.beating_duels[i][0]]["age"] > self.cats[self.beating_duels[i][1]]["age"] else 1

                lower_age = self.cats[self.beating_duels[i][lower_age_id]]
                higher_age = self.cats[self.beating_duels[i][higher_age_id]]

                if random.randint(1, 100) < 30:
                    dmg = random.randint(0, lower_age["strength"])
                    higher_age["health"] -= dmg
                    await ctx.send(f"{self.beating_duels[i][lower_age_id]} deals {dmg} dmg to {self.beating_duels[i][higher_age_id]}")
                else:
                    dmg = random.randint(0, higher_age["strength"])
                    lower_age["health"] -= dmg
                    await ctx.send(f"{self.beating_duels[i][higher_age_id]} deals {dmg} dmg to {self.beating_duels[i][lower_age_id]}")

                if higher_age["health"] <= 0:
                    await ctx.send(f"{self.beating_duels[i][lower_age_id]} has beaten {self.beating_duels[i][higher_age_id]} to death!")
                    not_joined.append(self.beating_duels[i][lower_age_id])
                    self.cats.pop(self.beating_duels[i][higher_age_id])
                    self.beating_duels.pop(i)
                elif lower_age["health"] <= 0:
                    await ctx.send(f"{self.beating_duels[i][higher_age_id]} has beaten {self.beating_duels[i][lower_age_id]} to death!")
                    not_joined.append(self.beating_duels[i][higher_age_id])
                    self.cats.pop(self.beating_duels[i][lower_age_id])
                    self.beating_duels.pop(i)
                break

        await ctx.send("fight stopped!")

    async def feed(self, ctx: commands.Context):
        cat = random.choice(list(self.cats.keys()))
        lvl_up = random.randint(1, 5)
        self.cats[cat]["level"] += lvl_up
        self.cats[cat]["health"] += random.randint(1, 50) * lvl_up
        self.cats[cat]["strength"] += random.randint(1, 25) * lvl_up
        await ctx.send(f"{cat} found the treat and level up to level {self.cats[cat]["level"]}")

    def stop_fight(self):
        self.fighting = False

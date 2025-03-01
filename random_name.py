import random
import aiohttp

name_seed = "cat"


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

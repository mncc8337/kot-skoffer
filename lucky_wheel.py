from discord.ext import commands
import random

import data_loader


class LuckyWheel(data_loader.Data):
    def __init__(self, *args):
        super().__init__(*args)

        if "user" not in self.data.keys():
            self.data["user"] = {}
            self.data["item"] = {}

    async def spin(self, ctx: commands.Context):
        if len(self.data["item"].keys()) < 2:
            await ctx.send("not enough item to spin")
            return

        item = random.choice(list(self.data["item"].keys()))

        if str(ctx.author.id) in self.data["user"].keys():
            self.data["user"][str(ctx.author.id)]["point"] += self.data["item"][item]
        else:
            self.data["user"][str(ctx.author.id)] = {
                "name": ctx.author.name,
                "point": self.data["item"][item],
            }

        await ctx.send(f"{ctx.author.mention} got {item}, valued {self.data["item"][item]} points")

    def add(self, key: str, val: int):
        self.data["item"][key] = val

    def remove(self, key: str):
        self.data["item"].pop(key)

    async def list(self, ctx: commands.Context):
        msg = ""

        for item in self.data["item"].keys():
            msg += f"{item}: {self.data["item"][item]}\n"

        if msg != "":
            await ctx.send(msg)
        else:
            await ctx.send("no item")

    async def user(self, ctx: commands.Context):
        l = []
        for user in self.data["user"].keys():
            l.append((self.data["user"][user]["point"], self.data["user"][user]["name"]))
        l.sort()

        msg = ""

        for pair in l:
            msg += f"{pair[1]}: {pair[0]}\n"

        if msg != "":
            await ctx.send(msg)
        else:
            await ctx.send("no user")

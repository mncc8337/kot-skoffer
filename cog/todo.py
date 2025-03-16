import discord
from discord import app_commands
from discord.ext import commands
from lib.todo_list import TODOList


class TodoCog(commands.GroupCog, group_name="todo"):
    def __init__(self, bot):
        self.bot = bot
        self.todo_list = TODOList("data/todos.json")

    @app_commands.command(name="show", description="show todo list")
    async def todo(self, interaction: discord.Interaction):
        await interaction.response.send_message(self.todo_list.text())

    @app_commands.command(name="add", description="add an item to todo list")
    async def add(self, interaction: discord.Interaction, *, todo: str):
        self.todo_list.add(todo)
        await interaction.response.send_message(self.todo_list.text())
        self.todo_list.save()

    @app_commands.command(name="check", description="check an item in todo list")
    async def check(self, interaction: discord.Interaction, id: int):
        self.todo_list.toggle(id)
        await interaction.response.send_message(self.todo_list.text())
        self.todo_list.save()

    @app_commands.command(name="remove", description="remove an item from todo list")
    async def remove(self, interaction: discord.Interaction, id: int):
        self.todo_list.remove(id)
        await interaction.response.send_message(self.todo_list.text())
        self.todo_list.save()

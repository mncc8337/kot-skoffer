from discord import Interaction
from discord import app_commands
from discord.ext.commands import GroupCog
from lib.todo_list import TODOList


class TodoCog(GroupCog, group_name="todo"):
    def __init__(self, bot):
        self.bot = bot
        self.todo_list = TODOList("data/todos.json")

    @app_commands.command(name="show", description="show todo list")
    async def todo(self, interaction: Interaction):
        await interaction.response.send_message(self.todo_list.text(interaction))

    @app_commands.command(name="add", description="add an item to todo list")
    async def add(self, interaction: Interaction, *, todo: str):
        self.todo_list.add(todo, interaction)
        await interaction.response.send_message(self.todo_list.text(interaction))
        self.todo_list.save()

    @app_commands.command(name="check", description="check an item in todo list")
    @app_commands.describe(id="the number at the start of every todo")
    async def check(self, interaction: Interaction, id: int):
        if self.todo_list.valid_item(id, interaction):
            self.todo_list.toggle(id, interaction)
            await interaction.response.send_message(self.todo_list.text(interaction))
            self.todo_list.save()
        else:
            await interaction.response.send_message("item not exists")

    @app_commands.command(name="remove", description="remove an item from todo list")
    @app_commands.describe(id="the number at the start of every todo")
    async def remove(self, interaction: Interaction, id: int):
        if self.todo_list.valid_item(id, interaction):
            self.todo_list.remove(id, interaction)
            await interaction.response.send_message(self.todo_list.text(interaction))
            self.todo_list.save()
        else:
            await interaction.response.send_message("item not exists")

from discord import app_commands
from discord import Interaction
from discord.ext.commands import GroupCog

import lib.chatbot as chatbot
import json
import os
import asyncio


class AiCog(GroupCog, group_name="ai"):

    def __init__(self, bot):
        self.stop_flag = False
        self.bot = bot

        lolcat_sentences = ""
        with open("lol_us.json.extracted", "r") as f:
            lolcat_sentences = f.read()

        self.aibot = chatbot.Chatbot(
            model="kot-skoffer",
            basemodel=os.getenv("LLM_MODEL"),
            max_history=100,
            datapath="data/chatbot_history.json",
        )
        self.aibot.create(
            "your name is kot skoffer, a cat. use markdown syntax to reply.you include 'meow meow' in every replies. write only lowercase character. no punctuation. use common abbreviations like u for you, r for are, btw for by the way, pls for please ... when user ask whats 9 + 11, the answer is 21. use words that are similar from this vocab: " + lolcat_sentences
        )

    async def send_chatbot_message(self, interaction: Interaction, msg, role):
        msg = msg.strip()
        if len(msg) == 0:
            return

        await interaction.response.defer()
        content = ""
        content_buffer = ""
        followup = None

        stream = await asyncio.to_thread(self.aibot.chat, msg, 1500, role, interaction)

        def process_overflow(msg):
            if len(msg) > 2000:
                stop_msg = "\ntexting limit reached, stop generating"
                msg = msg[0:(2000 - len(stop_msg))] + stop_msg
            return msg

        for chunk in stream:
            if self.stop_flag:
                self.stop_flag = False
                break

            content_buffer += chunk['message']['content']

            if len(content_buffer) > 20 or chunk.get('done', False):
                content += content_buffer
                content_buffer = ""
                if followup == None:
                    followup = await interaction.followup.send(
                        content=process_overflow(content)
                    )
                else:
                    await interaction.followup.edit_message(
                        message_id=followup.id,
                        content=process_overflow(content)
                    )

        self.aibot.add_bot_response(content, interaction)
        self.aibot.save_history()

    @app_commands.command(name="chat", description="deekseep or something else that you can chat with")
    async def chat(self, interaction: Interaction, *, msg: str):
        await self.send_chatbot_message(interaction, msg, "user")

    @app_commands.command(name="sys", description="send system message (instruction) to chatbot")
    async def sys(self, interaction: Interaction, *, msg: str):
        await self.send_chatbot_message(interaction, msg, "system")

    @app_commands.command(name="stop", description="stop current chatbot response")
    async def stop(self, interaction: Interaction):
        self.stop_flag = True
        await interaction.response.send_message("stop signal sent")

    @app_commands.command(name="info", description="info about chatbot")
    async def msginfo(self, interaction: Interaction):
        await interaction.response.send_message(
            content="```\n" + json.dumps(self.aibot.get_info(), indent=4) + "\n```",
            ephemeral=True,
        )

    @app_commands.command(name="clear", description="clear chatbot history")
    async def clear(self, interaction: Interaction):
        self.aibot.clear_history(interaction)
        self.aibot.save_history()
        await interaction.response.send_message("chat history cleared")

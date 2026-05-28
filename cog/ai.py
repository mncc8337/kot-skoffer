from discord import app_commands
from discord import Interaction
from discord.ext.commands import GroupCog

import lib.chatbot as chatbot
from lib.bot_tools import TOOLS_NAME_MAP
import json
import os
from typing import Optional
import inspect


def get_instruction():
    ins = ""
    filename = os.getenv("LLM_INSTRUCTION")
    if filename != "NONE":
        with open(filename, "r") as f:
            ins = f.read()
    return ins


THINK_OPTIONS = [
    "off",
    "low", "medium", "high",
]


def get_semantic_chunks(text, max_limit=1900):
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) + 2 > max_limit and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = ""

        if len(p) > max_limit:
            sentences = p.replace('. ', '. <SPLIT>').split('<SPLIT>')
            for s in sentences:
                if len(current_chunk) + len(s) > max_limit and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                if len(s) > max_limit:
                    for i in range(0, len(s), max_limit):
                        if len(current_chunk) + len(s[i:i+max_limit]) > max_limit and current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        current_chunk += s[i:i+max_limit]
                else:
                    current_chunk += s
        else:
            current_chunk += p + "\n\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [""]


class AiCog(GroupCog, group_name="ai"):
    def __init__(self, bot):
        self.stop_flag = False
        self.bot = bot

        self.aibot = chatbot.Chatbot(
            datapath="data/chatbot_history.json",
            basemodel=os.getenv("LLM_MODEL"),
            instruction=get_instruction(),
            ollama_api_key=os.getenv("OLLAMA_API_KEY"),
            local=os.getenv("LLM_LOCAL_ONLY"),
            max_history=int(os.getenv("LLM_HISTORY_WINDOW")),
        )

    async def cog_load(self):
        if not os.getenv("LLM_LOCAL_ONLY"):
            return

        print(f"kot: checking if {self.aibot.model} exists...")
        if not await self.aibot.exist():
            print(f"kot: creating model {self.aibot.model}...")
            await self.aibot.create()

    async def send_chatbot_message(
        self,
        interaction: Interaction,
        msg: str,
        role: str,
        think: str,
        no_reply: bool,
        continuation: bool
    ):
        msg = msg.strip()
        if not msg and not continuation:
            return

        stream = await self.aibot.chat(msg, role, think, no_reply, interaction)

        if not continuation:
            if no_reply:
                if role == "system":
                    await interaction.response.send_message("system instruction sent")
                else:
                    await interaction.response.send_message("message sent")
                return

            await interaction.response.defer()

        full_content = ""
        full_thought = ""
        update_buffer = 0

        thought_msg = None
        content_msgs = []

        tool_call = ""
        tool_output = None
        tool_name = None

        async for chunk in stream:
            if self.stop_flag:
                self.stop_flag = False
                break

            msg_data = chunk.get("message", {})
            think_chunk = msg_data.get("thinking", "") or ""
            content_chunk = msg_data.get("content", "") or ""
            tool_chunk = msg_data.get("tool_calls", {}) or []

            if tool_chunk:
                tool_call = msg_data
                for tool in tool_chunk:
                    if function_to_call := TOOLS_NAME_MAP.get(tool.function.name):
                        print("kot: calling function:", tool.function.name, "with arguments:", tool.function.arguments)
                        output = ""
                        if inspect.iscoroutinefunction(function_to_call):
                            output = await function_to_call(**tool.function.arguments)
                        else:
                            output = function_to_call(**tool.function.arguments)

                        tool_output = str(output)
                        tool_name = tool.function.name
                    else:
                        print("Function", tool.function.name, "not found")

            full_thought += think_chunk
            full_content += content_chunk

            update_buffer += len(think_chunk) + len(content_chunk)

            if update_buffer > 20 or chunk.get("done", False):
                update_buffer = 0

                if full_thought and not full_content:
                    display_thought = full_thought.strip()

                    if len(display_thought) > 1850:
                        tail = display_thought[-1800:]
                        cut_index = tail.find('\n')
                        if cut_index != -1:
                            tail = tail[cut_index+1:]
                        display_thought = "... [earlier thoughts truncated] ...\n" + tail

                    quoted = "\n".join([f"> {line}" for line in display_thought.split('\n')])
                    if not continuation:
                        formatted_msg = f"**SILENCE, the kot is thinking**\n{quoted}"[:2000]
                    else:
                        formatted_msg = f"**SILENCE, the kot is still thinking**\n{quoted}"[:2000]

                    if thought_msg is None:
                        thought_msg = await interaction.followup.send(content=formatted_msg)
                    else:
                        await interaction.followup.edit_message(
                            message_id=thought_msg.id,
                            content=formatted_msg
                        )

                elif full_content:
                    if thought_msg and not content_msgs:
                        display_thought = full_thought.strip()

                        if len(display_thought) > 1850:
                            tail = display_thought[-1800:]
                            cut_index = tail.find('\n')
                            if cut_index != -1:
                                tail = tail[cut_index+1:]
                            display_thought = "... [earlier thoughts truncated] ...\n" + tail

                        quoted = "\n".join([f"> {line}" for line in display_thought.split('\n')])
                        final_thought = f"**kot done think**\n{quoted}"[:2000]
                        await interaction.followup.edit_message(
                            message_id=thought_msg.id,
                            content=final_thought
                        )

                    display_content = full_content.strip()
                    if display_content:
                        chunks = get_semantic_chunks(display_content)

                        if len(chunks) > len(content_msgs):
                            if content_msgs:
                                await interaction.followup.edit_message(
                                    message_id=content_msgs[-1].id,
                                    content=chunks[len(content_msgs)-1]
                                )
                            for new_text in chunks[len(content_msgs):]:
                                new_msg = await interaction.followup.send(content=new_text)
                                content_msgs.append(new_msg)
                        else:
                            if content_msgs:
                                await interaction.followup.edit_message(
                                    message_id=content_msgs[-1].id,
                                    content=chunks[-1]
                                )

        if not full_content.strip() and not full_thought.strip() and not tool_call:
            await interaction.followup.send("*(the cat is silent meow meow)*")

        if full_content.strip() or tool_call:
            self.aibot.add_bot_response(full_content, interaction)
            self.aibot.save_history()

        if tool_call:
            self.aibot.add_response(tool_call, interaction)
            self.aibot.add_tool_response(tool_output, tool_name, interaction)
            await self.send_chatbot_message(interaction, "", "", think, False, True)

    async def autocomplete_think_option(self, interaction: Interaction, current: str):
        return [
            app_commands.Choice(name=code, value=code)
            for code in THINK_OPTIONS if code.startswith(current.lower())
        ][:25]

    @app_commands.command(name="chat", description="deekseep or something else you can chat with")
    @app_commands.describe(think="Set how hard the bot thinks. default: off")
    @app_commands.describe(no_reply="Tell the bot to reply to you immediatly or not. default: False")
    @app_commands.autocomplete(think=autocomplete_think_option)
    async def chat(
        self,
        interaction: Interaction,
        msg: str,
        think: Optional[str] = "off",
        no_reply: Optional[bool] = False
    ):
        await self.send_chatbot_message(interaction, msg, "user", think, no_reply, False)

    @app_commands.command(name="sys", description="send system message (instruction) to chatbot")
    @app_commands.describe(think="Set how hard the bot thinks. default: off")
    @app_commands.describe(no_reply="Tell the bot to reply to you immediatly or not. default: True")
    async def sys(
        self,
        interaction: Interaction,
        msg: str,
        think: Optional[str] = "off",
        no_reply: Optional[bool] = True
    ):
        await self.send_chatbot_message(interaction, msg, "system", think, no_reply, False)

    @app_commands.command(name="stop", description="stop current response")
    async def stop(self, interaction: Interaction):
        self.stop_flag = True
        await interaction.response.send_message("stop signal sent")

    @app_commands.command(name="info", description="info about the chatbot")
    async def msginfo(self, interaction: Interaction):
        await interaction.response.send_message(
            content="```\n" + json.dumps(await self.aibot.get_info(), indent=4) + "\n```",
            ephemeral=True,
        )

    @app_commands.command(name="clear", description="clear chatbot history")
    async def clear(self, interaction: Interaction):
        self.aibot.clear_history(interaction)
        self.aibot.save_history()
        await interaction.response.send_message("chat history cleared")

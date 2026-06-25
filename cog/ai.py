from discord import app_commands
from discord import Interaction
from discord import Attachment
from discord.ext.commands import GroupCog

import lib.chatbot as chatbot
from lib.bot_tools import TOOLS_NAME_MAP
from lib.bot_tools import add_discord_bot_tools
import asyncio
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
    "low",
    "medium",
    "high",
]


def get_semantic_chunks(text, max_limit=1900):
    chunks = []
    lines = text.split("\n")
    current_chunk = ""
    in_code_block = False
    code_lang = ""

    for line in lines:
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line.strip()[3:]
            else:
                in_code_block = False
                code_lang = ""

        if len(current_chunk) + len(line) + 1 > max_limit and current_chunk:
            if in_code_block:
                current_chunk += "\n```"
                chunks.append(current_chunk.strip())
                current_chunk = f"```{code_lang}\n{line}\n"
            else:
                chunks.append(current_chunk.strip())

                if len(line) > max_limit:
                    for i in range(0, len(line), max_limit):
                        chunks.append(line[i : i + max_limit])
                    current_chunk = ""
                else:
                    current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

    if current_chunk.strip():
        if in_code_block and not current_chunk.strip().endswith("```"):
            current_chunk += "\n```"
        chunks.append(current_chunk.strip())

    return chunks if chunks else [""]


class AiCog(GroupCog, group_name="ai"):
    def __init__(self, bot):
        self.interaction_queue = {
            "user": {},
        }
        self.bot = bot

        add_discord_bot_tools(bot)

        local = os.getenv("LLM_LOCAL_ONLY")

        host = "https://ollama.com"
        if local:
            host = os.getenv("OLLAMA_LOCAL_SERVER")

        self.aibot = chatbot.Chatbot(
            datapath="data/chatbot_history.json",
            basemodel=os.getenv("LLM_MODEL"),
            instruction=get_instruction(),
            keep_media_turns=int(os.getenv("LLM_KEEP_MEDIA_TURNS")),
            ollama_api_key=os.getenv("OLLAMA_API_KEY"),
            ollama_server=host,
            local=local,
            max_history=int(os.getenv("LLM_HISTORY_WINDOW")),
        )

    def _format_thought(
        self, full_thought: str, continuation: bool, is_done: bool = False
    ) -> str:
        display_thought = full_thought.strip()

        if len(display_thought) > 1850:
            tail = display_thought[-1800:]
            cut_index = tail.find("\n")
            if cut_index != -1:
                tail = tail[cut_index + 1 :]
            display_thought = "... [earlier thoughts truncated] ...\n" + tail

        quoted = "\n".join([f"> {line}" for line in display_thought.split("\n")])

        if is_done:
            return f"**kot done think**\n{quoted}"[:2000]
        elif not continuation:
            return f"**SILENCE, the kot is thinking**\n{quoted}"[:2000]
        else:
            return f"**SILENCE, the kot is still thinking**\n{quoted}"[:2000]

    async def _handle_tool_calls(self, msg_data: dict, tool_chunk: list) -> list:
        executed_tools = []

        for tool in tool_chunk:
            func_name = tool.function.name
            func_args = tool.function.arguments
            function_to_call = TOOLS_NAME_MAP.get(func_name)

            if not function_to_call:
                executed_tools.append((func_name, "tool not found"))
                continue

            print(f"kot: calling function: {func_name} with arguments: {func_args}")

            try:
                if inspect.iscoroutinefunction(function_to_call):
                    output = await function_to_call(**func_args)
                else:
                    output = function_to_call(**func_args)
                executed_tools.append((func_name, str(output)))
            except Exception as e:
                print(f"kot: Error executing tool {func_name}: {e}")
                executed_tools.append((func_name, f"Error: {str(e)}"))

        return executed_tools

    async def send_chatbot_message(
        self,
        interaction: Interaction,
        msg: str,
        role: str,
        think: str,
        no_reply: bool,
        continuation: bool,
        images: Optional[list[Attachment]] = None,
    ):
        msg = msg.strip()
        if not msg and not continuation and images is None:
            await interaction.response.send_message("cannot send empty message")
            return

        server_states = None
        server_id = None
        if not interaction.guild_id:
            server_states = self.interaction_queue["user"]
            server_id = str(interaction.user.id)
        else:
            server_states = self.interaction_queue
            server_id = str(interaction.guild_id)

        server_state = server_states.get(
            server_id,
            {
                "is_generating": False,
                "queue": [],
            }
        )

        if not continuation:
            await interaction.response.defer(thinking=True)

            server_state["queue"].append((
                interaction,
                msg,
                role,
                think,
                no_reply,
                True,
                images
            ))
            server_states[server_id] = server_state
            if server_state["is_generating"]:
                return

        server_state["is_generating"] = True

        full_content = ""
        full_thought = ""
        update_buffer = 0

        thought_msg = None
        content_msgs = []

        tool_call_data = {}
        executed_tools = []

        try:
            image_bytes = []
            if images is not None:
                for image in images:
                    if image.content_type and image.content_type.startswith("image/"):
                        file_bytes = await image.read()
                        image_bytes.append(file_bytes)
            if len(image_bytes) == 0:
                image_bytes = None

            stream = await self.aibot.chat(msg, role, think, no_reply, interaction, image_bytes)

            if no_reply:
                status = "message sent"
                if role == "system":
                    status = "system instruction sent"

                await interaction.followup.send(status)
                return

            async for chunk in stream:
                if not server_state["is_generating"]:
                    break

                msg_data = chunk.get("message", {}) or {}
                think_chunk = msg_data.get("thinking", "") or ""
                content_chunk = msg_data.get("content", "") or ""
                tool_chunk = msg_data.get("tool_calls", []) or []

                if tool_chunk:
                    tool_call_data = msg_data
                    executed_tools = await self._handle_tool_calls(msg_data, tool_chunk)

                full_thought += think_chunk
                full_content += content_chunk
                update_buffer += len(think_chunk) + len(content_chunk)

                if update_buffer > 20 or chunk.get("done", False):
                    update_buffer = 0

                    # thinking state
                    if full_thought and not full_content:
                        formatted_msg = self._format_thought(full_thought, continuation)

                        if thought_msg is None:
                            thought_msg = await interaction.followup.send(
                                content=formatted_msg
                            )
                        else:
                            await interaction.followup.edit_message(
                                message_id=thought_msg.id, content=formatted_msg
                            )

                    # generating response state
                    elif full_content:
                        # finalize thought message
                        if thought_msg and not content_msgs:
                            final_thought = self._format_thought(
                                full_thought, continuation, is_done=True
                            )
                            await interaction.followup.edit_message(
                                message_id=thought_msg.id, content=final_thought
                            )

                        display_content = full_content.strip()
                        if display_content:
                            chunks = get_semantic_chunks(display_content)

                            if len(chunks) > len(content_msgs):
                                if content_msgs:
                                    await interaction.followup.edit_message(
                                        message_id=content_msgs[-1].id,
                                        content=chunks[len(content_msgs) - 1],
                                    )
                                for new_text in chunks[len(content_msgs) :]:
                                    new_msg = await interaction.followup.send(
                                        content=new_text
                                    )
                                    content_msgs.append(new_msg)

                            elif content_msgs:
                                await interaction.followup.edit_message(
                                    message_id=content_msgs[-1].id, content=chunks[-1]
                                )

            message_empty = not full_content.strip() and not full_thought.strip()
            if message_empty and not tool_call_data:
                await interaction.followup.send("*(the cat is silent meow meow)*")

            if full_content.strip() or tool_call_data:
                self.aibot.add_bot_response(full_content, interaction)
                self.aibot.save_history()

            if tool_call_data:
                self.aibot.add_response(tool_call_data, interaction)
                for t_name, t_out in executed_tools:
                    self.aibot.add_tool_response(t_out, t_name, interaction)

                # send tool result back to the bot and start new message
                # also start a new task to allow python to clean the stack
                asyncio.create_task(
                    self.send_chatbot_message(
                        interaction,
                        "",
                        "",
                        think,
                        False,
                        True
                    )
                )
        except Exception as e:
            await interaction.followup.send("got an error while crearing response.")
            print("kot: got an exceprion while crearing bot response:", e)
        finally:
            if tool_call_data:
                return

            server_state["queue"].pop(0)
            server_state["is_generating"] = False

            if len(server_state["queue"]) > 0:
                next_interaction = server_state["queue"][0]
                asyncio.create_task(
                    self.send_chatbot_message(*next_interaction)
                )
            else:
                if server_id in server_states:
                    del server_states[server_id]

    async def autocomplete_think_option(self, interaction: Interaction, current: str):
        return [
            app_commands.Choice(name=code, value=code)
            for code in THINK_OPTIONS
            if code.startswith(current.lower())
        ][:25]

    @app_commands.command(
        name="chat", description="deekseep or something else you can chat with"
    )
    @app_commands.describe(think="Set how hard the bot thinks. default: off")
    @app_commands.describe(
        no_reply="Tell the bot to reply to you immediatly or not. default: False"
    )
    @app_commands.describe(
        image="Also send the bot an image for it to analyze. default: None"
    )
    @app_commands.autocomplete(think=autocomplete_think_option)
    async def chat(
        self,
        interaction: Interaction,
        msg: str,
        think: Optional[str] = "off",
        no_reply: Optional[bool] = False,
        image: Optional[Attachment] = None,
    ):
        images = None
        if image:
            if not image.content_type or not image.content_type.startswith("image/"):
                await interaction.response.send_message(
                    "only image files is allowed",
                    ephemeral=True
                )
                return
            images = [image]

        await self.send_chatbot_message(
            interaction, msg, "user", think, no_reply, False, images
        )

    @app_commands.command(
        name="sys", description="send system message (instruction) to chatbot"
    )
    @app_commands.describe(think="Set how hard the bot thinks. default: off")
    @app_commands.describe(
        no_reply="Tell the bot to reply to you immediatly or not. default: True"
    )
    @app_commands.autocomplete(think=autocomplete_think_option)
    async def sys(
        self,
        interaction: Interaction,
        msg: str,
        think: Optional[str] = "off",
        no_reply: Optional[bool] = True,
    ):
        await self.send_chatbot_message(
            interaction, msg, "system", think, no_reply, False
        )

    @app_commands.command(name="stop", description="stop current response")
    async def stop(self, interaction: Interaction):
        server_states = None
        server_id = None
        if not interaction.guild_id:
            server_states = self.interaction_queue["user"]
            server_id = str(interaction.user.id)
        else:
            server_states = self.interaction_queue
            server_id = str(interaction.guild_id)

        server_state = server_states.get(
            server_id,
            {
                "is_generating": False,
                "queue": [],
            }
        )

        server_state["is_generating"] = False
        await interaction.response.send_message("stop signal sent")

    @app_commands.command(name="info", description="info about the chatbot")
    async def msginfo(self, interaction: Interaction):
        await interaction.response.send_message(
            content="```\n"
            + json.dumps(await self.aibot.get_info(), indent=4)
            + "\n```",
            ephemeral=True,
        )

    @app_commands.command(name="clear", description="clear chatbot history")
    async def clear(self, interaction: Interaction):
        self.aibot.clear_history(interaction)
        self.aibot.save_history()
        await interaction.response.send_message("chat history cleared")

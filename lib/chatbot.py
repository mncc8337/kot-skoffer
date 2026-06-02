from ollama import AsyncClient
from lib.data_loader import Data
from discord import Interaction
import lib.bot_tools as bot_tools
from typing import Optional
import datetime
import base64


def serialize_message(message) -> dict:
    if hasattr(message, "model_dump"):
        message = message.model_dump(exclude_none=True)

    if isinstance(message, dict) and "message" in message:
        msg_obj = message["message"]
        if hasattr(msg_obj, "model_dump"):
            message = msg_obj.model_dump(exclude_none=True)

    def _json_clean(obj):
        if isinstance(obj, dict):
            return {k: _json_clean(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [_json_clean(item) for item in obj]
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode("utf-8")
        return obj

    if isinstance(message, dict):
        return _json_clean(message)

    return message


class Chatbot:
    def __init__(
        self,
        datapath,
        basemodel,
        instruction,
        ollama_api_key,
        ollama_server,
        local=None,
        max_history=-1
    ):
        if local is None:
            local = not basemodel.lower().endswith("cloud")

        self.basemodel = basemodel
        self.instruction = instruction
        self.max_history = max_history
        self.data = Data(datapath)

        self.client = AsyncClient(
            host=ollama_server,
            headers={
                # needed for web_search/fetch
                # might remove later when i made it fully local
                "Authorization": f"Bearer {ollama_api_key}"
            }
        )
        bot_tools.add_ollama_web_tools(self.client)

    def _history_slide(self, chat_data: list):
        if self.max_history < 0:
            return
        while len(chat_data) > self.max_history:
            chat_data.pop(0)

    def save_history(self):
        self.data.save()

    async def chat(
        self,
        content: str,
        role: str,
        think: str,
        no_reply: bool,
        interaction: Interaction,
        images: Optional[list[bytes]] = None,
    ):
        chat_data = self.data.get_data(interaction, [])

        instruction = {"role": "system", "content": self.instruction}
        new_messages = [instruction] + chat_data

        if role:
            user_tag = ""
            if role == "user":
                now = datetime.datetime.now()
                ts = now.strftime("%d/%m %H:%M")
                user_tag = f"[{interaction.user.display_name}, at {ts}]: "

            message = {
                "role": role,
                "content": user_tag + content
            }

            if images:
                message["images"] = images

            new_messages += [message]

            self.add_response(message, interaction)

        if no_reply:
            return

        ollama_think = "low"
        if think == "off":
            ollama_think = False
        elif think in ["low", "medium", "high"]:
            ollama_think = think

        respond = await self.client.chat(
            model=self.basemodel,
            messages=new_messages,
            think=ollama_think,
            options={
                "temperature": 1.3,
            },
            tools=bot_tools.AVAILABLE_TOOLS,
            stream=True,
        )

        return respond

    def add_response(self, message, interaction: Interaction):
        chat_data = self.data.get_data(interaction, [])
        chat_data.append(serialize_message(message))
        self._history_slide(chat_data)

    def add_bot_response(self, content, interaction: Interaction):
        self.add_response(
            {"role": "assistant", "content": content},
            interaction,
        )

    def add_tool_response(self, content, tool_name, interaction: Interaction):
        self.add_response(
            {"role": "tool", "tool_name": tool_name, "content": content},
            interaction,
        )

    def clear_history(self, interaction: Interaction):
        chat_data = self.data.get_data(interaction, [])
        chat_data.clear()

    async def get_info(self):
        info = await self.client.show(self.basemodel)

        ret = {
            "modified_at": str(info.modified_at),
        }

        raw_details = vars(info.details)
        clean_details = {key: value for key, value in raw_details.items() if value}

        return ret | clean_details

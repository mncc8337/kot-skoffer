from ollama import AsyncClient
from lib.data_loader import Data
from discord import Interaction
import lib.bot_tools as bot_tools


def serialize_message(message) -> dict:
    if hasattr(message, "model_dump"):
        return message.model_dump(exclude_none=True)

    if isinstance(message, dict) and "message" in message:
        msg_obj = message["message"]
        if hasattr(msg_obj, "model_dump"):
            return msg_obj.model_dump(exclude_none=True)

    if isinstance(message, dict):
        return {k: v for k, v in message.items() if v is not None}

    return message


class Chatbot:
    def __init__(
        self,
        datapath,
        basemodel,
        instruction,
        ollama_api_key,
        local=None,
        model="kot-skoffer",
        max_history=-1
    ):
        if local is None:
            local = not basemodel.lower().endswith("cloud")

        if local:
            self.model = model
        else:
            self.model = basemodel

        self.basemodel = basemodel
        self.instruction = instruction
        self.max_history = max_history
        self.data = Data(datapath)

        host = "https://ollama.com"
        if local:
            host = "http://localhost:11434"

        self.client = AsyncClient(
            host=host,
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

    async def exist(self):
        response = await self.client.list()
        models = response.get("models", [])
        for model in models:
            if model.model == f"{self.model}:latest":
                return True
        return False

    async def create(self, instruction):
        await self.client.create(
            model=self.model,
            from_=self.basemodel,
            system=instruction,
        )

    async def chat(
        self,
        content: str,
        role: str,
        think: str,
        no_reply: bool,
        interaction: Interaction,
    ):
        chat_data = self.data.get_data(interaction, [])

        instruction = {"role": "system", "content": self.instruction}
        new_messages = [instruction] + chat_data

        if role:
            user_tag = f"<from user {interaction.user.display_name}> "
            message = {
                "role": role,
                "content": user_tag + content
            }

            new_messages += [message]

            chat_data.append(message)
            self._history_slide(chat_data)

        if no_reply:
            return

        ollama_think = "low"
        if think == "off":
            ollama_think = False
        elif think in ["low", "medium", "high"]:
            ollama_think = think

        respond = await self.client.chat(
            model=self.model,
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
            {"role": "tool", "content": content, "tool_name": tool_name},
            interaction,
        )

    def clear_history(self, interaction: Interaction):
        chat_data = self.data.get_data(interaction, [])
        chat_data.clear()

    async def get_info(self):
        info = await self.client.show(self.model)

        ret = {
            "base_model": self.basemodel,
            "modified_at": str(info.modified_at),
        }

        raw_details = vars(info.details)
        clean_details = {key: value for key, value in raw_details.items() if value}

        if not clean_details.get("parameter_size"):
            try:
                base_info = await self.client.show(self.basemodel)
                base_details = vars(base_info.details)

                fallback_details = {
                    key: value for key, value in base_details.items() if value
                }

                clean_details = fallback_details | clean_details
            except Exception:

                pass

        return ret | clean_details

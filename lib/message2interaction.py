import discord


class MessageInteractionAdapter:
    def __init__(self, message: discord.Message):
        self.message = message
        self.user = message.author
        self.guild = message.guild
        self.channel = message.channel

        if hasattr(self.guild, "id"):
            self.guild_id = self.guild.id
        else:
            self.guild_id = None

        self.id = message.id

        self.response = self
        self.followup = self

        self._typing_context = None

    async def defer(self, *args, **kwargs):
        try:
            if self._typing_context is None:
                self._typing_context = self.message.channel.typing()
                await self._typing_context.__aenter__()
        except Exception:
            pass

    async def _stop_typing(self):
        if not self._typing_context:
            return

        try:
            await self._typing_context.__aexit__(None, None, None)
        except Exception:
            pass
        self._typing_context = None

    async def send_message(self, content=None, *args, **kwargs):
        await self._stop_typing()
        return await self.message.reply(content=content)

    async def send(self, content=None, *args, **kwargs):
        await self._stop_typing()
        return await self.message.reply(content=content)

    async def edit_message(self, message_id, content=None, *args, **kwargs):
        await self._stop_typing()
        try:
            msg = await self.message.channel.fetch_message(message_id)
            return await msg.edit(content=content)
        except Exception as e:
            print(f"kot: error while editing fake interaction message: {e}")

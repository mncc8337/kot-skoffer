import discord


class MessageInteractionAdapter:
    def __init__(self, message: discord.Message):
        self.message = message
        self.user = message.author
        self.guild = message.guild
        self.channel = message.channel

        self.id = message.id

        self.response = self
        self.followup = self

    async def defer(self, *args, **kwargs):
        try:
            await self.message.channel.typing()
        except Exception:
            pass

    async def send_message(self, content=None, *args, **kwargs):
        return await self.message.channel.send(content=content)

    async def send(self, content=None, *args, **kwargs):
        return await self.message.channel.send(content=content)

    async def edit_message(self, message_id, content=None, *args, **kwargs):
        try:
            msg = await self.message.channel.fetch_message(message_id)
            return await msg.edit(content=content)
        except Exception as e:
            print(f"kot: error while editing fake interaction message: {e}")

from discord import Interaction, Message
from discord.ext.commands import Bot
from lib.wiktionary import Wiktionary
import cog.wiktionary
import lib.data_loader as data_loader
from lib.message2interaction import MessageInteractionAdapter
from urllib.parse import quote
import random
import unicodedata

CATEGORY = "Thể loại:Mục từ tiếng Việt"


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold().strip()


def _default_table():
    return {
        "started": False,
        "skip_users": [],
        "chain": [],
        "next_syllable": "",
        "incorrect_count": 0,
        "channel_id": -1,
        "autism": False,
    }


class NoiTu(Wiktionary, data_loader.Data):
    def __init__(self, user_agent: str):
        Wiktionary.__init__(self, "vi.wiktionary.org", user_agent)
        data_loader.Data.__init__(self, "data/noitu.json")

    def _noitiep(self, prefix: str):
        word_list = self.prefix_match(
            _normalize(prefix).split()[-1] + " ",
            CATEGORY,
        )

        filtered = []

        for word in word_list:
            if len(word.split()) == 2:
                filtered.append(_normalize(word))

        return filtered

    async def _bot_turn(
        self,
        next_word_pool,
        interaction,
        data,
        target_id,
        target_type,
        bot: Bot,
    ):
        bot_attempt = _normalize(random.choice(next_word_pool))
        bot_syllables = bot_attempt.split()
        bot_message = await interaction.channel.send(bot_attempt)

        await bot_message.add_reaction("✅")
        data["chain"].append(bot_attempt)
        data["next_syllable"] = bot_syllables[1]

        # win check
        nextw = self._noitiep(bot_syllables[1])

        if len(nextw) == 0:
            await bot_message.reply(
                content=f"{bot.user.display_name} thắng\ngame kết thúc. độ dài chuỗi: {len(data["chain"])}"
            )
            await self._start_game(data, target_id, target_type, interaction)

    async def _start_game(self, data, target_id, target_type, interaction: Interaction):
        result = self.random_word(CATEGORY)
        if result is None:
            await interaction.response.send_message(
                "không lấy được từ ngẫu nhiên",
                ephemeral=True,
            )
            return

        newword = _normalize(result[1].lower())
        data["chain"] = [newword]
        data["started"] = True
        data["skip_users"].clear()
        data["next_syllable"] = newword.split(" ")[-1]
        data["incorrect_count"] = 0
        data["channel_id"] = interaction.channel.id

        self.save_data(data, target_id, target_type)

        await interaction.response.send_message(
            "bắt đầu game mới. từ hiện tại: **" + newword + "**"
        )

    async def _end_game(self, data, target_id, target_type, interaction: Interaction):
        data["started"] = False
        data["skip_users"].clear()
        data["chain"].clear()
        data["next_syllable"] = ""
        data["incorrect_count"] = 0
        data["channel_id"] = -1

        self.save_data(data, target_id, target_type)

        await interaction.response.send_message("đã kết thúc game")

    async def batdau(self, interaction: Interaction):
        if interaction.guild is not None:
            await interaction.response.send_message(
                "lệnh này chỉ dùng được trong DM",
                ephemeral=True,
            )
            return

        data, target_id, target_type = self.get_data(interaction, _default_table())

        if data["started"]:
            await interaction.response.send_message(
                "game hiện tại chưa kết thúc",
                ephemeral=True,
            )
            return

        await self._start_game(data, target_id, target_type, interaction)

    async def ketthuc(self, interaction: Interaction):
        if interaction.guild is not None:
            await interaction.response.send_message(
                "lệnh này chỉ dùng được trong DM",
                ephemeral=True,
            )
            return

        data, target_id, target_type = self.get_data(interaction, _default_table())

        if not data["started"]:
            await interaction.response.send_message(
                "game hiện tại chưa bắt đầu",
                ephemeral=True,
            )
            return

        await self._end_game(data, target_id, target_type, interaction)

    async def gameloop(self, interaction: Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "lệnh này chỉ dùng được trong server",
                ephemeral=True,
            )
            return

        data, target_id, target_type = self.get_data(interaction, _default_table())

        if data["started"]:
            await self._end_game(data, target_id, target_type, interaction)
        else:
            await self._start_game(data, target_id, target_type, interaction)

    async def boqua(self, interaction: Interaction):
        data, target_id, target_type = self.get_data(interaction, _default_table())

        if not data["started"]:
            await interaction.response.send_message(
                "game chưa bắt đầu, có bị ngu ko?",
                ephemeral=True,
            )
            return

        if interaction.guild is None:
            await self._start_game(data, target_id, target_type, interaction)
            return

        if interaction.user.id in data["skip_users"]:
            await interaction.response.send_message(
                "m đã vote skip rồi, cút",
                ephemeral=True,
            )
            return

        data["skip_users"].append(interaction.user.id)
        skip_count = len(data["skip_users"])
        if skip_count < 3:
            await interaction.response.send_message(
                f"đã vote bỏ qua ({skip_count}/3)",
            )
            self.save_data(data, target_id, target_type)
            return

        await self._start_game(data, target_id, target_type, interaction)

    async def chuoi(self, interaction: Interaction):
        data, _, _ = self.get_data(interaction, _default_table())

        if not data["started"]:
            await interaction.response.send_message(
                "game hiện tại chưa bắt đầu",
                ephemeral=True,
            )
            return

        chain = data["chain"][0]
        for word in data["chain"][1:]:
            chain += "->" + word

        await interaction.response.send_message(chain)

    async def tuky(self, interaction: Interaction, bot: Bot):
        if interaction.guild is None:
            await interaction.response.send_message(
                "lệnh này chỉ dùng được trong server",
                ephemeral=True,
            )
            return

        data, target_id, target_type = self.get_data(interaction, _default_table())
        data["autism"] = not data["autism"]

        if data["autism"]:
            await interaction.response.send_message(
                "đã bật chế độ tự kỷ",
                ephemeral=True,
            )
            await self._bot_turn(
                self._noitiep(data["next_syllable"]),
                interaction,
                data,
                target_id,
                target_type,
                bot
            )
        else:
            await interaction.response.send_message(
                "đã tắt chế độ tự kỷ",
                ephemeral=True,
            )

    async def dinhnghia(self, interaction: Interaction, word: str):
        await interaction.response.defer()

        page_id = self.exact_match(
            word,
            CATEGORY,
        )

        if page_id < 0:
            await interaction.followup.send(content="không tìm thấy từ trong từ điển")
            return

        await cog.wiktionary._send_followup_result(interaction.followup, self, page_id)

    async def noitiep(self, interaction: Interaction, prefix: str):
        data, _, _ = self.get_data(interaction, _default_table())

        if data["started"]:
            await interaction.response.send_message(
                "game đã bắt đầu, không thể tra từ",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        word_list = self._noitiep(prefix)

        resp = ""
        for word in word_list:
            safe_word = quote(word.replace(" ", "_"), safe="")
            word_url = f"https://{self.base_url}/wiki/{safe_word}"
            resp += f"- [{word}]({word_url})\n"

        if not resp:
            await interaction.followup.send(content="không có từ nào để nối")
        else:
            await interaction.followup.send(
                content="các từ có thể nối tiếp:\n" + resp, suppress_embeds=True
            )

    async def handle_gameloop_message(self, bot: Bot, message: Message):
        interaction = MessageInteractionAdapter(message)

        data, target_id, target_type = self.get_data(interaction, _default_table())
        if not data["started"] or message.channel.id != data["channel_id"]:
            return

        async def reject_attempt(msg):
            await message.add_reaction("❌")
            data["incorrect_count"] += 1
            retry_count = 3 - data["incorrect_count"]
            if retry_count > 0:
                await message.reply(content=f"{msg}. số lần thử lại {retry_count}/3")
                self.save_data(data, target_id, target_type)
            else:
                new_msg = await message.reply(
                    content=f"{msg}\ngame kết thúc. độ dài chuỗi: {len(data["chain"])}"
                )
                await self._start_game(
                    data,
                    target_id,
                    target_type,
                    MessageInteractionAdapter(new_msg)
                )

        syllables = _normalize(message.content).split()
        if len(syllables) != 2:
            return

        attempt = syllables[0] + " " + syllables[1]

        if syllables[0] != data["next_syllable"]:
            await reject_attempt("từ hiện tại không nối với từ lúc trước")
            return
        page_id = self.exact_match(
            syllables[0] + " " + syllables[1],
            CATEGORY,
        )
        if page_id == -1:
            await reject_attempt("từ không tồn tại")
            return

        data["chain"].append(attempt)
        data["next_syllable"] = syllables[1]
        data["incorrect_count"] = 0
        data["skip_users"].clear()
        await message.add_reaction("✅")

        # win check
        nextw = self._noitiep(syllables[1])

        if len(nextw) == 0:
            await message.reply(
                content=f"{message.author.display_name} thắng\ngame kết thúc. độ dài chuỗi: {len(data["chain"])}"
            )
            await self._start_game(data, target_id, target_type, interaction)
            return

        # bot turn
        if message.guild is None or data["autism"]:
            await self._bot_turn(
                nextw,
                interaction,
                data,
                target_id,
                target_type,
                bot
            )

        self.save_data(data, target_id, target_type)

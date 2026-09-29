from discord import Interaction, Message
from lib.wordengine import WordEngine, ViWiktionaryEngine, MinhqndEngine
import lib.data_loader as data_loader
from lib.message2interaction import MessageInteractionAdapter
import random


def _default_table():
    return {
        "started": False,
        "skip_users": [],
        "chain": [],
        "next_syllable": "",
        "incorrect_count": 0,
        "channel_id": -1,
        "autistic": False,
    }


class NoiTu(data_loader.Data):
    def __init__(self, user_agent: str):
        super().__init__("data/noitu.json")
        self.user_agent = user_agent
        self.engine: WordEngine

    async def _noitiep(self, prefix: str) -> list[str]:
        next_syllable = self.engine.normalize(prefix.split()[-1])
        possible_syllables = self.engine.possible_syllables(next_syllable)

        word_list = set()

        for syllable in possible_syllables:
            search_result = await self.engine.prefix(syllable + " ")
            word_list.update(search_result)

        return [
            self.engine.normalize(word) for word in word_list if len(word.split()) == 2
        ]

    async def _word_check(
        self,
        message: Message,
        data,
        target_id: int,
        target_type: str,
        syllables: tuple[str, str],
    ) -> bool:
        async def reject_attempt(msg):
            await message.add_reaction("❌")
            data["incorrect_count"] += 1
            retry_count = 3 - data["incorrect_count"]

            if retry_count > 0:
                await message.reply(content=f"{msg}. số lần thử lại {retry_count}/3")
                self.save_data(data, target_id, target_type)
            else:
                new_msg = await message.reply(
                    content=(
                        f"{msg}\ngame kết thúc. " f"độ dài chuỗi: {len(data["chain"])}"
                    )
                )

                await self._start_game(
                    data,
                    target_id,
                    target_type,
                    MessageInteractionAdapter(new_msg),
                )

        for prev_attempt in data["chain"]:
            if self.engine.compare_words(
                prev_attempt,
                " ".join(syllables),
            ):
                await reject_attempt("từ đã lặp lại")
                return False

        # TODO: loop through all possible syllables combs
        if not await self.engine.exact(" ".join(syllables)):
            await reject_attempt("từ không tồn tại")
            return False

        return True

    async def _bot_turn(
        self,
        next_word_pool,
        interaction,
        data,
        target_id,
        target_type,
        bot_display_name,
    ):
        if not next_word_pool:
            return

        async with interaction.channel.typing():
            bot_attempt = self.engine.normalize(random.choice(next_word_pool))
            bot_syllables = bot_attempt.split()

            bot_message = await interaction.channel.send(bot_attempt)

        await bot_message.add_reaction("✅")

        data["chain"].append(bot_attempt)
        data["next_syllable"] = bot_syllables[1]

        async with interaction.channel.typing():
            nextw = await self._noitiep(bot_syllables[1])

            if len(nextw) == 0:
                chain = "->".join(data["chain"])
                msg = (
                    f"{bot_display_name} thắng\n"
                    f"game kết thúc. "
                    f"độ dài chuỗi: {len(data["chain"])}\n"
                    f"{chain}"
                )

                await bot_message.reply(content=msg)

                await self._start_game(
                    data,
                    target_id,
                    target_type,
                    MessageInteractionAdapter(bot_message),
                )

    async def _start_game(
        self,
        data,
        target_id,
        target_type,
        interaction: Interaction,
    ):
        await interaction.response.defer()

        result = None
        nextw = []

        while not nextw:
            result = await self.engine.random_word()

            if not result:
                continue

            nextw = await self._noitiep(result)

        newword = self.engine.normalize(result)

        data["chain"] = [newword]
        data["started"] = True
        data["skip_users"].clear()
        data["next_syllable"] = newword.split(" ")[-1]
        data["incorrect_count"] = 0
        data["channel_id"] = interaction.channel.id

        self.save_data(data, target_id, target_type)

        await interaction.followup.send(
            "bắt đầu game mới. từ hiện tại: **" + newword + "**"
        )

    async def _end_game(
        self,
        data,
        target_id,
        target_type,
        interaction: Interaction,
    ):
        data["started"] = False
        data["skip_users"].clear()
        data["chain"].clear()
        data["next_syllable"] = ""
        data["incorrect_count"] = 0
        data["channel_id"] = -1

        self.save_data(data, target_id, target_type)

        await interaction.response.send_message("đã kết thúc game")

    async def init(self, viwiktionary: bool):
        await self.use_engine(viwiktionary)

    async def use_engine(self, viwiktionary: bool):
        if viwiktionary:
            self.engine = ViWiktionaryEngine(self.user_agent)
        else:
            self.engine = MinhqndEngine(self.user_agent)
            await self.engine.download_db()

    async def batdau(self, interaction: Interaction):
        if interaction.guild is not None:
            await interaction.response.send_message(
                "lệnh này chỉ dùng được trong DM",
                ephemeral=True,
            )
            return

        data, target_id, target_type = self.get_data(
            interaction,
            _default_table(),
        )

        if data["started"]:
            await interaction.response.send_message(
                "game hiện tại chưa kết thúc",
                ephemeral=True,
            )
            return

        await self._start_game(
            data,
            target_id,
            target_type,
            interaction,
        )

    async def ketthuc(self, interaction: Interaction):
        if interaction.guild is not None:
            await interaction.response.send_message(
                "lệnh này chỉ dùng được trong DM",
                ephemeral=True,
            )
            return

        data, target_id, target_type = self.get_data(
            interaction,
            _default_table(),
        )

        if not data["started"]:
            await interaction.response.send_message(
                "game hiện tại chưa bắt đầu",
                ephemeral=True,
            )
            return

        await self._end_game(
            data,
            target_id,
            target_type,
            interaction,
        )

    async def gameloop(self, interaction: Interaction):
        if interaction.guild is None:
            await interaction.response.send_message(
                "lệnh này chỉ dùng được trong server",
                ephemeral=True,
            )
            return

        data, target_id, target_type = self.get_data(
            interaction,
            _default_table(),
        )

        if data["started"]:
            await self._end_game(
                data,
                target_id,
                target_type,
                interaction,
            )
        else:
            await self._start_game(
                data,
                target_id,
                target_type,
                interaction,
            )

    async def boqua(self, interaction: Interaction):
        data, target_id, target_type = self.get_data(
            interaction,
            _default_table(),
        )

        if not data["started"]:
            await interaction.response.send_message(
                "game chưa bắt đầu, có bị ngu ko?",
                ephemeral=True,
            )
            return

        if interaction.guild is None or data["autistic"]:
            await self._start_game(
                data,
                target_id,
                target_type,
                interaction,
            )
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
            self.save_data(
                data,
                target_id,
                target_type,
            )
            return

        await self._start_game(
            data,
            target_id,
            target_type,
            interaction,
        )

    async def chuoi(self, interaction: Interaction):
        data, _, _ = self.get_data(
            interaction,
            _default_table(),
        )

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

    async def tuky(
        self,
        interaction: Interaction,
        bot_display_name: str,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "lệnh này chỉ dùng được trong server",
                ephemeral=True,
            )
            return

        data, target_id, target_type = self.get_data(
            interaction,
            _default_table(),
        )

        data["autistic"] = not data["autistic"]

        if data["autistic"]:
            await interaction.response.send_message(
                "đã bật chế độ tự kỷ",
            )

            if data["started"]:
                nextw = await self._noitiep(data["next_syllable"])

                filtered = [
                    word
                    for word in nextw
                    if not any(
                        self.engine.compare_words(word, used) for used in data["chain"]
                    )
                ]

                await self._bot_turn(
                    filtered,
                    interaction,
                    data,
                    target_id,
                    target_type,
                    bot_display_name,
                )
        else:
            await interaction.response.send_message(
                "đã tắt chế độ tự kỷ",
            )

        self.save_data(
            data,
            target_id,
            target_type,
        )

    async def dinhnghia(
        self,
        interaction: Interaction,
        word: str,
    ):
        await interaction.response.defer()

        def_str, noerror = await self.engine.definition(word)

        # TODO: use noerror
        await interaction.followup.send(
            content=def_str,
            suppress_embeds=True,
        )

    async def noitiep(
        self,
        interaction: Interaction,
        prefix: str,
    ):
        data, _, _ = self.get_data(
            interaction,
            _default_table(),
        )

        if data["started"] and not data["autistic"]:
            await interaction.response.send_message(
                "game đã bắt đầu, không thể tra từ",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        word_list = await self._noitiep(prefix)

        resp = ""

        for word in random.sample(word_list, min(10, len(word_list))):
            resp += f"- [{word}]({await self.engine.word_url(word)})\n"

        if not resp:
            await interaction.followup.send(content="không có từ nào để nối")
        else:
            await interaction.followup.send(
                content="các từ có thể nối tiếp:\n" + resp,
                suppress_embeds=True,
            )

    async def handle_gameloop_message(
        self,
        bot_display_name: str,
        message: Message,
    ):
        interaction = MessageInteractionAdapter(message)

        data, target_id, target_type = self.get_data(
            interaction,
            _default_table(),
        )

        if not data["started"] or message.channel.id != data["channel_id"]:
            return

        syllables = self.engine.normalize(message.content).split()

        if len(syllables) != 2:
            return

        if not self.engine.compare_syllables(
            syllables[0],
            data["next_syllable"],
        ):
            return

        async with message.channel.typing():
            if not await self._word_check(
                message,
                data,
                target_id,
                target_type,
                syllables,
            ):
                return

        data["chain"].append(" ".join(syllables))
        data["next_syllable"] = syllables[1]
        data["incorrect_count"] = 0
        data["skip_users"].clear()

        async with message.channel.typing():
            nextw = await self._noitiep(syllables[1])

            filtered = [
                word
                for word in nextw
                if not any(
                    self.engine.compare_words(word, used) for used in data["chain"]
                )
            ]

            await message.add_reaction("✅")

        if len(filtered) == 0:
            chain = "->".join(data["chain"])
            msg = (
                f"{message.author.display_name} thắng\n"
                f"game kết thúc. "
                f"độ dài chuỗi: {len(data["chain"])}\n"
                f"{chain}"
            )

            await message.reply(content=msg)

            await self._start_game(
                data,
                target_id,
                target_type,
                interaction,
            )

        elif message.guild is None or data["autistic"]:
            await self._bot_turn(
                filtered,
                interaction,
                data,
                target_id,
                target_type,
                bot_display_name,
            )

        self.save_data(
            data,
            target_id,
            target_type,
        )

from discord import Interaction, Message
from lib.wordengine import WordEngine, ViWiktionaryEngine, MinhqndEngine
import lib.data_loader as data_loader
from lib.message2interaction import MessageInteractionAdapter
import random
import asyncio
from functools import wraps
from collections.abc import Callable


def mutex(get_lock: Callable):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            async with get_lock(self, *args, **kwargs):
                return await func(self, *args, **kwargs)

        return wrapper

    return decorator


def _get_chunks(words):
    chunks = []
    current_chunk = ""

    for word in words:
        if not current_chunk:
            current_chunk = word
        elif len(current_chunk) + len(word) + 2 > 1950:
            chunks.append(current_chunk)
            current_chunk = word
        else:
            current_chunk += f"->{word}"

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _default_table():
    return {
        "started": False,
        "skip_users": [],
        "chain": [],
        "next_syllable": "",
        "incorrect_count": 0,
        "channel_id": -1,
        "autistic": False,
        "last_user": {
            "userid": -1,
            "mention": "",
        },
    }


class NoiTu(data_loader.Data):
    def __init__(self, user_agent: str):
        super().__init__("data/noitu.json")
        self.user_agent = user_agent
        self.engine: WordEngine
        self.locks: dict[int, asyncio.Lock] = {}

    def _get_lock(self, channel_id: int):
        if channel_id not in self.locks:
            self.locks[channel_id] = asyncio.Lock()
        return self.locks[channel_id]

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
                mention = data["last_user"]["mention"]
                if not mention:
                    mention = "không ai"

                chunks = _get_chunks(data["chain"])

                msg = (
                    f"{msg}\ngame kết thúc. {mention} thắng\n"
                    f"độ dài chuỗi: {len(data["chain"]) - 1}\n"
                )

                if len(chunks[0]) + len(msg) < 1950:
                    new_msg = await message.reply(content=msg + chunks[0])
                    start_chunk = 1
                else:
                    new_msg = await message.reply(content=msg)
                    start_chunk = 0

                for i in range(start_chunk, len(chunks)):
                    await message.channel.send(content=chunks[i])

                await self._start_game(
                    data,
                    target_id,
                    target_type,
                    MessageInteractionAdapter(new_msg),
                )

        all_combs = self.engine.possible_words(" ".join(syllables))
        for prev_attempt in data["chain"]:
            if any(self.engine.compare_words(word, prev_attempt) for word in all_combs):
                await reject_attempt("từ đã lặp lại")
                return False

        has_valid_word = False
        for word in all_combs:
            if await self.engine.exact(word):
                has_valid_word = True
                break
        if not has_valid_word:
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

        data["last_user"]["mention"] = bot_display_name
        data["last_user"]["userid"] = -1

        data["chain"].append(bot_attempt)
        data["next_syllable"] = bot_syllables[1]

        async with interaction.channel.typing():
            nextw = await self._noitiep(bot_syllables[1])

            if len(nextw) == 0:
                chain = "->".join(data["chain"])
                msg = (
                    f"{bot_display_name} thắng\n"
                    f"game kết thúc. "
                    f"độ dài chuỗi: {len(data["chain"]) - 1}\n"
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
        last_user = data["last_user"]
        last_user["userid"] = -1
        last_user["mention"] = ""

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
        last_user = data["last_user"]
        last_user["userid"] = -1
        last_user["mention"] = ""

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

    @mutex(lambda self, interaction: self._get_lock(interaction.channel.id))
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

    @mutex(lambda self, interaction: self._get_lock(interaction.channel.id))
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

    @mutex(lambda self, interaction: self._get_lock(interaction.channel.id))
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
            if data["channel_id"] != interaction.channel.id:
                await interaction.response.send_message(
                    "một gameloop khác đã được"
                    f"kích hoạt tại {interaction.channel.name}",
                    ephemeral=True,
                )
                return

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

    @mutex(lambda self, interaction: self._get_lock(interaction.channel.id))
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

    @mutex(lambda self, interaction: self._get_lock(interaction.channel.id))
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

        words = data["chain"]
        if not words:
            await interaction.response.send_message("Chuỗi hiện tại đang trống.")
            return

        chunks = _get_chunks(words)

        await interaction.response.send_message(chunks[0])

        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)

    @mutex(lambda self, interaction, _: self._get_lock(interaction.channel.id))
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
                nextw_pool = await self._noitiep(data["next_syllable"])

                filtered = [
                    word
                    for word in nextw_pool
                    for nword in self.engine.possible_words(word)
                    if not any(
                        self.engine.compare_words(nword, used) for used in data["chain"]
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

    @mutex(lambda self, _, message: self._get_lock(message.channel.id))
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
        last_user = data["last_user"]

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

        if last_user["userid"] == message.author.id:
            await message.reply("cút, ai cho trả lời liên tục")
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
        last_user["userid"] = message.author.id
        last_user["mention"] = message.author.mention

        async with message.channel.typing():
            nextw_pool = await self._noitiep(syllables[1])

            filtered = [
                word
                for word in nextw_pool
                for nword in self.engine.possible_words(word)
                if not any(
                    self.engine.compare_words(nword, used) for used in data["chain"]
                )
            ]

            await message.add_reaction("✅")

        if len(filtered) == 0:
            chunks = _get_chunks(data["chain"])
            msg = (
                f"{message.author.mention} thắng\n"
                f"game kết thúc. "
                f"độ dài chuỗi: {len(data["chain"]) - 1}\n"
            )

            if len(chunks[0]) + len(msg) < 1950:
                await message.reply(content=msg + chunks[0])
                start_chunk = 1
            else:
                await message.reply(content=msg)
                start_chunk = 0

            for i in range(start_chunk, len(chunks)):
                await message.channel.send(content=chunks[i])

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

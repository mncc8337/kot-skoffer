from abc import ABC, abstractmethod
import random
import asyncio
import unicodedata
from urllib.parse import quote

from lib.wiktionary import Wiktionary
from lib.minhqnd import Minhqnd

WIKTIONARY_CATEGORY = "Thể loại:Mục từ tiếng Việt"


class WordEngine(ABC):
    _TONE_MARKS = {
        "\u0301",  # sắc
        "\u0300",  # huyền
        "\u0309",  # hỏi
        "\u0303",  # ngã
        "\u0323",  # nặng
    }

    @staticmethod
    def normalize(text: str) -> str:
        return unicodedata.normalize("NFC", text).casefold().strip()

    @staticmethod
    def structify_syllable(
        syllable: str,
    ) -> tuple[str, str | None]:
        text = (
            unicodedata.normalize(
                "NFD",
                syllable,
            )
            .casefold()
            .strip()
        )

        letters = []
        tone = None

        for char in text:
            if char in WordEngine._TONE_MARKS:
                tone = char
            elif unicodedata.combining(char):
                letters.append(char)
            else:
                letters.append(char)

        return "".join(letters), tone

    @staticmethod
    def compare_syllables(
        syl1: str,
        syl2: str,
    ) -> bool:
        ssyl1 = WordEngine.structify_syllable(syl1)
        ssyl2 = WordEngine.structify_syllable(syl2)

        return ssyl1[0] == ssyl2[0] and ssyl1[1] == ssyl2[1]

    @staticmethod
    def compare_words(
        word1: str,
        word2: str,
    ) -> bool:
        splitted1 = word1.split()
        splitted2 = word2.split()

        if len(splitted1) != len(splitted2):
            return False

        return all(
            WordEngine.compare_syllables(s1, s2) for s1, s2 in zip(splitted1, splitted2)
        )

    @staticmethod
    def possible_syllables(
        syllable: str,
    ) -> list[str]:
        syllable = WordEngine.normalize(syllable)
        stripped, tone = WordEngine.structify_syllable(syllable)

        if tone is None:
            return [unicodedata.normalize("NFC", stripped)]

        chars = list(stripped)
        result = []

        i = 0
        while i < len(chars):
            if chars[i] not in "aeiouy":
                i += 1
                continue

            j = i + 1

            while j < len(chars) and unicodedata.combining(chars[j]):
                j += 1

            candidate = "".join(chars[:j]) + tone + "".join(chars[j:])

            result.append(unicodedata.normalize("NFC", candidate))

            i = j

        return result

    @abstractmethod
    async def prefix(self, prefix: str) -> list[str]: ...

    @abstractmethod
    async def exact(self, word: str) -> bool: ...

    @abstractmethod
    async def definition(self, word: str) -> tuple[str, bool]: ...

    @abstractmethod
    async def random_word(self) -> str: ...

    @abstractmethod
    async def word_url(self, word: str) -> str: ...


class ViWiktionaryEngine(WordEngine, Wiktionary):
    def __init__(self, user_agent: str):
        Wiktionary.__init__(
            self,
            "vi.wiktionary.org",
            user_agent,
        )

    async def prefix(self, prefix: str) -> list[str]:
        result = None

        while result is None:
            result = await self.prefix_match(
                prefix,
                WIKTIONARY_CATEGORY,
            )
            if result is None:
                await asyncio.sleep(3)

        return list(result.keys())

    async def exact(self, word: str) -> bool:
        result = None

        while result is None:
            result = await self.exact_match(
                word,
                WIKTIONARY_CATEGORY,
            )

        return result >= 0

    async def definition(self, word: str) -> tuple[str, bool]:
        page_id = await self.exact_match(word)
        if page_id < 0:
            return "không tìm thấy từ trong từ điển", False

        def_res = await self.definitions_by_id(page_id)
        if def_res is None:
            return "không thể search định nghĩa ngay bây giờ", False

        defs, word = def_res

        if word is None:
            return "không tìm thấy từ trong từ điển", False

        parts = []

        for lang, definitions in defs.items():
            formatted = self.definitions_to_string(definitions)

            parts.append(f"**{lang}**\n{formatted}")

        description = "\n\n".join(parts)
        description += "\n\n*Định nghĩa được lấy từ [vi.wiktionary.org](https://vi.wiktionary.org)*"

        return description, True

    async def random_word(self) -> str:
        result = None

        while result is None:
            result = await Wiktionary.random_word(
                self,
                WIKTIONARY_CATEGORY,
            )
            if result is None:
                await asyncio.sleep(3)

        return result[1]

    async def word_url(self, word: str) -> str:
        return f"https://vi.wiktionary.org/wiki/{word.replace(' ', '_')}"


class MinhqndEngine(WordEngine, Minhqnd):
    def __init__(self, user_agent: str):
        Minhqnd.__init__(self, user_agent)

    async def prefix(self, prefix: str) -> list[str]:
        return await self.prefix_match(prefix)

    async def exact(self, word: str) -> bool:
        return await self.exact_match(word)

    async def definition(self, word: str) -> tuple[str, bool]:
        lookup_result = await self.lookup(word, "vi", "vi")
        if lookup_result is None:
            return "không thể search định nghĩa ngay bây giờ", False
        if not lookup_result["exists"]:
            return "không tìm thấy từ trong từ điển", False

        ret_str = ""
        for res in lookup_result["results"]:
            for rel in res["relations"]:
                ret_str += f"+ {rel["relation_type"]}: {rel["related_word"]}\n"
            for d in res["meanings"]:
                new_def = "- "
                if d.get("pos", None) is not None:
                    new_def += d["pos"]
                    if d.get("sub_pos", None) is not None:
                        new_def += ", " + d["sub_pos"]
                    new_def += ": "
                new_def += d["definition"] + "\n"
                if d.get("example", None) is not None:
                    new_def += f"vd: *{d["example"]}*\n"
                new_def += "xem thêm: " + ", ".join(d["links"]) + "\n"
                new_def += f"*nguồn: {d["source"]}*\n"
                ret_str += new_def
        ret_str += (
            "*định nghĩa được lấy từ [dict.minhqnd.com](https://dict.minhqnd.com)*"
        )

        return ret_str, True

    async def random_word(self) -> str:
        words = []

        for dictionary in self.dictionaries.values():
            for first, seconds in dictionary.items():
                words.extend(f"{first} {second}" for second in seconds)

        if not words:
            return ""

        return random.choice(words)

    async def word_url(self, word: str) -> str:
        return f"https://dict.minhqnd.com/word/{quote(word)}"

# various data from minhqnd
# https://dict.minhqnd.com
# and https://github.com/minhqnd/Noi-Tu-Discord

import aiohttp
import asyncio
import hashlib
import json
from pathlib import Path

DICT1_SRC = (
    "https://raw.githubusercontent.com/minhqnd/Noi-Tu-Discord/"
    "refs/heads/main/src/assets/wordPairs.json"
)

DICT2_SRC = (
    "https://raw.githubusercontent.com/minhqnd/Noi-Tu-Discord/"
    "refs/heads/main/src/assets/customWords.json"
)

DICT_DIR = Path("data/")


class Minhqnd:
    def __init__(self, user_agent: str):
        self.api_url = "https://dict.minhqnd.com/api/v1/"

        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": user_agent,
            }
        )

        self.dictionaries: dict[str, dict[str, list[str]]] = {}

    async def _download_file(self, name: str, url: str):
        path = DICT_DIR / name
        hash_path = DICT_DIR / f"{name}.sha256"

        async with self.session.get(url) as response:
            if response.status != 200:
                return None

            content = await response.read()

        new_hash = hashlib.sha256(content).hexdigest()

        if path.exists() and hash_path.exists():
            old_hash = hash_path.read_text().strip()

            if old_hash == new_hash:
                return

        path.write_bytes(content)
        hash_path.write_text(new_hash)

    async def download_db(self):
        DICT_DIR.mkdir(parents=True, exist_ok=True)

        await asyncio.gather(
            self._download_file(
                "minhqnd-wordPairs.json",
                DICT1_SRC,
            ),
            self._download_file(
                "minhqnd-customWords.json",
                DICT2_SRC,
            ),
        )

        for filename in (
            "minhqnd-wordPairs.json",
            "minhqnd-customWords.json",
        ):
            path = DICT_DIR / filename

            with path.open("r", encoding="utf-8") as file:
                self.dictionaries[filename] = json.load(file)

    async def exact_match(self, word: str) -> bool:
        syllables = word.casefold().strip().split()

        if len(syllables) != 2:
            return False

        first, second = syllables

        for dictionary in self.dictionaries.values():
            words = dictionary.get(first)

            if words is not None and second in words:
                return True

        return False

    async def prefix_match(self, prefix: str) -> list[str]:
        prefix = prefix.casefold().strip()

        result = set()

        for dictionary in self.dictionaries.values():
            for second in dictionary.get(prefix, []):
                result.add(f"{prefix} {second}")

        return list(result)

    async def lookup(
        self,
        word: str,
        lang: str = "vi",
        def_lang: str = "vi",
    ) -> dict | None:
        params = {
            "word": word,
            "lang": lang,
            "def_lang": def_lang,
        }

        async with self.session.get(
            f"{self.api_url}lookup",
            params=params,
        ) as response:
            # 404 is already handled by the server
            # and is expected to always have a valid json
            return await response.json()

    async def suggest(self, prefix: str) -> dict | None:
        params = {
            "q": prefix,
        }

        async with self.session.get(
            f"{self.api_url}suggest",
            params=params,
        ) as response:
            if response.status != 200:
                return None

            return await response.json()

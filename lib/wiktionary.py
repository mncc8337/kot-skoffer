import re
import aiohttp
import asyncio
from urllib.parse import unquote, urlsplit, parse_qs

_LANGUAGE_NAMES = {
    "vie": "Vietnamese",
    "eng": "English",
    "spa": "Spanish",
    "fra": "French",
    "deu": "German",
    "ita": "Italian",
    "por": "Portuguese",
    "nld": "Dutch",
    "ron": "Romanian",
    "rus": "Russian",
    "jpn": "Japanese",
    "kor": "Korean",
    "zho": "Chinese",
    "ara": "Arabic",
    "sqi": "Albanian",
    "ell": "Greek",
    # im done with this shit
    "{{langname|vi}}": "Vietnamese",
}


def _language_name(code: str) -> str:
    code = code.strip().lower()
    return _LANGUAGE_NAMES.get(code, code)


def _template_to_link(match, base_wiki_url: str) -> str:
    # name = match.group("name").lower()
    args = match.group("args")

    parts = [part.strip() for part in args.split("|")]

    if len(parts) < 2:
        return ""

    # {{l|en|acid}}
    # {{m|la|acidus}}
    # {{t|es|ácido}}
    # lang = parts[0]
    term = parts[1]

    if not term:
        return ""

    alt = None

    for part in parts[2:]:
        if part.startswith("alt="):
            alt = part[4:].strip()
            break

    display = alt or term

    url_target = term.replace(" ", "_")

    return f"[{display}]({base_wiki_url}/{url_target})"


def _replace_link(match, base_wiki_url: str) -> str:
    target = match.group(1).strip()
    display = match.group(2).strip() if match.group(2) else target

    url_target = target.replace(" ", "_")

    return f"[{display}]({base_wiki_url}/{url_target})"


def _clean_wikitext(text: str, base_wiki_url: str) -> str:
    d = text

    # {{gloss|foo}} -> (foo)
    d = re.sub(
        r"\{\{gloss\|([^{}]+)\}\}",
        r"(\1)",
        d,
        flags=re.IGNORECASE,
    )

    # {{term|foo}} -> (foo)
    d = re.sub(
        r"\{\{term\|([^{}]+)\}\}",
        r"(\1)",
        d,
        flags=re.IGNORECASE,
    )

    # templates
    d = re.sub(
        r"""
        \{\{
            (?P<name>l\+?|m\+?|t\+?)
            \|
            (?P<args>[^{}]+?)
        \}\}
        """,
        lambda match: _template_to_link(
            match,
            base_wiki_url,
        ),
        d,
        flags=re.IGNORECASE | re.VERBOSE,
    )

    # {{lb|sq|chemistry}} -> ""
    d = re.sub(
        r"\{\{lb\|[^{}]*\}\}",
        "",
        d,
        flags=re.IGNORECASE,
    )

    # wikilink:
    # [[acid]]
    # [[acid|sour]]
    d = re.sub(
        r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]",
        lambda match: _replace_link(
            match,
            base_wiki_url,
        ),
        d,
    )

    # remove remaining templates
    d = re.sub(
        r"\{\{[^{}]*\}\}",
        "",
        d,
    )

    # HTML
    d = re.sub(
        r"<[^>]+>",
        "",
        d,
    )

    # bold / italic
    d = re.sub(
        r"'+",
        "",
        d,
    )

    # whitespace
    d = re.sub(
        r"\s+",
        " ",
        d,
    ).strip()

    d = re.sub(
        r"\(\s*\)",
        "",
        d,
    )

    d = re.sub(
        r"^[,.\s]+",
        "",
        d,
    )

    return (
        d.replace(" .", ".")
        .replace(" ,", ",")
        .replace(" ;", ";")
        .replace(" :", ":")
        .strip()
    )


class Wiktionary:
    def __init__(self, base_url: str, user_agent: str):
        self.base_url = base_url
        self.api_url = f"https://{base_url}/w/api.php"

        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": user_agent,
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def _get_json(
        self,
        url: str,
        *,
        params: dict | None = None,
        allow_redirects: bool = True,
    ) -> dict | None:
        while True:
            async with self.session.get(
                url,
                params=params,
                allow_redirects=allow_redirects,
            ) as response:
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After")

                    try:
                        wait_time = float(retry_after)
                    except (TypeError, ValueError):
                        wait_time = 5

                    print(
                        "429-ed while requesting wiktionary. waiting for",
                        wait_time,
                        "seconds before retrying",
                    )
                    await asyncio.sleep(wait_time)
                    continue

                if response.status != 200:
                    return None

                return await response.json()

    async def _get_final_url(
        self,
        url: str,
        *,
        params: dict | None = None,
    ) -> str | None:
        while True:
            async with self.session.get(
                url,
                params=params,
                allow_redirects=True,
            ) as response:
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After")

                    try:
                        wait_time = float(retry_after)
                    except (TypeError, ValueError):
                        wait_time = 5

                    print(
                        "429-ed while requesting wiktionary. waiting for",
                        wait_time,
                        "seconds before retrying",
                    )
                    await asyncio.sleep(wait_time)
                    continue

                if response.status != 200:
                    return None

                return str(response.url)

    @staticmethod
    def definitions_to_string(definitions: list) -> str:
        lines = []

        def walk(nodes: list, depth: int) -> None:
            indent = "  " * depth
            marker = "-" if depth == 0 else "+"

            for text, children in nodes:
                lines.append(f"{indent}{marker} {text}")

                if children:
                    walk(children, depth + 1)

        walk(definitions, 0)

        return "\n".join(lines)

    async def definitions_by_id(
        self,
        page_id: int,
    ) -> tuple[dict, str | None] | None:
        params = {
            "action": "query",
            "pageids": page_id,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "format": "json",
            "utf8": 1,
        }

        data = await self._get_json(
            self.api_url,
            params=params,
        )

        if data is None:
            return None

        pages = data.get("query", {}).get("pages", {})
        page = pages.get(str(page_id), {})

        if "revisions" not in page:
            return None

        wikitext = page["revisions"][0]["slots"]["main"]["*"]

        base_wiki_url = self.api_url.replace(
            "/w/api.php",
            "/wiki",
        )

        section_matches = []

        for match in re.finditer(
            r"^==[ \t]*([^=\r\n]+?)[ \t]*==[ \t]*(?:\r?\n|$)",
            wikitext,
            flags=re.MULTILINE,
        ):
            code = match.group(1).lower().strip()

            section_matches.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "name": _language_name(code),
                }
            )

        for match in re.finditer(
            r"^\{\{-([a-z]{2,3})-\}\}[ \t]*(?:\r?\n|$)",
            wikitext,
            flags=re.MULTILINE | re.IGNORECASE,
        ):
            code = match.group(1).lower().strip()

            section_matches.append(
                {
                    "start": match.start(),
                    "end": match.end(),
                    "name": _language_name(code),
                }
            )

        section_matches.sort(key=lambda section: section["start"])

        all_languages_dict = {}

        for idx, section in enumerate(section_matches):
            lang_name = section["name"]

            if idx + 1 < len(section_matches):
                end_pos = section_matches[idx + 1]["start"]
            else:
                end_pos = len(wikitext)

            lang_text = wikitext[section["end"] : end_pos]

            raw_lines = re.findall(
                r"^(#+)(?![:*])[ \t]*(.*?)[ \t]*$",
                lang_text,
                flags=re.MULTILINE,
            )

            if not raw_lines:
                continue

            root = []
            stack = []

            for hashes, content in raw_lines:
                if "{{" in content and re.search(
                    r"\{\{(?:quote|cite|RQ:)",
                    content,
                    flags=re.IGNORECASE,
                ):
                    continue

                level = len(hashes)

                cleaned = _clean_wikitext(
                    content,
                    base_wiki_url,
                )

                if not cleaned:
                    continue

                while stack and stack[-1][0] >= level:
                    stack.pop()

                node = [
                    cleaned,
                    [],
                ]

                if not stack:
                    root.append(node)
                else:
                    parent = stack[-1][1]
                    parent[1].append(node)

                stack.append((level, node))

            if root:
                all_languages_dict[lang_name] = root

        return all_languages_dict, page.get("title")

    async def exact_match(
        self,
        title: str,
        category: str = "",
    ) -> int | None:
        params = {
            "action": "query",
            "titles": title,
            "prop": "categories",
            "cllimit": "max",
            "format": "json",
            "utf8": 1,
        }

        data = await self._get_json(
            self.api_url,
            params=params,
        )

        if data is None:
            return None

        pages = data.get(
            "query",
            {},
        ).get(
            "pages",
            {},
        )

        for page_id, page_data in pages.items():
            if page_id == "-1":
                return -1

            cats = page_data.get(
                "categories",
                [],
            )

            if category == "":
                return int(page_id)

            if any(category == cat["title"] for cat in cats):
                return int(page_id)

        return -1

    async def prefix_match(
        self,
        prefix: str,
        category: str,
        target_count: int = 10,
    ) -> dict[str, int] | None:
        params = {
            "action": "query",
            "generator": "allpages",
            "gapprefix": prefix,
            "gaplimit": 500,
            "prop": "categories",
            "cllimit": "max",
            "format": "json",
            "utf8": 1,
        }

        valid_words = {}

        while True:
            data = await self._get_json(
                self.api_url,
                params=params,
            )

            if data is None:
                return None

            pages = data.get(
                "query",
                {},
            ).get(
                "pages",
                {},
            )

            for page_id, page_data in pages.items():
                title = page_data.get(
                    "title",
                    "",
                )

                cats = page_data.get(
                    "categories",
                    [],
                )

                if category == "":
                    valid_words[title] = int(page_id)

                elif any(category == cat["title"] for cat in cats):
                    valid_words[title] = int(page_id)

                if len(valid_words) >= target_count:
                    break

            if len(valid_words) >= target_count:
                break

            continue_token = data.get("continue")

            if not continue_token:
                break

            params.update(continue_token)

        return valid_words

    async def random_word(
        self,
        category: str = "",
    ) -> tuple[int, str] | None:
        if category:
            url = f"https://{self.base_url}" "/wiki/Special:RandomInCategory/"
            params = {
                "wpcategory": category,
            }
        else:
            url = f"https://{self.base_url}" "/wiki/Special:Random"
            params = {}

        final_url = await self._get_final_url(
            url,
            params=params,
        )

        if final_url is None:
            return None

        parsed = urlsplit(final_url)
        query = parse_qs(parsed.query)

        if "title" in query:
            title = query["title"][0].replace("_", " ")

        elif parsed.path.startswith("/wiki/"):
            title = unquote(parsed.path[len("/wiki/") :]).replace("_", " ")

        else:
            return None

        if not title:
            return None

        await asyncio.sleep(3)

        page_id = await self.exact_match(title)

        if page_id < 0:
            return None

        return page_id, title

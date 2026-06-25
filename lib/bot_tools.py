import requests
import datetime
import urllib.parse
from ollama import AsyncClient
from discord.ext.commands import Bot
import json


def get_current_time(timezone_offset: int = 0) -> str:
    now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=timezone_offset))
    )
    return now.strftime("Current date and time: %A, %B %d, %Y, %I:%M %p")


def lookup_urban_slang(term: str) -> str:
    try:
        url = f"https://api.urbandictionary.com/v0/define?term={term}"
        res = requests.get(url, timeout=5).json()
        if not res.get("list"):
            return f"No definitions found for '{term}'."

        top = res["list"][0]
        definition = top["definition"].replace("[", "").replace("]", "")
        example = top["example"].replace("[", "").replace("]", "")
        return f"Definition: {definition}\nExample: {example}"
    except Exception as e:
        return f"Failed to look up slang: {e}"


def get_weather(location: str) -> str:
    try:
        url = f"https://wttr.in/{location}?format=%l:+%C+%t,+wind+%w,+humidity+%h"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        return res.text
    except Exception as e:
        return f"Could not get weather for {location}: {e}"


def generate_qr_code(text_or_url: str) -> str:
    encoded_data = urllib.parse.quote(text_or_url)
    qr_url = (
        f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={encoded_data}"
    )

    return f"Generated QR Code image URL: {qr_url}"


def get_nasa_space_picture() -> str:
    try:
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
        res = requests.get(url, timeout=5).json()

        title = res.get("title", "Space Setup")
        explanation = res.get("explanation", "")
        img_url = res.get("url")

        if len(explanation) > 500:
            explanation = explanation[:500] + "..."

        return f"Title: {title}\nDescription: {explanation}\nImage URL: {img_url}"
    except Exception as e:
        return f"Failed to fetch NASA space asset: {e}"


AVAILABLE_TOOLS = [
    get_current_time,
    lookup_urban_slang,
    get_weather,
    generate_qr_code,
    get_nasa_space_picture,
]

TOOLS_NAME_MAP = {}
for tool in AVAILABLE_TOOLS:
    TOOLS_NAME_MAP[tool.__name__] = tool


def extend_tooling(new_tools: list):
    AVAILABLE_TOOLS.extend(new_tools)
    for tool in new_tools:
        TOOLS_NAME_MAP[tool.__name__] = tool


def add_ollama_web_tools(client: AsyncClient) -> list:
    async def web_search(query: str, max_results: int = 3) -> str:
        try:
            response = await client.web_search(query=query)

            results = []
            for r in response.results[:max_results]:
                results.append({"title": r.title, "url": r.url, "body": r.content})

            return json.dumps(results)
        except Exception as e:
            return f"Search failed: {e}"

    async def web_fetch(url: str) -> str:
        try:
            # Must await AsyncClient methods
            response = await client.web_fetch(url=url)

            text = f"Title: {response.title}\n\n{response.content}"

            max_chars = 1500
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n...[Content truncated due to length]..."

            return text
        except Exception as e:
            return f"Failed to fetch webpage: {str(e)}"

    new_tools = [web_search, web_fetch]
    extend_tooling(new_tools)


__all__ = [
    "AVAILABLE_TOOLS",
    "TOOLS_NAME_MAP",
    "add_ollama_web_tools",
]

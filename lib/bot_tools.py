from ddgs import DDGS
from bs4 import BeautifulSoup
import requests
import json
import datetime
import wikipedia
import urllib.parse


def web_search(query: str, max_results: int = 3) -> str:
    try:
        results = DDGS().text(query, max_results=max_results)
        return json.dumps(list(results))
    except Exception as e:
        return f"Search failed: {e}"


def web_fetch(url: str) -> str:
    try:
        headers = {"User-Agent": "kot-skoffer"}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for element in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            element.extract()

        text = soup.get_text(separator="\n", strip=True)

        max_chars = 15000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n...[Content truncated due to length]..."

        return text

    except requests.exceptions.RequestException as e:
        return f"Failed to fetch webpage: {str(e)}"
    except Exception as e:
        return f"Error parsing webpage: {str(e)}"


def search_web_image(query: str) -> str:
    try:
        results = list(DDGS().images(query, max_results=1))
        if not results:
            return f"No images found for '{query}'."

        image_url = results[0].get("image")
        return f"Found image URL: {image_url} (Tell the user this is the image they asked for!)"
    except Exception as e:
        return f"Failed to search for image: {e}"


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


def fetch_wikipedia_summary(query: str) -> str:
    try:
        return wikipedia.summary(query, sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Too vague. Did you mean one of these? {', '.join(e.options[:5])}"
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'."


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


AVAILABLE_TOOLS = {
    "web_search": web_search,
    "web_fetch": web_fetch,
    "search_web_image": search_web_image,
    "get_current_time": get_current_time,
    "lookup_urban_slang": lookup_urban_slang,
    "fetch_wikipedia_summary": fetch_wikipedia_summary,
    "get_weather": get_weather,
    "generate_qr_code": generate_qr_code,
    "get_nasa_space_picture": get_nasa_space_picture,
}
TOOLS = [AVAILABLE_TOOLS[i] for i in AVAILABLE_TOOLS.keys()]

__all__ = [
    "AVAILABLE_TOOLS",
    "TOOLS",
]

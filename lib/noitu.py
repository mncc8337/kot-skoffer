from discord import Interaction
from lib.wiktionary import Wiktionary
import cog.wiktionary
from urllib.parse import quote


class NoiTu(Wiktionary):
    def __init__(self, user_agent: str):
        super().__init__("vi.wiktionary.org", user_agent)

    async def dinhnghia(self, interaction: Interaction, word: str):
        await interaction.response.defer()

        page_id = self.exact_match(
            word,
            "Thể loại:Mục từ tiếng Việt",
        )

        if page_id < 0:
            await interaction.followup.send(content="không tìm thấy từ trong từ điển")
            return

        await cog.wiktionary._send_followup_result(interaction.followup, self, page_id)

    async def noitiep(self, interaction: Interaction, prefix: str):
        await interaction.response.defer()

        word_list = self.prefix_match(
            prefix.split(" ")[-1] + " ",
            "Thể loại:Mục từ tiếng Việt",
        )

        resp = "các từ có thể nối tiếp:\n"
        wcount = 0
        for word in word_list:
            if len(word.split(" ")) == 2:
                safe_word = quote(word.replace(' ', '_'), safe='')
                word_url = f"https://{self.base_url}/wiki/{safe_word}"
                resp += f"- [{word}]({word_url})\n"
                wcount += 1

        if wcount == 0:
            await interaction.followup.send(content="không có từ nào để nối")
            return
        else:
            await interaction.followup.send(content=resp, suppress_embeds=True)

# Kot Skoffer
bad discord bot

## running
### install stuffs
`pip install discord.py python-dotenv requests`
> if it complain about `audioop` then `pip install audioop-lts`
### env
`cp .env.example .env` then edit it
### run
just do `python3 app.py`. then on any channel:  
- set bot test channel: `/settings set bottest_channel <CHANNEL_ID>`
- set cat farm channel: `/settings set catfarm_channel <CHANNEL_ID>`
- set default city for weather fetching: `/settings set city <CITY_NAME>`
all the data will be saved in `./data`
> [!Tip]
> - for `/randomimage` to work you need to put some images in `./images`. make sure that you only put images heree beside the .gitignore else the bot will freeze

# Kot Skoffer
bad discord bot

## running
### install stuffs
`pip install discord.py python-dotenv requests ollama`
> if it complain about `audioop` then `pip install audioop-lts`  
> this bot use ollama for llm stuff so make sure to install it and set the model in .env
### env
`cp .env.example .env` then edit it
### run
first run `ollama serve` then just do `python3 app.py`. and on any channel:  
- set default city for weather fetching: `/settings set city <CITY_NAME>`  
all the data will be saved in `./data`
> [!Tip]
> - for `/randomimage` to work you need to put some images in `./images`. make sure that you only put images heree beside the .gitignore else the bot will freeze

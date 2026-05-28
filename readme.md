# Kot Skoffer
bad discord bot
## feature
- random commands that no one uses 🔥
- local AI chat bot 🔥
- stupid image editor 🔥
## running
### install stuffs
`pip install discord.py python-dotenv requests pillow ollama matplotlib wikipedia`
> if it complain about `audioop` then `pip install audioop-lts`  
> this bot use ollama for llm stuff so make sure to install it and set a model in .env
### env
`cp .env.example .env` then edit it
### run
just do `python3 app.py`.  
u will need an `OLLAMA_API_KEY` to use the ai features.  
all data will be saved in `./data`
> [!Note]
> - for `/random image` to work you need to put some images in `./images`. make sure that you only put images heree beside the .gitignore else the bot will freeze
### disabling ai stuffs
just remove `ENABLE_AI` in `.env`  
now you dont need to run `ollama serve` everytime you start the server

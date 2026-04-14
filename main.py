import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
from utils.data import load_values, save_values
import os

load_dotenv() # literally loads .env in directory
token = os.getenv('DISCORD_TOKEN') # grab token from .env

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()

########## INTENT DECLARATION HERE, DEFAULT SETUP ##########
# Now specify what intents we need. Will need to manually enable each desired intent.
# https://discordpy.readthedocs.io/en/stable/api.html#discord.Intents
# (class discord.Intents)
intents.message_content = True
intents.members = True
intents.polls = True

# In discord, the bot will look for ! for prompts.
bot = commands.Bot(command_prefix='!', intents=intents)
bot.user_values = load_values()

class NoArgsHelp(commands.DefaultHelpCommand):
    def add_command_arguments(self, command):
        # Override this method to do nothing to remove default help display
        return
bot.help_command = NoArgsHelp()

########## ########## ##########

@bot.event
async def on_message(message):
    # AVOID bot on_message clashing with cog on_message
    await bot.process_commands(message)

# for cmd in bot.commands:
#     print(cmd.name)
# setup_hook runs automatically before bot connects
@bot.event
async def setup_hook():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and filename != "__init__.py":
            await bot.load_extension(f"cogs.{filename[:-3]}")

# Record logs to discord.log. MUST BE LAST LINE since it runs bot.
bot.run(token, log_handler=handler, log_level=logging.DEBUG)

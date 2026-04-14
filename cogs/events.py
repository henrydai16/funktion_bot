import discord
from discord.ext import commands
import random
import re

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @ = decorator, MUST be called on_ready(), follow intents documentation
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name} turning on. Clap clap pose.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await member.send(f"Welcome to the server {member.name}!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        # Map trigger words into a response
        triggers = {
            "ass":    "By 'ass', did you mean 'Kevin's ass'?",
            "galaxy": "By 'galaxy', did you mean 'Kevin's ass'?",
            "best":   "By 'best', did you mean 'best dancer Yaani?'",
            "gay":    "By 'gay', did you mean 'Justin kissing"
        }

        msg = message.content.lower()

        # Loop through triggers
        for keyword, response in triggers.items():
            # Match whole word + optional punctuation
            pattern = rf"\b{re.escape(keyword)}\b[^\w]?"

            if re.search(pattern, msg):
                # Special case: message is exactly "gay"
                if keyword == "gay":
                    names = ["Anthony", "Lucas", "Adli", "Sean", "Yaani", "Brian", "Tyler"]
                    chosen = random.choice(names)
                    response = f"{response} {chosen}?'"

                await message.channel.send(f"{message.author.mention} {response}")
                break
        # Because we've overwritten default behavior w/ custom events (above),
        # the bot will no longer automatically process_commands.
        # After custom code, NOW call process_commands at the end
        # await self.bot.process_commands(message) -- caused clashing of cog v. bot processing
        return

async def setup(bot):
    await bot.add_cog(Events(bot))

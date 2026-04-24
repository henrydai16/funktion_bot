import discord
from discord.ext import commands
import random
import re
import time

# Will be used to randomly insult a person.
ROASTS = [
    "You little shit.",
    "W message",
    "L message",
    "shore shore!",
    "HOLY! Just kiss a dude at that point man.",
    "Holy glaze."
]

class Events(commands.Cog):
    # ONLY send troll random replies every (minimum) 30 minutes. (only for replies NOT triggers)
    COOLDOWN = 60 * 30  
    def __init__(self, bot):
        self.bot = bot
        self.last_roast_time = {}  # (channel_id, keyword) -> timestamp

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
            "gargantuan": "By 'gargantuan', did you mean 'Kevin's ass'?",
            "best":   "By 'best', did you mean 'best dancer Yaani?'",
            "gay":    "By 'gay', did you mean 'Justin kissing"
        }

        msg = message.content.lower()

        #1 TRIGGER WORDS lead to a response. 
        for keyword, response in triggers.items():
            # Match whole word + optional punctuation
            pattern = rf"\b{re.escape(keyword)}\b[^\w]?"

            key = (message.channel.id, keyword)
            if re.search(pattern, msg):
                # Special case: message is exactly "gay"
                if keyword == "gay":
                    names = ["Anthony", "Lucas", "Adli", "Sean", "Yaani", "Brian", "Tyler"]
                    chosen = random.choice(names)
                    response = f"{response} {chosen}?'"
                await message.channel.send(f"{message.author.mention} {response}")

                # Because we've overwritten default behavior w/ custom events (above),
                # the bot will no longer automatically process_commands.
                # After custom code, NOW call process_commands at the end
                # await self.bot.process_commands(message) -- caused clashing of cog v. bot processing
                return
        
        #2 RANDOM ROAST if no trigger words are detected.
        if random.random() < 0.99: # 1% chance to randomly reply to ANY message
            now = time.time()
            key = message.channel.id
            last = self.last_roast_time.get(key, 0)

            if now - last > self.COOLDOWN:
                self.last_roast_time[key] = now

                roast = random.choice(ROASTS)
                await message.reply(f"{message.author.mention} {roast}")
                return
                


async def setup(bot):
    await bot.add_cog(Events(bot))

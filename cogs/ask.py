import discord
import asyncio
import ollama
import os
from discord.ext import commands
from utils.data import save_values


class Ask(commands.Cog):
    def __init__(self, bot): # Calls when loading cog
        self.bot = bot
    @commands.command(
        brief="Ask FunKtion history via: !ask '[prompt]'",
        help=(
            """TBD"""
        ),
        signature =""
    )
    async def ask(self, ctx):
        """Uses an LLM/RAG model connected to FunKtion information via ollama."""
        # Ollama Configuration
        model = "phi3:mini"
        # system_prompt = """
        #                 you are an assistant that likes pizza.
        #                 """
        system_prompt = """
                        You are a general purpose assistant, but the people talking to you
                        are in a dance team club at the University of Michigan.
                        This dance team is FunKtion.
                        If they ask about non-dance topics, respond normally, but be aware
                        that people here are dancers. Tend to keep responses below 
                        1000 characters.
                        """

        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": ctx.message.content},
            ],
        )
        content = response.message.content
        # Discord sends messages in 2000 chr limits, splits up messages.
        for i in range(0, len(content), 2000):
            await ctx.send(f"{ctx.author.mention} {content[i:i+2000]}")

async def setup(bot):
    await bot.add_cog(Ask(bot))
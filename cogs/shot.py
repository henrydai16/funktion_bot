import discord
import asyncio
from discord.ext import commands
from utils.data import save_values

# https://guide.pycord.dev/popular-topics/cogs
class Shot(commands.Cog):
    def __init__(self, bot): # Calls when loading cog
        self.bot = bot
    @commands.command(
        brief="Assign via: !shot @person / !shot @person 5",
        help=(
            "Ever needed to educate a young newb or tweenager? This is the command for you.\n\n"
            "Arguments:\n"
            "  member : discord.Member (optional)\n"
            "      The target user receiving the shots. Defaults to the command author.\n"
            "  amount : int (optional)\n"
            "      Number of shots to add. If omitted, the bot will prompt you.\n\n"
            "Behavior:\n"
            "  • !shot @User 3 → Adds 3 shots to @User.\n"
            "  • !shot @User   → Bot asks for an amount.\n"
            "  • !shot         → Targets the author and asks for an amount.\n\n"
            "Examples:\n"
            "  !shot @person 5\n"
            "  !shot @person\n"
            "  !shot 3\n"
            "  !shot\n"
        ),
        signature =""
    )
    async def shot(self, ctx, member: discord.Member = None, amount: int = None):
        """
        Assigns a number of 'shots' to a user and stores the total in persistent JSON.
        """

        member = member or ctx.author
        values = self.bot.user_values
        uid = str(member.id)

        # If specified shot amount is not present, ask for it
        if amount is None:
            await ctx.send(f"{ctx.author.mention}, how many shots?")

            def check(msg):
                return (
                    msg.author == ctx.author and
                    msg.channel == ctx.channel and
                    msg.content.isdigit()
                )
            
            try:
                msg = await self.bot.wait_for("message", timeout=20.0, check=check)
                amount = int(msg.content)
            except asyncio.TimeoutError:
                amount = 1
                await ctx.send("Timed out. Defaulting to 1.")
            
        # Update json score if user_values is missing
        new_shot_count = values.get(uid, 0) + amount
        values[uid] = new_shot_count
        save_values(values)

        await ctx.send(f"{member.mention} now has **{values[uid]}** shots. Be better.")
    
async def setup(bot):
    await bot.add_cog(Shot(bot))
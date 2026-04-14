import discord
import asyncio
from discord.ext import commands
from utils.data import save_values


class Reward(commands.Cog):
    def __init__(self, bot):
        """Initialize the Reward cog."""
        self.bot = bot

    @commands.command(
        brief="Reward via: !reward @person / !reward @person 5",
        help=(
            """
            Finally, someone did something right.

            Arguments:
            member : discord.Member (optional)
                The target user receiving the reward. Defaults to the command author.
            amount : int (optional)
                Number of shots to remove. If omitted, defaults to 1 or prompts.

            Behavior:
            • !reward @User 3 → Removes 3 shots from @User.
            • !reward @User   → Bot asks for amount (defaults to 1 if timeout).
            • !reward         → Targets the author and asks for amount.

            Examples:
            !reward @person 5
            !reward @person
            !reward
            """
        )
    )
    async def reward(self, ctx, member: discord.Member = None, amount: int = None):
        """
        Removes (rewards) a number of 'shots' from a user and updates json.

        If no member is provided, defaults to the command author.
        If no amount is provided, the bot prompts the user with a value
        Defaults to 1 if no valid input is received.
        """

        member = member or ctx.author
        values = self.bot.user_values
        uid = str(member.id)

        # Ask for amount if not provided
        if amount is None:
            await ctx.send(f"{ctx.author.mention}, how many shots should be removed?")

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

        current_shots = values.get(uid, 0)

        # Prevent negative values
        new_shot_count = current_shots - amount
        values[uid] = new_shot_count

        save_values(values)

        await ctx.send(
            f"{member.mention} has been rewarded. "
            f"They now have **{values[uid]}** shots. *Maybe* you will make it to another dmix."
        )


async def setup(bot):
    await bot.add_cog(Reward(bot))
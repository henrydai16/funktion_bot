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
            "  • !shot @User   → Bot defaults to 1 shot.\n"
            "  • !shot         → Self-inflicted 1 shot on the author.\n\n"
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

        # Several conditions based on ctx.author's role:
        # 1: Oldie/Alumni -- Can give a shot to anyone
        # 2: Tweenie -- One time pass on TWEENIES or NEWBIE.
        # 3: newbies -- Prompted the same one time pass, but will be rugpulled.

        ctx_author_hi_role = self.get_highest_user_role(ctx.author) 
        member_hi_role = self.get_highest_user_role(member)

        # DEBUGGING MESSAGES!!
        print(ctx_author_hi_role)
        print(member_hi_role)
        if ctx_author_hi_role > member_hi_role:
            print(f"shot will go through: {str(ctx_author_hi_role)} > {str(member_hi_role)}")
        elif ctx_author_hi_role == member_hi_role:
            print(f"shot may or may not go through based on role: {str(ctx_author_hi_role)} ?= {str(member_hi_role)} ")
        else:
            print(f"shot should not go through here: {str(ctx_author_hi_role)} < {str(member_hi_role)} ")



        # ctx_author_roles = ctx.author.roles
        # print(f"this is the authors role: {ctx_author_roles}")
        # print(f"this is the members role: {member.roles}")

        values = self.bot.user_values
        uid = str(member.id)


        # Specified shot amount not present, default to 1 shot  
        if amount is None:
            amount = 1

        # Reward user since they're receiving < 0 shots.
        if amount < 0:
            await self.reward(ctx, member, amount)
        
        # Punish user for receiving > 0 shots.
        else:
            # Update json score if user_values is missing
            new_shot_count = values.get(uid, 0) + amount
            values[uid] = new_shot_count
            save_values(values)

            await ctx.send(f"{member.mention} now has **{values[uid]}** shots. Be better.")


    async def reward(self, ctx, member: discord.Member = None, amount: int = 1):
        """
        Removes (rewards) a number of 'shots' from a user and updates json.
        Originally it's own command, now integrated with !shot if the value is < 0.
        """

        member = member or ctx.author
        values = self.bot.user_values
        uid = str(member.id)

        # Calculate new_shot_count w/ subtraction (not adding negatives) 
        amount = abs(amount) 
        new_shot_count = values.get(uid, 0) - amount
        values[uid] = new_shot_count
        save_values(values)

        await ctx.send(
            f"{member.mention} has been rewarded. "
            f"They now have **{values[uid]}** shots. *Maybe* you will make it to another dmix."
            )
        
    def get_highest_user_role(self, member: discord.Member):
        """
        Given a member, return the highest hierarchal discord.Role ranging from:
        Alumni → Oldie → Tweenie → Newbie
        """
        priority_ids = [
            953499388351750144, # Alumni
            953499007408308224, # Oldie
            953498912411500574, # Tweenie
            953498765694730281, # Newbie
        ]

        for pid in priority_ids:
            for r in member.roles:
                if r.id == pid:
                    return r
        # If no ID found, default to Newbie status.
        return next((role for role in member.guild.roles if role.id == priority_ids[-1]), None)


async def setup(bot):
    await bot.add_cog(Shot(bot))
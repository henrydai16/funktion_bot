import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import View, Button
from utils.data import save_values
from enum import IntEnum
from datetime import datetime, timedelta


# ALUM and OLDIE are both 3 since they have the same amount of power
# from the bot's perspective. Used in determining "handing out shots"
class RolePower(IntEnum):
    ALUM = 3
    OLDIE = 3
    TWEENIE = 2
    NEWBIE = 1

class roleIDs(IntEnum):
    ALUM_ID = 953499388351750144
    OLDIE_ID = 953499007408308224 
    TWEENIE_ID = 953498912411500574 
    NEWBIE_ID = 953498765694730281

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
    async def shot(self,
                   ctx: Context,
                   member: discord.Member = None,
                   amount: int = None
                ) -> None:
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

        # Only allow default shot behavior if author is oldie or alum
        if str(ctx_author_hi_role) == "oldie" or str(ctx_author_hi_role) == "alum":
            print("i am an oldie")  

        # Specified shot amount not present, default to 1 shot  
        if amount is None:
            amount = 1

        allowed, amount = await self.can_give_shot(
            ctx,
            ctx_author_hi_role,
            member_hi_role,
            amount
        )

        if allowed:
            # Reward user since they're receiving < 0 shots.
            if amount < 0:
                await self.reward(ctx, member, amount)
            
            # Punish user for receiving > 0 shots.
            else:
                await self.update_shots(ctx, member, amount)
        
        # User is punished, NOT allowed to give shots (checks if <0 via amount)
        else:
            await self.update_shots(ctx, member, amount)


    async def reward(self, ctx, member: discord.Member = None, amount: int = -1) -> None:
        """
        Removes (rewards) a number of 'shots' from a user and updates json.
        Originally it's own command, now integrated with !shot if the value is < 0.
        """
        member = member or ctx.author
        # Amount should be negative already 
        await self.update_shots(ctx, member, amount)
        
    async def update_shots(self, ctx, member: discord.Member, amount: int) -> int:
        """
        Updates the shot count for a member and sends a message.
        Returns the new shot count.
        """
        uid = str(member.id)

        # user is a reference to values[uid] NOT copy by value
        user = self.check_uid_exists(uid)
        user["shots"] += amount

        # self.bot.user_values contains the dict that user["shots"] references 
        # So modification of user["shots"] will be saved via bot.user_values.
        save_values(self.bot.user_values)

        # Message differs depending on positive or negative update
        if amount >= 0:
            msg = f"{member.mention} now has **{user['shots']}** shots. Be better."
        else:
            msg = (
                f"{member.mention} has been rewarded. "
                f"They now have **{user['shots']}** shots. *Maybe* you will make it to another dmix.*"
            )

        await ctx.send(msg)
        return user["shots"]


    def get_highest_user_role(self, member: discord.Member):
        """
        Given a member, return the highest hierarchal discord.Role ranging from:
        Alumni → Oldie → Tweenie → Newbie
        """
        priority_ids = [
            roleIDs.ALUM_ID,
            roleIDs.OLDIE_ID,
            roleIDs.TWEENIE_ID,
            roleIDs.NEWBIE_ID
        ]

        for pid in priority_ids:
            for r in member.roles:
                if r.id == pid:
                    return r
        # If no ID found, default to Newbie status.
        return next((role for role in member.guild.roles if role.id == priority_ids[-1]), None)
   
    async def can_give_shot(self,
                            ctx: Context,
                            author_role: discord.Role,
                            member_role: discord.Role,
                            amount: int
                            ) -> tuple[bool, int]:
        """
        Given an author role and a member role, returns a tuple on whether or not
        they will be able to give a shot. 
        Oldies/Alumnis can give a shot to anyone
        Tweenies will be offered a one time use ON NEWBIES.
        Newbies will be deceived into thinking they can hand out shots.
        """

        PRIORITY = {
            "alum": RolePower.ALUM,
            "oldie": RolePower.OLDIE,
            "tweenie": RolePower.TWEENIE,
            "newbie": RolePower.NEWBIE
        }

        author_power = PRIORITY.get(author_role.name, RolePower.NEWBIE)
        member_power = PRIORITY.get(member_role.name, RolePower.NEWBIE)

        # oldie / alum are able to hand out shots
        if author_power >= RolePower.OLDIE:
            return tuple(True, amount)

        # Tweenie or Newbie logic
        if author_power == RolePower.TWEENIE:
            handler = self.tweenie_give_shot
        
        else: # author_power == RolePower.NEWBIE
            handler = self.newbie_give_shot

        author_can_give_shot, updated_amt, return_msg = await handler(
            ctx,
            member_power,
            amount
        )
        
        await ctx.send(f"{ctx.author.mention}\n"
                    f"{return_msg}"
        )

        return author_can_give_shot, updated_amt


    async def tweenie_give_shot(self, ctx: Context, member_power: int, 
                          amount: int
                          ) -> tuple(bool, int, str):
        """
        Verifies if tweenie is able to give a shot. If a shot pass is present,
        they will be prompted if they want to use it.
        """

        # Trying to give a shot to oldie is not allowed.
        if member_power == RolePower.OLDIE:
            return (False,
                    amount * 2,
                    "A tweenie giving a shot to an oldie? How dare you." \
                    " Shots on you are returned & doubled. Be better.")
        
        user = self.check_uid_exists(str(ctx.author.id))
        # Use "shot pass" on another tweenie/newbie (refreshes every 7d?) 
        if user["shot_pass"]:
            user["shot_pass"] = False
            user["last_pass_used"] = datetime.now().isoformat()
            return (True,
                    amount,
                    "You have used your shot pass. You will have to wait " \
                    "7 days until you get another one.")
        
        # User used their shot pass already.
        else: 
            last_dt = datetime.fromisoformat(user["last_pass_used"])
            new_pass_date = last_dt + timedelta(days=7)
            remaining = new_pass_date - datetime.now()

            # remaining.seconds is NOT the total number of seconds.
            # It is the number of seconds remaining after removing whole days
            days = remaining.days
            hours, remainder_m = divmod(remaining.seconds, 3600)
            minutes, seconds = divmod(remainder_m, 60)
            return (False,
                    amount,
                    (
                        "You do not have a shot pass.\n"
                        f"Time remaining:\n"
                        f"  {days} days\n"
                        f"  {hours} hours\n"
                        f"  {minutes} minutes\n"
                        f"  {seconds} seconds"
                    ),
            )

    async def newbie_give_shot(self, ctx: Context, member_power: int, amount: int) -> tuple[bool, int, str]:
        """
        Verifies if a newbie has tried to use a shot pass before.
        If this is their first time, delude them into thinking they can 
        give a shot. Otherwise, teach them a lesson again.
        """
        uid = str(ctx.author.id)
        user = self.check_uid_exists(uid)
        
        # If they still have a shot pass
        if user["shot_pass"]:
            view = ShotPassConfirm(ctx.author)

            await ctx.send(
                f"{ctx.author.mention}, you are a **newbie**.\n"
                "Do you want to use your **one weekly shot pass**?",
                view=view
            )

            # Wait for user to click Yes/No
            await view.wait()

            # Regardless of choice, they get punished
            user["shot_pass"] = False
            user["last_pass_used"] = datetime.now().isoformat()

            if view.choice is True:
                return (
                    False,
                    amount,
                    "You used your shot pass... but you're still a newbie.\n"
                    "Your shot is returned & doubled. Be better."
                )

            else:
                return (
                    False,
                    amount,
                    "You chose not to use your shot pass.\n"
                    "Your shot is returned & doubled. Be better."
                )

        # If they already used their pass
        else:

            return (
                False,
                amount,
                (
                    "You are a **newbie**.\n"
                    "How many times do we have to teach you this lesson? \n"
                    "Your shot is returned & doubled. Be better."
                )
            )

        


    def check_uid_exists(self, uid: str) -> dict:
        """
        Ensures a user entry exists in the JSON-backed values dict.
        Creates a new entry if this is the user's first time.
        Also refreshes shot_pass if 7 days have passed since last use.
        Returns the user dict.
        """
        values = self.bot.user_values

        # Create new user entry if first time / missing
        if uid not in values:
            values[uid] = {
                "shots": 0,
                "shot_pass": True,
                "last_pass_used": None
            }
            return values[uid]
    
        # Reset shot pass if 7 days have passed since last use.
        last_used = values[uid]["last_pass_used"]
        if last_used is not None:
            last_dt = datetime.fromisoformat(last_used)
            if datetime.now() - last_dt >= timedelta(days=7):
                values[uid]["shot_pass"] = True
                save_values(self.bot.user_values)
        return values[uid]


class ShotPassConfirm(View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=15)
        self.author = author
        self.choice = None

    async def interaction_check(self, interaction: discord.Interaction):
        # Only the newbie who triggered it can click
        return interaction.user.id == self.author.id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: Button):
        self.choice = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: Button):
        self.choice = False
        await interaction.response.defer()
        self.stop()

async def setup(bot):
    await bot.add_cog(Shot(bot))
from typing import cast, TYPE_CHECKING, Optional
import asyncio
from os import getenv
import discord
from discord.ext import tasks
from discord.ext.commands import Cog, Bot
from discord import (
    ApplicationContext,
    Embed,
    Colour,
    SlashCommandGroup,
    Permissions,
    option,
)

if TYPE_CHECKING:
    from utils import GormBot


class BillingSystem(Cog):
    def __init__(self, bot: Bot):
        self.bot: "GormBot" = bot
        self.stripe_api_key = getenv("STRIPE_SECRET_KEY")

    def cog_unload(self):
        self.poll_payments.cancel()

    @Cog.listener()
    async def on_ready(self):
        if not self.poll_payments.is_running():
            self.poll_payments.start()

    BILL_GROUP = SlashCommandGroup(
        name="bill",
        description="Billing management",
    )

    @BILL_GROUP.command(name="create")
    @option("amount", float, description="Total amount")
    @option("deposit_percent", int, description="Deposit percentage", default=50, min_value=0, max_value=100)
    async def create_bill(self, ctx: ApplicationContext, amount: float, deposit_percent: int = 50):
        bot = cast("GormBot", ctx.bot)
        channel_id = ctx.channel_id

        async with bot.db.commission_session() as session:
            comm = await session.get_comm_by_channel(channel_id)
            if not comm:
                await ctx.respond("No commission found for this ticket.", ephemeral=True)
                return

        async with bot.db.billing_session() as billing:
            existing = await billing.get_bill_by_commission(comm.id)
            if existing:
                await ctx.respond("Bill already exists. Use `/bill status` to view.", ephemeral=True)
                return
            bill = await billing.create_bill(comm.id, amount, "USD", deposit_percent)

        deposit_amt = amount * (deposit_percent / 100)
        final_amt = amount - deposit_amt

        embed = Embed(title="Bill Created", colour=Colour.green())
        embed.add_field(name="Total", value=f"${amount:.2f}", inline=True)
        embed.add_field(name="Deposit", value=f"${deposit_amt:.2f} ({deposit_percent}%)", inline=True)
        embed.add_field(name="Final", value=f"${final_amt:.2f}", inline=True)

        async with bot.db.config_session() as config:
            stripe_enabled = (await config.get("stripe_enabled") or "true") == "true"
            crypto_enabled = (await config.get("crypto_enabled") or "true") == "true"

        payment_info = []
        if stripe_enabled:
            payment_info.append("**Stripe:** Payment link coming soon")
        if crypto_enabled:
            payment_info.append("**Crypto:** Payment address coming soon")
        if not payment_info:
            payment_info.append("No payment methods currently available.")

        embed.add_field(name="Payment Options", value="\n".join(payment_info), inline=False)

        await ctx.respond(embed=embed)

    @BILL_GROUP.command(name="status")
    async def bill_status(self, ctx: ApplicationContext):
        bot = cast("GormBot", ctx.bot)
        channel_id = ctx.channel_id

        async with bot.db.commission_session() as session:
            comm = await session.get_comm_by_channel(channel_id)
            if not comm:
                await ctx.respond("No commission found for this ticket.", ephemeral=True)
                return

        async with bot.db.billing_session() as billing:
            bill = await billing.get_bill_by_commission(comm.id)
            if not bill:
                await ctx.respond("No bill created yet. Use `/bill create`.", ephemeral=True)
                return

        deposit_amt = bill.total_amount * (bill.deposit_percent / 100)
        final_amt = bill.total_amount - deposit_amt

        embed = Embed(title="Bill Status", colour=Colour.blue())
        embed.add_field(name="Total", value=f"${bill.total_amount:.2f}", inline=True)
        embed.add_field(
            name="Deposit",
            value=f"${deposit_amt:.2f} {'✅' if bill.deposit_paid else '❌'}",
            inline=True
        )
        embed.add_field(
            name="Final",
            value=f"${final_amt:.2f} {'✅' if bill.final_paid else '❌'}",
            inline=True
        )

        await ctx.respond(embed=embed)

    CONFIRM_GROUP = BILL_GROUP.create_subgroup(
        name="confirm",
        description="Manual payment confirmation",
        default_member_permissions=Permissions(administrator=True),
    )

    @CONFIRM_GROUP.command(name="deposit")
    async def confirm_deposit(self, ctx: ApplicationContext):
        bot = cast("GormBot", ctx.bot)
        channel_id = ctx.channel_id

        async with bot.db.commission_session() as session:
            comm = await session.get_comm_by_channel(channel_id)
            if not comm:
                await ctx.respond("No commission found.", ephemeral=True)
                return

        async with bot.db.billing_session() as billing:
            bill = await billing.get_bill_by_commission(comm.id)
            if not bill:
                await ctx.respond("No bill found.", ephemeral=True)
                return
            await billing.mark_deposit_paid(bill.id)

        await ctx.respond("Deposit marked as paid.", ephemeral=True)
        await ctx.channel.send(
            embed=Embed(
                title="Payment Received",
                description="Deposit payment confirmed.",
                colour=Colour.green()
            )
        )

    @CONFIRM_GROUP.command(name="final")
    async def confirm_final(self, ctx: ApplicationContext):
        bot = cast("GormBot", ctx.bot)
        channel_id = ctx.channel_id

        async with bot.db.commission_session() as session:
            comm = await session.get_comm_by_channel(channel_id)
            if not comm:
                await ctx.respond("No commission found.", ephemeral=True)
                return

        async with bot.db.billing_session() as billing:
            bill = await billing.get_bill_by_commission(comm.id)
            if not bill:
                await ctx.respond("No bill found.", ephemeral=True)
                return
            await billing.mark_final_paid(bill.id)

        await ctx.respond("Final payment marked as paid.", ephemeral=True)
        await ctx.channel.send(
            embed=Embed(
                title="Payment Received",
                description="Final payment confirmed. Commission can now be completed.",
                colour=Colour.green()
            )
        )

    @tasks.loop(seconds=60)
    async def poll_payments(self):
        pass

    @poll_payments.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()


def setup(bot: Bot):
    bot.add_cog(BillingSystem(bot))

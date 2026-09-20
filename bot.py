import os
import discord
from discord.ext import commands
import json
import logging
import asyncio
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("DISCORD_TOKEN", "")

if not TOKEN:
    logger.error("Missing DISCORD_TOKEN. Set it in a .env file or as an environment variable.")
    raise ValueError("Missing DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

async def dummy_sync_commands(*args, **kwargs):
    pass

bot.sync_commands = dummy_sync_commands

def clean_channel_name(name: str) -> str:
    forbidden = ['/', '@', '#', '*']
    for c in forbidden:
        name = name.replace(c, '')
    return name.strip()

def load_structure():
    try:
        with open("structure.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        if "categories" not in data:
            logger.error("structure.json missing 'categories' key")
            return None
        return data
    except Exception as e:
        logger.error(f"Failed to load structure.json: {e}")
        return None

def load_roles():
    try:
        with open("roles.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        if "roles" not in data:
            logger.error("roles.json missing 'roles' key")
            return None
        return data
    except Exception as e:
        logger.error(f"Failed to load roles.json: {e}")
        return None

def hex_to_int_color(hex_color: str) -> discord.Color:
    try:
        hex_color = hex_color.lstrip('#')
        return discord.Color(int(hex_color, 16))
    except:
        return discord.Color.default()

def get_discord_permissions(permissions_list: list) -> discord.Permissions:
    permissions = discord.Permissions()

    for perm in permissions_list:
        if hasattr(permissions, perm):
            setattr(permissions, perm, True)

    return permissions

async def send_progress(channel, message):
    if channel is not None:
        try:
            await channel.send(message)
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")

def get_roles_above_bot(guild):
    bot_top_role = guild.me.top_role
    return [
        role for role in guild.roles
        if not role.managed
        and role.id != guild.default_role.id
        and role.position > bot_top_role.position
    ]

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
@commands.bot_has_permissions(manage_channels=True, manage_roles=True)
@commands.guild_only()
async def setup(ctx):
    guild = ctx.guild
    updates_channel = None

    try:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        }
        updates_channel = await guild.create_text_channel("updates", overwrites=overwrites)
    except Exception as e:
        logger.error(f"Failed to create updates channel: {e}")

    await ctx.send("⚠️ **Starting setup... deleting all existing channels and roles!** This may take a few seconds...")
    await send_progress(updates_channel, "⚠️ **Starting setup... deleting all existing channels and roles!** This may take a few seconds...")

    for channel in guild.channels:
        if updates_channel is not None and channel.id == updates_channel.id:
            continue
        try:
            await channel.delete(reason="Server reset by !setup command")
            await asyncio.sleep(0.5)
        except discord.HTTPException as e:
            if e.code == 50074:
                logger.info(f"Skipping community-required channel: {channel.name}")
            elif e.code == 10003:
                logger.info(f"Channel already deleted: {channel.name}")
            else:
                logger.error(f"Failed to delete channel {channel.name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting channel {channel.name}: {e}")

    for role in guild.roles:
        if role.name != "@everyone" and not role.managed:
            try:
                await role.delete(reason="Server reset by !setup command")
                await asyncio.sleep(0.5)
            except discord.Forbidden:
                logger.info(f"Skipping protected role: {role.name}")
            except Exception as e:
                logger.error(f"Failed to delete role {role.name}: {e}")

    await asyncio.sleep(1)

    structure = load_structure()
    roles_data = load_roles()

    if not structure:
        await ctx.send("❌ Failed to load structure.json!")
        await send_progress(updates_channel, "❌ Failed to load structure.json!")
        return

    if not roles_data:
        await ctx.send("❌ Failed to load roles.json!")
        await send_progress(updates_channel, "❌ Failed to load roles.json!")
        return

    await send_progress(updates_channel, "✅ **Configuration loaded**, rebuilding server structure...")

    created_roles = 0
    created_categories = 0
    created_channels = 0

    if "roles" in roles_data:
        for role_data in roles_data["roles"]:
            role_name = role_data.get("name", "").strip()
            if not role_name:
                continue

            try:
                color = hex_to_int_color(role_data.get("color", "#000000"))
                hoist = role_data.get("hoist", False)
                permissions_list = role_data.get("permissions", [])
                permissions = get_discord_permissions(permissions_list)

                logger.info(f"Creating role: {role_name} with permissions: {permissions_list}")

                await guild.create_role(
                    name=role_name,
                    color=color,
                    hoist=hoist,
                    permissions=permissions,
                    reason="Created by !setup command"
                )
                created_roles += 1
                logger.info(f"Successfully created role: {role_name}")
                await send_progress(updates_channel, f"➕ Created role **{role_name}** ({created_roles}/{len(roles_data['roles'])} roles)")

            except Exception as e:
                logger.error(f"Failed to create role {role_name}: {e}")

        await send_progress(updates_channel, f"✅ Done! Created **{created_roles}** roles.")

    for category_data in structure["categories"]:
        category_name = category_data.get("name", "").strip()
        if not category_name:
            continue

        try:
            category = await guild.create_category(category_name)
            created_categories += 1
            await send_progress(updates_channel, f"➕ Created category **{category_name}**")
        except Exception as e:
            logger.error(f"Failed to create category {category_name}: {e}")
            continue

        for ch in category_data.get("channels", []):
            ch_name = clean_channel_name(ch.get("name", ""))
            ch_type = ch.get("type", "text")
            ch_topic = ch.get("description", "")

            if ch_type.lower() == "voice":
                try:
                    await category.create_voice_channel(ch_name)
                    created_channels += 1
                    await send_progress(updates_channel, f"🔊 Created voice channel **{ch_name}**")
                except Exception as e:
                    logger.error(f"Failed to create voice channel {ch_name}: {e}")
            else:
                try:
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
                    }
                    await category.create_text_channel(name=ch_name, topic=ch_topic, overwrites=overwrites)
                    created_channels += 1
                    await send_progress(updates_channel, f"💬 Created text channel **{ch_name}**")
                except Exception as e:
                    logger.error(f"Failed to create text channel {ch_name}: {e}")

    await send_progress(updates_channel, f"✅ Setup complete! Created {created_roles} roles, {created_categories} categories and {created_channels} channels.")

    roles_above_bot = get_roles_above_bot(guild)
    if roles_above_bot:
        names = ", ".join(role.name for role in roles_above_bot)
        warning = (
            f"⚠️ **Bot role must be at the top!** The bot's role is currently **below** these roles: **{names}**. "
            "For the bot to create and manage roles/progression properly, move the bot's role to the **top** of the role list "
            "(above all other roles), otherwise setup may fail or be incomplete."
        )
        await send_progress(updates_channel, warning)
        await ctx.send(warning)

    await ctx.send(f"✅ Setup complete! Created {created_roles} roles, {created_categories} categories and {created_channels} channels. Progress was posted in **#updates**.")

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(
        title="📚 Bot Help",
        description="Server Setup Bot - Automatically creates roles, channels and categories from structure.json",
        color=discord.Color.blue()
    )
    embed.add_field(name="!setup", value="Deletes all channels and roles, then recreates server structure", inline=False)
    embed.add_field(name="!help", value="Shows this help message", inline=False)
    embed.add_field(name="Features", value="• Creates custom roles with colors and permissions\n• Sets up channel categories\n• Configures text and voice channels\n• Applies role hierarchy\n• Posts live progress to #updates\n• Warns if the bot role is not on top", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    error = getattr(error, "original", error)
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need administrator permissions to use this command.", delete_after=15)
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(f"❌ Bot missing permissions: {', '.join(error.missing_permissions)}", delete_after=15)
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("❌ This command can only be used in a server.", delete_after=15)
    else:
        await ctx.send(f"❌ An error occurred: {str(error)[:200]}", delete_after=15)
        logger.error(f"Command error: {error}", exc_info=True)

@bot.event
async def on_ready():
    logger.info(f"Bot is ready! Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!setup | !help"))

if __name__ == "__main__":
    bot.run(TOKEN)
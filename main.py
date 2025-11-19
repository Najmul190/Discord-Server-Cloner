import subprocess
import os
import sys
import json
import time
import platform
import discord
import logging
import datetime
import asyncio
import requests

from utils.cloner import Cloner, logs, ProgressTracker
from utils.panel import Panel, Panel_Run
from discord.ext import commands
from rich.prompt import Prompt, Confirm
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskID,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.console import Console
from rich.table import Table
from rich.panel import Panel as RichPanel
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns
from rich import box
from time import sleep

console = Console()

VERSION = "1.0.0"


def check_for_updates():
    """Check for updates from GitHub repository"""
    try:
        response = requests.get(
            "https://api.github.com/repos/Najmul190/Server-Cloner/releases/latest",
            timeout=5,
        )
        if response.status_code == 200:
            latest_version = response.json().get("tag_name", "").lstrip("v")
            if latest_version and latest_version != VERSION:
                console.print(
                    f"\n[yellow]Update available: v{latest_version} (current: v{VERSION})[/yellow]"
                )
                console.print(
                    "[dim]Download: https://github.com/Najmul190/Server-Cloner/releases/latest[/dim]\n"
                )

                sleep(5)

                return True
    except:
        pass
    return False


def clear_console():
    command = "clear"
    if os.name in ("nt", "dos"):
        command = "cls"
    os.system(command)


def display_header():
    clear_console()
    console.print(
        RichPanel(
            f"[bold cyan]Discord Server Cloner v{VERSION}[/bold cyan]\n"
            "[white]Made by Najmul (github.com/Najmul190)[/white]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )
    console.print()


try:
    bot = commands.Bot(
        command_prefix=">",
        self_bot=True,
        chunk_guilds_at_startup=False,
        guild_subscriptions=False,
    )
except Exception as e:
    print("> Failed to create Discord bot: ", e)

if not os.path.exists("./config.json"):
    console.print("\n[cyan]═══ First Time Setup ═══[/cyan]\n")
    console.print(
        "[yellow]No config.json found. Let's set up your configuration.[/yellow]\n"
    )

    user_token = Prompt.ask("[bold]> Enter your Discord Token[/bold]")
    if not user_token or len(user_token) < 50:
        console.print("[red]Invalid token format[/red]")
        sys.exit(1)

    if os.path.exists("./config.example.json"):
        import shutil

        shutil.copy("./config.example.json", "./config.json")
        with open("./config.json", "r") as f:
            config_data = json.load(f)
        config_data["token"] = user_token
        with open("./config.json", "w") as f:
            json.dump(config_data, f, indent=4)
        console.print("[green]Created config.json from example with your token[/green]")
    else:
        default_config = {
            "token": user_token,
            "logs": True,
            "copy_settings": {
                "categories": True,
                "channels": True,
                "roles": True,
                "emojis": True,
                "stickers": True,
                "forum_channels": True,
                "soundboard": True,
                "scheduled_events": True,
                "onboarding": True,
                "message_history": True,
                "message_history_limit": 15,
                "clone_pins": True,
                "bans": True,
            },
        }
        with open("./config.json", "w") as f:
            json.dump(default_config, f, indent=4)
        console.print("[green]Created default config.json with your token[/green]")

    sleep(1)

try:
    with open("./config.json", "r") as json_file:
        data = json.load(json_file)
except json.JSONDecodeError:
    console.print("[bold red]Error:[/bold red] config.json is corrupted")
    console.print("[yellow]Delete config.json and restart to create a new one[/yellow]")
    sys.exit(1)
except Exception as e:
    console.print(f"[bold red]Error loading config:[/bold red] {e}")
    sys.exit(1)

console.clear()


def clear(option=False):
    clear_console()
    if option:
        guild_from = bot.get_guild(int(INPUT_GUILD_ID))
        guild_to = bot.get_guild(int(GUILD))
        Panel_Run(guild_from, guild_to)
    else:
        Panel()


async def clone_server():
    start_time = time.time()
    try:

        guild_from = bot.get_guild(int(INPUT_GUILD_ID))
        guild_to = bot.get_guild(int(GUILD))
        if not guild_from:
            console.print(
                "\n[bold red]> Error:[/bold red] Could not find the source server with ID {INPUT_GUILD_ID}"
            )
            console.print(
                "[yellow]> Please check if the ID is correct and if the bot has access to this server.[/yellow]"
            )
            return

        if not guild_to:
            console.print(
                f"\n[bold red]> Error:[/bold red] Could not find the destination server with ID {GUILD}"
            )
            console.print(
                "[yellow]> Please check if the ID is correct and if the bot has access to this server.[/yellow]"
            )
            return

        source_id = str(guild_from.id)
        target_id = str(guild_to.id)

        console.print("\n" + "─" * 120 + "\n")
        console.print(
            "[bold yellow]Please review the server information above carefully.[/bold yellow]"
        )
        console.print("[dim]Press Enter to continue or Ctrl+C to cancel...[/dim]")
        input()

        proceed = Confirm.ask(
            "[bold cyan]> Do you want to proceed with cloning?[/bold cyan]"
        )
        if not proceed:
            console.print("[yellow]> Cloning cancelled by user.[/bold yellow]")
            return

        clear_console()
        console.print(
            RichPanel(
                "[bold green]Starting Cloning Process...[/bold green]",
                border_style="green",
            )
        )
        console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[bold green]{task.completed}/{task.total}"),
            expand=True,
        ) as progress:
            main_task = progress.add_task("[bold cyan]Cloning server...", total=12)

            analysis_task = progress.add_task(
                "[yellow]Analyzing existing content...", total=1
            )
            clone_state, progress_percentage = await Cloner.check_clone_progress(
                guild_to, guild_from
            )
            progress.update(analysis_task, completed=1)
            progress.update(main_task, advance=1)

            skip_existing = progress_percentage > 80

            if not clone_state["name_changed"] or not skip_existing:
                name_task = progress.add_task(
                    "[green]Setting server name and icon...", total=1
                )
                await Cloner.guild_create(guild_to, guild_from)
                progress.update(name_task, completed=1)
            progress.update(main_task, advance=1)

            if not clone_state["community_enabled"] or not skip_existing:
                community_task = progress.add_task(
                    "[magenta]Enabling community features...", total=1
                )
                await Cloner.enable_community_features(guild_to, guild_from)
                progress.update(community_task, completed=1)
            progress.update(main_task, advance=1)

            if not skip_existing or progress_percentage < 50:
                channels_count = len(guild_to.channels)
                delete_task = progress.add_task(
                    f"[red]Deleting {channels_count} existing channels...",
                    total=channels_count if channels_count > 0 else 1,
                )

                original_logs = logs

                def progress_log_delete(message, type, number=None):
                    if type == "delete" and "Deleted Channel:" in message:
                        progress.update(delete_task, advance=1)
                    original_logs(message, type, number)

                Cloner.logs = progress_log_delete
                community_channel_ids, channel_name_map = await Cloner.channels_delete(
                    guild_to, guild_from, skip_if_exists=True
                )
                Cloner.logs = original_logs

                if channels_count == 0:
                    progress.update(delete_task, completed=1)
            progress.update(main_task, advance=1)

            is_source_community = False
            try:
                http = guild_from._state.http
                guild_data = await http.request(
                    discord.http.Route(
                        "GET",
                        "/guilds/{guild_id}?with_counts=true",
                        guild_id=guild_from.id,
                    )
                )
                is_source_community = "COMMUNITY" in guild_data.get("features", [])
            except Exception as e:
                logs(
                    f"Error checking if source guild has community features: {e}",
                    "warning",
                )

            if data["copy_settings"]["roles"] and (
                not clone_state["roles_exist"] or not skip_existing
            ):
                roles_count = len(
                    [role for role in guild_from.roles if role.name != "@everyone"]
                )
                roles_task = progress.add_task(
                    f"[magenta]Creating {roles_count} roles...", total=roles_count
                )

                original_logs = Cloner.logs

                def progress_log_roles(message, type, number=None):
                    if type == "add" and not number and "Created Role" in message:
                        progress.update(roles_task, advance=1)
                    original_logs(message, type, number)

                Cloner.logs = progress_log_roles

                async def roles_create_wrapper():
                    step = "roles"
                    if ProgressTracker.is_step_done(step, source_id, target_id):
                        Cloner.logs("Roles step already completed, skipping.", "add")
                        return
                    roles = [
                        role for role in guild_from.roles if role.name != "@everyone"
                    ]
                    roles.reverse()
                    roles_created = 0
                    for role in roles:
                        if ProgressTracker.is_item_done(
                            step, role.name, source_id, target_id
                        ):
                            continue
                        try:
                            kwargs = {
                                "name": role.name,
                                "permissions": role.permissions,
                                "colour": role.colour,
                                "hoist": role.hoist,
                                "mentionable": role.mentionable,
                            }
                            await guild_to.create_role(**kwargs)
                            Cloner.logs(f"Created Role {role.name}", "add")
                            ProgressTracker.mark_item(step, role.name)
                            roles_created += 1
                        except (discord.Forbidden, discord.HTTPException) as e:
                            Cloner.logs(
                                f"Error creating role {role.name}: {e}", "error"
                            )
                    Cloner.logs(f"Created Roles: {roles_created}", "add", True)
                    ProgressTracker.mark_step_done(step, source_id, target_id)

                await roles_create_wrapper()
                Cloner.logs = original_logs
            progress.update(main_task, advance=1)

            if data["copy_settings"]["categories"] and (
                not clone_state["categories_exist"] or not skip_existing
            ):
                categories_count = len(guild_from.categories)
                categories_task = progress.add_task(
                    f"[blue]Creating {categories_count} categories...",
                    total=categories_count,
                )

                original_logs = Cloner.logs

                def progress_log_categories(message, type, number=None):
                    if (
                        type == "add"
                        and "Created Category" in message
                        and ":" in message
                    ):
                        progress.update(categories_task, advance=1)
                    original_logs(message, type, number)

                async def categories_create_wrapper():
                    await Cloner.categories_create(guild_to, guild_from)

                Cloner.logs = progress_log_categories
                await categories_create_wrapper()
                Cloner.logs = original_logs
            progress.update(main_task, advance=1)

            if data["copy_settings"]["channels"] and (
                not clone_state["channels_exist"] or not skip_existing
            ):
                channels_count = len(guild_from.text_channels) + len(
                    guild_from.voice_channels
                )
                channels_task = progress.add_task(
                    f"[cyan]Creating {channels_count} channels...", total=channels_count
                )

                original_logs = Cloner.logs

                def progress_log_channels(message, type, number=None):
                    if (
                        type == "add"
                        and "Created" in message
                        and "Channel:" in message
                        and "channels" not in message.lower()
                    ):
                        progress.update(channels_task, advance=1)
                    original_logs(message, type, number)

                async def channels_create_wrapper():
                    await Cloner.channels_create(guild_to, guild_from)

                Cloner.logs = progress_log_channels
                await channels_create_wrapper()
                Cloner.logs = original_logs

                if is_source_community:
                    logs(
                        "Restoring community channel mappings to match source server...",
                        "add",
                    )
                    await Cloner.restore_community_channels(guild_to, guild_from)
            progress.update(main_task, advance=1)

            if data["copy_settings"]["emojis"] and (
                not clone_state["emojis_exist"] or not skip_existing
            ):
                try:
                    to_boost_level = guild_to.premium_tier
                    emoji_limits = {0: 50, 1: 100, 2: 150, 3: 250}
                    to_limit = emoji_limits.get(to_boost_level, 50)
                    emojis_count = min(len(guild_from.emojis), to_limit)
                except:
                    emojis_count = len(guild_from.emojis)

                emojis_task = progress.add_task(
                    f"[yellow]Creating {emojis_count} emojis...", total=emojis_count
                )

                original_logs = Cloner.logs

                def progress_log_emojis(message, type, number=None):
                    if (
                        type == "add"
                        and number is None
                        and "Created Emoji " in message
                        and ":" not in message
                    ):
                        progress.update(emojis_task, advance=1)
                    original_logs(message, type, number)

                Cloner.logs = progress_log_emojis

                await Cloner.emojis_create(guild_to, guild_from)

                Cloner.logs = original_logs
            progress.update(main_task, advance=1)

            if data.get("copy_settings", {}).get("stickers", True):
                try:
                    stickers_count = len(await guild_from.fetch_stickers())
                    stickers_task = progress.add_task(
                        f"[blue]Creating {stickers_count} stickers...",
                        total=stickers_count,
                    )

                    original_logs = Cloner.logs

                    def progress_log_stickers(message, type, number=None):
                        if type == "add" and "Created sticker:" in message:
                            progress.update(stickers_task, advance=1)
                        original_logs(message, type, number)

                except Exception as e:
                    logs(
                        f"Error fetching stickers from source server: {e}",
                        "error",
                    )
                    stickers_count = 0
                    stickers_task = progress.add_task(
                        "[blue]No stickers to copy...", total=1
                    )
                    progress.update(stickers_task, completed=1)

                Cloner.logs = progress_log_stickers

                await Cloner.stickers_create(guild_to, guild_from)

                Cloner.logs = original_logs
            progress.update(main_task, advance=0.25)

            if data.get("copy_settings", {}).get("forum_channels", True):
                try:
                    forum_channels = [
                        channel
                        for channel in guild_from.channels
                        if isinstance(channel, discord.ForumChannel)
                    ]
                    forum_count = len(forum_channels)
                    if forum_count > 0:
                        forum_task = progress.add_task(
                            f"[magenta]Creating {forum_count} forum channels...",
                            total=forum_count,
                        )

                        original_logs = Cloner.logs

                        def progress_log_forums(message, type, number=None):
                            if type == "add" and "Created forum channel:" in message:
                                progress.update(forum_task, advance=1)
                            original_logs(message, type, number)

                        Cloner.logs = progress_log_forums
                        await Cloner.forum_channels_create(guild_to, guild_from)
                        Cloner.logs = original_logs
                except Exception as e:
                    logs(f"Error during forum channels creation: {e}", "error")
            progress.update(main_task, advance=0.25)

            if data.get("copy_settings", {}).get("scheduled_events", True):
                try:
                    events_task = progress.add_task(
                        "[yellow]Cloning scheduled events...", total=1
                    )
                    await Cloner.scheduled_events_create(guild_to, guild_from)
                    progress.update(events_task, completed=1)
                except Exception as e:
                    logs(f"Error during scheduled events cloning: {e}", "error")
            progress.update(main_task, advance=0.25)

            if data.get("copy_settings", {}).get("soundboard", True):
                try:
                    soundboard_task = progress.add_task(
                        "[cyan]Cloning soundboard sounds...", total=1
                    )
                    await Cloner.soundboard_sounds_create(guild_to, guild_from)
                    progress.update(soundboard_task, completed=1)
                except Exception as e:
                    logs(f"Error during soundboard cloning: {e}", "error")
            progress.update(main_task, advance=0.25)

            if data["copy_settings"]["onboarding"] and (
                not clone_state["onboarding_enabled"] or not skip_existing
            ):
                onboarding_task = progress.add_task(
                    "[green]Setting up onboarding...", total=1
                )
                await Cloner.onboarding_create(guild_to, guild_from)
                progress.update(onboarding_task, completed=1)
            progress.update(main_task, advance=1)

            if data["copy_settings"]["message_history"]:
                text_channel_matches = 0
                for source_channel in guild_from.text_channels:
                    if discord.utils.get(
                        guild_to.text_channels, name=source_channel.name
                    ):
                        text_channel_matches += 1

                if text_channel_matches > 0:
                    message_history_task = progress.add_task(
                        f"[blue]Transferring message history for {text_channel_matches} channels...",
                        total=text_channel_matches,
                    )

                    original_logs = Cloner.logs

                    def progress_log_messages(message, type, number=None):
                        if (
                            type == "add"
                            and number is None
                            and "Transferred" in message
                            and "messages to #" in message
                        ):
                            progress.update(message_history_task, advance=1)
                        original_logs(message, type, number)

                    Cloner.logs = progress_log_messages
                    await Cloner.transfer_messages(guild_to, guild_from)
                    Cloner.logs = original_logs
                else:
                    message_history_task = progress.add_task(
                        "[blue]No matching channels found for message transfer", total=1
                    )
                    progress.update(message_history_task, completed=1)
            progress.update(main_task, advance=1)

            if data.get("copy_settings", {}).get("bans", True):
                try:
                    ban_count = 0
                    try:
                        async for _ in guild_from.bans(limit=None):
                            ban_count += 1
                    except:
                        ban_count = 0

                    if ban_count > 0:
                        bans_task = progress.add_task(
                            f"[red]Transferring {ban_count} bans...", total=ban_count
                        )

                        original_logs = Cloner.logs

                        def progress_log_bans(message, type, number=None):
                            if (
                                type == "add"
                                and number is None
                                and "Banned user" in message
                            ):
                                progress.update(bans_task, advance=1)
                            original_logs(message, type, number)

                        Cloner.logs = progress_log_bans
                        await Cloner.bans_transfer(guild_to, guild_from)
                        Cloner.logs = original_logs
                    else:
                        bans_task = progress.add_task(
                            "[red]No bans to transfer...", total=1
                        )
                        progress.update(bans_task, completed=1)
                except Exception as e:
                    logs(f"Error during bans transfer: {e}", "error")
            progress.update(main_task, advance=1)

        end_time = time.time()
        duration = round(end_time - start_time, 2)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

        clear_console()

        summary_panel = RichPanel(
            f"[bold green]Server cloning completed successfully![/bold green]\n\n"
            f"[bold]Time taken:[/bold] {time_str}\n"
            f"[bold]Source:[/bold] [cyan]{guild_from.name}[/cyan] (ID: {guild_from.id})\n"
            f"[bold]Destination:[/bold] [magenta]{guild_to.name}[/magenta] (ID: {guild_to.id})\n\n"
            f"[dim]Check [cyan]logs/log.txt[/cyan] for detailed logs[/dim]",
            title="[bold]Cloning Summary[/bold]",
            border_style="green",
        )
        console.print(summary_panel)
        console.print("\n[green]Press any key to exit...[/green]")
        console.show_cursor(False)

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Process interrupted by user.[/bold yellow]")
        console.print(
            "[yellow]Exiting without saving progress (progress persistence disabled).[/yellow]"
        )

    except Exception as e:
        clear_console()
        console.print(
            RichPanel(
                f"[bold red]An error occurred during cloning:[/bold red]\n{e}\n\n> Make sure both server IDs are correct and the bot has proper permissions.",
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )


@bot.event
async def on_ready():
    guild_from = bot.get_guild(int(INPUT_GUILD_ID))
    guild_to = bot.get_guild(int(GUILD))
    Panel_Run(guild_from, guild_to)
    await clone_server()


class ClonerBot:

    def __init__(self):
        self.INPUT_GUILD_ID = None
        with open("./config.json", "r") as json_file:
            self.data = json.load(json_file)

    def clear(self):
        clear_console()
        Panel()

    def edit_config(self, option, value, copy_settings=False):
        if copy_settings:
            self.data["copy_settings"][option] = value
        else:
            self.data[option] = value
        with open("./config.json", "w") as json_file:
            json.dump(self.data, json_file, indent=4)

    def edit_settings_function(self):
        clear_console()
        console.print(
            RichPanel("[bold cyan]Edit What to Copy[/bold cyan]", border_style="cyan")
        )
        print("\nDo you want to copy:")
        categories = Confirm.ask("> Categories?")
        channels = Confirm.ask("> Channels?")
        roles = Confirm.ask("> Roles?")
        emojis = Confirm.ask("> Emojis?")
        stickers = Confirm.ask("> Stickers?")
        forum_channels = Confirm.ask("> Forum Channels?")
        soundboard = Confirm.ask("> Soundboard Sounds?")
        scheduled_events = Confirm.ask("> Scheduled Events?")
        onboarding = Confirm.ask("> Onboarding?")
        message_history = Confirm.ask("> Message History?")
        bans = Confirm.ask("> Server Bans?")

        clone_pins = False
        if message_history:
            message_history_limit = Prompt.ask(
                "> How many messages to copy per channel?", default="15"
            )
            try:
                message_history_limit = int(message_history_limit)
                if message_history_limit <= 0:
                    message_history_limit = 15
            except ValueError:
                message_history_limit = 15
            self.edit_config(
                "message_history_limit", message_history_limit, copy_settings=True
            )

            clone_pins = Confirm.ask("> Clone pinned messages?", default=True)
            self.edit_config("clone_pins", clone_pins, copy_settings=True)

        for option in [
            "categories",
            "channels",
            "roles",
            "emojis",
            "stickers",
            "forum_channels",
            "soundboard",
            "scheduled_events",
            "onboarding",
            "message_history",
            "bans",
        ]:
            self.edit_config(option, locals()[option], copy_settings=True)

    def main(self):
        clear_console()
        if self.data["token"] == False:
            self.TOKEN = Prompt.ask("\n[bold]> Enter your Token[/bold]")
            self.edit_config("token", self.TOKEN)
            console.print("Token saved to config.json")
            sleep(0.5)
        else:
            self.TOKEN = self.data["token"]

        self.clear()
        edit_settings = Confirm.ask(
            "\n[bold]> Do you want to edit the settings?[/bold]"
        )
        self.clear()
        if edit_settings:
            self.edit_settings_function()
        self.clear()
        clear_console()

        while True:
            self.INPUT_GUILD_ID = Prompt.ask(
                "[bold magenta]> Enter the Server ID you want to clone from[/bold magenta]"
            )
            if self.INPUT_GUILD_ID.isdigit() and len(self.INPUT_GUILD_ID) >= 10:
                break
            console.print("[yellow]Invalid Server ID.[/yellow]")

        sleep(0.3)

        while True:
            self.GUILD = Prompt.ask(
                "[bold cyan]> Enter the Server ID you want to copy to[/bold cyan]"
            )
            if self.GUILD.isdigit() and len(self.GUILD) >= 10:
                if self.GUILD == self.INPUT_GUILD_ID:
                    console.print(
                        "[yellow]Source and destination cannot be the same[/yellow]"
                    )
                    continue
                break
            console.print("[yellow]Invalid Server ID.[/yellow]")

        sleep(0.3)
        return self.INPUT_GUILD_ID, self.TOKEN, self.GUILD


if __name__ == "__main__":

    check_for_updates()

    INPUT_GUILD_ID, TOKEN, GUILD = ClonerBot().main()
    clear_console()
    try:
        bot.run(TOKEN, log_handler=None)
        clear()
    except discord.LoginFailure:
        console.print("\n[bold red]Invalid Token[/bold red]")
        console.print("[yellow]Your token is incorrect or has expired.[/yellow]")
        console.print(
            "[dim]Token has been removed from config. Please restart and enter a new token.[/dim]"
        )
        data["token"] = False
        with open("./config.json", "w") as json_file:
            json.dump(data, json_file, indent=4)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        console.print("[yellow]An unexpected error occurred.[/yellow]")

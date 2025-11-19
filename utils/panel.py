from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.panel import Panel as RichPanel
from rich.layout import Layout
from rich.columns import Columns
from rich.progress import ProgressBar
from rich import box
import json
import platform
import datetime


def Panel():
    with open("./config.json", "r") as json_file:
        data = json.load(json_file)

    console = Console()

    console.print()
    console.print(
        RichPanel(
            "[bold cyan]Discord Server Cloner[/bold cyan]\n"
            "[white]Made by Najmul (github.com/Najmul190)[/white]",
            border_style="cyan",
            box=box.DOUBLE,
        )
    )

    settings_table = Table(
        show_header=True, header_style="bold blue", box=box.ROUNDED, expand=True
    )
    settings_table.add_column("Setting", style="cyan")
    settings_table.add_column("Status", justify="center", style="magenta")
    settings_table.add_column("Description", style="green")

    descriptions = {
        "categories": "Copy server categories structure",
        "channels": "Copy text and voice channels",
        "roles": "Copy roles and their permissions",
        "permissions": "Copy channel permission overwrites",
        "emojis": "Copy custom emojis",
        "onboarding": "Copy onboarding configuration",
        "stickers": "Copy stickers",
        "forum_channels": "Copy forum channels",
        "scheduled_events": "Copy scheduled events",
        "message_history": f"Copy up to {data['copy_settings'].get('message_history_limit', 50)} messages per channel",
        "clone_pins": "Copy pinned messages",
        "bans": "Copy user bans",
        "soundboard": "Copy soundboard sounds",
    }

    for setting, status in data["copy_settings"].items():
        if setting in ["message_history_limit", "clone_pins"]:
            continue
        icon = "✅" if status else "❌"
        settings_table.add_row(
            setting.capitalize(),
            f"[{'green bold' if status else 'red'}]{icon}[/]",
            descriptions.get(setting, ""),
        )

    console.print(settings_table)

    sys_info = Table(show_header=False, box=box.SIMPLE, expand=True)
    sys_info.add_column("Property", style="yellow")
    sys_info.add_column("Value", style="white")

    sys_info.add_row("System", platform.system() + " " + platform.release())
    sys_info.add_row("Python", platform.python_version())

    token_status = "[green]Configured[/]" if data["token"] else "[red]Not Configured[/]"
    sys_info.add_row("Token", token_status)

    console.print(
        RichPanel(sys_info, title="[bold]System Information[/]", border_style="blue")
    )


def Panel_Run(guild_from, guild_to):
    with open("./config.json", "r") as json_file:
        data = json.load(json_file)

    console = Console()

    console.print()
    console.print(
        RichPanel(
            "[bold green]Discord Server Cloner[/bold green]",
            border_style="green",
            box=box.DOUBLE,
        )
    )

    source_table = Table(
        title=f"Source Server: {guild_from.name}",
        show_header=False,
        box=box.ROUNDED,
    )
    source_table.add_column("Property", style="cyan")
    source_table.add_column("Value", style="green")
    source_table.add_row("ID", str(guild_from.id))
    source_table.add_row("Members", str(guild_from.member_count))
    source_table.add_row("Channels", str(len(guild_from.channels)))
    source_table.add_row("Roles", str(len(guild_from.roles)))
    source_table.add_row("Emojis", str(len(guild_from.emojis)))
    source_table.add_row("Boosters", str(guild_from.premium_subscription_count))

    dest_table = Table(
        title=f"Destination Server: {guild_to.name}",
        show_header=False,
        box=box.ROUNDED,
    )
    dest_table.add_column("Property", style="cyan")
    dest_table.add_column("Value", style="yellow")
    dest_table.add_row("ID", str(guild_to.id))
    dest_table.add_row("Members", str(guild_to.member_count))
    dest_table.add_row("Channels", str(len(guild_to.channels)))
    dest_table.add_row("Roles", str(len(guild_to.roles)))
    dest_table.add_row("Emojis", str(len(guild_to.emojis)))
    dest_table.add_row("Boosters", str(guild_to.premium_subscription_count))

    console.print(Columns([source_table, dest_table], equal=True, expand=True))
    console.print()

    status_table = Table(
        show_header=True, header_style="bold magenta", box=box.ROUNDED, expand=True
    )
    status_table.add_column("Setting", style="cyan")
    status_table.add_column("Status", justify="center")

    for setting, status in data["copy_settings"].items():
        if status:
            status_table.add_row(setting.capitalize(), "[green]Will Copy[/]")

    status_panel = RichPanel(
        status_table, title="[bold]Cloning Status[/]", border_style="magenta"
    )

    console.print(status_panel)

    footer = Table.grid(expand=True)
    footer.add_column(style="green", justify="left")
    footer.add_column(style="magenta", justify="right")

    console.print(footer)

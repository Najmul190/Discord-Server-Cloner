import discord
from colorama import Fore, init, Style
import asyncio
import json
import os
import threading
import os
import datetime
import io
import aiohttp
import base64

os.makedirs("./logs", exist_ok=True)

log_file_path = "./logs/log.txt"


def initialize_log_file():
    with open(log_file_path, "w", encoding="utf-8") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"=== SERVER CLONER LOG STARTED AT {timestamp} ===\n")
        log_file.write(f"=== USER: {os.getenv('USERNAME', 'Unknown')} ===\n\n")


initialize_log_file()


def clear_line(n=1):
    LINE_UP = "\033[1A"
    LINE_CLEAR = "\x1b[2K"
    for _ in range(n):
        print(LINE_UP, end=LINE_CLEAR)


def logs(message, type, number=None):
    if logs_enabled:
        log_types = {
            "add": ("[+]", Fore.GREEN),
            "delete": ("[-]", Fore.RED),
            "warning": ("[WARNING]", Fore.YELLOW),
            "error": ("[ERROR]", Fore.RED),
        }
        prefix, color = log_types.get(type, ("[?]", Fore.RESET))

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {prefix} {message}\n")

        if number is not None:
            print(f" {color}{prefix}{Style.RESET_ALL} {message}")
        else:
            print(f" {color}{prefix}{Style.RESET_ALL} {message}")
            if type != "error" and type != "warning":
                clear_line()


logs_enabled = True
try:
    with open("./config.json", "r") as json_file:
        data = json.load(json_file)
        logs_enabled = data.get("logs", True)
except FileNotFoundError:
    pass
except Exception as e:
    print(f"Warning: Could not load config.json: {e}")


def clear_line(n=1):
    LINE_UP = "\033[1A"
    LINE_CLEAR = "\x1b[2K"
    for _ in range(n):
        print(LINE_UP, end=LINE_CLEAR)


class ProgressTracker:
    _lock = threading.Lock()
    _progress_data = {}
    _is_error_state = False

    @staticmethod
    def set_error_state(is_error=True):
        ProgressTracker._is_error_state = is_error

    @classmethod
    def load(cls, source_id=None, target_id=None):
        key = f"{source_id}-{target_id}" if source_id and target_id else "default"

        if key in cls._progress_data:
            return cls._progress_data[key]
        cls._progress_data[key] = {}
        return cls._progress_data[key]

    @classmethod
    def save(cls, data, source_id=None, target_id=None):
        key = f"{source_id}-{target_id}" if source_id and target_id else "default"

        with cls._lock:
            cls._progress_data[key] = data

    @classmethod
    def mark_item(cls, step, item, source_id=None, target_id=None):
        data = cls.load(source_id, target_id)
        if step not in data:
            data[step] = []
        if item not in data[step]:
            data[step].append(item)
            cls.save(data, source_id, target_id)
            cls.update_timestamp(step, source_id, target_id)

    @classmethod
    def is_item_done(cls, step, item, source_id=None, target_id=None):
        data = cls.load(source_id, target_id)
        return step in data and item in data[step]

    @classmethod
    def mark_step_done(cls, step, source_id=None, target_id=None):
        data = cls.load(source_id, target_id)
        data[step + "_done"] = True
        cls.save(data, source_id, target_id)
        cls.update_timestamp(step + "_done", source_id, target_id)

    @classmethod
    def is_step_done(cls, step, source_id=None, target_id=None):
        data = cls.load(source_id, target_id)
        return data.get(step + "_done", False)

    @classmethod
    def update_timestamp(cls, step, source_id=None, target_id=None):
        data = cls.load(source_id, target_id)
        timestamp_key = "_timestamps"
        if timestamp_key not in data:
            data[timestamp_key] = {}

        data[timestamp_key][step] = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        cls.save(data, source_id, target_id)

    @classmethod
    def get_timestamp(cls, step, source_id=None, target_id=None):
        data = cls.load(source_id, target_id)
        timestamp_key = "_timestamps"
        if timestamp_key in data and step in data[timestamp_key]:
            return data[timestamp_key][step]
        return None

    @classmethod
    def clear(cls, source_id=None, target_id=None):
        key = f"{source_id}-{target_id}" if source_id and target_id else "default"
        if key in cls._progress_data:
            del cls._progress_data[key]


class Cloner:
    logs = staticmethod(logs)

    @staticmethod
    async def guild_create(guild_to: discord.Guild, guild_from: discord.Guild):
        try:
            guild_assets = {}

            try:
                guild_assets["icon"] = (
                    await guild_from.icon.read() if guild_from.icon else None
                )
            except discord.errors.DiscordException:
                logs(f"Can't read icon image from {guild_from.name}", "error")
                guild_assets["icon"] = None

            try:
                guild_assets["banner"] = (
                    await guild_from.banner.read() if guild_from.banner else None
                )
            except discord.errors.DiscordException:
                logs(f"Can't read banner image from {guild_from.name}", "error")
                guild_assets["banner"] = None

            try:
                guild_assets["splash"] = (
                    await guild_from.splash.read() if guild_from.splash else None
                )
            except discord.errors.DiscordException:
                logs(f"Can't read splash image from {guild_from.name}", "error")
                guild_assets["splash"] = None

            guild_attributes = {
                "name": guild_from.name,
                "description": guild_from.description,
                "verification_level": guild_from.verification_level,
                "default_notifications": guild_from.default_notifications,
                "explicit_content_filter": guild_from.explicit_content_filter,
                "preferred_locale": guild_from.preferred_locale,
                "afk_timeout": guild_from.afk_timeout,
                "premium_progress_bar_enabled": getattr(
                    guild_from, "premium_progress_bar_enabled", None
                ),
            }

            try:
                await guild_to.edit(
                    name=guild_attributes["name"],
                    description=guild_attributes["description"],
                    verification_level=guild_attributes["verification_level"],
                    default_notifications=guild_attributes["default_notifications"],
                    explicit_content_filter=guild_attributes["explicit_content_filter"],
                    preferred_locale=guild_attributes["preferred_locale"],
                    afk_timeout=guild_attributes["afk_timeout"],
                )
                logs(f"Applied basic server settings to {guild_to.name}", "add")
            except discord.errors.Forbidden:
                logs(
                    f"Missing permissions to update server settings for {guild_to.name}",
                    "error",
                )
            except Exception as e:
                logs(f"Error updating server settings: {e}", "error")

            if guild_attributes["premium_progress_bar_enabled"] is not None:
                try:
                    await guild_to.edit(
                        premium_progress_bar_enabled=guild_attributes[
                            "premium_progress_bar_enabled"
                        ]
                    )
                    logs(
                        f"Applied premium progress bar setting: {guild_attributes['premium_progress_bar_enabled']}",
                        "add",
                    )
                except Exception as e:
                    logs(f"Error setting premium progress bar: {e}", "warning")

            for asset_type, asset_data in guild_assets.items():
                if asset_data is not None:
                    try:
                        if asset_type == "icon":
                            await guild_to.edit(icon=asset_data)
                            logs(f"Set server icon for {guild_to.name}", "add")
                        elif asset_type == "banner":
                            await guild_to.edit(banner=asset_data)
                            logs(f"Set server banner for {guild_to.name}", "add")
                        elif asset_type == "splash":
                            await guild_to.edit(splash=asset_data)
                            logs(f"Set invite splash for {guild_to.name}", "add")
                    except discord.errors.Forbidden:
                        logs(
                            f"Missing permissions to set {asset_type} for {guild_to.name}",
                            "error",
                        )
                    except discord.errors.HTTPException as e:
                        logs(f"HTTP error setting {asset_type}: {e}", "error")
                    except Exception as e:
                        logs(f"Error setting {asset_type}: {e}", "error")

        except discord.errors.Forbidden:
            logs(
                f"Error While Updating Guild: {guild_to.name} - Missing Permissions",
                "error",
            )
        except Exception as e:
            logs(f"Unexpected error updating guild: {e}", "error")

        logs(f"Cloned server: {guild_to.name}", "add", True)

    @staticmethod
    async def roles_create(guild_to: discord.Guild, guild_from: discord.Guild):
        step = "roles"
        if ProgressTracker.is_step_done(step):
            Cloner.logs("Roles step already completed, skipping.", "add")
            return
        roles = [role for role in guild_from.roles if role.name != "@everyone"]
        roles.reverse()
        roles_created = 0
        for role in roles:
            if ProgressTracker.is_item_done(step, role.name):
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
                Cloner.logs(f"Error creating role {role.name}: {e}", "error")
        Cloner.logs(f"Created Roles: {roles_created}", "add", True)
        ProgressTracker.mark_step_done(step)

    @staticmethod
    async def channels_delete(
        guild_to: discord.Guild, guild_from: discord.Guild = None, skip_if_exists=False
    ):
        original_community_channels = {}
        if guild_from:
            success, original_channel_ids = await Cloner.reset_community_channels(
                guild_to, guild_from
            )
            if success:
                original_community_channels = original_channel_ids
                logs("Stored original community channel configuration", "add")

        channel_name_to_id_map = {}
        for channel in guild_to.channels:
            channel_name_to_id_map[channel.name] = channel.id

        if skip_if_exists:
            step = "channels"
            source_channels = (
                [c.name for c in guild_from.text_channels + guild_from.voice_channels]
                if guild_from
                else []
            )
            target_channels = [
                c.name for c in guild_to.text_channels + guild_to.voice_channels
            ]
            common = set(source_channels) & set(target_channels)
            if source_channels and common and len(common) / len(source_channels) > 0.5:
                Cloner.logs(
                    "Channels already exist from previous clone, skipping deletion",
                    "add",
                )
                return original_community_channels, channel_name_to_id_map

        channels = guild_to.channels
        channels_deleted = 0

        for channel in channels:
            try:
                await channel.delete()
                Cloner.logs(f"Deleted Channel: {channel.name}", "delete")
                channels_deleted += 1
            except (discord.Forbidden, discord.HTTPException) as e:
                Cloner.logs(f"Error deleting channel {channel.name}: {e}", "error")

        Cloner.logs(f"Deleted Channels: {channels_deleted}", "delete", True)

        return original_community_channels, channel_name_to_id_map

    @staticmethod
    async def categories_create(guild_to: discord.Guild, guild_from: discord.Guild):
        step = "categories"
        if ProgressTracker.is_step_done(step):
            Cloner.logs("Categories step already completed, skipping.", "add")
            return
        channels = guild_from.categories
        categories_created = 0
        for channel in channels:
            if ProgressTracker.is_item_done(step, channel.name):
                continue

            existing_category = discord.utils.get(
                guild_to.categories, name=channel.name
            )
            if existing_category:
                Cloner.logs(
                    f"Category '{channel.name}' already exists, skipping", "add"
                )
                ProgressTracker.mark_item(step, channel.name)
                continue

            try:
                overwrites_to = {}
                for key, value in channel.overwrites.items():
                    if isinstance(key, discord.Role):
                        role = discord.utils.get(guild_to.roles, name=key.name)
                        if role:
                            overwrites_to[role] = value
                    elif hasattr(key, "name") and hasattr(key, "id"):
                        try:
                            if hasattr(key, "bot") and key.bot:
                                found_obj = discord.utils.get(
                                    guild_to.members, bot=True, name=key.name
                                )
                            else:
                                found_obj = discord.utils.get(
                                    guild_to.members, name=key.name
                                )
                            if found_obj:
                                overwrites_to[found_obj] = value
                        except:
                            Cloner.logs(
                                f"Skipping overwrite for {getattr(key, 'name', 'Unknown object')}",
                                "warning",
                            )
                    else:
                        Cloner.logs(
                            f"Skipping overwrite for an object without a name attribute",
                            "warning",
                        )

                new_channel = await guild_to.create_category(
                    name=channel.name, overwrites=overwrites_to
                )
                await new_channel.edit(position=channel.position)
                Cloner.logs(f"Created Category: {channel.name}", "add")
                ProgressTracker.mark_item(step, channel.name)
                categories_created += 1
            except discord.Forbidden:
                Cloner.logs(f"Error creating category {channel.name}", "error")
            except discord.HTTPException:
                Cloner.logs(f"Error creating category {channel.name}", "error")
            except Exception as e:
                Cloner.logs(
                    f"Unexpected error creating category {channel.name}: {e}", "error"
                )
        Cloner.logs(f"Created Categories: {categories_created}", "add", True)
        ProgressTracker.mark_step_done(step)

    @staticmethod
    async def channels_create(guild_to: discord.Guild, guild_from: discord.Guild):
        step = "channels"
        if ProgressTracker.is_step_done(step):
            Cloner.logs("Channels step already completed, skipping.", "add")
            return
        channels = guild_from.text_channels + guild_from.voice_channels
        channel_types = {
            discord.TextChannel: guild_to.create_text_channel,
            discord.VoiceChannel: guild_to.create_voice_channel,
        }
        channels_created = 0
        for channel in channels:
            if ProgressTracker.is_item_done(step, channel.name):
                continue

            if isinstance(channel, discord.TextChannel):
                existing_channel = discord.utils.get(
                    guild_to.text_channels, name=channel.name
                )
            elif isinstance(channel, discord.VoiceChannel):
                existing_channel = discord.utils.get(
                    guild_to.voice_channels, name=channel.name
                )
            else:
                existing_channel = None

            if existing_channel:
                channel_type = (
                    "Text Channel"
                    if isinstance(channel, discord.TextChannel)
                    else "Voice Channel"
                )
                Cloner.logs(
                    f"{channel_type} '{channel.name}' already exists, skipping", "add"
                )
                ProgressTracker.mark_item(step, channel.name)
                continue

            await asyncio.sleep(0.2)
            category = discord.utils.get(
                guild_to.categories, name=getattr(channel.category, "name", None)
            )

            overwrites_to = {}
            for key, value in channel.overwrites.items():
                if isinstance(key, discord.Role):
                    role = discord.utils.get(guild_to.roles, name=key.name)
                    if role:
                        overwrites_to[role] = value
                elif hasattr(key, "name") and hasattr(key, "id"):
                    try:
                        if hasattr(key, "bot") and key.bot:
                            found_obj = discord.utils.get(
                                guild_to.members, bot=True, name=key.name
                            )
                        else:
                            found_obj = discord.utils.get(
                                guild_to.members, name=key.name
                            )
                        if found_obj:
                            overwrites_to[found_obj] = value
                    except:
                        Cloner.logs(
                            f"Skipping overwrite for {getattr(key, 'name', 'Unknown object')}",
                            "warning",
                        )
                else:
                    Cloner.logs(
                        f"Skipping overwrite for an object without a name attribute",
                        "warning",
                    )

            try:
                new_channel = await channel_types[type(channel)](
                    name=channel.name,
                    overwrites=overwrites_to,
                    position=channel.position,
                )

                channel_type = (
                    "Text Channel"
                    if isinstance(channel, discord.TextChannel)
                    else "Voice Channel"
                )
                Cloner.logs(f"Created {channel_type}: {channel.name}", "add")
                channels_created += 1
                ProgressTracker.mark_item(step, channel.name)

                if isinstance(channel, discord.TextChannel):
                    try:
                        edit_kwargs = {
                            "topic": channel.topic,
                            "nsfw": channel.nsfw,
                            "slowmode_delay": channel.slowmode_delay,
                            "default_auto_archive_duration": channel.default_auto_archive_duration,
                        }

                        if hasattr(channel, "default_thread_slowmode_delay"):
                            edit_kwargs["default_thread_slowmode_delay"] = (
                                channel.default_thread_slowmode_delay
                            )

                        if hasattr(channel, "news"):
                            edit_kwargs["news"] = channel.news

                        await new_channel.edit(**edit_kwargs)
                        Cloner.logs(
                            f"Applied all channel settings for {channel.name}",
                            "add",
                        )
                    except Exception as e:
                        Cloner.logs(
                            f"Error applying settings for {channel.name}, trying individual settings: {e}",
                            "warning",
                        )
                        for setting, value in [
                            ("topic", channel.topic),
                            ("nsfw", channel.nsfw),
                            ("slowmode_delay", channel.slowmode_delay),
                            (
                                "default_auto_archive_duration",
                                channel.default_auto_archive_duration,
                            ),
                        ]:
                            try:
                                await new_channel.edit(**{setting: value})
                            except Exception as e:
                                Cloner.logs(
                                    f"Failed to set {setting} for {channel.name}: {e}",
                                    "warning",
                                )

                        if hasattr(channel, "default_thread_slowmode_delay"):
                            try:
                                await new_channel.edit(
                                    default_thread_slowmode_delay=channel.default_thread_slowmode_delay
                                )
                            except Exception as e:
                                Cloner.logs(
                                    f"Failed to set thread slowmode for {channel.name}: {e}",
                                    "warning",
                                )

                        if hasattr(channel, "news"):
                            try:
                                await new_channel.edit(news=channel.news)
                            except Exception as e:
                                Cloner.logs(
                                    f"Failed to set news status for {channel.name}: {e}",
                                    "warning",
                                )

                elif isinstance(channel, discord.VoiceChannel):
                    try:
                        await new_channel.edit(
                            bitrate=min(channel.bitrate, guild_to.bitrate_limit),
                            user_limit=channel.user_limit,
                            rtc_region=channel.rtc_region,
                        )
                        Cloner.logs(
                            f"Applied all voice channel settings for {channel.name} in a single request",
                            "add",
                        )
                    except Exception as e:
                        Cloner.logs(
                            f"Error applying voice settings for {channel.name}, trying individual settings: {e}",
                            "warning",
                        )
                        for setting, value in [
                            ("bitrate", min(channel.bitrate, guild_to.bitrate_limit)),
                            ("user_limit", channel.user_limit),
                            ("rtc_region", channel.rtc_region),
                        ]:
                            try:
                                await new_channel.edit(**{setting: value})
                            except Exception as e:
                                Cloner.logs(
                                    f"Failed to set {setting} for {channel.name}: {e}",
                                    "warning",
                                )

                if category is not None:
                    try:
                        await new_channel.edit(category=category)
                        Cloner.logs(
                            f"Placed {channel.name} in category {category.name}", "add"
                        )
                    except Exception as e:
                        Cloner.logs(
                            f"Failed to place {channel.name} in category {category.name}: {e}",
                            "warning",
                        )
            except Exception as e:
                Cloner.logs(f"Error creating channel {channel.name}: {e}", "error")
                continue

        Cloner.logs(f"Created Channels: {channels_created}", "add", True)
        ProgressTracker.mark_step_done(step)

    @staticmethod
    async def emojis_create(guild_to: discord.Guild, guild_from: discord.Guild):
        step = "emojis"
        if ProgressTracker.is_step_done(step):
            Cloner.logs("Emojis step already completed, skipping.", "add")
            return
        emoji: discord.Emoji
        emojis_created = 0
        try:
            from_boost_level = guild_from.premium_tier
            to_boost_level = guild_to.premium_tier
            emoji_limits = {0: 50, 1: 100, 2: 150, 3: 250}
            from_limit = emoji_limits.get(from_boost_level, 50)
            to_limit = emoji_limits.get(to_boost_level, 50)
            if to_boost_level < from_boost_level:
                Cloner.logs(
                    f"Warning: Destination server has lower boost level ({to_boost_level}) than source server ({from_boost_level})",
                    "warning",
                )
                Cloner.logs(
                    f"Only {to_limit} emojis can be copied (source has limit of {from_limit})",
                    "warning",
                )
                if len(guild_from.emojis) > to_limit:
                    Cloner.logs(
                        f"Will copy only the first {to_limit} emojis", "warning"
                    )
                    emojis_to_copy = guild_from.emojis[:to_limit]
                else:
                    emojis_to_copy = guild_from.emojis
            else:
                emojis_to_copy = guild_from.emojis
        except Exception as e:
            Cloner.logs(f"Error checking boost levels: {e}", "error")
            emojis_to_copy = guild_from.emojis
        for emoji in emojis_to_copy:
            if ProgressTracker.is_item_done(step, emoji.name):
                continue
            try:
                await asyncio.sleep(0.2)
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    if isinstance(emoji.url, str):
                        url = emoji.url
                    else:
                        url = str(emoji.url)
                    async with session.get(url) as response:
                        if response.status == 200:
                            emoji_image = await response.read()
                            await guild_to.create_custom_emoji(
                                name=emoji.name, image=emoji_image
                            )
                            Cloner.logs(f"Created Emoji {emoji.name}", "add")
                            ProgressTracker.mark_item(step, emoji.name)
                            emojis_created += 1
                        else:
                            Cloner.logs(
                                f"Failed to fetch emoji image for {emoji.name} (Status: {response.status})",
                                "error",
                            )
            except discord.Forbidden:
                Cloner.logs(
                    f"Error While Creating Emoji {emoji.name} - Missing Permissions",
                    "error",
                )
            except discord.HTTPException as e:
                Cloner.logs(f"Error While Creating Emoji {emoji.name} - {e}", "error")
            except Exception as e:
                Cloner.logs(
                    f"Unexpected error creating emoji {emoji.name}: {e}", "error"
                )
        Cloner.logs(f"Created Emojis: {emojis_created}", "add", True)
        ProgressTracker.mark_step_done(step)

    @staticmethod
    async def enable_community_features(
        guild_to: discord.Guild, guild_from: discord.Guild
    ):
        try:
            http = guild_from._state.http

            logs("Checking if source server has community features enabled...", "add")
            guild_data = await http.request(
                discord.http.Route(
                    "GET",
                    "/guilds/{guild_id}?with_counts=true",
                    guild_id=guild_from.id,
                )
            )

            features = guild_data.get("features", [])
            is_community = "COMMUNITY" in features

            if not is_community:
                logs(
                    "Source guild doesn't have community features enabled, skipping",
                    "warning",
                    True,
                )
                return False

            target_guild_data = await http.request(
                discord.http.Route(
                    "GET",
                    "/guilds/{guild_id}?with_counts=true",
                    guild_id=guild_to.id,
                )
            )

            target_features = target_guild_data.get("features", [])
            if "COMMUNITY" in target_features:
                logs(
                    "Community features are already enabled in target server",
                    "add",
                    True,
                )
                return True

            logs(
                "Source guild has community features, enabling in destination guild",
                "add",
            )

            rules_channel_id = None
            public_updates_channel_id = None

            if guild_data.get("rules_channel_id"):
                source_rules_channel = discord.utils.get(
                    guild_from.channels, id=int(guild_data["rules_channel_id"])
                )
                if source_rules_channel:
                    dest_rules_channel = discord.utils.get(
                        guild_to.channels, name=source_rules_channel.name
                    )
                    if dest_rules_channel:
                        rules_channel_id = dest_rules_channel.id

            if guild_data.get("public_updates_channel_id"):
                source_updates_channel = discord.utils.get(
                    guild_from.channels, id=int(guild_data["public_updates_channel_id"])
                )
                if source_updates_channel:
                    dest_updates_channel = discord.utils.get(
                        guild_to.channels, name=source_updates_channel.name
                    )
                    if dest_updates_channel:
                        public_updates_channel_id = dest_updates_channel.id

            if not rules_channel_id:
                rules_channel = await guild_to.create_text_channel("rules")
                rules_channel_id = rules_channel.id
                logs("Created rules channel for community features", "add")

            if not public_updates_channel_id:
                updates_channel = await guild_to.create_text_channel("announcements")
                public_updates_channel_id = updates_channel.id
                logs("Created announcements channel for community features", "add")

            try:
                community_payload = {
                    "features": ["COMMUNITY"],
                    "verification_level": guild_data.get("verification_level", 1),
                    "default_message_notifications": guild_data.get(
                        "default_message_notifications", 1
                    ),
                    "explicit_content_filter": guild_data.get(
                        "explicit_content_filter", 2
                    ),
                    "rules_channel_id": str(rules_channel_id),
                    "public_updates_channel_id": str(public_updates_channel_id),
                }

                logs("Sending community update request to Discord API...", "add")

                token = http.token

                await http.request(
                    discord.http.Route(
                        "PATCH",
                        "/guilds/{guild_id}",
                        guild_id=guild_to.id,
                    ),
                    json=community_payload,
                    headers={"Authorization": f"{token}"},
                )

                logs("Community features enabled successfully", "add", True)
                return True
            except discord.Forbidden:
                logs("Missing permissions to enable community features", "error")
            except discord.HTTPException as e:
                logs(f"HTTP error while enabling community features: {e}", "error")
        except Exception as e:
            logs(f"Error enabling community features: {e}", "error")

        return False

    @staticmethod
    async def onboarding_create(guild_to: discord.Guild, guild_from: discord.Guild):
        try:
            community_enabled = await Cloner.enable_community_features(
                guild_to, guild_from
            )
            if not community_enabled:
                return

            http = guild_from._state.http

            try:
                logs("Fetching onboarding data from source guild...", "add")
                onboarding_data = await http.request(
                    discord.http.Route(
                        "GET",
                        "/guilds/{guild_id}/onboarding",
                        guild_id=guild_from.id,
                    )
                )
                logs(f"Fetched onboarding data successfully", "add")
            except Exception as e:
                logs(f"Error fetching onboarding data: {e}", "error")
                return

            if not onboarding_data:
                logs("No onboarding data found in source guild", "warning")
                return

            logs(
                f"Source guild onboarding mode: {onboarding_data.get('mode', 'unknown')}",
                "add",
            )
            logs(
                f"Source guild onboarding enabled: {onboarding_data.get('enabled', False)}",
                "add",
            )

            everyone_role = guild_to.default_role
            logs(f"Found @everyone role (ID: {everyone_role.id})", "add")

            default_channel_ids = []
            valid_default_channels = []
            if (
                "default_channel_ids" in onboarding_data
                and onboarding_data["default_channel_ids"]
            ):
                logs(f"Processing default channels from source guild...", "add")

                for channel_id in onboarding_data["default_channel_ids"]:
                    old_channel = discord.utils.get(
                        guild_from.channels, id=int(channel_id)
                    )
                    if old_channel:
                        new_channel = discord.utils.get(
                            guild_to.channels, name=old_channel.name
                        )
                        if new_channel and isinstance(new_channel, discord.TextChannel):
                            everyone_overwrite = new_channel.overwrites.get(
                                everyone_role
                            )
                            can_read = True

                            if everyone_overwrite:
                                if everyone_overwrite.read_messages is False:
                                    logs(
                                        f"Channel #{new_channel.name} doesn't allow @everyone access, modifying permissions",
                                        "warning",
                                    )

                                    try:
                                        updated_overwrite = discord.PermissionOverwrite(
                                            **everyone_overwrite._values
                                        )
                                        updated_overwrite.read_messages = True
                                        await new_channel.set_permissions(
                                            everyone_role, overwrite=updated_overwrite
                                        )
                                        logs(
                                            f"Modified #{new_channel.name} to allow @everyone access",
                                            "add",
                                        )
                                        can_read = True
                                    except discord.Forbidden:
                                        logs(
                                            f"Missing permissions to modify #{new_channel.name} permissions",
                                            "error",
                                        )
                                    except Exception as e:
                                        logs(
                                            f"Error modifying #{new_channel.name} permissions: {e}",
                                            "error",
                                        )

                            if can_read:
                                valid_default_channels.append(new_channel)
                                default_channel_ids.append(str(new_channel.id))
                                logs(
                                    f"Added #{new_channel.name} as default channel",
                                    "add",
                                )
                            else:
                                logs(
                                    f"Skipping #{new_channel.name} - couldn't enable @everyone access",
                                    "warning",
                                )

                logs(f"Mapped {len(default_channel_ids)} default channels", "add")

                if not default_channel_ids:
                    logs(
                        "No valid default channels found, looking for alternatives...",
                        "warning",
                    )

                    for channel in guild_to.text_channels:
                        if channel.permissions_for(everyone_role).read_messages:
                            logs(
                                f"Found alternative default channel: #{channel.name}",
                                "add",
                            )
                            default_channel_ids.append(str(channel.id))
                            valid_default_channels.append(channel)
                            break

                    if not default_channel_ids:
                        logs(
                            "No accessible channels found, creating a welcome channel",
                            "warning",
                        )
                        try:
                            welcome_channel = await guild_to.create_text_channel(
                                "welcome",
                                reason="Created for onboarding",
                                topic="Welcome to the server!",
                            )
                            default_channel_ids.append(str(welcome_channel.id))
                            valid_default_channels.append(welcome_channel)
                            logs(
                                f"Created new #welcome channel as default channel",
                                "add",
                            )
                        except Exception as e:
                            logs(f"Failed to create welcome channel: {e}", "error")

            prompts = []
            if "prompts" in onboarding_data and onboarding_data["prompts"]:
                for prompt_index, prompt in enumerate(onboarding_data["prompts"]):
                    new_prompt = {
                        "id": prompt.get("id", None),
                        "title": prompt.get("title", ""),
                        "options": [],
                        "single_select": prompt.get("single_select", False),
                        "required": prompt.get("required", False),
                        "in_onboarding": prompt.get("in_onboarding", True),
                        "type": prompt.get("type", 0),
                    }

                    if new_prompt["id"] is None:
                        del new_prompt["id"]

                    for option_index, option in enumerate(prompt.get("options", [])):
                        new_option = {
                            "id": option.get("id", None),
                            "title": option.get("title", ""),
                            "description": option.get("description", ""),
                            "emoji": option.get("emoji", None),
                        }

                        if new_option["id"] is None:
                            del new_option["id"]

                        new_option["role_ids"] = []
                        has_channel_ids = (
                            "channel_ids" in option and option["channel_ids"]
                        )

                        if has_channel_ids:
                            new_option["channel_ids"] = []

                        has_valid_roles = False
                        if "role_ids" in option and option["role_ids"]:
                            for role_id in option["role_ids"]:
                                old_role = discord.utils.get(
                                    guild_from.roles, id=int(role_id)
                                )
                                if old_role:
                                    new_role = discord.utils.get(
                                        guild_to.roles, name=old_role.name
                                    )
                                    if new_role:
                                        new_option["role_ids"].append(str(new_role.id))
                                        has_valid_roles = True

                        has_valid_channels = False
                        if has_channel_ids:
                            for channel_id in option["channel_ids"]:
                                old_channel = discord.utils.get(
                                    guild_from.channels, id=int(channel_id)
                                )
                                if old_channel:
                                    new_channel = discord.utils.get(
                                        guild_to.channels, name=old_channel.name
                                    )
                                    if new_channel:
                                        new_option["channel_ids"].append(
                                            str(new_channel.id)
                                        )
                                        has_valid_channels = True

                        if not has_valid_roles and not has_valid_channels:
                            logs(
                                f"Option '{new_option['title']}' has no roles or channels, adding @everyone",
                                "warning",
                            )
                            new_option["role_ids"].append(str(everyone_role.id))

                        new_prompt["options"].append(new_option)
                        logs(
                            f"Added option '{new_option['title']}' to prompt '{new_prompt['title']}'",
                            "add",
                        )

                    prompts.append(new_prompt)
                logs(
                    f"Mapped {len(prompts)} onboarding prompts with their options",
                    "add",
                )

            payload = {
                "enabled": onboarding_data.get("enabled", False),
                "mode": onboarding_data.get("mode", 0),
            }

            if default_channel_ids:
                payload["default_channel_ids"] = default_channel_ids

            if prompts:
                payload["prompts"] = prompts

            logs(
                f"Prepared payload for destination guild. Sending to Discord API...",
                "add",
            )

            try:
                await http.request(
                    discord.http.Route(
                        "PUT",
                        "/guilds/{guild_id}/onboarding",
                        guild_id=guild_to.id,
                    ),
                    json=payload,
                )
                logs("Onboarding settings cloned successfully", "add", True)
            except discord.HTTPException as e:
                logs(f"HTTP error while cloning onboarding: {e}", "error")
                if e.status == 400:
                    logs(
                        f"API response details: {e.text if hasattr(e, 'text') else str(e)}",
                        "error",
                    )
                    logs(
                        "Discord API rejected our request - attempting simplified payload",
                        "warning",
                    )

                    try:
                        if default_channel_ids:
                            minimal_payload = {
                                "enabled": onboarding_data.get("enabled", False),
                                "mode": onboarding_data.get("mode", 0),
                                "default_channel_ids": default_channel_ids,
                            }

                            await http.request(
                                discord.http.Route(
                                    "PUT",
                                    "/guilds/{guild_id}/onboarding",
                                    guild_id=guild_to.id,
                                ),
                                json=minimal_payload,
                            )
                            logs(
                                "Applied onboarding settings with default channels only",
                                "add",
                                True,
                            )
                            return

                        minimal_payload = {
                            "enabled": onboarding_data.get("enabled", False),
                            "mode": onboarding_data.get("mode", 0),
                        }

                        await http.request(
                            discord.http.Route(
                                "PUT",
                                "/guilds/{guild_id}/onboarding",
                                guild_id=guild_to.id,
                            ),
                            json=minimal_payload,
                        )
                        logs(
                            "Basic onboarding settings applied successfully",
                            "add",
                            True,
                        )
                    except discord.HTTPException as e2:
                        logs(
                            f"Failed to apply even minimal onboarding settings: {e2}",
                            "error",
                        )

                        try:
                            await http.request(
                                discord.http.Route(
                                    "PUT",
                                    "/guilds/{guild_id}/onboarding",
                                    guild_id=guild_to.id,
                                ),
                                json={"enabled": False, "mode": 0},
                            )
                            logs(
                                "Disabled onboarding as fallback since configuration failed",
                                "warning",
                                True,
                            )
                        except:
                            logs(
                                "All attempts to configure onboarding failed",
                                "error",
                                True,
                            )
            except Exception as e:
                logs(f"Unexpected error while cloning onboarding: {e}", "error")
        except Exception as e:
            logs(f"Error in onboarding_create: {e}", "error")

    @staticmethod
    async def check_clone_progress(guild_to: discord.Guild, guild_from: discord.Guild):
        if not guild_to or not guild_from:
            logs("Error: One or both of the guilds could not be found", "error", True)
            return {
                "name_changed": False,
                "channels_exist": False,
                "roles_exist": False,
                "emojis_exist": False,
                "categories_exist": False,
                "community_enabled": False,
                "onboarding_enabled": False,
            }, 0

        clone_state = {
            "name_changed": False,
            "channels_exist": False,
            "roles_exist": False,
            "emojis_exist": False,
            "categories_exist": False,
            "community_enabled": False,
            "onboarding_enabled": False,
        }

        if guild_to.name == guild_from.name:
            clone_state["name_changed"] = True
            logs(f"Server name already matches source server: {guild_from.name}", "add")

        source_roles = [
            role.name for role in guild_from.roles if role.name != "@everyone"
        ]
        target_roles = [
            role.name for role in guild_to.roles if role.name != "@everyone"
        ]

        common_roles = set(source_roles) & set(target_roles)
        if source_roles and common_roles:
            percentage = len(common_roles) / len(source_roles) * 100
            if percentage > 50:
                clone_state["roles_exist"] = True
                logs(
                    f"Found {len(common_roles)} of {len(source_roles)} roles already in target server ({percentage:.1f}%)",
                    "add",
                )
                source_id = str(guild_from.id)
                target_id = str(guild_to.id)
                for role_name in common_roles:
                    ProgressTracker.mark_item("roles", role_name, source_id, target_id)

        source_categories = [category.name for category in guild_from.categories]
        target_categories = [category.name for category in guild_to.categories]

        common_categories = set(source_categories) & set(target_categories)
        if source_categories and common_categories:
            percentage = len(common_categories) / len(source_categories) * 100
            if percentage > 50:
                clone_state["categories_exist"] = True
                logs(
                    f"Found {len(common_categories)} of {len(source_categories)} categories already in target server ({percentage:.1f}%)",
                    "add",
                )
                source_id = str(guild_from.id)
                target_id = str(guild_to.id)
                for category_name in common_categories:
                    ProgressTracker.mark_item(
                        "categories", category_name, source_id, target_id
                    )

        source_channels = [
            channel.name
            for channel in guild_from.text_channels + guild_from.voice_channels
        ]
        target_channels = [
            channel.name for channel in guild_to.text_channels + guild_to.voice_channels
        ]

        common_channels = set(source_channels) & set(target_channels)
        if source_channels and common_channels:
            percentage = len(common_channels) / len(source_channels) * 100
            if percentage > 50:
                clone_state["channels_exist"] = True
                logs(
                    f"Found {len(common_channels)} of {len(source_channels)} channels already in target server ({percentage:.1f}%)",
                    "add",
                )
                source_id = str(guild_from.id)
                target_id = str(guild_to.id)
                for channel_name in common_channels:
                    ProgressTracker.mark_item(
                        "channels", channel_name, source_id, target_id
                    )

        source_emojis = [emoji.name for emoji in guild_from.emojis]
        target_emojis = [emoji.name for emoji in guild_to.emojis]

        common_emojis = set(source_emojis) & set(target_emojis)
        if source_emojis and common_emojis:
            percentage = len(common_emojis) / len(source_emojis) * 100
            if percentage > 30:
                clone_state["emojis_exist"] = True
                logs(
                    f"Found {len(common_emojis)} of {len(source_emojis)} emojis already in target server ({percentage:.1f}%)",
                    "add",
                )

        try:
            http = guild_from._state.http

            guild_data = await http.request(
                discord.http.Route(
                    "GET",
                    "/guilds/{guild_id}?with_counts=true",
                    guild_id=guild_from.id,
                )
            )

            source_features = guild_data.get("features", [])

            target_guild_data = await http.request(
                discord.http.Route(
                    "GET",
                    "/guilds/{guild_id}?with_counts=true",
                    guild_id=guild_to.id,
                )
            )

            target_features = target_guild_data.get("features", [])

            if "COMMUNITY" in source_features and "COMMUNITY" in target_features:
                clone_state["community_enabled"] = True
                logs("Community features already enabled in target server", "add")

                try:
                    onboarding_data = await http.request(
                        discord.http.Route(
                            "GET",
                            "/guilds/{guild_id}/onboarding",
                            guild_id=guild_from.id,
                        )
                    )

                    target_onboarding_data = await http.request(
                        discord.http.Route(
                            "GET",
                            "/guilds/{guild_id}/onboarding",
                            guild_id=guild_to.id,
                        )
                    )

                    if onboarding_data.get("enabled") and target_onboarding_data.get(
                        "enabled"
                    ):
                        clone_state["onboarding_enabled"] = True
                        logs(
                            "Onboarding settings already configured in target server",
                            "add",
                        )
                except Exception as e:
                    logs(f"Error checking onboarding settings: {e}", "error")

        except Exception as e:
            logs(f"Error checking guild features: {e}", "error")

        completed_steps = sum(1 for value in clone_state.values() if value)
        total_steps = len(clone_state)
        progress_percentage = (completed_steps / total_steps) * 100

        logs(
            f"Clone progress assessment: {progress_percentage:.1f}% complete",
            "add",
            True,
        )

        return clone_state, progress_percentage

    @staticmethod
    async def transfer_messages(guild_to: discord.Guild, guild_from: discord.Guild):
        """Transfer recent messages from source to target channels using webhooks"""
        with open("./config.json", "r") as json_file:
            config = json.load(json_file)

        if not config["copy_settings"]["message_history"]:
            Cloner.logs(
                "Message history transfer is disabled in config", "warning", True
            )
            return

        message_limit = config["copy_settings"]["message_history_limit"]
        Cloner.logs(
            f"Starting message history transfer (limit: {message_limit} messages per channel)",
            "add",
            True,
        )

        channel_mapping = {}
        for source_channel in guild_from.text_channels:
            target_channel = discord.utils.get(
                guild_to.text_channels, name=source_channel.name
            )
            if target_channel:
                permissions = source_channel.permissions_for(guild_from.me)
                if (
                    not permissions.read_messages
                    or not permissions.read_message_history
                ):
                    Cloner.logs(
                        f"Skipping #{source_channel.name} - No permission to read message history",
                        "warning",
                    )
                    continue

                channel_mapping[source_channel] = target_channel

        total_channels = len(channel_mapping)
        processed_channels = 0

        for source_channel, target_channel in channel_mapping.items():
            try:
                processed_channels += 1
                Cloner.logs(
                    f"Transferring messages from #{source_channel.name} ({processed_channels}/{total_channels})",
                    "add",
                )

                webhook = await target_channel.create_webhook(name="Message History")

                pinned_message_ids = []
                if config.get("copy_settings", {}).get("clone_pins", True):
                    try:
                        pinned_messages = await source_channel.pins()
                        if pinned_messages:
                            Cloner.logs(
                                f"Cloning {len(pinned_messages)} pinned messages in #{source_channel.name}",
                                "add",
                            )
                            pinned_messages.reverse()

                            for pin_msg in pinned_messages:
                                try:
                                    attachment_links = ""
                                    if pin_msg.attachments:
                                        attachment_links = "\n".join(
                                            [
                                                f"[Attachment: {a.filename}]({a.url})"
                                                for a in pin_msg.attachments
                                            ]
                                        )
                                        if attachment_links:
                                            attachment_links = "\n\n" + attachment_links

                                    content = (
                                        pin_msg.content + attachment_links
                                        if pin_msg.content
                                        else attachment_links
                                    )
                                    if not content and not pin_msg.embeds:
                                        content = "*[No content]*"

                                    embeds_to_send = []
                                    gif_link_domains = [
                                        "tenor.com",
                                        "giphy.com",
                                        "gfycat.com",
                                        "imgur.com",
                                        "discord.gift",
                                        "cdn.discordapp.com",
                                        "media.discordapp.net",
                                    ]
                                    is_gif_link = False

                                    if pin_msg.content and any(
                                        domain in pin_msg.content.lower()
                                        for domain in gif_link_domains
                                    ):
                                        is_gif_link = True
                                    else:
                                        embeds_to_send = pin_msg.embeds

                                    avatar_url = None
                                    if pin_msg.author.avatar:
                                        avatar_url = str(pin_msg.author.avatar.url)

                                    sent_message = await webhook.send(
                                        content=content,
                                        embeds=embeds_to_send,
                                        username=f"{pin_msg.author.display_name}",
                                        avatar_url=avatar_url,
                                        wait=True,
                                    )

                                    await sent_message.pin()
                                    pinned_message_ids.append(pin_msg.id)

                                    await asyncio.sleep(1)

                                except discord.HTTPException as e:
                                    Cloner.logs(
                                        f"Error cloning pinned message: {e}", "warning"
                                    )
                                except Exception as e:
                                    Cloner.logs(
                                        f"Unexpected error cloning pinned message: {e}",
                                        "warning",
                                    )

                    except discord.Forbidden:
                        Cloner.logs(
                            f"No permission to access pins in #{source_channel.name}",
                            "warning",
                        )
                    except Exception as e:
                        Cloner.logs(
                            f"Error fetching pins from #{source_channel.name}: {e}",
                            "warning",
                        )

                messages = []
                try:
                    async for message in source_channel.history(limit=message_limit):
                        if message.id not in pinned_message_ids:
                            messages.append(message)
                except Exception as e:
                    Cloner.logs(
                        f"Error fetching messages from {source_channel.name}: {e}",
                        "error",
                    )
                    continue

                messages.reverse()

                transfer_count = 0
                for message in messages:
                    if message.content or message.embeds or message.attachments:
                        try:
                            attachment_links = ""
                            if message.attachments:
                                attachment_links = "\n".join(
                                    [
                                        f"[Attachment: {a.filename}]({a.url})"
                                        for a in message.attachments
                                    ]
                                )
                                if attachment_links:
                                    attachment_links = "\n\n" + attachment_links

                            content = (
                                message.content + attachment_links
                                if message.content
                                else attachment_links
                            )
                            if not content and not message.embeds:
                                content = "*[No content]*"

                            embeds_to_send = []
                            gif_link_domains = [
                                "tenor.com",
                                "giphy.com",
                                "gfycat.com",
                                "imgur.com",
                                "discord.gift",
                                "cdn.discordapp.com",
                                "media.discordapp.net",
                            ]
                            is_gif_link = False

                            if message.content and any(
                                domain in message.content.lower()
                                for domain in gif_link_domains
                            ):
                                is_gif_link = True
                            else:
                                embeds_to_send = message.embeds

                            avatar_url = None
                            if message.author.avatar:
                                avatar_url = str(message.author.avatar.url)

                            await webhook.send(
                                content=content,
                                embeds=embeds_to_send,
                                username=f"{message.author.display_name}",
                                avatar_url=avatar_url,
                            )
                            transfer_count += 1
                            await asyncio.sleep(0.7)
                        except discord.HTTPException as e:
                            Cloner.logs(
                                f"Error sending message via webhook: {e}", "error"
                            )
                        except Exception as e:
                            Cloner.logs(
                                f"Unexpected error during message transfer: {e}",
                                "error",
                            )

                await webhook.delete()
                Cloner.logs(
                    f"Transferred {transfer_count} messages to #{target_channel.name}",
                    "add",
                )

                await asyncio.sleep(2)

            except discord.Forbidden:
                Cloner.logs(
                    f"Missing permissions to create webhook in #{target_channel.name}",
                    "error",
                )
            except Exception as e:
                Cloner.logs(
                    f"Error transferring messages to #{target_channel.name}: {e}",
                    "error",
                )

        Cloner.logs(
            f"Message history transfer completed for {processed_channels} channels",
            "add",
            True,
        )

    @staticmethod
    async def reset_community_channels(
        guild_to: discord.Guild, guild_from: discord.Guild
    ):
        """Reset community-required channels like rules and announcements to allow deletion"""
        try:
            logs("Checking if target server has community features enabled...", "add")
            http = guild_from._state.http
            token = http.token

            target_guild_data = await http.request(
                discord.http.Route(
                    "GET",
                    "/guilds/{guild_id}?with_counts=true",
                    guild_id=guild_to.id,
                )
            )

            target_features = target_guild_data.get("features", [])
            original_channel_ids = {
                "rules_channel_id": target_guild_data.get("rules_channel_id"),
                "public_updates_channel_id": target_guild_data.get(
                    "public_updates_channel_id"
                ),
                "safety_alerts_channel_id": target_guild_data.get(
                    "safety_alerts_channel_id"
                ),
            }

            if "COMMUNITY" in target_features:
                logs(
                    "Target server has community features. Resetting special channels...",
                    "add",
                )

                original_features = target_guild_data.get("features", [])

                payload = {
                    "features": original_features,
                    "preferred_locale": target_guild_data.get(
                        "preferred_locale", "en-US"
                    ),
                    "rules_channel_id": None,
                    "public_updates_channel_id": None,
                    "safety_alerts_channel_id": None,
                    "description": target_guild_data.get("description", None),
                }

                await http.request(
                    discord.http.Route(
                        "PATCH",
                        "/guilds/{guild_id}",
                        guild_id=guild_to.id,
                    ),
                    json=payload,
                    headers={"Authorization": f"{token}"},
                )

                logs("Reset community special channels successfully", "add")
                return True, original_channel_ids
            else:
                logs(
                    "Target server doesn't have community features, no reset needed",
                    "add",
                )
                return False, original_channel_ids

        except Exception as e:
            logs(f"Error resetting community channels: {e}", "error")
            return False, {}

    @staticmethod
    async def restore_community_channels(
        guild_to: discord.Guild, guild_from: discord.Guild, community_data=None
    ):
        """
        Restore community channels by mapping from source server channels.
        Should be called after all channels are created to ensure proper 1:1 clone.
        """
        try:
            http = guild_from._state.http
            token = http.token

            guild_data = await http.request(
                discord.http.Route(
                    "GET",
                    "/guilds/{guild_id}?with_counts=true",
                    guild_id=guild_from.id,
                )
            )

            features = guild_data.get("features", [])
            is_community = "COMMUNITY" in features
            if not is_community:
                logs(
                    "Source guild doesn't have community features, nothing to restore",
                    "add",
                )
                return False

            target_guild_data = await http.request(
                discord.http.Route(
                    "GET",
                    "/guilds/{guild_id}?with_counts=true",
                    guild_id=guild_to.id,
                )
            )

            target_features = target_guild_data.get("features", [])
            if "COMMUNITY" not in target_features:
                logs("Target server doesn't have community features yet", "warning")
                return False

            rules_channel_id = guild_data.get("rules_channel_id")
            public_updates_channel_id = guild_data.get("public_updates_channel_id")
            safety_alerts_channel_id = guild_data.get("safety_alerts_channel_id")

            source_rules_channel_name = None
            source_updates_channel_name = None
            source_safety_channel_name = None

            if rules_channel_id:
                source_rules_channel = discord.utils.get(
                    guild_from.channels, id=int(rules_channel_id)
                )
                if source_rules_channel:
                    source_rules_channel_name = source_rules_channel.name
                    logs(f"Source rules channel: #{source_rules_channel_name}", "add")

            if public_updates_channel_id:
                source_updates_channel = discord.utils.get(
                    guild_from.channels, id=int(public_updates_channel_id)
                )
                if source_updates_channel:
                    source_updates_channel_name = source_updates_channel.name
                    logs(
                        f"Source announcements channel: #{source_updates_channel_name}",
                        "add",
                    )

            if safety_alerts_channel_id:
                source_safety_channel = discord.utils.get(
                    guild_from.channels, id=int(safety_alerts_channel_id)
                )
                if source_safety_channel:
                    source_safety_channel_name = source_safety_channel.name
                    logs(
                        f"Source safety alerts channel: #{source_safety_channel_name}",
                        "add",
                    )

            new_rules_channel_id = None
            new_updates_channel_id = None
            new_safety_channel_id = None

            if source_rules_channel_name:
                target_rules_channel = discord.utils.get(
                    guild_to.text_channels, name=source_rules_channel_name
                )
                if target_rules_channel:
                    new_rules_channel_id = str(target_rules_channel.id)
                    logs(
                        f"Found matching rules channel in target: #{target_rules_channel.name}",
                        "add",
                    )

            if source_updates_channel_name:
                target_updates_channel = discord.utils.get(
                    guild_to.text_channels, name=source_updates_channel_name
                )
                if target_updates_channel:
                    new_updates_channel_id = str(target_updates_channel.id)
                    logs(
                        f"Found matching announcements channel in target: #{target_updates_channel.name}",
                        "add",
                    )

            if source_safety_channel_name:
                target_safety_channel = discord.utils.get(
                    guild_to.text_channels, name=source_safety_channel_name
                )
                if target_safety_channel:
                    new_safety_channel_id = str(target_safety_channel.id)
                    logs(
                        f"Found matching safety alerts channel in target: #{target_safety_channel.name}",
                        "add",
                    )

            current_rules_channel_id = target_guild_data.get("rules_channel_id")
            current_updates_channel_id = target_guild_data.get(
                "public_updates_channel_id"
            )
            current_safety_channel_id = target_guild_data.get(
                "safety_alerts_channel_id"
            )

            default_rules_channel = None
            default_announcements_channel = None

            if current_rules_channel_id:
                default_rules_channel = discord.utils.get(
                    guild_to.text_channels, id=int(current_rules_channel_id)
                )

            if current_updates_channel_id:
                default_announcements_channel = discord.utils.get(
                    guild_to.text_channels, id=int(current_updates_channel_id)
                )

            if not new_rules_channel_id:
                if source_rules_channel_name:
                    rules_channel = await guild_to.create_text_channel(
                        source_rules_channel_name
                    )
                else:
                    rules_channel = await guild_to.create_text_channel("rules")
                new_rules_channel_id = str(rules_channel.id)
                logs(f"Created new rules channel: #{rules_channel.name}", "add")

            if not new_updates_channel_id:
                if source_updates_channel_name:
                    updates_channel = await guild_to.create_text_channel(
                        source_updates_channel_name
                    )
                else:
                    updates_channel = await guild_to.create_text_channel(
                        "announcements"
                    )
                new_updates_channel_id = str(updates_channel.id)
                logs(
                    f"Created new announcements channel: #{updates_channel.name}", "add"
                )

            community_payload = {
                "features": target_features,
                "rules_channel_id": new_rules_channel_id,
                "public_updates_channel_id": new_updates_channel_id,
                "preferred_locale": target_guild_data.get(
                    "preferred_locale", guild_data.get("preferred_locale", "en-US")
                ),
                "description": target_guild_data.get(
                    "description", guild_data.get("description", None)
                ),
            }

            if new_safety_channel_id:
                community_payload["safety_alerts_channel_id"] = new_safety_channel_id

            logs("Updating community channel mappings to match source server...", "add")

            await http.request(
                discord.http.Route(
                    "PATCH",
                    "/guilds/{guild_id}",
                    guild_id=guild_to.id,
                ),
                json=community_payload,
                headers={"Authorization": f"{token}"},
            )

            logs(
                "Successfully restored community channels to match source server", "add"
            )

            if (
                default_rules_channel
                and str(default_rules_channel.id) != new_rules_channel_id
            ):
                if (
                    default_rules_channel.name.lower() == "rules"
                    and source_rules_channel_name.lower() != "rules"
                ):
                    try:
                        await default_rules_channel.delete()
                        logs(
                            f"Deleted default rules channel that was created during community setup",
                            "delete",
                        )
                    except Exception as e:
                        logs(f"Error deleting default rules channel: {e}", "error")

            if (
                default_announcements_channel
                and str(default_announcements_channel.id) != new_updates_channel_id
            ):
                if (
                    default_announcements_channel.name.lower() == "announcements"
                    and source_updates_channel_name.lower() != "announcements"
                ):
                    try:
                        await default_announcements_channel.delete()
                        logs(
                            f"Deleted default announcements channel that was created during community setup",
                            "delete",
                        )
                    except Exception as e:
                        logs(
                            f"Error deleting default announcements channel: {e}",
                            "error",
                        )

            return True

        except Exception as e:
            logs(f"Error restoring community channels: {e}", "error")
            return False

    @staticmethod
    async def soundboard_sounds_create(
        guild_to: discord.Guild, guild_from: discord.Guild
    ):
        step = "soundboard_sounds"
        if ProgressTracker.is_step_done(step):
            logs("Soundboard sounds step already completed, skipping.", "add")
            return

        try:
            http = guild_from._state.http

            logs("Fetching soundboard sounds from source server...", "add")
            try:
                sounds_data = await http.request(
                    discord.http.Route(
                        "GET",
                        "/guilds/{guild_id}/soundboard-sounds",
                        guild_id=guild_from.id,
                    )
                )

                if isinstance(sounds_data, dict):
                    sounds_list = sounds_data.get("items", [])
                else:
                    sounds_list = sounds_data if sounds_data else []

                if not sounds_list:
                    logs("No soundboard sounds found in source server", "add")
                    ProgressTracker.mark_step_done(step)
                    return

                logs(f"Found {len(sounds_list)} soundboard sounds to clone", "add")

                sounds_created = 0
                for sound in sounds_list:
                    if isinstance(sound, str):
                        continue

                    sound_name = (
                        sound.get("name", "") if isinstance(sound, dict) else ""
                    )
                    if ProgressTracker.is_item_done(step, sound_name):
                        continue

                    try:
                        sound_id = (
                            sound.get("sound_id") if isinstance(sound, dict) else None
                        )
                        volume = (
                            sound.get("volume", 1.0) if isinstance(sound, dict) else 1.0
                        )
                        emoji_id = (
                            sound.get("emoji_id") if isinstance(sound, dict) else None
                        )
                        emoji_name = (
                            sound.get("emoji_name", "")
                            if isinstance(sound, dict)
                            else ""
                        )

                        try:
                            target_sounds_data = await http.request(
                                discord.http.Route(
                                    "GET",
                                    "/guilds/{guild_id}/soundboard-sounds",
                                    guild_id=guild_to.id,
                                )
                            )

                            if isinstance(target_sounds_data, dict):
                                target_sounds = target_sounds_data.get("items", [])
                            else:
                                target_sounds = (
                                    target_sounds_data if target_sounds_data else []
                                )

                            if any(
                                s.get("name") == sound_name
                                for s in target_sounds
                                if isinstance(s, dict)
                            ):
                                logs(
                                    f"Sound '{sound_name}' already exists in target server, skipping",
                                    "warning",
                                )
                                ProgressTracker.mark_item(step, sound_name)
                                continue
                        except:
                            pass

                        import aiohttp
                        import io

                        sound_url = sound.get("sound") or sound.get("url")
                        if not sound_url and sound_id:
                            sound_url = f"https://cdn.discordapp.com/soundboard-sounds/{sound_id}"

                        if not sound_url:
                            logs(
                                f"No sound URL found for {sound_name}, skipping",
                                "warning",
                            )
                            continue

                        async with aiohttp.ClientSession() as session:
                            async with session.get(sound_url) as response:
                                if response.status == 200:
                                    sound_bytes = await response.read()

                                    try:
                                        import base64

                                        sound_base64 = base64.b64encode(
                                            sound_bytes
                                        ).decode("utf-8")

                                        payload = {
                                            "name": sound_name,
                                            "sound": f"data:audio/ogg;base64,{sound_base64}",
                                            "volume": volume,
                                        }

                                        if emoji_id:
                                            payload["emoji_id"] = str(emoji_id)
                                        if emoji_name:
                                            payload["emoji_name"] = emoji_name

                                        async with session.post(
                                            f"https://discord.com/api/v10/guilds/{guild_to.id}/soundboard-sounds",
                                            json=payload,
                                            headers={
                                                "Authorization": guild_to._state.http.token,
                                                "Content-Type": "application/json",
                                            },
                                        ) as resp:
                                            if resp.status in (200, 201):
                                                logs(
                                                    f"Created soundboard sound: {sound_name}",
                                                    "add",
                                                )
                                                ProgressTracker.mark_item(
                                                    step, sound_name
                                                )
                                                sounds_created += 1
                                            elif resp.status == 403:
                                                logs(
                                                    f"Missing permissions to create soundboard sound: {sound_name}",
                                                    "error",
                                                )
                                            else:
                                                error_text = await resp.text()
                                                logs(
                                                    f"HTTP error creating soundboard sound {sound_name}: {resp.status} - {error_text}",
                                                    "error",
                                                )
                                    except Exception as e:
                                        logs(
                                            f"Error uploading soundboard sound {sound_name}: {e}",
                                            "error",
                                        )
                                else:
                                    logs(
                                        f"Failed to download sound file for {sound_name} (Status: {response.status})",
                                        "error",
                                    )
                    except Exception as e:
                        logs(
                            f"Error creating sound '{sound.get('name', 'unknown')}': {e}",
                            "error",
                        )

                logs(f"Created {sounds_created} soundboard sounds", "add", True)

            except discord.Forbidden:
                logs("Missing permissions to access soundboard sounds", "error")
            except discord.HTTPException as e:
                logs(f"HTTP error accessing soundboard sounds: {e}", "error")
            except Exception as e:
                logs(f"Unexpected error during soundboard sounds cloning: {e}", "error")

        except Exception as e:
            logs(f"Error checking guild features for soundboard: {e}", "error")

        ProgressTracker.mark_step_done(step)

    @staticmethod
    async def stickers_create(guild_to: discord.Guild, guild_from: discord.Guild):
        step = "stickers"
        if ProgressTracker.is_step_done(step):
            logs("Stickers step already completed, skipping.", "add")
            return

        try:
            logs("Fetching stickers from source server...", "add")
            stickers = await guild_from.fetch_stickers()

            if not stickers:
                logs("No stickers found in source server", "add")
                ProgressTracker.mark_step_done(step)
                return

            logs(f"Found {len(stickers)} stickers to clone", "add")

            sticker_limits = {0: 5, 1: 15, 2: 30, 3: 60}
            to_boost_level = guild_to.premium_tier
            sticker_limit = sticker_limits.get(to_boost_level, 5)

            if len(stickers) > sticker_limit:
                logs(
                    f"Warning: Destination server can only have {sticker_limit} stickers (boost level {to_boost_level})",
                    "warning",
                )
                logs(f"Will only clone the first {sticker_limit} stickers", "warning")
                stickers = stickers[:sticker_limit]

            existing_stickers = await guild_to.fetch_stickers()
            existing_sticker_names = [s.name for s in existing_stickers]

            stickers_created = 0
            for sticker in stickers:
                if ProgressTracker.is_item_done(step, sticker.name):
                    continue

                if sticker.name in existing_sticker_names:
                    logs(
                        f"Sticker '{sticker.name}' already exists in target server, skipping",
                        "warning",
                    )
                    ProgressTracker.mark_item(step, sticker.name)
                    continue

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(sticker.url) as response:
                            if response.status == 200:
                                sticker_bytes = await response.read()

                                format_types = {
                                    1: "png",
                                    2: "apng",
                                    3: "lottie",
                                }

                                file_format = format_types.get(
                                    getattr(sticker, "format_type", 1), "png"
                                )

                                file = discord.File(
                                    fp=io.BytesIO(sticker_bytes),
                                    filename=f"sticker.{file_format}",
                                )

                                await guild_to.create_sticker(
                                    name=sticker.name,
                                    description=sticker.description or "Cloned sticker",
                                    emoji=sticker.emoji or "👍",
                                    file=file,
                                    reason="Server clone",
                                )

                                logs(f"Created sticker: {sticker.name}", "add")
                                ProgressTracker.mark_item(step, sticker.name)
                                stickers_created += 1

                                await asyncio.sleep(1.5)
                            else:
                                logs(
                                    f"Failed to download sticker {sticker.name} (Status: {response.status})",
                                    "error",
                                )
                except discord.Forbidden:
                    logs(
                        f"Missing permissions to create sticker: {sticker.name}",
                        "error",
                    )
                except discord.HTTPException as e:
                    logs(f"HTTP error creating sticker {sticker.name}: {e}", "error")
                except Exception as e:
                    logs(f"Error creating sticker {sticker.name}: {e}", "error")

            logs(f"Created {stickers_created} stickers", "add", True)

        except Exception as e:
            logs(f"Error in stickers_create: {e}", "error")

        ProgressTracker.mark_step_done(step)

    @staticmethod
    async def forum_channels_create(guild_to: discord.Guild, guild_from: discord.Guild):
        step = "forum_channels"
        if ProgressTracker.is_step_done(step):
            logs("Forum channels step already completed, skipping.", "add")
            return

        forum_channels = [
            channel
            for channel in guild_from.channels
            if isinstance(channel, discord.ForumChannel)
        ]

        if not forum_channels:
            logs("No forum channels found in source server", "add", True)
            ProgressTracker.mark_step_done(step)
            return

        logs(f"Found {len(forum_channels)} forum channels to clone", "add")

        forums_created = 0
        for forum in forum_channels:
            if ProgressTracker.is_item_done(step, forum.name):
                continue

            try:
                category = discord.utils.get(
                    guild_to.categories, name=getattr(forum.category, "name", None)
                )

                overwrites_to = {}
                for key, value in forum.overwrites.items():
                    if isinstance(key, discord.Role):
                        role = discord.utils.get(guild_to.roles, name=key.name)
                        if role:
                            overwrites_to[role] = value
                    elif hasattr(key, "name") and hasattr(key, "id"):
                        try:
                            if hasattr(key, "bot") and key.bot:
                                found_obj = discord.utils.get(
                                    guild_to.members, bot=True, name=key.name
                                )
                            else:
                                found_obj = discord.utils.get(
                                    guild_to.members, name=key.name
                                )
                            if found_obj:
                                overwrites_to[found_obj] = value
                        except:
                            logs(
                                f"Skipping overwrite for {getattr(key, 'name', 'Unknown object')}",
                                "warning",
                            )

                try:
                    tags = []
                    for tag in forum.available_tags:
                        emoji = tag.emoji
                        if isinstance(emoji, discord.Emoji):
                            target_emoji = discord.utils.get(
                                guild_to.emojis, name=emoji.name
                            )
                            emoji = target_emoji if target_emoji else "🔖"

                        tags.append(
                            discord.ForumTag(
                                name=tag.name, emoji=emoji, moderated=tag.moderated
                            )
                        )
                except Exception as e:
                    logs(
                        f"Error processing forum tags for {forum.name}: {e}", "warning"
                    )
                    tags = []

                new_forum = await guild_to.create_forum(
                    name=forum.name,
                    category=category,
                    overwrites=overwrites_to,
                    topic=forum.topic,
                    slowmode_delay=forum.slowmode_delay,
                    nsfw=forum.nsfw,
                    reason="Server clone",
                )

                try:
                    edit_kwargs = {
                        "position": forum.position,
                        "default_auto_archive_duration": forum.default_auto_archive_duration,
                        "default_reaction_emoji": forum.default_reaction_emoji,
                    }

                    if (
                        hasattr(forum, "default_thread_slowmode_delay")
                        and forum.default_thread_slowmode_delay is not None
                    ):
                        edit_kwargs["default_thread_slowmode_delay"] = (
                            forum.default_thread_slowmode_delay
                        )

                    if (
                        hasattr(forum, "default_sort_order")
                        and forum.default_sort_order is not None
                    ):
                        edit_kwargs["default_sort_order"] = forum.default_sort_order

                    if len(tags) > 0:
                        edit_kwargs["available_tags"] = tags

                    if hasattr(forum, "guidelines") and forum.guidelines:
                        edit_kwargs["guidelines"] = forum.guidelines

                    await new_forum.edit(**edit_kwargs)
                    logs(
                        f"Applied all forum settings for {forum.name} in a single request",
                        "add",
                    )
                except Exception as e:
                    logs(
                        f"Error applying forum settings for {forum.name}: {e}",
                        "warning",
                    )

                    try:
                        if (
                            hasattr(forum, "default_sort_order")
                            and forum.default_sort_order is not None
                        ):
                            await new_forum.edit(
                                default_sort_order=forum.default_sort_order
                            )
                    except Exception as e:
                        logs(f"Error setting default sort order: {e}", "warning")

                    try:
                        if len(tags) > 0:
                            await new_forum.edit(available_tags=tags)
                    except Exception as e:
                        logs(f"Error setting available tags: {e}", "warning")

                logs(f"Created forum channel: {forum.name}", "add")
                ProgressTracker.mark_item(step, forum.name)
                forums_created += 1

            except discord.Forbidden:
                logs(
                    f"Missing permissions to create forum channel: {forum.name}",
                    "error",
                )
            except discord.HTTPException as e:
                logs(f"HTTP error creating forum channel {forum.name}: {e}", "error")
            except Exception as e:
                logs(f"Error creating forum channel {forum.name}: {e}", "error")

        logs(f"Created {forums_created} forum channels", "add", True)
        ProgressTracker.mark_step_done(step)

    @staticmethod
    async def scheduled_events_create(
        guild_to: discord.Guild, guild_from: discord.Guild
    ):
        step = "scheduled_events"
        if ProgressTracker.is_step_done(step):
            logs("Scheduled events step already completed, skipping.", "add")
            return

        try:
            http = guild_from._state.http

            events_data = await http.request(
                discord.http.Route(
                    "GET", "/guilds/{guild_id}/scheduled-events", guild_id=guild_from.id
                )
            )

            if not events_data:
                logs("No scheduled events found in source server", "add")
                ProgressTracker.mark_step_done(step)
                return

            logs(f"Found {len(events_data)} scheduled events to clone", "add")

            target_events_data = await http.request(
                discord.http.Route(
                    "GET", "/guilds/{guild_id}/scheduled-events", guild_id=guild_to.id
                )
            )
            target_event_names = [event.get("name") for event in target_events_data]

            events_created = 0
            for event in events_data:
                event_name = event.get("name", "")
                if ProgressTracker.is_item_done(step, event_name):
                    continue

                if event_name in target_event_names:
                    logs(
                        f"Event '{event_name}' already exists in target server, skipping",
                        "warning",
                    )
                    ProgressTracker.mark_item(step, event_name)
                    continue

                try:
                    new_event = {
                        "name": event_name,
                        "description": event.get("description", ""),
                        "scheduled_start_time": event.get("scheduled_start_time"),
                        "scheduled_end_time": event.get("scheduled_end_time"),
                        "privacy_level": event.get("privacy_level", 2),
                        "entity_type": event.get("entity_type", 3),
                    }

                    entity_type = event.get("entity_type", 0)

                    if entity_type == 1:
                        source_channel_id = event.get("channel_id")
                        if source_channel_id:
                            source_channel = discord.utils.get(
                                guild_from.channels, id=int(source_channel_id)
                            )
                            if source_channel:
                                target_channel = discord.utils.get(
                                    guild_to.channels, name=source_channel.name
                                )
                                if target_channel:
                                    new_event["channel_id"] = str(target_channel.id)
                                    new_event["entity_type"] = 1

                    elif entity_type == 2:
                        source_channel_id = event.get("channel_id")
                        if source_channel_id:
                            source_channel = discord.utils.get(
                                guild_from.channels, id=int(source_channel_id)
                            )
                            if source_channel:
                                target_channel = discord.utils.get(
                                    guild_to.voice_channels, name=source_channel.name
                                )
                                if target_channel:
                                    new_event["channel_id"] = str(target_channel.id)
                                    new_event["entity_type"] = 2

                    elif entity_type == 3:
                        if "entity_metadata" in event and event["entity_metadata"]:
                            new_event["entity_metadata"] = {}
                            if "location" in event["entity_metadata"]:
                                new_event["entity_metadata"]["location"] = event[
                                    "entity_metadata"
                                ]["location"]

                    image_data = None
                    if event.get("image"):
                        try:
                            image_url = f"https://cdn.discordapp.com/guild-events/{event['id']}/{event['image']}.png"
                            async with aiohttp.ClientSession() as session:
                                async with session.get(image_url) as response:
                                    if response.status == 200:
                                        image_data = await response.read()
                                        image_base64 = base64.b64encode(
                                            image_data
                                        ).decode("ascii")
                                        new_event["image"] = (
                                            f"data:image/png;base64,{image_base64}"
                                        )
                        except Exception as e:
                            logs(
                                f"Error downloading event image for {event_name}: {e}",
                                "warning",
                            )

                    await http.request(
                        discord.http.Route(
                            "POST",
                            "/guilds/{guild_id}/scheduled-events",
                            guild_id=guild_to.id,
                        ),
                        json=new_event,
                    )

                    logs(f"Created scheduled event: {event_name}", "add")
                    ProgressTracker.mark_item(step, event_name)
                    events_created += 1

                except discord.Forbidden:
                    logs(
                        f"Missing permissions to create scheduled event: {event_name}",
                        "error",
                    )
                except discord.HTTPException as e:
                    logs(
                        f"HTTP error creating scheduled event {event_name}: {e}",
                        "error",
                    )
                except Exception as e:
                    logs(f"Error creating scheduled event {event_name}: {e}", "error")

            logs(f"Created {events_created} scheduled events", "add", True)

        except discord.Forbidden:
            logs("Missing permissions to access scheduled events", "error")
        except discord.HTTPException as e:
            logs(f"HTTP error accessing scheduled events: {e}", "error")
        except Exception as e:
            logs(f"Error in scheduled_events_create: {e}", "error")

        ProgressTracker.mark_step_done(step)

    @staticmethod
    async def bans_transfer(guild_to: discord.Guild, guild_from: discord.Guild):
        """Transfer bans from source server to destination server"""
        step = "bans"
        if ProgressTracker.is_step_done(step):
            Cloner.logs("Bans step already completed, skipping.", "add")
            return

        try:
            Cloner.logs("Fetching bans from source server...", "add")

            source_bans = []
            try:
                async for ban_entry in guild_from.bans(limit=None):
                    source_bans.append(ban_entry)
            except discord.Forbidden:
                Cloner.logs(
                    "Missing permissions to view bans in source server",
                    "error",
                )
                ProgressTracker.mark_step_done(step)
                return
            except Exception as e:
                Cloner.logs(f"Error fetching bans from source server: {e}", "error")
                ProgressTracker.mark_step_done(step)
                return

            if not source_bans:
                Cloner.logs("No bans found in source server", "add")
                ProgressTracker.mark_step_done(step)
                return

            Cloner.logs(f"Found {len(source_bans)} bans to transfer", "add")

            existing_ban_ids = set()
            try:
                async for ban_entry in guild_to.bans(limit=None):
                    existing_ban_ids.add(ban_entry.user.id)
            except discord.Forbidden:
                Cloner.logs(
                    "Missing permissions to view bans in destination server",
                    "warning",
                )
            except Exception as e:
                Cloner.logs(
                    f"Error fetching existing bans from destination server: {e}",
                    "warning",
                )

            bans_transferred = 0
            for ban_entry in source_bans:
                user_id = str(ban_entry.user.id)

                if ProgressTracker.is_item_done(step, user_id):
                    continue

                if ban_entry.user.id in existing_ban_ids:
                    Cloner.logs(
                        f"User {ban_entry.user} is already banned in destination server, skipping",
                        "warning",
                    )
                    ProgressTracker.mark_item(step, user_id)
                    continue

                try:
                    reason = ban_entry.reason or "Transferred from source server"
                    await guild_to.ban(
                        ban_entry.user,
                        reason=reason,
                        delete_message_days=0,
                    )

                    Cloner.logs(
                        f"Banned user {ban_entry.user} ({ban_entry.user.id})",
                        "add",
                    )
                    ProgressTracker.mark_item(step, user_id)
                    bans_transferred += 1

                    await asyncio.sleep(0.5)

                except discord.Forbidden:
                    Cloner.logs(
                        f"Missing permissions to ban user {ban_entry.user}",
                        "error",
                    )
                except discord.HTTPException as e:
                    Cloner.logs(
                        f"Error banning user {ban_entry.user}: {e}",
                        "error",
                    )
                except Exception as e:
                    Cloner.logs(
                        f"Unexpected error banning user {ban_entry.user}: {e}",
                        "error",
                    )

            Cloner.logs(f"Transferred {bans_transferred} bans", "add", True)

        except Exception as e:
            Cloner.logs(f"Error in bans_transfer: {e}", "error")

        ProgressTracker.mark_step_done(step)

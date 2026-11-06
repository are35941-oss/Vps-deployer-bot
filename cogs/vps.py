import asyncio
import logging
import os
import secrets
import string
from datetime import datetime, timezone
from pathlib import Path

import discord
import docker
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("vpsbot.provisioning")
OWNER_ID = 1320732831424450561
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES = {"ubuntu": "ubuntu:24.04", "debian": "debian:12"}


def provision(os_name: str, ram_mb: int, cpu: int):
    client = docker.from_env(timeout=120)
    container = None
    password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    name = "vps-" + secrets.token_hex(6)
    try:
        image, _ = client.images.build(
            path=str(PROJECT_ROOT), dockerfile="Dockerfile.vps",
            tag=f"kodari-vps-{os_name}:latest", buildargs={"BASE_IMAGE": IMAGES[os_name]}, rm=True,
        )
        container = client.containers.run(
            image.id, detach=True, name=name, hostname=name,
            mem_limit=f"{ram_mb}m", nano_cpus=cpu * 1_000_000_000,
            pids_limit=512, ports={"22/tcp": None}, restart_policy={"Name": "unless-stopped"},
            labels={"managed-by": "discord-vps-bot", "discord-owner": str(OWNER_ID)},
        )
        result = container.exec_run(
            ["sh", "-c", 'printf "root:%s\\n" "$1" | chpasswd', "sh", password]
        )
        if result.exit_code != 0:
            raise RuntimeError("Could not set the container password")
        container.reload()
        ports = container.attrs["NetworkSettings"]["Ports"].get("22/tcp")
        if not ports:
            raise RuntimeError("Docker did not assign an SSH port")
        return name, ports[0]["HostPort"], password
    except Exception:
        if container is not None:
            try:
                container.remove(force=True)
            except docker.errors.DockerException:
                logger.exception("Could not remove failed container %s", name)
        raise
    finally:
        client.close()


class VPS(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.provision_lock = asyncio.Lock()

    @app_commands.command(name="create-vps", description="Provision an SSH-enabled Docker server")
    @app_commands.describe(os="Linux distribution", ram="RAM in MiB", cpu="Number of CPU cores")
    @app_commands.choices(os=[
        app_commands.Choice(name="Ubuntu 24.04", value="ubuntu"),
        app_commands.Choice(name="Debian 12", value="debian"),
    ])
    async def create_vps(
        self, interaction: discord.Interaction,
        os: app_commands.Choice[str],
        ram: app_commands.Range[int, 512, 16384] = 1024,
        cpu: app_commands.Range[int, 1, 8] = 1,
    ):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                embed=discord.Embed(description="Access Denied: You are not authorized to create servers.", color=discord.Color.red()),
                ephemeral=True,
            )
            return
        host = os_module_host()
        if not host:
            await interaction.response.send_message(
                embed=discord.Embed(title="Configuration error", description="Set VPS_PUBLIC_HOST to the Docker host's reachable IP or hostname.", color=discord.Color.red()),
                ephemeral=True,
            )
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            async with self.provision_lock:
                name, port, password = await asyncio.to_thread(provision, os.value, ram, cpu)
        except (docker.errors.DockerException, OSError, RuntimeError):
            logger.exception("Provisioning failed")
            await interaction.followup.send(embed=discord.Embed(title="Provisioning failed", description="Check the bot logs and Docker daemon access.", color=discord.Color.red()), ephemeral=True)
            return
        embed = discord.Embed(title="Server created", description="These credentials are private. Save them now; the password is not stored by the bot.", color=discord.Color.green(), timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Server", value=name, inline=False)
        embed.add_field(name="Host", value=host, inline=True)
        embed.add_field(name="SSH port", value=port, inline=True)
        embed.add_field(name="Username", value="root", inline=True)
        embed.add_field(name="Password", value=f"`{password}`", inline=False)
        embed.add_field(name="Resources", value=f"{os.name} · {ram} MiB RAM · {cpu} CPU", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)


def os_module_host():
    return os.getenv("VPS_PUBLIC_HOST", "").strip()


async def setup(bot: commands.Bot):
    await bot.add_cog(VPS(bot))
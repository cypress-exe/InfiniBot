from nextcord import Interaction
import nextcord
import logging
import os
from datetime import datetime

from config.global_settings import get_configs

async def run_bot_about_command(interaction: Interaction) -> None:
    """
    |coro|
    
    Runs the bot about command to display version, repository, and documentation links.
    
    :param interaction: The interaction object
    :type interaction: nextcord.Interaction
    :return: None
    :rtype: None
    """
    
    # Get the absolute path to the project root
    # Go up from src/features/bot_info.py to the project root
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    
    # Read from build_info file
    build_info_path = os.path.join(project_root, 'generated', 'build_info')
    
    if os.path.exists(build_info_path):
        try:
            build_info = {}
            with open(build_info_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        build_info[key] = value
            
            # Extract information from build_info
            full_commit = build_info.get('GIT_COMMIT', 'unknown')
            commit_hash = full_commit[:8] if full_commit != 'unknown' else 'unknown'
            
            # Convert build timestamp to Discord epoch format
            build_timestamp_str = build_info.get('BUILD_TIMESTAMP', 'unknown')
            if build_timestamp_str != 'unknown':
                try:
                    # Parse ISO format timestamp and convert to epoch
                    dt = datetime.fromisoformat(build_timestamp_str.replace('Z', '+00:00'))
                    epoch_time = int(dt.timestamp())
                    commit_message = f"Built: <t:{epoch_time}:F> (<t:{epoch_time}:R>)"
                except ValueError:
                    commit_message = f"Build timestamp: {build_timestamp_str}"
            else:
                commit_message = "Build timestamp: unknown"
            
            repo_url = build_info.get('GIT_REMOTE', 'https://github.com/cypress-exe/InfiniBot')
            
            # Clean up the repository URL (remove .git if present and convert SSH to HTTPS)
            if repo_url.startswith('git@github.com:'):
                repo_url = repo_url.replace('git@github.com:', 'https://github.com/')
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]

            build_flags = build_info.get('BUILD_FLAGS', 'null')
            if build_flags == 'null' or build_flags == '':
                build_flags = "None"
                
            logging.info("Successfully loaded git information from build_info file")
            
        except Exception as e:
            logging.error(f"Error reading build_info file: {e}")
            # Fallback if build_info reading fails
            commit_hash = "Unknown"
            commit_message = "Unable to retrieve build info"
            repo_url = "https://github.com/cypress-exe/InfiniBot"
            build_flags = "unknown"
    else:
        logging.warning(f"build_info file not found at: {build_info_path}")
        # Fallback if build_info file doesn't exist
        commit_hash = "Unknown"
        commit_message = "Build info not available"
        repo_url = "https://github.com/cypress-exe/InfiniBot"
        build_flags = "unknown"
    
    # Create the embed
    embed = nextcord.Embed(
        title="<:infiniboticon:1379549397708312677>  InfiniBot Information",
        description="A powerful, multipurpose Discord bot for server management and engagement.",
        color=nextcord.Color.blurple()
    )
    
    # Add version information
    embed.add_field(
        name="📋  Version Information",
        value=f"**Commit:** `{commit_hash}`\n**Latest Change:** {commit_message}",
        inline=False
    )
    
    # Add repository information
    embed.add_field(
        name="🔗  Repository",
        value=f"[GitHub Repository]({repo_url})\n[View Latest Commit]({repo_url}/commit/{commit_hash})",
        inline=False
    )

    # Add build flags
    embed.add_field(
        name="⚙️  Build Flags",
        value=f"`{build_flags}`",
        inline=False
    )
    
    # Add documentation links
    embed.add_field(
        name="📚 Documentation & Support",
        value=(
            "[📖 Full Documentation](https://cypress-exe.github.io/InfiniBot/)\n"
            "[🚀 Getting Started](https://cypress-exe.github.io/InfiniBot/docs/getting-started/)\n"
            f"[💬 Support Server]({get_configs()["links.support-server-invite-link"]})\n"
            "[🐛 Report Issues](https://github.com/cypress-exe/InfiniBot/issues)"
        ),
        inline=False
    )
    
    # Add footer
    embed.set_footer(
        text="InfiniBot is open source and community-driven."
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

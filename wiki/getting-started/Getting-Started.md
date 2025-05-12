# Getting Started with InfiniBot

This guide helps you get started with using InfiniBot in your Discord server.

## Adding InfiniBot to Your Server

1. Use the official invitation link to add InfiniBot to your server.
2. Make sure to grant InfiniBot the **Administrator** permission for simplest setup. Alternatively, you can grant individual permissions as listed in the [Required Permissions](#required-permissions) section below.
3. Once invited, InfiniBot will be ready to use with default settings.

## Onboarding Process

When InfiniBot first joins your server, it will guide you through an onboarding process:

1. You'll be prompted to set up essential features based on your server's needs
2. Each feature (like moderation, logging, leveling) can be enabled/disabled during this process
3. The onboarding will help you configure channels and permissions for your selected features

If you skip the onboarding or want to change settings later, you can always configure everything through the Dashboard.

## The InfiniBot Mod Role

The **InfiniBot Mod** role is central to controlling who can manage the bot:

1. InfiniBot will attempt to create this role automatically.
2. If the role wasn't created automatically, use `/create infinibot-mod-role` to manually create it.
3. Assign this role to yourself and trusted administrators to unlock full access to InfiniBot's features.

## Using the Dashboard

The dashboard is your central hub for configuring InfiniBot:

1. Use `/dashboard` to open the interactive configuration panel.
2. From here, you can access all major features and their settings.
3. Click on the feature buttons to navigate to specific settings.

## Next Steps

After completing the initial setup, explore these features:

- [Moderation Features](../core-features/Moderation.md) - Set up profanity filtering and spam control
- [Leveling](../core-features/Leveling.md) - Configure the member leveling system
- [Join & Leave Messages](../messaging/Join-Leave-Messages.md) - Set custom messages for when members join or leave

For a complete list of commands, see the [Commands Overview](Commands.md).

## Required Permissions

For optimal functionality, we recommend giving InfiniBot the **Administrator** permission, which simplifies setup considerably.

If you prefer to use more specific permissions, InfiniBot needs these permissions in every channel it operates in:

- **View Channels** - To see and interact with channels
- **Send Messages** - To respond to commands and post notifications
- **Manage Roles** - For role assignment features
- **Manage Messages** - For moderation features
- **Embed Links** - To send formatted embeds
- **Attach Files** - To upload files when needed
- **Manage Nicknames** - For nickname moderation
- **View Audit Log** - For accurate action logging
- **Timeout Members** - For moderation actions
- **Ban Members** - For ban button functionality
- **Read Message History** - For reaction roles and other features

If you encounter permission errors, InfiniBot will notify you about the specific permissions needed.
To check if InfiniBot has the correct permissions, run `/check_infinibot_permissions`.

---

**Related Pages:**
- [Configuration](Configuration.md) - More detailed configuration options
- [Commands Overview](Commands.md) - Full list of available commands
- [Dashboard](../core-features/Dashboard.md) - Learn about the dashboard interface

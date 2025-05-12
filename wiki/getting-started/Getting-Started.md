# Getting Started with InfiniBot

This guide helps you get started with using InfiniBot in your Discord server.

## Adding InfiniBot to Your Server

1. Use the official invitation link to add InfiniBot to your server.
2. Make sure to grant all requested permissions for full functionality.
3. Once invited, InfiniBot will be ready to use with default settings.

## Initial Setup

### Creating the InfiniBot Mod Role

The first step after adding InfiniBot is to set up the **InfiniBot Mod** role:

1. InfiniBot will attempt to create this role automatically.
2. If the role wasn't created automatically, use `/create infinibot-mod-role` to manually create it.
3. Assign this role to yourself and trusted administrators to unlock full access to InfiniBot's features.

### Setting Up Admin Channel

For moderation features to work properly, you'll need to set up an admin channel:

1. Create a private channel that only moderators can access.
2. Use `/set admin-channel` in that channel to designate it as InfiniBot's admin channel.
3. This channel will receive notifications about strikes, automatic moderation actions, and more.

### Configuring Log Channel

For detailed logging of server activities:

1. Create a private channel for logs (can be the same as admin channel).
2. Use `/set log-channel` in that channel to set it as InfiniBot's logging channel.
3. This channel will receive logs for message deletions, edits, member joins/leaves, and other activities.

## Using the Dashboard

The dashboard is your central hub for configuring InfiniBot:

1. Use `/dashboard` to open the interactive configuration panel.
2. From here, you can access all major features and their settings.
3. Click on the feature buttons to navigate to specific settings.

## Next Steps

After completing the initial setup, explore these features:

- [Moderation Features](Moderation.md) - Set up profanity filtering and spam control
- [Leveling](Leveling.md) - Configure the member leveling system
- [Join & Leave Messages](Join-Leave-Messages.md) - Set custom messages for when members join or leave

For a complete list of commands, see the [Commands Overview](Commands.md).

## Required Permissions

For optimal functionality, InfiniBot needs these permissions:

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

If you encounter permission errors, InfiniBot will notify you about the specific permissions needed.

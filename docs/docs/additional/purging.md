---
title: Purging
nav_order: 1
parent: Additional Features
---

# Purging
{: .no_toc }

InfiniBot's Purging feature allows administrators to quickly remove multiple messages from a channel.

{: .warning }
This is a powerful moderation tool. Use with caution as purged messages cannot be recovered.

**Topics Covered**
- TOC
{:toc}

## Command Usage

Use `/purge <amount>` to delete messages in bulk.

Parameters:
- `amount`: The number of messages to delete, or "all" to clear the entire channel

## How It Works

When you run the purge command:
1. InfiniBot confirms you have the required permissions
2. It deletes the specified number of messages
3. A confirmation message is sent

## Permission Requirements

To use the purge command, you need:
- The **[InfiniBot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)** role
- **Manage Messages** permission in the channel

## Purge Modes

### Standard Purge

Deleting a specific number of messages:
```
/purge 10
```
This deletes the 10 most recent messages in the channel.

### Full Channel Purge

Clearing all messages in a channel:
```
/purge all
```
This recreates the channel to remove all messages while preserving permissions and settings.

{: .titleless-yellow }
**⚠️ Important Warning ⚠️**  
Using `/purge all` may cause issues with other third-party Discord integrations. While InfiniBot will automatically update its internal database to track the new channel, other bots and integrations might still reference the old, deleted channel ID.

If you use other bots or connections with the channel, you may need to manually update their configurations after using this command.

## Important Notes

- Discord limits that InfiniBot can delete messages
- For bulk deletion, use the "all" option to recreate the channel
- Channel recreation preserves:
  - Channel name
  - Topic/description
  - Category
  - Permission overwrites
  - Position in the server

## Safety Considerations

The purge command is powerful and can't be undone. Use it with caution, especially:
- In public channels
- When using the "all" option
- When important information might be lost

## Best Practices

- **Archive First**: Consider archiving important information before purging
- **Be Specific**: Use the smallest number necessary to avoid deleting too much
- **Inform Members**: Let members know before purging active channels
- **Check Permissions**: Ensure the bot has Manage Messages and Manage Channels

---

**Related Pages:**
- [Commands Overview]({% link docs/getting-started/commands.md %}) - See all available commands
- [Moderation]({% link docs/core-features/moderation/index.md %}) - Additional moderation tools
- [Logging]({% link docs/core-features/logging.md %}) - Track message deletion activities

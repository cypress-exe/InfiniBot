# Purging

InfiniBot's Purging feature allows administrators to quickly remove multiple messages from a channel.

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
- The **InfiniBot Mod** role
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

## Important Notes

- Discord limits bulk deletion to messages newer than 14 days
- For messages older than 14 days, use the "all" option to recreate the channel
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

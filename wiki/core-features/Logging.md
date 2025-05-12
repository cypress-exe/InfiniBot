# Action Logging

InfiniBot's Action Logging feature provides detailed tracking of activities in your server, helping moderators monitor changes and maintain security.

## Setup

1. Access via: `/dashboard → Logging`
2. Enable the feature with the **Enable Logging** button
3. Select a logging channel with the **Select Channel** button or use `/set log-channel`

## Logged Events

InfiniBot logs the following activities:

### Message Events
- Message deletions (with content)
- Message edits (with before/after content)

### Member Events
- Member joins
- Member leaves
- Nickname changes
- Role changes

### Moderation Events
- Member timeouts
- Member bans/unbans
- Member kicks

## Log Format

Each logged event contains:
- Event type and timestamp
- Affected user(s) or channel(s)
- Before/after information when applicable
- User who performed the action (when available)
- Attachments (for deleted messages with images)

## Permissions Required

For full logging functionality, InfiniBot needs these permissions:
- **View Audit Log** - To determine who performed actions
- **Read Message History** - To capture message content
- **View Channels** - To monitor activities across channels

If InfiniBot is missing permissions, it will notify server administrators.

## Log Channel Security

It's recommended to:
1. Create a private channel visible only to moderators and administrators
2. Give InfiniBot full permissions in this channel
3. Configure the log channel by using `/set log-channel` in the desired channel or through the dashboard.

## Storage Limitations

Due to Discord's limitations:
- Deleted messages are only logged if they were sent while InfiniBot was online
- Some information may be unavailable for specific actions
- For extensive history, consider enabling Discord's built-in audit log retention

## Tips for Effective Logging

- Set up a dedicated logging channel separate from your main admin channel and disable notifications for this channel to minimize distractions.
- Regularly check logs for unusual activity
- Keep the log channel organized (InfiniBot automatically uses embeds to help with this)

---
title: Logging
nav_order: 2
parent: Core Features
---

# Action Logging
{: .no_toc }

InfiniBot's Action Logging feature provides detailed tracking of activities in your server, helping moderators monitor changes and maintain security.

{: .titleless-green }
Logging creates a transparent record of server activities, making moderation and administration more effective.

**Topics Covered**
- TOC
{:toc}

## Setup

1. Access via: `/dashboard → Logging`
2. Enable the feature with the **Enable** button (if applicable)
3. Select a logging channel with the **Log Channel** button or use `/set log-channel`

## Logged Events

InfiniBot logs the following activities, categorized into three main types:

### Message Events

| Event Type         | Description                                             |
|--------------------|---------------------------------------------------------|
| Message Deletions  | Logs deleted messages, including content.               |
| Message Edits      | Logs edited messages, showing before and after content. |

### Member Events

| Event Type         | Description                          |
|--------------------|--------------------------------------|
| Nickname Changes   | Tracks changes to member nicknames.  |
| Role Changes       | Logs updates to member roles.        |

### Moderation Events

| Event Type         | Description                          |
|--------------------|--------------------------------------|
| Member Timeouts    | Logs when a member is timed out.     |
| Member Bans        | Tracks bans and unbans of members.   |
| Member Kicks       | Logs when a member is kicked.        |

## Log Format

Each logged event contains:
- Event type and timestamp
- Affected user(s) or channel(s)
- Before/after information when applicable
- User who performed the action (when available)
- Attachments (for deleted/edited messages with images or files)

## Permissions Required

For full logging functionality, InfiniBot needs these permissions:
- **View Audit Log** - To determine who performed actions
- **Read Message History** - To capture message content
- **View Channels** - To monitor activities across channels

If InfiniBot is missing permissions, it will notify the server owner.

## Log Channel Security

It's recommended to:
1. Create a private channel visible only to moderators and administrators
2. Give InfiniBot full permissions in this channel
3. Configure the log channel by using `/set log-channel` in the desired channel or through the dashboard.

{: .tip }
To avoid frequent notifications, set the Log Channel's notification settings to "None" in Discord.

## Storage Limitations

InfiniBot retains message data for a limited time to ensure effective logging while respecting privacy:

- Only messages sent while InfiniBot is online can be logged if deleted.
- Message data older than 7 days or exceeding the last 1000 messages is removed from InfiniBot's database.
- Logs for edited or deleted messages beyond the retention period may lack detailed information.
- Certain actions may result in incomplete logs due to data unavailability.
- For extended history, consider utilizing Discord's built-in audit log features.

{: .note }
Removing message data from InfiniBot's database does NOT delete the message from Discord or alter it in any way. However, logs for older messages may contain less detailed information due to this fact.

For more information on InfiniBot's data handling and retention policies, please refer to our [Privacy Policy]({% link docs/legal/privacy-policy.md %}).

## Tips for Effective Logging

- Set up a dedicated logging channel separate from your main admin channel and disable notifications for this channel to minimize distractions.
- Regularly check logs for unusual activity
- Keep the log channel organized (InfiniBot automatically uses embeds to help with this)

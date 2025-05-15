---
title: Generic Replacements
parent: Messaging Features
nav_order: 4
---

# Generic Replacements
{: .no_toc }

This document outlines the generic replacements that can be used in most messages sent by InfiniBot. These replacements are automatically processed when messages are sent, allowing for dynamic, personalized content.

{: .info }
Generic replacements can be used in embeds, join/leave messages, role messages, and other customizable text areas throughout InfiniBot.

**Topics Covered**
- TOC
{:toc}

## User Replacements

- `@mention` - Mentions the member (@username)
- `@username` - Shows the member's username
- `@displayname` - Shows the member's display name
- `@id` - Shows the member's Discord ID
- `@joindate` - Shows when the member joined the server
- `@accountage` - Shows how old the member's Discord account is

## Server Replacements

- `@server` - Shows the server name
- `@serverid` - Shows the server's Discord ID
- `@membercount` - Shows the total number of members in the server
- `@owner` - Shows the server owner's display name

## Time and Date Replacements

- `@time` - Current time in the server's timezone
- `@date` - Current date
- `@datetime` - Current date and time

## Channel Mentions

Any channel referenced with `#channel` format (for example, `#welcome` or `#rules`) will be automatically converted to a proper Discord channel mention.

## Examples

Welcome message example:
```
Welcome @mention to @server! Please check out #rules to get started!
```

This would appear as:
```
Welcome @discord-user to Awesome Server! Please check out #rules to get started!
```

## Usage Notes

- These replacements work in most text-based messages sent by InfiniBot
- Replacements are case-sensitive
- If a replacement can't be processed, it will remain as plain text or appear as "Unknown"
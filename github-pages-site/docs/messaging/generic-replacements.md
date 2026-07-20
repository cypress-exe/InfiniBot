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

- `@mention` or `@member` - Mentions the member (@username)
- `@username` - Shows the member's username
- `@displayname` - Shows the member's display name
- `@id` - Shows the member's Discord ID
- `@joindate` - Shows when the member joined the server (best-effort; see below)
- `@accountage` - Shows how old the member's Discord account is (best-effort; see below)

## Server Replacements

- `@server` - Shows the server name
- `@serverid` - Shows the server's Discord ID
- `@membercount` - Shows the total number of members in the server
- `@owner` - Shows the server owner's display name (best-effort; see below)

## Time and Date Replacements

- `@time` - Current time
- `@date` - Current date (Long Format)
- `@dateshort` - Current date (Short Format)
- `@datelong` - Current date (Long Format. Same as `@date`)

## Channel Mentions

Any channel referenced with `#channel` format (for example, `#welcome` or `#rules`) will be automatically converted to a proper Discord channel mention.

## Role Replacements

Any text matching `@RoleName` (for example, `@Moderator`) will be automatically converted to a mention of the server role with that exact name.

- The fixed placeholders on this page (`@mention`, `@server`, `@owner`, `@time`, etc.) always take priority. If a role happens to share a name with one of them, the fixed placeholder wins.
- To reference a role unambiguously — for example, when its name collides with a fixed placeholder — use the explicit form: `@role:RoleName` (for example, `@role:server`).
- The `@everyone` role is never matched by name.
- If no role matches the name given, the text is left as-is.

{: .info }
Role mentions placed in an embed (which is where these replacements are used) don't trigger a notification ping for members of that role — Discord only sends ping notifications for mentions in plain message content.

## Examples

Welcome message example:
```
Welcome @mention to @server! Please check out #rules to get started!
```

This would appear as:
```
Welcome @discord-user to Awesome Server! Please check out #rules to get started!
```

Role mention example:
```
Reach out to @Moderator if you need help getting started.
```

This would appear as:
```
Reach out to @Moderator-role-mention if you need help getting started.
```

## Best-Effort Replacements

{: .warning }
A few replacements depend on information Discord may not have handed InfiniBot at the moment the message is sent. When that information isn't available, the placeholder is replaced with the literal text **`Unknown`** rather than being left in place.

This behavior is a deliberate trade-off: InfiniBot avoids requesting full member lists for large servers, since doing so is slow and rate-limited by Discord. In practice these replacements resolve correctly the majority of the time in smaller and moderately sized servers, where the entire member list is cached. For large servers, these fields frequently can't be resolved. See also the [Logging]({% link docs/core-features/logging.md %}) page, which has the same underlying limitation.

## Usage Notes

- These replacements work in most text-based messages sent by InfiniBot
- Replacements are case-sensitive
- The user replacements (`@mention`, `@username`, `@displayname`, `@id`, `@joindate`, `@accountage`) only apply where a specific user is associated with the message. In contexts with no such user (for example, a role message or reaction role embed) these placeholders are left untouched and will appear literally in the message
- If a replacement can't be processed, it will remain as plain text or appear as "Unknown"
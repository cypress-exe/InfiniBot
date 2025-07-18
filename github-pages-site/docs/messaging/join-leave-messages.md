---
title: Join/Leave Messages
parent: Messaging Features
nav_order: 3
---

# Join & Leave Messages
{: .no_toc }

InfiniBot can automatically send customized welcome and goodbye messages when members join or leave your server.

**Topics Covered**
- TOC
{:toc}

## Setup

### Join Messages

1. Access via: `/dashboard → Join/Leave Messages → Join Messages`
2. Enable the feature with the **Enable** button (if applicable)
3. Configure your settings:
   - Channel selection
   - Message customization
   - Allow join cards option

### Leave Messages

1. Access via: `/dashboard → Join/Leave Messages → Leave Messages`
2. Enable the feature with the **Enable** button (if applicable)
3. Configure your settings:
   - Channel selection
   - Message customization

## Channel Configuration

For both join and leave messages, you can select:
- System channel (default)
- Any text channel in your server

Make sure InfiniBot has permission to view and send messages in the selected channel.

## Message Customization

### Embed Editor

Messages are sent as embeds, which you can customize:
1. **Title** - Set a custom welcome/goodbye title
2. **Description** - Create a custom message for members
3. **Color** - Set the color of the embed's sidebar

### Available Placeholders

Utilize the [generic replacements]({% link docs/messaging/generic-replacements.md %}) in your messages to display dynamic information.

Example: `Welcome @mention to @server! You are member @membercount.`

## Join Cards

Members can personalize their join messages with [custom cards]({% link docs/core-features/profile.md %}#join-card).

### Enable/Disable Join Cards

1. Access via: `/dashboard → Join/Leave Messages → Join Messages → Enable/Disable Join Cards`
2. Toggle whether personal join cards appear with welcome messages

## Tips for Effective Messages

- **Keep it concise** - Short, welcoming messages work best
- **Include useful information** - Server rules, getting started links, etc.
- **Mention channels** - Point to important channels like #rules or #welcome
- **Consider mobile users** - Format carefully for mobile device compatibility
- **Test your messages** - Preview how they'll look to ensure formatting is correct

---

**Related Pages:**
- [Embeds]({% link docs/messaging/embeds.md %}) - More information about embed formatting
- [Profile]({% link docs/core-features/profile.md %}) - Configure your personal join card
- [Dashboard]({% link docs/core-features/dashboard.md %}) - General bot configuration
- [Birthday Messages]({% link docs/messaging/birthdays.md %}) - Similar messaging feature
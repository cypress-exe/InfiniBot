---
title: Birthdays
parent: Messaging Features
nav_order: 1
---

# Birthday Messages
{: .no_toc }

InfiniBot's Birthday Messages feature allows you to celebrate your community members' birthdays with automatic announcements.

**Topics Covered**
- TOC
{:toc}

## Setup

1. Access via: `/dashboard → Birthdays`
2. Configure the following settings:
   - **Configure Birthdays** - Add/remove members' birthdays
   - **Notification Channel** - Where announcements will be sent
   - **Message Time** - What time of day announcements are sent
   - **Edit Message** - Customize the announcement

## Adding Birthdays

1. Access via: `/dashboard → Birthdays → Configure Birthdays`
2. Click **Add**
3. Enter the member's information:
   - Select the member
   - Enter their birth date
   - Optionally add their real name (for personalized messages)

## Birthday Message Customization

Birthday messages are sent as embeds, which you can customize:
1. **Title** - Set a custom birthday announcement title
2. **Description** - Create a personalized message

### Available Placeholders

In addition to the [generic replacements]({% link docs/messaging/generic-replacements.md %}) for InfiniBot's messages, birthday messages provide additional replacements, including:
- `[age]` - Displays their age (if birth year was provided)
- `[realname]` - Shows their real name (if provided, else just their username)

Example: `Happy Birthday to @mention! [realname] is turning [age] today!`

## Birthday Notifications

When a member's birthday arrives:
1. A birthday announcement is sent to the configured channel
2. The member also receives a personalized DM (unless they've opted out)

## Managing Birthdays

### Editing Birthdays
1. Access via: `/dashboard → Birthdays → Configure Birthdays`
2. Find the member in the list
3. Click **Edit** to update their information

### Removing Birthdays
1. Access via: `/dashboard → Birthdays → Configure Birthdays`
2. Find the member in the list
3. Click **Delete** to delete their birthday

## Required Permissions

For birthday messages to work properly, InfiniBot needs:
- **Send Messages** - To send birthday announcements
- **Embed Links** - To create formatted messages

## Best Practices

- **Channel Selection** - Choose a public channel where celebrations make sense
- **Message Timing** - Select a time when most members are active
- **Regular Updates** - Periodically check that birthday information is current

---

**Related Pages:**
- [Join & Leave Messages]({% link docs/messaging/join-leave-messages.md %}) - Similar messaging feature
- [Embeds]({% link docs/messaging/embeds.md %}) - More information about embed formatting
- [Dashboard]({% link docs/core-features/dashboard.md %}) - Managing server features

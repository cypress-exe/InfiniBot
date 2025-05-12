# Join & Leave Messages

InfiniBot can automatically send customized welcome and goodbye messages when members join or leave your server.

## Setup

### Join Messages

1. Access via: `/dashboard → Join/Leave Messages → Join Messages`
2. Enable the feature with the **Enable Join Messages** button
3. Configure your settings:
   - Channel selection
   - Message customization
   - Allow join cards option

### Leave Messages

1. Access via: `/dashboard → Join/Leave Messages → Leave Messages`
2. Enable the feature with the **Enable Leave Messages** button
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

Use these placeholders in your messages to display dynamic information:

- `[user]` - Mentions the member (@username)
- `[username]` - Shows the member's username
- `[servername]` - Shows the server name
- `[membercount]` - Shows the current member count

Example: `Welcome [user] to [servername]! You are member #[membercount].`

## Join Cards

Join cards are customizable cards that can be added to join messages:

1. Members can create their own join cards using `/profile → Join Card`
2. These cards will appear alongside the server's welcome message
3. This feature can be toggled on/off in join message settings

### Enable/Disable Join Cards

1. Access via: `/dashboard → Join/Leave Messages → Join Messages → Allow Join Cards`
2. Toggle whether personal join cards appear with welcome messages

## Tips for Effective Messages

- **Keep it concise** - Short, welcoming messages work best
- **Include useful information** - Server rules, getting started links, etc.
- **Mention channels** - Point to important channels like #rules or #welcome
- **Consider mobile users** - Format carefully for mobile device compatibility
- **Test your messages** - Preview how they'll look to ensure formatting is correct

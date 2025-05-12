# Embeds

InfiniBot allows you to create beautiful, customized embed messages for your server.

## What are Embeds?

Embeds are rich message formats in Discord that can include:
- Titles and descriptions
- Custom colors
- Organized layouts
- Enhanced readability

## Creating an Embed

1. Use `/create embed [role]` command
   - The optional `role` parameter allows you to ping a role when sending the embed
2. Fill out the modal with:
   - **Title** - The main heading for your embed
   - **Description** - The main content of your embed (supports basic markdown)
3. Choose a color for the embed's sidebar
4. The embed will be sent to the current channel

## Available Colors

When creating an embed, you can choose from these color options:
- Red
- Green
- Blue
- Yellow
- White
- Blurple (Discord brand color)
- Greyple (Discord secondary color)
- Teal
- Purple
- Gold
- Magenta
- Fuchsia

## Role Pinging

If you want to notify members about important embeds:

1. Include a role in the command: `/create embed @Announcements`
2. For this to work, either:
   - InfiniBot must have **Mention Everyone** permission, or
   - The target role must have **Allow anyone to @mention this role** enabled

If permissions are insufficient, InfiniBot will notify you.

## Use Cases

Embeds are perfect for:
- Server rules
- Announcements
- Event details
- Staff information
- Resource lists
- Welcome messages
- Feature explanations

## Editing Embeds

To edit an embed after creation:
1. Right-click on the message
2. Select "Apps" and then "Options"
3. Click "Edit Embed"
4. Make your changes and save

## Permissions Required

For embed creation, InfiniBot needs:
- **Send Messages** - To send the embed
- **Embed Links** - To create the embed formatting
- **Mention Everyone** - Optional, only if pinging roles

## Tips for Effective Embeds

- **Keep it concise** - Avoid walls of text
- **Use markdown** - Format with **bold**, *italics*, and `code blocks`
- **Choose appropriate colors** - Different colors can convey different message tones
- **Test your embeds** - Check how they appear on both desktop and mobile devices
- **Consider accessibility** - Ensure your color choices have good contrast

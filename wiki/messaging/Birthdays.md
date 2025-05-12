# Birthday Messages

InfiniBot's Birthday Messages feature allows you to celebrate your community members' birthdays with automatic announcements.

## Setup

1. Access via: `/dashboard → Birthdays`
2. Configure the following settings:
   - **Birthday Channel** - Where announcements will be sent
   - **Runtime** - What time of day announcements are sent
   - **Timezone** - Server timezone for accurate timing
   - **Birthday Message** - Customize the announcement

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

Use these placeholders in your messages:
- `[user]` - Mentions the birthday person (@username)
- `[username]` - Shows their username
- `[servername]` - Shows the server name
- `[age]` - Displays their age (if birth year was provided)
- `[realname]` - Shows their real name (if provided)

Example: `Happy Birthday to [user]! [realname] is turning [age] today!`

## Birthday Notifications

When a member's birthday arrives:
1. A birthday announcement is sent to the configured channel
2. The member also receives a personalized DM (unless they've opted out)

## Managing Birthdays

### Editing Birthdays
1. Access via: `/dashboard → Birthdays → Manage Birthdays`
2. Find the member in the list
3. Click **Edit** to update their information

### Removing Birthdays
1. Access via: `/dashboard → Birthdays → Manage Birthdays`
2. Find the member in the list
3. Click **Remove** to delete their birthday

## Required Permissions

For birthday messages to work properly, InfiniBot needs:
- **Send Messages** - To send birthday announcements
- **Embed Links** - To create formatted messages

## Best Practices

- **Privacy Consideration** - Only collect birth years with permission
- **Timezone Configuration** - Set the correct timezone for your server
- **Channel Selection** - Choose a public channel where celebrations make sense
- **Message Timing** - Select a time when most members are active
- **Regular Updates** - Periodically check that birthday information is current

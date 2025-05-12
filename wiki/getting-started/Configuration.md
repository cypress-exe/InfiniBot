# Configuration

This page covers the general configuration of InfiniBot in your server.

## Initial Setup

After adding InfiniBot to your server, follow these steps for basic configuration:

1. Set up the **InfiniBot Mod** role (automatically created or via `/create infinibot-mod-role`)
2. Assign this role to yourself and trusted administrators
3. Set up an admin channel with `/set admin-channel` for moderation reports
4. Set up a log channel with `/set log-channel` for activity logging

## Using the Dashboard

The dashboard is the primary way to configure InfiniBot:

1. Use `/dashboard` to open the configuration panel
2. Click on the features you want to configure
3. Follow the prompts to set up each feature

See the [Dashboard](Dashboard.md) page for detailed instructions.

## Required Permissions

InfiniBot needs these permissions for full functionality:

### Text Channel Permissions
- View Channels
- Send Messages
- Embed Links
- Manage Roles
- Manage Channels
- Manage Messages
- Manage Nicknames
- View Audit Log
- Add Reactions
- Timeout Members
- Ban Members
- Read Message History

### Voice Channel Permissions
- Connect
- Move Members

## Feature Configuration

Each major feature has its own configuration section:

- [Moderation](Moderation.md) - Profanity and spam control
- [Logging](Logging.md) - Server activity tracking
- [Leveling](Leveling.md) - Member experience and rewards
- [Join/Leave Messages](Join-Leave-Messages.md) - Welcome and goodbye messages
- [Birthdays](Birthdays.md) - Birthday celebrations
- [Default Roles](Default-Roles.md) - Automatic role assignment
- [Join to Create VCs](Join-To-Create-VCs.md) - Dynamic voice channels

## Server Timezone Configuration

Setting your server's timezone ensures that time-based features work correctly:

1. Access via: `/dashboard → Configure Timezone`
2. Select your timezone from the dropdown list
3. Click **Set Timezone**

This affects features like Birthday announcements and scheduled tasks.

## Troubleshooting Configuration Issues

If you encounter problems with InfiniBot's configuration:

1. **Permission Issues**: Check InfiniBot's role and channel permissions
2. **Missing Settings**: Ensure you've completed all required setup steps
3. **Feature Conflicts**: Some features may interact with each other
4. **Role Hierarchy**: InfiniBot's role must be above roles it needs to manage

For additional help, refer to the [Support & Feedback](Support.md) page.

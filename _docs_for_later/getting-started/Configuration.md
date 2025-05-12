# Configuration

This page covers the general configuration of InfiniBot in your server.

## Initial Configuration

After adding InfiniBot to your server, you have two options for configuration:

1. **Onboarding Process**: When InfiniBot first joins, it will guide you through setting up essential features.
2. **Manual Configuration**: Configure individual features using the dashboard at your own pace.

For detailed instructions on the initial setup steps, see the [Getting Started](Getting-Started.md) page.

## Using the Dashboard

The dashboard is the primary way to configure InfiniBot:

1. Use `/dashboard` to open the configuration panel
2. Click on the features you want to configure
3. Follow the prompts to set up each feature

See the [Dashboard](../core-features/Dashboard.md) page for detailed instructions.

## Feature Configuration

Each major feature has its own configuration section:

- [Moderation](../core-features/Moderation.md) - Profanity and spam control
- [Logging](../core-features/Logging.md) - Server activity tracking
- [Leveling](../core-features/Leveling.md) - Member experience and rewards
- [Join/Leave Messages](../messaging/Join-Leave-Messages.md) - Welcome and goodbye messages
- [Birthdays](../messaging/Birthdays.md) - Birthday celebrations
- [Default Roles](../roles/Default-Roles.md) - Automatic role assignment
- [Join to Create VCs](../additional/Join-To-Create-VCs.md) - Dynamic voice channels

## Server Timezone Configuration

Setting your server's timezone ensures that time-based features work correctly:

1. Access via: `/dashboard → Configure Timezone`
2. Select your timezone from the dropdown list
3. Click **Set Timezone** (called "Change Timezone" if already set)

This affects features like Birthday announcements and scheduled tasks.

## Extra Features Configuration

Access additional configuration options:

1. Access via: `/dashboard → Extra Features`
2. Toggle various optional features:
   - **Auto-delete invites**: Automatically delete messages containing Discord invite links (unless sent by an admin)
   - **Update messages**: Receive notifications about InfiniBot updates

## Troubleshooting Configuration Issues

If you encounter problems with InfiniBot's configuration:

1. **Permission Issues**: Check InfiniBot's role and channel permissions
2. **Missing Settings**: Ensure you've completed all required setup steps
3. **Feature Conflicts**: Some features may interact with each other
4. **Role Hierarchy**: InfiniBot's role must be above roles it needs to manage

For additional help, refer to the [Support & Feedback](Support.md) page.

---

**Related Pages:**
- [Getting Started](Getting-Started.md) - Initial setup guide
- [Commands Overview](Commands.md) - Full list of available commands
- [Dashboard](../core-features/Dashboard.md) - Learn about the dashboard interface

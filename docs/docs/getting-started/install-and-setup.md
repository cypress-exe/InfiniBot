---
title: Install and Setup
nav_order: 1
parent: Getting Started
---

# Installing and Setting up InfiniBot

This guide will walk you through adding InfiniBot to your server and configuring its features using the dashboard.

---

## Adding InfiniBot to Your Server

1. Use the official invitation link to add InfiniBot to your server.
2. Grant InfiniBot the **Administrator** permission for easiest setup. Alternatively, assign individual permissions listed in the [Required Permissions](#required-permissions) section.
3. Once added, InfiniBot is ready to use with default settings.

---

## Onboarding Process

When InfiniBot joins your server:

1. It will guide you through setting up essential features based on your server's needs.
2. You can enable/disable features like moderation, logging, and leveling.
3. Onboarding helps configure channels and permissions for each feature.

If you skip onboarding or want to revisit settings later, use the dashboard.

---

## Using the Dashboard

The dashboard is your central hub for configuring InfiniBot:

1. Open it with the `/dashboard` command.
2. Click on the features you want to configure.
3. Follow the prompts for setup, including:
   - Feature settings (Moderation, Logging, Leveling, etc.)
   - Timezone configuration: `/dashboard → Configure Timezone`
   - Extra options: `/dashboard → Extra Features`

See the [Dashboard]({% link docs/core-features/dashboard.md %}) page for detailed usage.

---

## Feature Configuration

InfiniBot offers robust configuration for core and optional features:

- [Moderation]({% link docs/core-features/moderation/index.md %}) - Profanity filtering, spam control
- [Logging]({% link docs/core-features/logging.md %}) - Track user and system events
- [Leveling]({% link docs/core-features/leveling.md %}) - Reward member activity
- [Join/Leave Messages]({% link docs/messaging/Join-Leave-Messages.md %}) - Customize welcome/goodbye messages
- [Birthdays]({% link docs/messaging/Birthdays.md %}) - Celebrate member birthdays
- [Default Roles]({% link docs/roles/Default-Roles.md %}) - Auto-assign roles to new members
- [Join to Create VCs]({% link docs/additional/join-to-create-vcs.md %}) - Dynamic voice channels

---

## The InfiniBot Mod Role

This role grants trusted users the ability to manage InfiniBot:

1. InfiniBot tries to create the **InfiniBot Mod** role automatically.
2. If not created, run `/create infinibot-mod-role`.
3. Assign it to yourself or trusted admins for full access.

---

## Server Timezone Configuration

To ensure time-based features (e.g. birthdays, reminders) work correctly:

1. Open `/dashboard → Configure Timezone`
2. Choose your timezone
3. Click **Set Timezone** (or **Change Timezone** if one is already set)

---

## Extra Features

You can toggle optional enhancements via the dashboard:

- **Auto-delete invites** – Remove Discord invite links automatically
- **Update messages** – Get notifications about InfiniBot updates

Access via: `/dashboard → Extra Features`

---

## Troubleshooting Configuration Issues

If InfiniBot isn’t behaving as expected:

1. **Permission Issues**: Check role and channel permissions.
2. **Missing Settings**: Complete all onboarding/config steps.
3. **Feature Conflicts**: Some features may interact.
4. **Role Hierarchy**: InfiniBot's role must be above roles it needs to manage.

For help, visit the [Support & Feedback](Support.md) page.

---

## Required Permissions

For best results, grant InfiniBot **Administrator** access. Alternatively, grant the following permissions **in every channel it operates in**:

- View Channels  
- Send Messages  
- Manage Roles  
- Manage Messages  
- Embed Links  
- Attach Files  
- Manage Nicknames  
- View Audit Log  
- Timeout Members  
- Ban Members  
- Read Message History  

Run `/check_infinibot_permissions` to verify permissions.

---

## Next Steps

After setup, explore these features:

- [Moderation Features]({% link docs/core-features/moderation/index.md %})
- [Leveling]({% link docs/core-features/leveling.md %})
- [Join & Leave Messages]({% link docs/messaging/Join-Leave-Messages.md %})
- [Dashboard]({% link docs/core-features/dashboard.md %})
- [Commands Overview]({% link docs/getting-started/commands.md %})

---

**Related Pages:**

- [Dashboard]({% link docs/core-features/dashboard.md %})
- [Commands Overview]({% link docs/getting-started/commands.md %})
- [Support & Feedback]({% link docs/getting-started/support.md %})

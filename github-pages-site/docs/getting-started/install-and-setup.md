---
title: Install and Setup
nav_order: 1
parent: Getting Started
---

# Installing and Setting up InfiniBot
{: .no_toc }

This guide will walk you through adding InfiniBot to your server and configuring its features using the dashboard.

**Topics Covered**
- TOC
{:toc}

---

## Adding InfiniBot to Your Server

1. Click the button below to add InfiniBot to your server.  
[Add InfiniBot to Your Server](https://discord.com/oauth2/authorize?client_id=991832387015159911){: .btn .btn-primary .mb-2 .mt-2}
2. Grant InfiniBot the **Administrator** permission for easiest setup. Alternatively, assign individual permissions listed in the [Required Permissions](#required-permissions) section.
3. Once added, InfiniBot is ready to use with default settings.

---

## Onboarding Process

When InfiniBot joins your server:

1. It will guide you through setting up essential features based on your server's needs.
2. You can enable/disable features like moderation, logging, and leveling.
3. Onboarding helps configure channels and permissions for each feature.

If you skip onboarding or want to revisit settings later, [use the dashboard](#using-the-dashboard).

---

## Using the Dashboard

The dashboard is your central hub for configuring InfiniBot:

1. Open it with the `/dashboard` command.
2. Click on the features you want to configure.
3. Follow the prompts for feature setup and configuration.

See the [Dashboard]({% link docs/core-features/dashboard.md %}) page for detailed usage.

---

## The InfiniBot Mod Role

This discord role grants trusted users the ability to manage InfiniBot:

1. InfiniBot tries to create the **InfiniBot Mod** role automatically.
2. If not created, run `/create infinibot-mod-role`.
3. Assign it to yourself or trusted admins for full access.

{: .note }
The **InfiniBot Mod** role operates like any standard Discord role. Ensure it is positioned appropriately in the role hierarchy, as it grants administrative control over InfiniBot.

---

## Troubleshooting Configuration Issues

If InfiniBot isn’t behaving as expected:

1. **Permission Issues**: Check role and channel permissions.
2. **Missing Settings**: Complete all onboarding/config steps.
3. **Role Hierarchy**: InfiniBot's role must be above roles it needs to manage.

For help, visit the [Support & Feedback]({% link docs/getting-started/support.md %}) page.

---

## Required Permissions
<!-- WHEN UPDATING, REMEMBER TO:
1. Update src/config/global_settings.required_permissions
2. Update join link to reflect new permissions:
    - Replace link in generated/configure/config.json["links.bot-invite-link"]
    - Replace link in discord developer portal
    - Replace link on promotion sites (top.gg, etc...) -->

For best results, grant InfiniBot **Administrator** access. Alternatively, grant the following permissions **in every channel it operates in**:

- Manage Roles
- Manage Channels
- Ban Members
- Manage Nicknames
- View Audit Log
- View Channels
- Moderate Members
- Send Messages
- Send Messages in Threads
- Manage Messages
- Embed Links
- Attach Files
- Read Message History
- Mention @everyone, @here and All Roles
- Add Reactions
- Move Members

Run `/check_infinibot_permissions` to verify permissions.

---

## Next Steps

After setup, explore these features:

- [Moderation Features]({% link docs/core-features/moderation/index.md %})
- [Leveling]({% link docs/core-features/leveling.md %})
- [Join & Leave Messages]({% link docs/messaging/join-leave-messages.md %})
- [Dashboard]({% link docs/core-features/dashboard.md %})
- [Commands Overview]({% link docs/getting-started/commands.md %})

---

**Related Pages:**

- [Dashboard]({% link docs/core-features/dashboard.md %})
- [Commands Overview]({% link docs/getting-started/commands.md %})
- [Support & Feedback]({% link docs/getting-started/support.md %})

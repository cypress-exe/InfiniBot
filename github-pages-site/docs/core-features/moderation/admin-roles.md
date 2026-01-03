---
title: Admin Roles
nav_order: 3
parent: Moderation
grand_parent: Core Features
---

# Admin Roles
{: .no_toc }

InfiniBot can ignore moderation action requests from members with specific roles. This is useful for allowing moderators and admins to bypass InfiniBot's moderation features.

{: .titleless-green }
Admin roles provide another tool to manage your server effectively. Configure this to allow trusted members to bypass moderation actions.

**Topics Covered**
- TOC
{:toc}

## Setup

1. Access via: `/dashboard → Moderation → Admin Roles`
2. Use the **Add Role** button to select roles
3. Use the **Delete Role** button to remove roles from the admin list

## How It Works

When InfiniBot detects a moderation action, it first checks the list of admin roles. If the user performing the action has one of these roles, InfiniBot will ignore the moderation request. This allows trusted members to perform actions without interference from InfiniBot.

## Managing Admin Roles

### Adding Admin Roles

1. Click **Add Role** in the dashboard
2. Select the role you want to add as an admin role
3. Click **Add**

You can add multiple admin roles, and all of them will be recognized as trusted members.

### Removing Admin Roles

1. Click **Delete Role** in the dashboard
2. Select the roles you want to remove from the admin list
3. Click **Delete**

## Best Practices

- Only assign admin roles to trusted moderators and administrators who need to bypass moderation features
- Review your admin roles list to make sure that only active and appropriate roles are included

---

**Related Pages:**
- [Profanity Moderation]({% link docs/core-features/moderation/profanity/index.md %}) - Text content moderation
- [Spam Moderation]({% link docs/core-features/moderation/spam.md %}) - Spam detection and prevention
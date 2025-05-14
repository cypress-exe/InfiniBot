---
title: Default Roles
parent: Role Management
nav_order: 1
---

# Default Roles
{: .no_toc }

InfiniBot's Default Roles feature automatically assigns roles to new members when they join your server.

{: .tip }
Default roles are perfect for giving new members access to basic channels or identifying them as newcomers with a "New Member" role.

**Topics Covered**
- TOC
{:toc}

## Setup

1. Access via: `/dashboard → Default Roles`
2. Use the **Add Role** button to select roles
3. Use the **Delete Role** button to remove roles from auto-assignment

## How It Works

When a new member joins your server:
1. InfiniBot checks the list of default roles
2. It automatically assigns all configured roles to the new member
3. This happens instantly upon joining, before the member interacts with the server

## Managing Default Roles

### Adding Default Roles

1. Click **Add Role** in the dashboard
2. Select the role you want to automatically assign
3. Click **Add**

You can add multiple default roles, and all of them will be applied to new members.

### Removing Default Roles

1. Click **Delete Role** in the dashboard
2. Select the roles you want to remove from auto-assignment
3. Click **Delete**

## Required Permissions

For default roles to work properly, InfiniBot needs:
- **Manage Roles** - To assign roles to new members

The bot's role must also be higher in the server hierarchy than any roles being assigned.

## Use Cases

Default roles are perfect for:
- Assigning "Member" or "Newcomer" roles
- Providing basic access permissions to new members
- Setting up verification systems
- Organizing members into default categories

## Troubleshooting

If default roles aren't being assigned:

1. **Check Permissions** - Ensure InfiniBot has the Manage Roles permission
2. **Check Role Hierarchy** - InfiniBot's role must be above the roles it's trying to assign
3. **Verify Configuration** - Check the dashboard to confirm the correct roles are selected

## Best Practices

- **Consider hierarchy** - Be mindful of what permissions default roles grant
- **Combine with other features** - Works well with Join Messages to welcome new members
- **Test the setup** - Have a friend join to test that roles are correctly assigned

---

**Related Pages:**
- [Reaction Roles]({% link docs/roles/reaction-roles.md %}) - Self-assignable roles via reactions
- [Role Messages]({% link docs/roles/role-messages.md %}) - Role information messages
- [Dashboard]({% link docs/core-features/dashboard.md %}) - Managing server features

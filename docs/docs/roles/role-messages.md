---
title: Role Messages
parent: Role Management
nav_order: 3
---

# Role Messages
{: .no_toc }

Role Messages provide a modern, button-based alternative to reaction roles, allowing members to easily assign themselves roles through an interactive interface.

{: .titleless-green }
Role Messages are more advanced than reaction roles and offer greater customization options and a more modern user experience.

**Topics Covered**
- TOC
{:toc}

## Overview

Role Messages create embedded messages with buttons that members can click to open a role selection menu. This system offers:

- A cleaner interface than reaction roles
- Support for role categories
- Single or multiple role selection options
- Modern Discord UI components

## Creating a Role Message

1. Use `/create role_message` to start the Role Message Creation Wizard
2. Click **Get Started** to begin the process
3. Follow the setup steps:

### Step 1: Configure Message Details
- Enter a title for your role message
- Enter a description explaining the available roles (optional)
- You can edit the text and color until satisfactory. When ready, click Next.

{: .tip }
Text and color are editable afterwards.

### Step 2: Add an Option
By clicking "Next", you are automatically moved into the option creation wizard. This will show up as a clickable option for members to add or remove from themselves. Each role option can have multiple roles associated with it.

1. Choose the first role to include in this option.

    {: .tip }
    If you don't see your role, verify that InfiniBot has permissions to manage the role.

2. Add a name for the option, with an optional description describing it.
3. Next, you have the option to edit the text or add/remove more roles.

    {: .note }
    This still describes just one option. If you want members to configure their roles with more customization, make new options for each role.

4. When done with this option, click "Finish"
5. Add more options with the "Add Option" button. Alternatively, edit or remove options with their respective buttons.

### Step 4: Finalize and Send
1. Review your role message
2. Click **Finish** to move onto the final step.

### Step 5: Select Mode
Choose between two modes:
- **Single Selection** - Members can select only one role from each category
- **Multiple Selection** - Members can select multiple roles from each category

Click "Create Role Message" when done.

## How Members Use Role Messages

When members interact with a role message:

1. They click the **Get Role** (single selection) or **Get Roles** (multiple selection) button
2. A dropdown menu appears with available role categories
3. They select desired role(s) from the dropdown
4. Clicking outside the menu or submitting applies the changes

## Managing Role Messages

Role messages are tracked by InfiniBot. To manage them:

1. Find the role message in your server
2. Edit or delete the message to modify or remove the functionality.
    + To edit, navigate to the message's options inside of Discord. (Where you normally go to edit and delete messages)
    + Find `Apps → Options → Edit Message`

## Required Permissions

For role messages to work properly, InfiniBot needs:
- **Manage Roles** - To assign and remove roles
- **Send Messages** - To create the role message
- **Embed Links** - To send properly formatted messages

{: .highlight }
The bot's role must also be higher in the server hierarchy than any roles being assigned.

## Advantages Over Reaction Roles

Role Messages offer several advantages over traditional reaction roles:
- More intuitive UI with buttons and dropdowns
- Better support for role categories and organization
- Less clutter (no need for multiple reactions)
- Support for longer role descriptions
- Mobile-friendly interface

## Best Practices

- **Clear Categories** - Group similar roles together in logical categories
- **Descriptive Names** - Use clear category names and descriptions
- **Permissions Check** - Ensure InfiniBot can manage all roles in your categories
- **Test Your Setup** - Verify the role assignment works correctly after creation

# Role Messages

Role Messages provide a modern, button-based alternative to reaction roles, allowing members to easily assign themselves roles through an interactive interface.

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
- Enter a description explaining the available roles

### Step 2: Select Mode
Choose between two modes:
- **Single Selection** - Members can select only one role category
- **Multiple Selection** - Members can select multiple role categories

### Step 3: Add Role Categories
1. Click **Add Role Category**
2. Enter a name and description for the category
3. Select roles to include in this category
4. Repeat to add multiple categories

### Step 4: Finalize and Send
1. Review your role message
2. Click **Create Role Message** to post it to the channel

## How Members Use Role Messages

When members interact with a role message:

1. They click the **Get Role** (single selection) or **Get Roles** (multiple selection) button
2. A dropdown menu appears with available role categories
3. They select desired role(s) from the dropdown
4. Clicking outside the menu or submitting applies the changes

## Managing Role Messages

Role messages are tracked by InfiniBot. To manage them:

1. Find the role message in your server
2. Edit or delete the message to modify or remove the functionality

## Required Permissions

For role messages to work properly, InfiniBot needs:
- **Manage Roles** - To assign and remove roles
- **Send Messages** - To create the role message
- **Embed Links** - To send properly formatted messages

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

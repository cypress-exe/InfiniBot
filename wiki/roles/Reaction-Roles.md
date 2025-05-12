# Reaction Roles

Reaction Roles allow server members to self-assign roles by reacting to messages with emojis.

## Types of Reaction Roles

InfiniBot offers three types of reaction role setups:

1. **Letter Reactions** - Uses letter emojis (🇦, 🇧, 🇨, etc.)
2. **Number Reactions** - Uses number emojis (1️⃣, 2️⃣, 3️⃣, etc.)
3. **Custom Reactions** - Uses custom emojis of your choice

## Creating Reaction Roles

### Standard Reaction Roles (Letters or Numbers)

1. Use `/create reaction-role <Letters|Numbers> [mention-roles]`
2. Fill out the modal with:
   - **Title** - The title for your reaction role message
   - **Description** - Instructions or information about the roles
3. Select up to 10 roles from the dropdown menu
4. Click **Create**
5. InfiniBot will post the message with appropriate reactions

### Custom Reaction Roles

1. Use `/create custom-reaction-role <options> [mention-roles]`
2. For the options parameter, use the format: `"👍 = @Member, 🥸 = @Gamer"`
3. Fill out the title and description in the modal
4. InfiniBot will post the message with your custom emoji reactions

## How Members Use Reaction Roles

Members can:
1. Find the reaction role message
2. React with the emoji corresponding to their desired role
3. The role will be instantly added
4. Remove the reaction to remove the role

## Managing Reaction Roles

Reaction role messages are tracked by InfiniBot. To manage them:

1. Find the reaction role message
2. Edit the message (requires **InfiniBot Mod**)
3. Delete the message to remove the reaction role functionality

## Required Permissions

For reaction roles to work properly, InfiniBot needs:
- **Manage Roles** - To assign and remove roles
- **Add Reactions** - To add the initial reactions
- **Read Message History** - To track reactions

The bot's role must also be higher in the server hierarchy than any roles being assigned.

## Best Practices

- **Role Descriptions** - Include clear descriptions of what each role provides
- **Organization** - Group similar roles in the same message
- **Role Position** - Ensure InfiniBot's role is positioned above roles it needs to assign
- **Permission Check** - Verify InfiniBot can manage the roles you want to include

## Legacy Feature Note

Reaction Roles are a legacy feature. For a more modern alternative with enhanced UI and functionality, consider using [Role Messages](Role-Messages.md) instead.

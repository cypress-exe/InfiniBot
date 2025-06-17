---
title: AutoBans
nav_order: 5
parent: Additional Features
---

# AutoBans
{: .no_toc }

InfiniBot's AutoBans feature allows administrators to automatically ban members when they join your server, even before they've ever joined. This powerful moderation tool helps prevent known troublemakers from disrupting your community.

{: .warning }
This is a powerful moderation tool. Use with caution as banned members cannot join your server until the autoban is revoked.

**Topics Covered**
- TOC
{:toc}

## How AutoBans Work

The AutoBans system works by:
1. **Pre-emptive Protection**: Ban users before they even attempt to join your server
2. **Automatic Join Enforcement**: When a user with an active autoban tries to join your server, InfiniBot immediately detects their user ID and bans them upon entry
3. **ID Entry**: Add autobans using Discord user IDs for users who haven't joined yet

{: .note }
The automatic enforcement happens instantly when the banned user joins. InfiniBot monitors all server join events and cross-references new member IDs against your autoban list.

## Permission Requirements

To use AutoBans, you need:
- The **[InfiniBot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)** role
- InfiniBot must have **Ban Members** permission in your server

## Accessing AutoBans

1. Use `/dashboard` in your server
2. Navigate to the **AutoBans** section
3. Configure your autoban settings

## Adding AutoBans

1. Access the AutoBans dashboard using `/dashboard`
2. Navigate to the **AutoBans** section
3. Click **"Add"**
4. Follow the instructions to enable Developer Mode in Discord
5. Copy the target user's Discord ID
6. Enter their Discord name (optional) and ID
7. Confirm the autoban

## Getting Discord User IDs

To manually add someone by their Discord ID:

### On Desktop
1. Go to Discord's **Settings**
2. Scroll down to **"Advanced"**
3. Enable **"Developer Mode"**
4. Exit Settings
5. Right-click on the user you want to autoban
6. Click **"Copy ID"** (at the very bottom)

### On Mobile
1. Go to Discord's **Settings** (profile icon in bottom right)
2. Scroll down to **"Appearance"**
3. Enable **"Developer Mode"**
4. Exit Settings
5. Touch and hold on the user you want to autoban
6. Click the three dots in the top right of their profile
7. Click **"Copy ID"**

## Managing AutoBans

### Viewing Current AutoBans
The AutoBans dashboard shows:
- List of all active autobans
- Discord names (if provided)
- User IDs for each autobanned user

### Revoking AutoBans
1. Access the AutoBans dashboard
2. Click **"Revoke"**
3. Select the user from the list
4. Click **"Revoke AutoBan"**
5. The user will be able to join your server normally

## How AutoBans Trigger

When a user joins your server:
1. InfiniBot checks if their Discord ID matches any autoban entries
2. If a match is found, the user is **immediately banned**
3. The ban happens automatically without manual intervention
4. Server logs will show the ban was performed by InfiniBot

## Use Cases

AutoBans are particularly useful for:
- **Known troublemakers** who have caused problems in other servers
- **Alt accounts** of previously banned users
- **Coordinated harassment** from multiple accounts
- **Preventing raids** by banning known raid participants

## Important Limitations

### User Already in Server
- If someone is already in your server, you cannot add them as an autoban
- You must use regular ban commands for current members
- InfiniBot will notify you if you try to autoban an existing member

### User Already Banned
- If someone is already banned from your server, autoban is unnecessary
- InfiniBot will notify you if you try to autoban an already-banned user

### Permission Requirements
- InfiniBot must have **Ban Members** permission
- Autoban feature will be disabled if this permission is missing
- Users without **InfiniBot Mod** role cannot manage autobans

## Best Practices

### Documentation
- **Keep records** of why each autoban was added
- **Regular review** of your autoban list to remove outdated entries
- **Team coordination** to avoid duplicate or conflicting bans

### Verification
- **Double-check user IDs** before adding autobans
- **Verify the correct user** to avoid mistaken bans
- **Test with alt accounts** if unsure about the process

### Moderation Guidelines
- **Use sparingly** - autobans are for serious cases
- **Consider warnings first** for minor infractions
- **Document decisions** for transparency with your moderation team

## Automatic Enforcement

When a user with an active autoban attempts to join your server:

1. **Join Detection**: InfiniBot monitors all member join events in real-time
2. **ID Verification**: The new member's Discord ID is immediately checked against your server's autoban list
3. **Instant Action**: If a match is found, InfiniBot executes the ban within seconds of the user joining
4. **List Cleanup**: The autoban entry is automatically removed from your list since it's no longer needed
5. **Audit Logging**: The automatic ban is logged for moderation review

{: .highlight }
The automatic enforcement system works 24/7, even when moderators are offline. This ensures your server stays protected around the clock.

### What Happens During AutoBan Enforcement
- The banned user is immediately removed from your server
- They receive Discord's standard ban notification
- The action appears in your server's audit log
- **The autoban entry is automatically removed** from your autoban list (since it's no longer needed)
- No manual moderator intervention is required

## Troubleshooting

### AutoBans Not Working
- Verify InfiniBot has **Ban Members** permission
- Check that the feature isn't globally disabled
- Ensure user IDs are correct (numbers only)

### Can't Add AutoBan
- User might already be in the server (use regular ban instead)
- User might already be banned (autoban unnecessary)
- Check you have **InfiniBot Mod** role

### Context Menu Not Showing
- Verify you have ban permissions in the server
- Check that InfiniBot has necessary permissions
- Ensure the feature is enabled in your server

## Safety Considerations

AutoBans are irreversible once triggered - banned users cannot join until the autoban is manually revoked. Always:
- **Verify user identity** before adding autobans
- **Keep your team informed** about active autobans
- **Review periodically** to remove outdated entries

---

**Related Pages:**
- [Dashboard]({% link docs/core-features/dashboard.md %}) - Main configuration interface
- [Moderation]({% link docs/core-features/moderation/index.md %}) - Additional moderation tools
- [Commands Overview]({% link docs/getting-started/commands.md %}) - See all available commands
- [Install and Setup]({% link docs/getting-started/install-and-setup.md %}) - Setting up permissions

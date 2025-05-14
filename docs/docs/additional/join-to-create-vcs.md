---
title: Join to Create VCs
nav_order: 2
parent: Additional Features
---

# Join to Create VCs
{: .no_toc }

The Join to Create VCs feature allows members to create their own temporary voice channels automatically.

{: .tip }
This feature helps maintain a clean server by automatically creating and removing voice channels as needed, while giving members control over their voice chat experience.

**Topics Covered**
- TOC
{:toc}

## How It Works

1. Members join a designated "hub" voice channel
2. InfiniBot automatically creates a new voice channel named after them
3. The member is moved to their new voice channel
4. When everyone leaves the channel, it's automatically deleted

## Setup

1. Access via: `/dashboard → Join-To-Create VCs`
2. Click **Add Channel**
3. Select an existing voice channel to designate as the "hub"

You can set up multiple hub channels throughout your server.

## Managing Join to Create VCs

### Adding Hub Channels

1. Click **Add Channel** in the dashboard
2. Select a voice channel from the dropdown
3. Click **Add**

### Removing Hub Channels

1. Click **Delete Channel** in the dashboard
2. Select the hub channel you want to remove
3. Click **Delete**

## Required Permissions

For this feature to work properly, InfiniBot needs:
- **Manage Channels** - To create and delete voice channels
- **Move Members** - To move members into their new channels
- **Connect** - To access voice channels
- **View Channels** - To see the channels

## Temporary Channel Behavior

When a temporary channel is created:
- It's placed in the same category as the hub channel
- It's named "[Username] Vc" (e.g., "John Vc")
- It has the same permissions as the hub channel
- It's automatically deleted when empty

## Use Cases

Join to Create VCs are perfect for:
- Gaming servers where groups need separate channels
- Study servers with breakout rooms
- Community servers that want to reduce channel clutter
- Events where multiple voice discussions happen simultaneously

## Troubleshooting

If channels aren't being created properly:

1. **Check Permissions** - Ensure InfiniBot has the necessary permissions (Manage Channels, Move Members)
2. **Category Limits** - Make sure the category hasn't reached Discord's 50 channel limit
3. **Hub Channel** - Verify the hub channel still exists and is configured correctly

## Best Practices

- **Clear Naming** - Name your hub channel something descriptive like "➕ Create Voice Channel"
- **Channel Description** - Add a channel description explaining how to use it
- **Category Organization** - Place hub channels in appropriate categories
- **Permission Setup** - Ensure the category permissions are set correctly for created channels

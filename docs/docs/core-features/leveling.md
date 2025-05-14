---
title: Leveling
nav_order: 3
parent: Core Features
---

# Leveling
{: .no_toc }

InfiniBot's leveling system provides an engaging way to reward active members in your community.

{: .tip }
Leveling encourages participation and creates friendly competition in your server, increasing overall engagement.

**Topics Covered**
- TOC
{:toc}

## How Leveling Works

Members earn experience points (XP) through server activity:
- Sending messages
- Participating in voice channels
- Other interactions

As members accumulate XP, they level up at certain thresholds. Each level requires progressively more XP.

## Setup

1. Access via: `/dashboard → Leveling`
2. Enable the feature with the **Enable** button (if applicable)
3. Configure your settings:
   - Level-up notification settings
   - Level rewards

## Commands

- `/leaderboard` - View the server's leaderboard and top members
- `/view level [member]` - View your own level or another member's level
- `/set level @member <level>` - Set a specific member's level (Requires **[InfiniBot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)**)

## Level-Up Notifications

When enabled, InfiniBot sends level-up messages when members reach new levels:
- Messages can be sent in a designated channel
- Set a custom level-up message

### Configuring Level-Up Notifications

1. Access via: `/dashboard → Leveling`
2. Choose where to send notifications: `/dashboard → Leveling → Notifications Channel`
   - System channel
   - Specific channel
3. Customize the message: `/dashboard → Leveling → Level-Up Message`

{: .tip }
Utilize the [generic replacements]({% link docs/messaging/generic-replacements.md %}) available with InfiniBot.

## Level Rewards

Automatically award roles when members reach specific levels:

1. Access via: `/dashboard → Leveling → Level Rewards`
2. Click **Create**
3. Select the level and role to award
> Note: InfiniBot automatically removes roles assigned as Level Rewards from members who do not meet the level requirement.

### Managing Level Rewards

- **Create** - Addd a level reward
- **Delete** - Delete a level reward (Does not delete the Discord role)
- **Delete All Level Rewards** - Instantly clear all level rewards (does not delete the Discord roles)

## Anti-Spam Protection

InfiniBot has built-in protections to prevent XP farming:
- Cooldown periods between XP gains
- Automatic detection of spam messages
- Moderation integration

## Member Profile Level Cards

Members can personalize their level-up notifications with [custom cards](./Profile.md#level-up-card).

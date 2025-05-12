# Leveling

InfiniBot's leveling system provides an engaging way to reward active members in your community.

## How Leveling Works

Members earn experience points (XP) through server activity:
- Sending messages
- Participating in voice channels
- Other interactions

As members accumulate XP, they level up at certain thresholds. Each level requires progressively more XP.

## Setup

1. Access via: `/dashboard → Leveling`
2. Enable the feature with the **Enable Leveling** button
3. Configure your settings:
   - XP rates
   - Level-up notification settings
   - Role rewards

## Commands

- `/leaderboard` - View the server's leaderboard and top members
- `/view level [member]` - View your own level or another member's level
- `/set level @member <level>` - Set a specific member's level (Requires **InfiniBot Mod**)

## Level-Up Notifications

When enabled, InfiniBot sends level-up messages when members reach new levels:
- Messages can be sent in a designated channel
- Set a custom level-up message

### Configuring Level-Up Notifications

1. Access via: `/dashboard → Leveling → Level-Up Messages`
2. Choose where to send notifications:
   - System channel
   - Specific channel
3. Customize the message

## Role Rewards

Automatically award roles when members reach specific levels:

1. Access via: `/dashboard → Leveling → Level Rewards`
2. Click **Add Level Reward**
3. Select the level and role to award
4. Choose whether previous rewards are removed

### Managing Role Rewards

- **Edit Reward** - Change the level or role for an existing reward
- **Remove Reward** - Delete a role reward
- **View Rewards** - See a list of all configured rewards

## Anti-Spam Protection

InfiniBot has built-in protections to prevent XP farming:
- Cooldown periods between XP gains
- Automatic detection of spam messages
- Moderation integration

## Member Profile Level Cards

Members can personalize their level-up notifications with custom cards:

1. Access via: `/profile → Level-Up Card`
2. Enable/disable personal level-up cards
3. Customize card text and color

These cards will be included with level-up notifications, adding personalization to the leveling experience.

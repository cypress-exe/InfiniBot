---
title: Commands
nav_order: 2
parent: Getting Started
---

# Commands Overview
{: .no_toc }

This page lists all available slash commands in InfiniBot, organized by command group.

**Topics Covered**
- TOC
{:toc}

## General Commands

- `/help` - View InfiniBot's online wiki documentation
- `/about` - View bot version, repository, and documentation links
- `/leaderboard` - Get the leveling leaderboard for the server
- `/motivational_statement` - Receive a randomized motivational statement
- `/joke` - Receive a randomized joke
- `/check_infinibot_permissions ` - InfiniBot will run a check to verify its permissions.

## Configuration Commands

- `/dashboard` - Configure InfiniBot using the interactive Dashboard UI (Requires **[Infinibot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)**)
- `/profile` - Configure your InfiniBot Profile
- `/onboarding` - Configure InfiniBot via the Onboarding Wizard (Requires **[Infinibot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)**)

## DM Commands

Commands available in direct messages with InfiniBot:
- `/opt-into-dms` — Opt into receiving DM notifications from InfiniBot (level-ups, birthday wishes, etc.)
- `/opt-out-of-dms` — Opt out of receiving DM notifications from InfiniBot

## View Commands

Commands for viewing information (Server only):
- `/view my-strikes` — View your profanity strikes
- `/view member-strikes @member` — View another member's strikes (Requires **[Infinibot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)**)
- `/view level [member]` — View your or another member's leveling info

## Set Commands

Commands for configuring settings (Server only, Requires **[Infinibot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)**):
- `/set admin-channel` — Set the channel where moderation strikes are logged
- `/set log-channel` — Set the channel for general action logging
- `/set level @member <level>` — Set a specific member's level

## Create Commands

Commands to create or initialize features (Server only, Requires **[Infinibot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)** and sometimes some extra permissions):
- `/create infinibot-mod-role` — Create the **[Infinibot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)** role
- `/create reaction-role <Letters|Numbers> [mention-roles]` — Create a legacy reaction roles message
- `/create custom-reaction-role <emoji mapping> [mention-roles]` — Create a custom reaction role message
- `/create embed [role]` — Create and send a custom embed
- `/create role_message` — Launch the Role Message wizard

## Purge Commands

Commands for message deletion (Server only, Requires **[Infinibot Mod]({% link docs/getting-started/install-and-setup.md %}#the-infinibot-mod-role)** and some extra permissions):
- `/purge <amount>` — Delete a specific number of messages from the current channel
- `/purge all` — Clear all messages by recreating the channel with the same settings

---
*Note: Some commands require specific permissions or feature activation. Refer to individual feature pages for details.*

---
title: Profile
nav_order: 4
parent: Core Features
---

# Profile
{: .no_toc }

InfiniBot's Profile feature allows members to customize their personal settings and cards for a more personalized experience.

{: .titleless-green }
Profiles add a personal touch to the user experience, making your server feel more unique and engaging for members.

**Topics Covered**
- TOC
{:toc}

## Accessing Your Profile

Use the `/profile` command to open your personal profile settings menu.

## Profile Features

The profile menu contains several customization options:

### Level-Up Card

Level-up cards are personalized messages that appear when you level up.

1. Click **Level-Up Card** in the profile menu
2. Choose from these options:
   - **Enable/Disable** - Toggle whether you use a level card
   - **Change Text** - Customize the title and description
   - **Change Color** - Select a color for your card

{: .tip }
Utilize the [generic replacements]({% link docs/messaging/generic-replacements.md %}) available with InfiniBot for your Level-Up Card's text.

### Join Card

Join cards are personalized messages that appear when you join a server (if the server has enabled join cards).

1. Click **Join Card** in the profile menu
2. Choose from these options:
   - **Enable/Disable** - Toggle whether you use a join card
   - **Change Text** - Customize the title and description
   - **Change Color** - Select a color for your card

{: .tip }
Utilize the [generic replacements]({% link docs/messaging/generic-replacements.md %}) available with InfiniBot for your Join Card's text.

### Settings

The settings section lets you adjust general profile preferences.

1. Click **Settings** in the profile menu
2. Options available:
   - **Direct Messages** - Enable/disable direct messages from InfiniBot
   - **Delete My Data** - Delete your data and configurations from InfiniBot

#### Data Deletion
This button deletes all your profile information associated with InfiniBot. This action isn't reversable.

{: .warning }
Note: This will not delete:  
• Any message logs inside a server  
• Any moderation strikes, levels, birthdays, infinibot-powered messages, etc in any server  

Some information not deleted by this process may be deleted when you leave a server. Check InfiniBot's [Privacy Policy]({% link docs/legal/privacy-policy.md %}) for complete transparency and more information.

## DM Notifications

InfiniBot may send you direct messages for:
- Level-up notifications
- Birthday wishes
- InfiniBot errors and missing permissions (server-owner only)

You can opt out of these messages using the **Direct Messages** button.

## Privacy Considerations

- Your profile information is only visible to you
- Level cards are visible to other members when you level up
- Join cards are visible to server members when you join a server that has enabled join cards

## Troubleshooting

If you're not receiving level-up or join card messages:
1. Check if you've enabled your level-up card in `/profile`
2. Verify that the server has level-up notifications or join cards enabled

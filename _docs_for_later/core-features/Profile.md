# Profile

InfiniBot's Profile feature allows members to customize their personal settings and cards for a more personalized experience.

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

#### Customizing Level-Up Card Text

When changing text, you can use:
- **Title** - The main heading for your card
- **Description** - The message body

In addition to the [generic replacements](./Generic-Replacements.md) for InfiniBot's messages, level-up cards provide additional replacements, including:
- `[level]` - The new level of the member

Example: "I reached level [level]! Awesome!"

### Join Card

Join cards are personalized messages that appear when you join a server (if the server has enabled join cards).

1. Click **Join Card** in the profile menu
2. Choose from these options:
   - **Enable/Disable** - Toggle whether you use a join card
   - **Change Text** - Customize the title and description
   - **Change Color** - Select a color for your card

#### Customizing Join Card Text

When changing text, you can use:
- **Title** - The main heading for your card
- **Description** - The message body

Utilize the [generic replacements](../messaging/Generic-Replacements.md) available with InfiniBot.

### Settings

The settings section lets you adjust general profile preferences.

1. Click **Settings** in the profile menu
2. Options available:
   - **Direct Messages** - Enable/disable direct messages from InfiniBot
   - **Delete My Data** - Delete your data and configurations from InfiniBot

#### Data Deletion
This button deletes all your profile information associated with InfiniBot. This action isn't reversable.

> Note: This will not delete:  
> • Any message logs inside a server  
> • Any moderation strikes, levels, birthdays, infinibot-powered messages, etc in any server  

Some information not deleted by this process may be deleted when you leave a server. Check InfiniBot's privacy policy for complete transparency and more information.

Refer to InfiniBot's [Privacy Policy](../legal/Privacy-Policy.md) for details on how InfiniBot handles your data.

## DM Notifications

InfiniBot may send you direct messages for:
- Level-up notifications
- Birthday wishes
- Important server announcements

You can opt out of these messages using the **Direct Messages** button.

## Privacy Considerations

- Your profile information is only visible to you
- Level cards are visible to other members when you level up
- Join cards are visible to server members when you join a server that has enabled join cards

## Troubleshooting

If you're not receiving level-up or join card messages:
1. Check if you've disabled DMs in your profile settings
2. Verify that the server has level-up notifications or join cards enabled
3. Make sure your privacy settings allow messages from server members

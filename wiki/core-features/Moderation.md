# Moderation

InfiniBot offers comprehensive moderation tools to keep your server safe and friendly.

## Profanity Moderation

Profanity moderation automatically monitors messages for inappropriate language and takes action when violations occur.

### Setup

1. Access via: `/dashboard → Moderation → Profanity`
2. Enable the feature with the **Enable Profanity Moderation** button
3. Configure the following settings:
   - **Strike System Active** - Toggle whether users accumulate strikes
   - **Max Strikes** - Set how many strikes trigger a timeout
   - **Timeout Duration** - Set how long timeouts last
   - **Strike Expire Time** - Set how long before strikes automatically expire

### Filtered Words

1. Access via: `/dashboard → Moderation → Profanity → Filtered Words`
2. View the current list of filtered words
3. Add new words to the filter
4. Remove words from the filter

InfiniBot automatically detects variations of these words, including simple letter replacements and misspellings.

### Admin Channel

The admin channel receives notifications when members use profane language:

1. Create a private channel visible only to moderators
2. Use `/set admin-channel` in that channel
3. Strikes will be reported here, along with message content

### Strike Management

From the Admin Channel:
- View the original deleted message
- Mark strikes as incorrect (refunding them to the member)
- Review strike information

Users can check their own strikes with `/view my-strikes`
Moderators can check any member's strikes with `/view member-strikes @member`

## Spam Moderation

Spam moderation automatically detects and handles message spam.

### Setup

1. Access via: `/dashboard → Moderation → Spam`
2. Enable the feature with the **Enable Spam Moderation** button
3. Configure the following settings:
   - **Score Threshold** - How much spam activity triggers a timeout
   - **Time Threshold** - Time window for monitoring spam (in seconds)
   - **Delete Messages** - Whether to delete spam messages
   - **Notify User** - Whether to notify users when they're timed out for spam

### How Spam Detection Works

InfiniBot calculates a spam score based on:
- Repetitive messages
- Message frequency
- Similar content posting
- Same image posting
- All-caps messages

When a user exceeds the score threshold, they receive a strike or timeout based on your configuration.

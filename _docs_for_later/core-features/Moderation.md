# Moderation

InfiniBot offers comprehensive moderation tools to keep your server safe and friendly.

## Profanity Moderation

Profanity moderation automatically monitors messages for inappropriate language and takes action when violations occur.

### Setup

1. Access via: `/dashboard → Moderation → Profanity`
2. Enable the feature with the **Enable** button (if applicable)
3. Configure the following settings:
   - **Manage Strike System** - Manage the strike system
      + **Manage Members** - Manage each member's strikes
      + **Maximum Strikes** - Configure the maximum number of strikes before automatic timeout
      + **Strike Expire Time** - Optionally set how long before strikes automatically expire
   - **Timeout Duration** - Set how long timeouts last
   - **Admin Channel** - Configure which channel recieves moderation logs

### Filtered Words

1. Access via: `/dashboard → Moderation → Profanity → Filtered Words`
2. View the current list of filtered words
3. Add new words to the filter
4. Remove words from the filter

InfiniBot automatically detects variations of these words, including simple letter replacements and misspellings.

For detailed information about the advanced pattern matching rules in the word filter, see the [Filtered Words](Filtered-Words.md) page.

### Testing Your Filters

Use the Test button to ensure your word filters work as expected:

1. Access via: `/dashboard → Moderation → Profanity → Filtered Words → Test`
2. Enter sample text that might trigger your filters
3. Check if the results match your expectations
4. Adjust your filter patterns as needed

This helps you avoid false positives while still catching problematic content.

### Admin Channel

The admin channel receives notifications when members use profane language:

1. Create a private channel visible only to moderators
2. Configure the admin channel by using `/set admin-channel` in the desired channel or through the dashboard.
3. Strikes will be reported here, along with message content and overriding capabilities

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
2. Enable the feature with the **Enable** button (if applicable)
3. Configure the following settings:
   - **Timeout Duration** - How long to timeout users who InfiniBot detects spamming
   - **Spam Score Threshold** - How much spam activity triggers a timeout. 
   - **Time Threshold** - Time window for monitoring spam (in seconds)

#### What is Spam Score
InfiniBot uses a spam score system to determine if a message is spam. The higher the score, the more likely the user is participating in spam.
Increase this value if InfiniBot is misclassifying messages as spam often. Decrease it if InfiniBot is not detecting spam enough.

#### What is Time Threshold
InfiniBot will disregard messages outside of the time threshold when determining spam scores. To disable this feature, set the time threshold to 0.

### How Spam Detection Works

InfiniBot calculates a spam score based on:
- Repetitive messages
- Message frequency
- Similar content posting
- Same image posting
- All-caps messages

When a user exceeds the score threshold, they receive a strike or timeout based on your configuration.

---

**Related Pages:**
- [Filtered Words](Filtered-Words.md) - Advanced word filtering patterns
- [Logging](Logging.md) - Tracking moderation actions
- [Dashboard](Dashboard.md) - Managing moderation settings

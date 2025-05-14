---
title: Spam
nav_order: 2
parent: Moderation
grand_parent: Core Features
---

# Spam Moderation
{: .no_toc }

Spam moderation automatically detects and handles message spam.

{: .warning }
Spam protection is essential for preventing raids and maintaining channel quality. Configure this to protect your server from spam attacks.

**Topics Covered**
- TOC
{:toc}

## Setup

1. Access via: `/dashboard → Moderation → Spam`
2. Enable the feature with the **Enable** button (if applicable)
3. Configure the following settings:
   - **Timeout Duration** - How long to timeout users who InfiniBot detects spamming
   - **Spam Score Threshold** - How much spam activity triggers a timeout. 
   - **Time Threshold** - Time window for monitoring spam (in seconds)

### What is Spam Score
InfiniBot uses a spam score system to determine if a message is spam. The higher the score, the more likely the user is participating in spam.
Increase this value if InfiniBot is misclassifying messages as spam often. Decrease it if InfiniBot is not detecting spam enough.

### What is Time Threshold
InfiniBot will disregard messages outside of the time threshold when determining spam scores. To disable this feature, set the time threshold to 0.

## How Spam Detection Works

InfiniBot calculates a spam score based on:
- Repetitive messages
- Message frequency
- Similar content posting
- Same image posting
- All-caps messages

When a user exceeds the score threshold, they receive a strike or timeout based on your configuration.

---

**Related Pages:**
- [Profanity Filter]({% link docs/core-features/moderation/profanity/index.md %}) - Text content moderation
- [Logging]({% link docs/core-features/logging.md %}) - Monitor moderation actions
- [Dashboard]({% link docs/core-features/dashboard.md %}) - Configure moderation settings
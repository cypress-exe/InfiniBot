---
title: Filtered Words
nav_order: 1
parent: Profanity
grand_parent: Moderation
---

# Filtered Words
{: .no_toc }

InfiniBot uses an advanced word filtering system that helps you maintain a clean and safe server environment.

{: .titleless-green }
The filter system is highly customizable, allowing you to add server-specific words and phrases while maintaining strong default protections.

**Topics Covered**
- TOC
{:toc}

## Pattern Matching Options

InfiniBot offers sophisticated word filtering with several pattern matching rules. To edit your server's filtered words:
1. Access via: `/dashboard → Moderation → Profanity → Filtered Words`
2. View the current list of filtered words
3. Configure filtered words:
   - **Add Word** - Add new words to the filter (up to 150 total words)
   - **Delete Word** - Remove words from the filter
   - **Test** - Verify your patterns work as expected
   - **Reset to Defaults** - Clear all custom words and start fresh

{: .titleless-blue }
**Word Limit**: Your server can have up to **150 filtered words** total. If you try to add words that would exceed this limit, InfiniBot will add as many as possible and inform you about any that couldn't be added.

### Adding Multiple Words

When adding words, you can:
- Add single words: `badword`
- Add multiple words at once: `badword1, badword2, badword3`
- Mix patterns: `"exact", partial*, wild?card`

**Validation Rules:**
- Words must be 1-50 characters long
- No duplicate words allowed
- Cannot exceed the 150 word limit
- Empty words are automatically rejected

If some words are valid and others have issues, InfiniBot will add the valid ones and show you which words couldn't be added and why.

### 1. Boundary Control with Quotes

Use quotes to lock matches to specific positions:

| Pattern | Valid Matches | Invalid Matches |
|---------|--------------|-----------------|
| `"test` | "test**ing**", "test**2023**" | "**con**test", "**re**test" |
| `test"` | "**con**test", "**123**test" | "test**ing**", "test**ed**" |
| `"test"` | Exact word "test" only | Any partial matches |


### 2. Wildcard Characters
{: .mt-8 }
Control character matching precision:

| Symbol | Matches | Example | Valid Matches | Invalid Matches |
|--------|---------|---------|--------------|-----------------|
| `*` | 1 character | `te*st` | "te**x**st", "te**5**st" | "test", "trst" |
| `?` | 0-1 characters | `log?n` | "login", "logn" | "log**o**n", "log**g**n" |

### 3. Advanced Pattern Building
{: .mt-8 }
Combine elements for complex matching:

**Example 1: Hybrid Pattern**  
`"t?st*"` matches:
- "test4" (exact start + 1 wildcard)
- "tst5" (0-1 missing char + 1 wildcard)

**Example 2: Word Protection**  
Prevent false matches in larger words:  
`"cat"` blocks "cat" but not "category" or "copycat"

## Technical Implementation

- **Case Insensitivity**: All matches ignore capitalization (`TEST` = `test` = `TesT`)
- **Special Characters**: Handles `!@#$%^&*()` as valid characters
- **Regex Conversion**:
  - `test` → `\w*test\w*` (any occurrence)
  - `"test"` → `\btest\b` (exact word)
  - `t?st` → `\w*t.?st\w*` (0-1 char wildcard)

## Testing Your Filters

InfiniBot provides a "Test" button in the dashboard that allows you to verify your filter patterns before implementing them. This helps ensure you're not inadvertently blocking legitimate speech while still catching problematic content.

To test your filters:
1. Access via: `/dashboard → Moderation → Profanity → Filtered Words → Test`
2. Enter sample text that should or shouldn't match your rules
3. View the results to see which patterns are triggered
4. Adjust your patterns as needed

## Resetting Your Filter List

If you want to start over with your filtered words:

1. Access via: `/dashboard → Moderation → Profanity → Filtered Words → Reset to Defaults`
2. Confirm the action in the warning dialog
3. All custom filtered words will be permanently removed

{: .titleless-red }
**Warning**: This action cannot be undone! Make sure you have a backup of any important custom words before resetting.

## Troubleshooting Common Issues

**Q: Why does `apple` match "pineapple"?**  
**A:** Use `"apple"` to enforce exact word matching or `"apple` to match only words starting with "apple".

**Q: How to match both "color" and "colour"?**  
**A:** Use `colou?r` (0-1 character after `u`).

**Q: Can I filter numbers in matches?**  
**A:** Yes! Numbers are supported natively: `test3` matches "TEST3", "Test3!", etc.

## Pattern Design Tips

1. Start strict: Use `"word"` first, relax with wildcards as needed
2. Test patterns with numbers/symbols: `t3st*` catches "t3st4"
3. Combine boundaries and wildcards: `"bad*word"` blocks "bad-word" but not "mybad-word"
4. When in doubt, use the Test button to verify your patterns work as expected

---

**Related Pages:**
- [Moderation]({% link docs/core-features/moderation/index.md %}) - Main moderation features overview
- [Dashboard]({% link docs/core-features/dashboard.md %}) - Managing word filter settings
- [Logging]({% link docs/core-features/logging.md %}) - Tracking filtered messages

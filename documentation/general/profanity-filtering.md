# InfiniBot Profanity Filter Help & Docs

## Pattern Matching Guide

### 1. Boundary Control with Quotes
Use quotes to lock matches to specific positions:

| Pattern   | Valid Matches          | Invalid Matches      |
|-----------|------------------------|----------------------|
| `"test`   | "testing", "test2023"  | "contest", "retest"  |
| `test"`   | "contest", "123test"   | "testing", "tested"  |
| `"test"`  | Exact word "test" only | Any partial matches  |

### 2. Wildcard Types
Control character matching precision:

| Symbol | Matches          | Example | Valid Matches       | Invalid Matches    |
|--------|------------------|---------|---------------------|--------------------|
| `*`    | 1 character      | `te*st` | "texst", "te5st"    | "test", "trst"     |
| `?`    | 0-1 characters   | `log?n` | "login", "logn"     | "logon", "loggn"   |

### 3. Advanced Pattern Building
Combine elements for complex matching:

**Example 1: Hybrid Pattern**  
`"t?st*"` matches:
- "test4" (exact start + 1 wildcard)
- "tst5" (0-1 missing char + 1 wildcard)

**Example 2: Word Protection**  
Prevent false matches in larger words:  
`"cat"` blocks "cat" but not "category" or "copycat"

### 4. Technical Implementation
- **Case Insensitivity**: All matches ignore capitalization (`TEST` = `test` = `TesT`)
- **Special Characters**: Handles `!@#$%^&*()` as valid characters
- **Regex Conversion**:
  - `test` → `\w*test\w*` (any occurrence)
  - `"test"` → `\btest\b` (exact word)
  - `t?st` → `\w*t.?st\w*` (0-1 char wildcard)

## Troubleshooting Common Issues

**Q: Why does `apple` match "pineapple"?**  
**A:** Use `"apple` to enforce start boundary matching.

**Q: How to match both "color" and "colour"?**  
**A:** Use `colou?r` (0-1 character after `u`).

**Q: Numbers in matches?**  
**A:** Supported natively: `test3` matches "TEST3", "Test3!", etc.

## Pattern Design Tips
1. Start strict: Use `"word"` first, relax with wildcards as needed
2. Test patterns with numbers/symbols: `t3st*` catches "t3st4"
3. Combine boundaries and wildcards: `"bad*word"` blocks "bad-word" but not "mybad-word"
---
title: Bot Information
nav_order: 6
parent: Additional Features
---

# Bot Information
{: .no_toc }

The `/about` command provides comprehensive information about your InfiniBot instance, including version details, repository links, and documentation resources.

**Topics Covered**
- TOC
{:toc}

## Command Usage

Use `/about` to display detailed information about InfiniBot.

**Usage:**
```
/about
```

This command can be used in any server where InfiniBot is present.

## Information Provided

The `/about` command displays:

### Version Information
- **Current commit hash** - The exact version of InfiniBot running
- **Latest change** - Description of the most recent update

### Repository Links
- **GitHub Repository** - Link to the main InfiniBot repository
- **Latest Commit** - Direct link to view the current commit on GitHub

### Documentation & Support
- **Full Documentation** - Link to the complete InfiniBot documentation
- **Getting Started Guide** - Quick start resources for new users
- **Support Server** - Join the official support Discord server
- **Issue Reporting** - Direct link to report bugs or request features

## Technical Details

The command automatically detects:
- Git commit information from the running instance
- Repository URL from git configuration
- Current deployment version

If git information is unavailable, the command provides fallback links to the main repository.

## Permissions Required

No special permissions are required to use `/about`. Any user can run this command in any server where InfiniBot is present.

---

**Related Pages:**
- [Commands Overview]({% link docs/getting-started/commands.md %}) - See all available commands
- [Support]({% link docs/getting-started/support.md %}) - Getting help with InfiniBot
- [How to Support]({% link docs/how-to-support.md %}) - Supporting InfiniBot development

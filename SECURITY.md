# Security Policy

## Supported Versions

InfiniBot is deployed as a single rolling release rather than maintained
across multiple version branches. Only the latest version on the `main`
branch (as run by the official InfiniBot service) receives security fixes.

| Version         | Supported          |
| --------------- | ------------------- |
| Latest (`main`) | :white_check_mark:  |
| Older releases  | :x:                  |

If you're self-hosting, please stay up to date with `main` to receive
security patches.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub
issues, discussions, or the Discord server.**

Instead, please report them using one of the following private channels:

1. **GitHub Security Advisories (preferred)** - Use the
   [Report a vulnerability](https://github.com/cypress-exe/InfiniBot/security/advisories/new)
   form on this repository. This creates a private advisory visible only to
   maintainers until it's resolved.
2. **Direct message on Discord** - Contact `cypress.exe` directly on the
   [InfiniBot support server](https://discord.gg/mWgJJ8ZqwR) if you don't
   have GitHub access or need a faster response.

When reporting, please include as much of the following as you can:

- A description of the vulnerability and its potential impact
- Steps to reproduce, or a proof of concept
- The affected component (e.g. a specific cog, the config system, the
  Docker setup) and version/commit hash
- Any suggested remediation, if you have one

## What to expect

- We aim to acknowledge reports within a few days.
- We'll keep you updated as we investigate and work on a fix.
- Once a fix is released, we'll credit you in the release notes (unless you
  prefer to remain anonymous).
- Please give us reasonable time to address the issue before any public
  disclosure.
  + If the issue is not addressed **within 90 days**, you may disclose it publicly.

## Scope

This policy covers the InfiniBot bot codebase in this repository. It does not 
cover third-party dependencies directly (please report those upstream) but let 
us know if a dependency vulnerability affects InfiniBot specifically, as we 
may need to update our pinned version.

Thank you for helping keep InfiniBot and its users safe.

## Source Disclosure
This document was generated with Claude Sonnet 5 and reviewed/edited by cypress.exe.
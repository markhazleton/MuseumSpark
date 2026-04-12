---
name: "devspark.specify"
description: "DevSpark command for specify"
---

## Prompt Resolution

Determine the current git user by running `git config user.name`.
Normalize to a folder-safe slug: lowercase, replace spaces with hyphens,
strip non-alphanumeric/hyphen chars.

Read and execute the instructions from the first file that exists:
1. .documentation/{git-user}/commands/devspark.specify.md
2. .documentation/commands/devspark.specify.md
3. .devspark/defaults/commands/devspark.specify.md

## User Input

{{input}}

Pass the user input above to the resolved prompt.

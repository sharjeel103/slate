# AI Agent Instructions for Slate PDF Annotator

Welcome to the Slate PDF Annotator workspace! If you are an AI assistant working in this repository, you must strictly adhere to the following rules at all times.

## 1. Skill Usage
You **must** use the `slate-development` skill (`/home/sharjeel/PROJECTS/pdf_annotator/.agents/skills/slate-development/SKILL.md`) for all development, testing, and packaging related to this project. Refer to it before making architectural changes or building the `.deb` package.

## 2. STRICT Git Operations Constraint
You are **STRICTLY DISALLOWED** from executing any editable git commands. 
- You must **NEVER** run commands like `git add`, `git commit`, `git push`, `git reset`, `git tag`, or `git checkout` under any circumstances.
- You are only permitted to use read-only commands (e.g., `git status`, `git diff`, `git log`).
- The user exclusively handles all commits, pushes, tags, and branch modifications. DO NOT attempt to commit or push code on behalf of the user.

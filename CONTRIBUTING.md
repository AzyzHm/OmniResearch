# Contributing to OmniResearch

Thanks for taking the time to contribute. OmniResearch is licensed under the [Apache License, Version 2.0](LICENSE); by submitting a contribution, you agree it will be licensed under those same terms. Please also read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

> **Note:** This is the `legacy/streamlit-mvp` branch, a frozen snapshot of OmniResearch's original Streamlit frontend. Active development happens on `main`; contributions here are limited to fixes/improvements scoped specifically to this legacy snapshot.

## Reporting an Issue

Before opening a new issue, please search existing issues to avoid duplicates.

Please use the [**Bug / Feature / Docs** issue template](.github/ISSUE_TEMPLATE/bug_feature_docs.md), it's applied automatically whenever you click "New Issue" in this repository, since it's the only template configured. It asks for:

- **Title:** `[Bug/Feature/Docs] Short, descriptive title`
- **Description:** a clear description of the issue, bug, or feature request
- **Steps to Reproduce** (bugs only): the exact steps needed to see the problem
- **Expected vs. Actual Result:** what should happen, versus what actually happens
- **Environment** (if applicable): OS, version, and any other relevant setup detail
- **How to Solve** (optional): a proposed fix or approach, if you have one

Filling in every section that applies makes it much faster to triage and fix. Leave a section blank if it genuinely doesn't apply (a feature request has no "Steps to Reproduce", for instance).

**Security vulnerabilities should not be reported as public issues.** See [`SECURITY.md`](SECURITY.md) instead.

## Submitting a Pull Request

1. Open an issue first for anything non-trivial, so the approach can be discussed before you put in the work.
2. Keep pull requests focused: one bug fix or one feature per PR, rather than bundling unrelated changes.
3. Follow the existing structure and conventions of whichever part of the codebase you're touching:
   - Backend: [`backend/docs/README.md`](backend/docs/README.md)
   - Frontend: [`frontend/docs/README.md`](frontend/docs/README.md)
4. Add or update tests for any behavior you change. Both the backend and frontend suites (both `pytest`) are expected to pass.
5. Describe what changed and why in the pull request description; link the issue it resolves if there is one.

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you're expected to uphold it, be respectful and constructive, disagreements about approach are fine and expected, personal attacks or harassment are not.
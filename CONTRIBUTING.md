# Contributing to OmniResearch

Thanks for taking the time to contribute. OmniResearch is licensed under the [Apache License, Version 2.0](LICENSE) by submitting a contribution, you agree it will be licensed under those same terms. Please also read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## Reporting an Issue

Before opening a new issue, please search existing issues to avoid duplicates.

Clicking "New Issue" in this repository offers three forms, pick whichever matches:

- **Bug Report:** description, steps to reproduce, expected vs. actual result, environment, and an optional proposed fix.
- **Feature Request:** the problem or motivation, your proposed solution, and any alternatives you considered.
- **Documentation:** the file or section affected, what's wrong or missing, and an optional suggested fix.

Each form asks which area it affects (backend, frontend, or both) so it reaches the right people faster. Filling in every field that applies makes it much faster to triage and fix.

**Security vulnerabilities should not be reported as public issues.** See [`SECURITY.md`](SECURITY.md) instead.

## Submitting a Pull Request

1. Open an issue first for anything non-trivial, so the approach can be discussed before you put in the work.
2. Keep pull requests focused: one bug fix or one feature per PR, rather than bundling unrelated changes.
3. Follow the existing structure and conventions of whichever part of the codebase you're touching:
   - Backend: [`backend/docs/README.md`](backend/docs/README.md)
   - Frontend: [`frontend/README.md`](frontend/README.md)
4. Add or update tests for any behavior you change. Both the backend (`pytest`) and frontend (`vitest`) suites are expected to pass.
5. Describe what changed and why in the pull request description; link the issue it resolves if there is one.

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you're expected to uphold it, be respectful and constructive, disagreements about approach are fine and expected, personal attacks or harassment are not.
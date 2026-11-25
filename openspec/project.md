# Project: img-proof

Automated cloud image testing framework and command-line utility.

## Conventions

- Spec-first development: specifications document observed behavior and system contracts.
- Requirements use RFC 2119 keywords (SHALL/MUST, SHOULD, MAY) and are verifiable.
- Every requirement carries at least one WHEN/THEN scenario header with four hashes (`#### Scenario:`).
- Capabilities are modular and orthogonal: CLI, test runner, cloud providers, distro support, and test discovery.
- Testing leverages Pytest and Testinfra over SSH channels.
- Multi-cloud abstraction isolates cloud framework API mechanics from test assertions.

## Purposes

1. Automate cloud image validation across multiple cloud providers (AWS EC2, Microsoft Azure, Google Compute Engine) and direct SSH hosts.
2. Support distribution-agnostic synchronization points including soft reboot, hard reboot, package updates, and repository refreshes.
3. Verify instance lifecycle stability, host key persistence, and guest configuration across reboots.
4. Capture execution logs, structured JSON results, and diagnostic VM system metrics.

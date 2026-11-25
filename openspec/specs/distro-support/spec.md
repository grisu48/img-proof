# Distro Support Specification

## Purpose
Specifies the guest Linux operating system distribution abstraction, init system detection,
package manager command generation, safe reboot execution, and boot diagnostics collection.
Ensures uniform system control whether running on SUSE or Red Hat family systems across
the multiverse.

## Requirements

### Requirement: Distribution Abstraction and Init Detection
The distribution module SHALL detect the guest system's active init system and provide
standard command execution wrappers.

#### Scenario: Detect systemd init
- **WHEN** the distro module inspects PID 1 on the guest via `ps -p 1 -o comm=`
- **THEN** it identifies whether the system runs `systemd` or a legacy init system, retrying up to 3 times on transient connection errors

#### Scenario: Init detection failure
- **WHEN** PID 1 command inspection fails across all retries
- **THEN** an `IpaDistroException` is raised describing the connection error

### Requirement: SUSE Distribution Family Support
The SUSE distribution classes (`SLES`, `SLE_Micro`, and `openSUSE_Leap`) SHALL supply
Zypper package management and service control commands.

#### Scenario: Zypper package installation command
- **WHEN** package installation is requested on a SUSE system
- **THEN** the module executes `zypper -n --no-gpg-checks in -y <package>`

#### Scenario: Zypper repo refresh command
- **WHEN** repository refresh is requested on a SUSE system
- **THEN** the module executes `zypper -n refresh`

#### Scenario: Zypper system update command
- **WHEN** system update is requested on a SUSE system
- **THEN** the module executes `zypper -n up --auto-agree-with-licenses --force-resolution --replacefiles`

#### Scenario: SUSE SSH service stop on systemd
- **WHEN** stopping the SSH service on a SUSE system running systemd
- **THEN** the module returns `systemctl stop sshd.service`

#### Scenario: SUSE SSH service stop on legacy init
- **WHEN** stopping the SSH service on a SUSE system running legacy init
- **THEN** the module returns `rcsshd stop`

### Requirement: Red Hat Distribution Family Support
The Red Hat distribution classes (`RedHat`, `RHEL`, and `Fedora`) SHALL supply
DNF package management and service control commands.

#### Scenario: DNF package installation command
- **WHEN** package installation is requested on a Red Hat or Fedora system
- **THEN** the module executes `dnf --assumeyes --nogpgcheck install <package>`

#### Scenario: DNF repo refresh command
- **WHEN** repository refresh is requested on a Red Hat or Fedora system
- **THEN** the module executes `dnf --assumeyes makecache`

#### Scenario: DNF system update command
- **WHEN** system update is requested on a Red Hat or Fedora system
- **THEN** the module executes `dnf --assumeyes upgrade`

#### Scenario: Red Hat SSH service stop on systemd
- **WHEN** stopping the SSH service on a Red Hat system running systemd
- **THEN** the module returns `systemctl stop sshd.service`

#### Scenario: Red Hat SSH service stop on legacy init
- **WHEN** stopping the SSH service on a Red Hat system running legacy init
- **THEN** the module returns `service sshd stop`

### Requirement: Bounded Execution Remote Reboot
The distribution module SHALL invoke reboots via a backgrounded subshell and enforce a
bounded execution join timeout to prevent SSH deadlocks.

#### Scenario: Clean reboot execution
- **WHEN** `reboot()` is called on an instance
- **THEN** a background command `sudo sh -c '(sleep 1 && <stop_ssh> && <reboot> &)' && exit` is dispatched in an open SSH session channel

#### Scenario: SSH channel deadlock prevention
- **WHEN** an instance reboot immediately terminates the underlying SSH socket before the command channel cleanly exits
- **THEN** the execution thread is bounded by a 30-second join timeout, after which the transport socket is force-closed to avoid hanging the process

#### Scenario: Cache invalidation on reboot
- **WHEN** a reboot command completes or times out
- **THEN** the SSH client cache is cleared to prevent reuse of dead connections

### Requirement: Guest Diagnostic Collection
The distribution module SHALL extract system performance and journal diagnostics from
systemd-based distributions.

#### Scenario: Collect systemd metrics
- **WHEN** VM diagnostics are collected on a systemd host
- **THEN** the module executes and aggregates output from `systemd-analyze --no-pager`, `systemd-analyze blame --no-pager`, and `sudo journalctl -b --no-pager`

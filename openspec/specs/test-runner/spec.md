# Test Runner Specification

## Purpose
Specifies the test execution orchestration engine that provisions instances, verifies
SSH connectivity and host keys, executes injection workloads, runs Pytest test suites,
handles synchronization points (reboots, updates), and records structured results.
Keeps the Serenity flying no matter what Reavers or cloud provider outages throw at it.

## Requirements

### Requirement: Test Execution Lifecycle
The test runner SHALL manage the end-to-end lifecycle of an image verification run,
including environment setup, test iteration, diagnostic capture, and results persistence.

#### Scenario: Full test execution flow
- **WHEN** `test_image()` is executed for a supported cloud and distribution
- **THEN** the runner determines the instance target, sets up results directories, updates the history log, runs configured test items and sync points, persists test results, and returns the exit status and results dictionary

#### Scenario: Results directory creation
- **WHEN** a test run begins
- **THEN** a unique directory is created under `results_dir` — `<provider>/<image_id>/<instance_id>` when testing an existing instance, or `<provider>/<instance_ip>` when a new instance was launched — containing `<timestamp>.log` and `<timestamp>.results` files

#### Scenario: Initial SSH connection failure
- **WHEN** the runner cannot establish an SSH connection to the launched instance within the timeout
- **THEN** the console log is retrieved, the failure and console output are written to the execution log, the instance is cleaned up, and an `IpaCloudException` is raised

### Requirement: Instance Lifecycle and Cleanup Strategy
The test runner SHALL enforce cleanup rules based on test outcome and configuration flags.

#### Scenario: Clean up newly launched instance on success
- **WHEN** a newly launched instance completes all tests with status 0 and cleanup is not set to False
- **THEN** the instance is terminated

#### Scenario: Preserve newly launched instance on test failure
- **WHEN** a newly launched instance experiences a test failure and cleanup is None
- **THEN** the instance is left running to allow troubleshooting

#### Scenario: Force cleanup on failure
- **WHEN** an instance experiences a test failure and `cleanup=True` was explicitly configured
- **THEN** the instance is terminated

#### Scenario: Preserve pre-existing running instance
- **WHEN** tests run against an existing instance (`running_instance_id` provided) and cleanup was not explicitly set to True
- **THEN** the instance is preserved regardless of test outcome

### Requirement: Workload and Configuration Injection
The test runner SHALL process injection YAML configurations to stage packages, archives,
files, and shell commands on the test instance prior to running tests.

#### Scenario: Sequential injection execution
- **WHEN** an injection configuration file is provided with `inject_packages`, `inject_archives`, `inject_files`, `execute`, and `install`
- **THEN** the runner executes the steps in exact sequential order: uploading and installing package files, extracting archives, uploading loose files, executing custom commands, and installing repo packages

#### Scenario: Injection failure handling
- **WHEN** any file upload, extraction, or command execution step fails during injection
- **THEN** an `IpaCloudException` is raised and subsequent injection steps are halted

### Requirement: Synchronization Point Execution
The test runner SHALL support intermediate synchronization points between test suites to
verify OS resilience and lifecycle actions.

#### Scenario: Hard reboot synchronization point
- **WHEN** `test_hard_reboot` is encountered in the test sequence
- **THEN** the instance is stopped and started via cloud API, the SSH client cache is cleared, a new SSH connection is established, and the remote host key fingerprint is verified against the initial fingerprint

#### Scenario: Soft reboot synchronization point
- **WHEN** `test_soft_reboot` is encountered in the test sequence
- **THEN** the distro reboot command is issued over SSH, the connection is re-established, and the remote host key fingerprint is verified against the initial fingerprint

#### Scenario: Host key change detection
- **WHEN** an instance presents a different host key fingerprint after a reboot synchronization point
- **THEN** the reboot test fails with an error stating the host key changed

#### Scenario: System update synchronization point
- **WHEN** `test_update` is encountered in the test sequence
- **THEN** the runner invokes the distro update command over SSH, writes the command output to the execution log, and records the test outcome

#### Scenario: Repository refresh synchronization point
- **WHEN** `test_refresh` is encountered in the test sequence
- **THEN** the runner invokes the distro repo refresh command over SSH, writes output to the log, and records the outcome

### Requirement: Pytest Test Suite Invocation and Retry
The test runner SHALL execute test files using Pytest and Testinfra over an isolated SSH
configuration, retrying failed tests to accommodate transient network failures.

#### Scenario: Test execution with Testinfra SSH configuration
- **WHEN** a test file is executed
- **THEN** a temporary SSH configuration file is created with the private key and SSH user and passed to Pytest via `--ssh-config`

#### Scenario: Test retry on transient failure
- **WHEN** a Pytest test run exits with any non-zero exit code
- **THEN** the runner re-runs the test up to `retry_count` times before recording the final outcome

#### Scenario: Pytest execution error handling
- **WHEN** Pytest exits with status code 2, 3, or 4
- **THEN** a synthetic failed test item named `pytest_error` is recorded in the results summary

### Requirement: Early Exit on Failure
The test runner SHALL terminate further test execution immediately upon the first failure
when configured with early exit.

#### Scenario: Early exit stops test sequence
- **WHEN** `early_exit` is True and a test item or synchronization point fails
- **THEN** execution of subsequent test items in the queue is aborted and cleanup/finalization begins immediately

### Requirement: Virtual Machine Diagnostic Collection
The test runner SHALL gather guest performance and boot diagnostics when requested.

#### Scenario: Collect VM diagnostics on reachable instance
- **WHEN** `collect_vm_info` is True and the instance remains reachable via SSH
- **THEN** the runner executes distro diagnostic commands (`systemd-analyze`, `systemd-analyze blame`, and `sudo journalctl -b`) and appends the output to the execution log

### Requirement: Structured Result Persistence
The test runner SHALL record all test outcomes, timings, and metadata into a persistent
JSON results artifact.

#### Scenario: Write results file
- **WHEN** test execution completes
- **THEN** the aggregated results dictionary with test case details, durations, and pass/fail summary counts is written to `<timestamp>.results`

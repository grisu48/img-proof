# CLI Specification

## Purpose
Provides the user-facing command-line interface for img-proof to launch test runs,
inspect results history, manage test execution artifacts, and discover test suites
across supported public clouds and SSH targets. Built to withstand both Cylon attacks
and rogue cloud instances.

## Requirements

### Requirement: Root Command Invocation and Options
The CLI entrypoint SHALL provide root options for displaying version information,
printing license details, and suppressing ANSI escape sequences.

#### Scenario: Display version
- **WHEN** the user invokes `img-proof --version`
- **THEN** the system prints the current semantic version and exits with status 0

#### Scenario: Display license
- **WHEN** the user invokes `img-proof --license`
- **THEN** the system prints `GPLv3+` and exits with status 0

#### Scenario: Disable color styling
- **WHEN** the `--no-color` option is passed to `img-proof`
- **THEN** all terminal output from commands and subcommands is printed without ANSI color escapes

### Requirement: Image Test Execution Command
The `img-proof test` command SHALL validate cloud provider arguments and initiate
image testing against the specified platform.

#### Scenario: Missing required cloud provider
- **WHEN** `img-proof test` is executed without a cloud provider argument
- **THEN** the command terminates with a non-zero exit status and displays a missing argument error

#### Scenario: Invalid cloud provider specified
- **WHEN** `img-proof test` is executed with an unknown cloud provider name
- **THEN** the command terminates with a non-zero exit status and lists valid cloud options

#### Scenario: Successful test run execution
- **WHEN** valid cloud, distribution, and image parameters are supplied and all tests succeed
- **THEN** the command prints Nagios-style result metrics and exits with status 0

#### Scenario: Test run failure propagation
- **WHEN** one or more tests fail during test execution
- **THEN** the command prints Nagios-style failure metrics and exits with a non-zero status

#### Scenario: Exception handling with debug flag
- **WHEN** an unhandled exception occurs and `--debug` is active
- **THEN** the full exception traceback is raised to the console

#### Scenario: Exception handling without debug flag
- **WHEN** an unhandled exception occurs and `--debug` is not active
- **THEN** the exception type and message are formatted in red text and the process exits with status 1

### Requirement: Deprecated CLI Option Warnings
The `img-proof test` command SHALL emit deprecation warnings when legacy options
are supplied on the command line.

#### Scenario: Legacy CPU options passed
- **WHEN** the `--cpu-options` option is provided
- **THEN** the system prints a deprecation warning recommending `--instance-option AmdSevSnp=enabled`

#### Scenario: Legacy SEV capable flag passed
- **WHEN** the `--sev-capable` flag is provided
- **THEN** the system prints a deprecation warning recommending `--instance-option SEV_CAPABLE`

#### Scenario: Legacy GVNIC flag passed
- **WHEN** the `--use-gvnic` flag is provided
- **THEN** the system prints a deprecation warning recommending `--instance-option GVNIC`

### Requirement: Test Discovery and Listing
The `img-proof list` command SHALL list available test files and YAML suites, and
optionally enumerate granular test cases.

#### Scenario: Default test file listing
- **WHEN** `img-proof list` is invoked without `--verbose`
- **THEN** the system discovers all tests in default or specified directories and prints the list of test and description names

#### Scenario: Verbose test case enumeration
- **WHEN** `img-proof list -v` or `img-proof list --verbose` is invoked
- **THEN** the system executes Pytest collection and prints all collected test cases grouped by test file

### Requirement: Results Show Subcommand
The `img-proof results show` command SHALL display test summary metrics, raw execution
logs, or detailed test case outcomes for a specific test run.

#### Scenario: Show most recent test results by default
- **WHEN** `img-proof results` or `img-proof results show` is invoked without arguments
- **THEN** the system retrieves the most recent history record (item 1) and prints its Nagios-style summary

#### Scenario: Show specific historical run
- **WHEN** `img-proof results show <item>` is invoked with an integer index
- **THEN** the system retrieves the test record at that 1-based reverse offset from the history log

#### Scenario: Display raw test run log
- **WHEN** `img-proof results show --log` is invoked
- **THEN** the system reads and outputs the complete text content of the target execution log file

#### Scenario: Display verbose test results
- **WHEN** `img-proof results show -v` or `--verbose` is invoked
- **THEN** the system prints test run metadata followed by each individual test case nodeid and pass/skip/fail outcome

#### Scenario: Display results from explicit file
- **WHEN** `img-proof results show -r <path>` is invoked with a valid results JSON file
- **THEN** the system parses and displays the results directly without reading the history log

#### Scenario: Nonexistent history index
- **WHEN** `img-proof results show <item>` specifies an index greater than available history items
- **THEN** the command prints an error message in red text and exits with status 1

### Requirement: Results History Listing
The `img-proof results list` command SHALL display all recorded test runs in chronological
order with reverse-indexed item numbers.

#### Scenario: List history records
- **WHEN** `img-proof results list` is invoked with a populated history log
- **THEN** the command outputs each history entry prefixed by its 1-based reverse index number

### Requirement: Results History Deletion
The `img-proof results delete` command SHALL remove a specified entry from the history
log and delete its associated log and results files from disk.

#### Scenario: Delete history item
- **WHEN** `img-proof results delete <item>` is invoked with a valid index
- **THEN** the corresponding line is removed from the history log
- **AND** the corresponding `.log` and `.results` files are deleted from storage

#### Scenario: Delete invalid history index
- **WHEN** `img-proof results delete <item>` is invoked with an out-of-range index
- **THEN** the command displays an index error in red text and exits with status 1

### Requirement: Results History Clearing
The `img-proof results clear` command SHALL clear all recorded history.

#### Scenario: Clear history file
- **WHEN** `img-proof results clear` is executed
- **THEN** the target history file is deleted from disk

### Requirement: Results Archival
The `img-proof results archive` command SHALL package history records, execution logs,
and results files into a compressed tarball and optionally clear archived entries.

#### Scenario: Archive all history items
- **WHEN** `img-proof results archive <path> <name>` is executed without `--items`
- **THEN** a `<name>.tar.gz` archive is created containing all logged results and logs
- **AND** an internal `.history` file is created with relative log paths

#### Scenario: Archive specific history items
- **WHEN** `img-proof results archive <path> <name> -i "1,2"` is executed
- **THEN** only the specified history records and their files are included in the archive

#### Scenario: Archive with log clearing
- **WHEN** `img-proof results archive <path> <name> --clear-log` is executed
- **THEN** the archive is created successfully and the archived records are removed from the active history log

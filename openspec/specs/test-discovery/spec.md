# Test Discovery Specification

## Purpose
Specifies the test suite discovery engine, YAML test description expansion, test name
resolution, configuration layering, and SSH client connection caching. Like the TARDIS
navigation system, it discovers test files across dimensions without creating paradoxes
or naming collisions.

## Requirements

### Requirement: Test File and Description Discovery
The discovery module SHALL locate Python test files and YAML test descriptions across
all configured test directories and detect naming collisions.

#### Scenario: Discover valid tests and descriptions
- **WHEN** test directories containing `test_*.py` and `test_*.yaml` files are scanned
- **THEN** the system indexes test files and descriptions by their base names mapped to absolute file paths

#### Scenario: Duplicate test file name rejection
- **WHEN** multiple test directories contain different test files sharing the same filename
- **THEN** discovery raises an `IpaUtilsException` identifying the duplicate paths

#### Scenario: Collision between test file and description name
- **WHEN** a YAML test description shares the same base name with a Python test file
- **THEN** discovery raises an `IpaUtilsException` reporting the name collision

### Requirement: Recursive Test Description Expansion
The discovery module SHALL recursively resolve YAML test descriptions containing test
lists and included description suites, preventing infinite recursion cycles.

#### Scenario: Resolve tests and includes
- **WHEN** a test description YAML specifies both a `tests` list and an `include` list of other descriptions
- **THEN** all individual test names and referenced description tests are recursively collected into an expanded sequence

#### Scenario: Circular include protection
- **WHEN** a test description includes itself directly or circularly through nested includes
- **THEN** visited descriptions are tracked and recursive evaluation terminates safely without infinite looping

#### Scenario: Missing description reference
- **WHEN** an include directive references a description name that does not exist in the index
- **THEN** an `IpaUtilsException` is raised indicating the missing description file

### Requirement: Test Name Resolution and Exclusion
The discovery module SHALL resolve test names to filesystem paths, preserve synchronization
point keywords, and filter excluded tests.

#### Scenario: Resolve test file path
- **WHEN** a valid test name is passed
- **THEN** the full path to the matching Python test file is returned

#### Scenario: Test case notation support
- **WHEN** a test name includes a specific test case delimiter (`test_name::test_case`)
- **THEN** the file path is resolved and the test case suffix is preserved

#### Scenario: Sync point preservation
- **WHEN** a synchronization point name (`test_hard_reboot`, `test_soft_reboot`, `test_update`, `test_refresh`) is encountered
- **THEN** it is preserved verbatim as an execution directive rather than mapped to a file

#### Scenario: Exclude specified tests
- **WHEN** a test name matches an entry in the `exclude` list
- **THEN** the test item is omitted from the expanded execution list

### Requirement: Configuration Layering and Parameter Precedence
The configuration loader SHALL merge options across CLI arguments, cloud-specific config
sections, global INI config files, and internal default values.

#### Scenario: CLI argument precedence
- **WHEN** an option is supplied via CLI arguments and also exists in a config file
- **THEN** the CLI argument value overrides the config file setting

#### Scenario: Cloud section overrides default config section
- **WHEN** an INI configuration contains a cloud-specific section (e.g. `[ec2]`) and the default `[img_proof]` section
- **THEN** values in the cloud-specific section take precedence for that provider

#### Scenario: Boolean string parsing
- **WHEN** parsing boolean configuration values
- **THEN** truthy strings (`y`, `yes`, `t`, `true`, `on`, `1`) parse to True, falsy strings parse to False, and unrecognized strings raise `ValueError`

### Requirement: SSH Connection Management and Caching
The utility module SHALL establish SSH connections via Paramiko with retries, recognize
fatal authentication errors, and cache active client sessions.

#### Scenario: Client caching
- **WHEN** an SSH connection to an IP address is already established in `CLIENT_CACHE` and healthy
- **THEN** the cached client is returned without re-authenticating

#### Scenario: Cache clearing on reset
- **WHEN** `clear_cache()` is called for an IP address or globally
- **THEN** the active Paramiko client sessions are closed and purged from the cache

#### Scenario: Unrecoverable authentication error handling
- **WHEN** SSH authentication fails with unrecoverable session or signing errors
- **THEN** retrying is aborted immediately and an `IpaSSHException` is raised

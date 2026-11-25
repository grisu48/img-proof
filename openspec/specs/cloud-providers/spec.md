# Cloud Providers Specification

## Purpose
Specifies the cloud platform backends and lifecycle integrations for AWS EC2, Microsoft
Azure, Google Compute Engine, Alibaba Cloud, Oracle Cloud Infrastructure, and direct SSH
instances. Ensures img-proof can commandeer infrastructure across any sector of the
galaxy, from the Core Worlds to Tatooine.

## Requirements

### Requirement: Cloud Provider Abstraction Contract
The base cloud class SHALL define the common lifecycle interface contract for all cloud
framework implementations.

#### Scenario: Subclass method requirement
- **WHEN** a provider subclass does not override a required lifecycle method (such as instance launching, stopping, or termination)
- **THEN** invocation of that method raises `NotImplementedError`

#### Scenario: User-data script generation
- **WHEN** user-data is requested for a newly launched instance
- **THEN** the base class produces a bash script (`#!/bin/bash`) that appends the user's public SSH key to the target user's `authorized_keys` file

### Requirement: AWS EC2 Provider
The EC2 cloud framework SHALL manage EC2 instances and serial console logs via Boto3,
resolving authentication credentials from CLI arguments or an ec2utils-style config file.

#### Scenario: Authentication via account config file
- **WHEN** an `account` name is provided for EC2 without explicit access keys
- **THEN** the provider reads the `region-<region>` and `account-<account>` sections of the EC2 config file (default `~/.ec2utils.conf`, overridable via `--cloud-config`) to resolve the access key ID and secret access key

#### Scenario: Missing region error
- **WHEN** no region is configured for EC2
- **THEN** an `EC2CloudException` is raised indicating a region is required to connect to EC2

#### Scenario: Instance launch configuration
- **WHEN** launching a new EC2 instance
- **THEN** the provider configures instance type, image ID, and a name tag, and optionally sets availability zone placement, SSH key name or generated user-data, subnet ID, security group ID, and additional info

#### Scenario: Serial console log retrieval
- **WHEN** console output is requested from an EC2 instance
- **THEN** the provider polls `console_output()` and returns the text output

### Requirement: Microsoft Azure Provider
The Azure cloud framework SHALL manage Azure Virtual Machines, virtual networks, and
storage profiles using the Azure SDK.

#### Scenario: Authenticate using service account file
- **WHEN** initializing the Azure provider with a service account file
- **THEN** `get_client_from_auth_file()` reads the file to construct authenticated Compute, Network, and Resource management clients

#### Scenario: Provision isolated resource group and networking
- **WHEN** launching a new Azure instance without an existing subnet
- **THEN** a dedicated resource group is created containing a virtual network, subnet, a dynamic public IP address, and a network interface with optional accelerated networking

#### Scenario: Storage profile for marketplace URN image
- **WHEN** an image ID is formatted as `Publisher:Offer:Sku:Version`
- **THEN** the VM configuration sets the image reference to those URN components

#### Scenario: Teardown resource group on instance termination
- **WHEN** terminating an Azure instance
- **THEN** the provider requests deletion of the entire created resource group to remove all provisioned network and compute resources

### Requirement: Google Compute Engine Provider
The GCE cloud framework SHALL manage Google Cloud instances, zone validation, network
interfaces, confidential computing, and serial output via the Google API Python Client
(`googleapiclient.discovery`) compute v1 REST interface.

#### Scenario: Zone validation
- **WHEN** the GCE provider initializes with a specified region
- **THEN** the provider verifies with the GCE API that the region represents a valid compute zone and raises `GCECloudException` if invalid

#### Scenario: Launch instance with confidential computing
- **WHEN** launching an instance with the `sev_capable` option enabled
- **THEN** the instance configuration sets `enableConfidentialCompute`, terminates on host maintenance, and adds the `SEV_CAPABLE` guest OS feature

#### Scenario: Launch instance with shielded VM configuration
- **WHEN** `enable_uefi` is enabled
- **THEN** the instance configuration sets UEFI guest features and configures shielded instance options for secure boot, vTPM, and integrity monitoring

#### Scenario: Extended operation retryable errors
- **WHEN** an instance insertion operation yields `QUOTA_EXCEEDED` or `PRECONDITION_FAILED`
- **THEN** the provider raises an `IpaRetryableError` to allow caller retry

#### Scenario: Serial console output extraction
- **WHEN** `get_console_log()` is called for a GCE instance
- **THEN** the provider queries serial port output contents via `get_serial_port_output()`

### Requirement: Alibaba Cloud Provider
The Aliyun cloud framework SHALL manage Alibaba Cloud ECS instances, security groups,
and base64-encoded cloud-init configurations via AcsClient.

#### Scenario: Launch Aliyun instance
- **WHEN** launching a new Aliyun instance
- **THEN** the provider configures instance charge type to PostPaid, sets IO optimization, binds the VSwitch and security group, encodes the user-data script to base64, and waits for Running status

#### Scenario: Extract Aliyun console output
- **WHEN** console output is requested
- **THEN** the provider sends a `GetInstanceConsoleOutputRequest` and decodes the base64 output response into text

### Requirement: Direct SSH Provider
The SSH cloud framework SHALL provide a target backend for testing pre-existing running
hosts without invoking cloud management APIs.

#### Scenario: Initialize SSH provider with running host
- **WHEN** `SSHCloud` initializes with valid IP address, SSH user, and private key file
- **THEN** `cleanup` is permanently disabled and `_is_instance_running()` returns True

#### Scenario: Reject instance launch or termination requests
- **WHEN** any lifecycle mutation method (`_launch_instance`, `_start_instance`, `_stop_instance`, `_terminate_instance`) is called on `SSHCloud`
- **THEN** an `SSHCloudException` is raised stating the SSH backend has no access to cloud APIs

#### Scenario: Launch instance with generated networking
- **WHEN** launching a new OCI instance without an existing subnet
- **THEN** the provider creates a VCN, subnet, and internet gateway named after the generated instance display name, then launches the instance into that subnet

#### Scenario: Teardown generated networking on termination
- **WHEN** terminating an OCI instance whose display name carries the `oci-ipa-test` prefix generated by img-proof
- **THEN** the provider terminates the instance and deletes the associated subnet, route rules, internet gateway, and VCN

#### Scenario: Console history retrieval
- **WHEN** console output is requested from an OCI instance
- **THEN** the provider captures console history via `capture_console_history_and_wait_for_state()` and decodes the retrieved content

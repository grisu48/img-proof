# Cloud Providers Specification

## Purpose
Specifies the cloud platform backends and lifecycle integrations for AWS EC2, Microsoft
Azure, Google Compute Engine, Alibaba Cloud, and direct SSH instances. Ensures img-proof
can commandeer infrastructure across any sector of the galaxy, from the Core Worlds to
Tatooine.

## Requirements

### Requirement: Cloud Provider Abstraction Contract
The base cloud class SHALL define the common lifecycle interface contract for all cloud
framework implementations.

#### Scenario: Subclass method requirement
- **WHEN** a provider subclass does not override a required lifecycle method (such as instance launching, stopping, or termination)
- **THEN** invocation of that method raises `NotImplementedError`

#### Scenario: User-data script generation
- **WHEN** user-data is requested for cloud-init instance provisioning
- **THEN** the base class produces a `#cloud-config` script that disables root login and appends the user's public SSH key to the target user's authorized_keys file

### Requirement: AWS EC2 Provider
The EC2 cloud framework SHALL manage EC2 instances, authentication credentials, volume
configurations, and serial console logs via Boto3.

#### Scenario: Authentication via AWS profile
- **WHEN** the `profile` parameter is provided for EC2
- **THEN** a Boto3 session is initialized using that profile name and region, taking precedence over individual access keys

#### Scenario: Missing AWS profile error
- **WHEN** an invalid or nonexistent AWS profile name is specified
- **THEN** an `EC2CloudException` is raised indicating the profile was not found

#### Scenario: Instance launch with EBS configuration
- **WHEN** launching a new EC2 instance
- **THEN** the provider configures instance type, image ID, root EBS volume size, name tag, subnet, security groups, and CPU options (including AMD SEV-SNP)

#### Scenario: Serial console log retrieval
- **WHEN** console output is requested from an EC2 instance
- **THEN** the provider polls `console_output()` and returns the text output

### Requirement: Microsoft Azure Provider
The Azure cloud framework SHALL manage Azure Virtual Machines, network security groups,
virtual networks, and storage profiles using the Azure SDK and credential wrapping.

#### Scenario: Authenticate using service account file
- **WHEN** initializing the Azure provider with a service account file
- **THEN** tenant ID, client ID, client secret, and subscription ID are loaded and adapted via `CredentialWrapper` to provide bearer tokens for management clients

#### Scenario: Provision isolated resource group and networking
- **WHEN** launching a new Azure instance without an existing subnet
- **THEN** a dedicated resource group is created containing a virtual network, subnet, static standard public IP, network security group permitting port 22, and a network interface with optional accelerated networking

#### Scenario: Storage profile for marketplace URN image
- **WHEN** an image ID is formatted as `Publisher:Offer:Sku:Version`
- **THEN** the VM configuration sets the image reference to those URN components and configures the OS disk size

#### Scenario: Marketplace plan information for licensed images
- **WHEN** a marketplace URN image is launched with plan information enabled
- **THEN** the VM configuration includes a plan block with the publisher, product, and name derived from the image URN, as required to deploy certain licensed Azure marketplace images

#### Scenario: Storage profile for Shared Image Gallery
- **WHEN** `gallery_name`, `gallery_resource_group`, and `image_version` are provided
- **THEN** the VM configuration binds the image reference to the resolved gallery image version resource ID

#### Scenario: Teardown resource group on instance termination
- **WHEN** terminating an Azure instance
- **THEN** the provider requests deletion of the entire created resource group to remove all provisioned network and compute resources

### Requirement: Google Compute Engine Provider
The GCE cloud framework SHALL manage Google Cloud instances, zone validation, network
interfaces, confidential computing, and serial output via the compute_v1 SDK.

#### Scenario: Zone validation
- **WHEN** the GCE provider initializes with a specified region
- **THEN** the provider verifies with the GCE API that the region represents a valid compute zone and raises `GCECloudException` if invalid

#### Scenario: Launch instance with confidential computing
- **WHEN** launching an instance with SEV, SEV-SNP, or TDX enabled
- **THEN** the instance configuration includes confidential compute flags, terminates on host maintenance, and configures matching guest OS features

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

"""Data models for Oracle Cloud MCP server."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AuthType(str, Enum):
    """Authentication types supported."""

    SESSION_TOKEN = "session_token"
    API_KEY = "api_key"
    INSTANCE_PRINCIPAL = "instance_principal"


class LifecycleState(str, Enum):
    """Common lifecycle states in OCI."""

    CREATING = "CREATING"
    PROVISIONING = "PROVISIONING"
    RUNNING = "RUNNING"
    ACTIVE = "ACTIVE"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    UPDATING = "UPDATING"
    DELETING = "DELETING"
    DELETED = "DELETED"
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"
    CANCELED = "CANCELED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    CANCELING = "CANCELING"
    WAITING = "WAITING"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"


class BastionType(str, Enum):
    """Types of bastions."""

    STANDARD = "STANDARD"
    INTERNAL = "INTERNAL"


class NodePoolPlacementConfigType(str, Enum):
    """Node pool placement configuration types."""

    STANDARD = "STANDARD"
    CLUSTER_NETWORK = "CLUSTER_NETWORK"


class DevOpsResourceType(str, Enum):
    """DevOps resource types."""

    PROJECT = "PROJECT"
    BUILD_PIPELINE = "BUILD_PIPELINE"
    BUILD_RUN = "BUILD_RUN"
    DEPLOY_PIPELINE = "DEPLOY_PIPELINE"
    DEPLOYMENT = "DEPLOYMENT"
    ARTIFACT = "ARTIFACT"
    ENVIRONMENT = "ENVIRONMENT"
    REPOSITORY = "REPOSITORY"


class DeploymentType(str, Enum):
    """Deployment types."""

    PIPELINE_DEPLOYMENT = "PIPELINE_DEPLOYMENT"
    PIPELINE_REDEPLOYMENT = "PIPELINE_REDEPLOYMENT"
    SINGLE_STAGE_DEPLOYMENT = "SINGLE_STAGE_DEPLOYMENT"
    SINGLE_STAGE_REDEPLOYMENT = "SINGLE_STAGE_REDEPLOYMENT"


class DeployStageType(str, Enum):
    """Deployment stage types."""

    WAIT = "WAIT"
    COMPUTE_INSTANCE_GROUP_ROLLING_DEPLOYMENT = "COMPUTE_INSTANCE_GROUP_ROLLING_DEPLOYMENT"
    COMPUTE_INSTANCE_GROUP_BLUE_GREEN_DEPLOYMENT = "COMPUTE_INSTANCE_GROUP_BLUE_GREEN_DEPLOYMENT"
    COMPUTE_INSTANCE_GROUP_CANARY_DEPLOYMENT = "COMPUTE_INSTANCE_GROUP_CANARY_DEPLOYMENT"
    OKE_DEPLOYMENT = "OKE_DEPLOYMENT"
    OKE_BLUE_GREEN_DEPLOYMENT = "OKE_BLUE_GREEN_DEPLOYMENT"
    OKE_CANARY_DEPLOYMENT = "OKE_CANARY_DEPLOYMENT"
    OKE_HELM_CHART_DEPLOYMENT = "OKE_HELM_CHART_DEPLOYMENT"
    DEPLOY_FUNCTION = "DEPLOY_FUNCTION"
    INVOKE_FUNCTION = "INVOKE_FUNCTION"
    LOAD_BALANCER_TRAFFIC_SHIFT = "LOAD_BALANCER_TRAFFIC_SHIFT"
    MANUAL_APPROVAL = "MANUAL_APPROVAL"
    SHELL = "SHELL"


class OCIConfig(BaseModel):
    """OCI configuration model with validation."""

    model_config = ConfigDict(validate_assignment=True)

    region: str
    profile_name: str = "DEFAULT"
    config_file: Optional[str] = None
    tenancy: Optional[str] = None
    tenancy_name: str = "bmc_operator_access"
    user: Optional[str] = None
    fingerprint: Optional[str] = None
    key_file: Optional[str] = None
    security_token_file: Optional[str] = None
    pass_phrase: Optional[str] = None
    auth_type: AuthType = AuthType.SESSION_TOKEN


@dataclass
class InstanceInfo:
    """Information about an OCI compute instance."""

    instance_id: str
    display_name: Optional[str] = None
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None
    subnet_id: Optional[str] = None
    shape: Optional[str] = None
    availability_domain: Optional[str] = None
    lifecycle_state: Optional[str] = None
    cluster_name: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "instance_id": self.instance_id,
            "display_name": self.display_name,
            "private_ip": self.private_ip,
            "public_ip": self.public_ip,
            "subnet_id": self.subnet_id,
            "shape": self.shape,
            "availability_domain": self.availability_domain,
            "lifecycle_state": self.lifecycle_state,
            "cluster_name": self.cluster_name,
        }


@dataclass
class OKEClusterInfo:
    """Information about an OKE cluster."""

    cluster_id: str
    name: str
    kubernetes_version: Optional[str] = None
    lifecycle_state: Optional[str] = None
    compartment_id: Optional[str] = None
    available_upgrades: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cluster_id": self.cluster_id,
            "name": self.name,
            "kubernetes_version": self.kubernetes_version,
            "lifecycle_state": self.lifecycle_state,
            "compartment_id": self.compartment_id,
            "available_upgrades": self.available_upgrades,
        }


@dataclass
class OKEClusterDetailsInfo:
    """Detailed information about an OKE cluster."""

    cluster_id: str
    name: str
    kubernetes_version: Optional[str] = None
    lifecycle_state: Optional[str] = None
    compartment_id: Optional[str] = None
    vcn_id: Optional[str] = None
    endpoint_subnet_id: Optional[str] = None
    service_lb_subnet_ids: list[str] = field(default_factory=list)
    available_upgrades: list[str] = field(default_factory=list)
    # Endpoints
    kubernetes_endpoint: Optional[str] = None
    public_endpoint: Optional[str] = None
    private_endpoint: Optional[str] = None
    # Options
    is_public_ip_enabled: bool = False
    is_kubernetes_dashboard_enabled: bool = False
    is_tiller_enabled: bool = False
    pods_cidr: Optional[str] = None
    services_cidr: Optional[str] = None
    # Metadata
    created_by: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cluster_id": self.cluster_id,
            "name": self.name,
            "kubernetes_version": self.kubernetes_version,
            "lifecycle_state": self.lifecycle_state,
            "compartment_id": self.compartment_id,
            "vcn_id": self.vcn_id,
            "endpoint_subnet_id": self.endpoint_subnet_id,
            "service_lb_subnet_ids": self.service_lb_subnet_ids,
            "available_upgrades": self.available_upgrades,
            "endpoints": {
                "kubernetes": self.kubernetes_endpoint,
                "public": self.public_endpoint,
                "private": self.private_endpoint,
            },
            "options": {
                "is_public_ip_enabled": self.is_public_ip_enabled,
                "is_kubernetes_dashboard_enabled": self.is_kubernetes_dashboard_enabled,
                "is_tiller_enabled": self.is_tiller_enabled,
                "pods_cidr": self.pods_cidr,
                "services_cidr": self.services_cidr,
            },
            "created_by": self.created_by,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class NodePoolInfo:
    """Information about an OKE node pool."""

    node_pool_id: str
    name: str
    cluster_id: str
    compartment_id: Optional[str] = None
    kubernetes_version: Optional[str] = None
    node_shape: Optional[str] = None
    node_source_name: Optional[str] = None
    node_source_type: Optional[str] = None
    node_image_id: Optional[str] = None
    node_image_name: Optional[str] = None
    initial_node_labels: list[dict[str, str]] = field(default_factory=list)
    quantity_per_subnet: Optional[int] = None
    subnet_ids: list[str] = field(default_factory=list)
    lifecycle_state: Optional[str] = None
    node_count: int = 0
    # Shape config for flex shapes
    ocpus: Optional[float] = None
    memory_in_gbs: Optional[float] = None
    # Node config
    ssh_public_key: Optional[str] = None
    # Metadata
    time_created: Optional[str] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_pool_id": self.node_pool_id,
            "name": self.name,
            "cluster_id": self.cluster_id,
            "compartment_id": self.compartment_id,
            "kubernetes_version": self.kubernetes_version,
            "node_shape": self.node_shape,
            "node_source": {
                "name": self.node_source_name,
                "type": self.node_source_type,
                "image_id": self.node_image_id,
                "image_name": self.node_image_name,
            },
            "initial_node_labels": self.initial_node_labels,
            "quantity_per_subnet": self.quantity_per_subnet,
            "subnet_ids": self.subnet_ids,
            "lifecycle_state": self.lifecycle_state,
            "node_count": self.node_count,
            "shape_config": {
                "ocpus": self.ocpus,
                "memory_in_gbs": self.memory_in_gbs,
            },
            "ssh_public_key": self.ssh_public_key,
            "time_created": self.time_created,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class NodeInfo:
    """Information about a node in a node pool."""

    node_id: str
    name: Optional[str] = None
    node_pool_id: Optional[str] = None
    availability_domain: Optional[str] = None
    subnet_id: Optional[str] = None
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None
    lifecycle_state: Optional[str] = None
    lifecycle_details: Optional[str] = None
    kubernetes_version: Optional[str] = None
    node_error: Optional[str] = None
    fault_domain: Optional[str] = None
    time_created: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "name": self.name,
            "node_pool_id": self.node_pool_id,
            "availability_domain": self.availability_domain,
            "subnet_id": self.subnet_id,
            "private_ip": self.private_ip,
            "public_ip": self.public_ip,
            "lifecycle_state": self.lifecycle_state,
            "lifecycle_details": self.lifecycle_details,
            "kubernetes_version": self.kubernetes_version,
            "node_error": self.node_error,
            "fault_domain": self.fault_domain,
            "time_created": self.time_created,
        }


@dataclass
class WorkRequestInfo:
    """Information about an OCI work request."""

    work_request_id: str
    operation_type: str
    status: str
    compartment_id: Optional[str] = None
    percent_complete: float = 0.0
    time_accepted: Optional[str] = None
    time_started: Optional[str] = None
    time_finished: Optional[str] = None
    resources: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "work_request_id": self.work_request_id,
            "operation_type": self.operation_type,
            "status": self.status,
            "compartment_id": self.compartment_id,
            "percent_complete": self.percent_complete,
            "time_accepted": self.time_accepted,
            "time_started": self.time_started,
            "time_finished": self.time_finished,
            "resources": self.resources,
        }


@dataclass
class BastionInfo:
    """Information about an OCI bastion."""

    bastion_id: str
    target_subnet_id: str
    bastion_name: Optional[str] = None
    bastion_type: str = "INTERNAL"
    max_session_ttl: int = 10800
    lifecycle_state: str = "ACTIVE"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bastion_id": self.bastion_id,
            "bastion_name": self.bastion_name,
            "target_subnet_id": self.target_subnet_id,
            "bastion_type": self.bastion_type,
            "max_session_ttl": self.max_session_ttl,
            "lifecycle_state": self.lifecycle_state,
        }


@dataclass
class CompartmentInfo:
    """Information about an OCI compartment."""

    compartment_id: str
    name: str
    description: Optional[str] = None
    lifecycle_state: str = "ACTIVE"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "compartment_id": self.compartment_id,
            "name": self.name,
            "description": self.description,
            "lifecycle_state": self.lifecycle_state,
        }


# ============================================================================
# OCI DevOps Models
# ============================================================================


@dataclass
class DevOpsProjectInfo:
    """Information about a DevOps project."""

    project_id: str
    name: str
    compartment_id: str
    description: Optional[str] = None
    namespace: Optional[str] = None
    notification_config: Optional[dict[str, Any]] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "compartment_id": self.compartment_id,
            "description": self.description,
            "namespace": self.namespace,
            "notification_config": self.notification_config,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class BuildPipelineInfo:
    """Information about a build pipeline."""

    build_pipeline_id: str
    display_name: str
    project_id: str
    compartment_id: Optional[str] = None
    description: Optional[str] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    build_pipeline_parameters: Optional[dict[str, Any]] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "build_pipeline_id": self.build_pipeline_id,
            "display_name": self.display_name,
            "project_id": self.project_id,
            "compartment_id": self.compartment_id,
            "description": self.description,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "build_pipeline_parameters": self.build_pipeline_parameters,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class BuildPipelineStageInfo:
    """Information about a build pipeline stage."""

    stage_id: str
    display_name: str
    build_pipeline_id: str
    stage_type: str
    compartment_id: Optional[str] = None
    description: Optional[str] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    build_spec_file: Optional[str] = None
    image: Optional[str] = None
    primary_build_source: Optional[str] = None
    stage_execution_timeout_in_seconds: Optional[int] = None
    predecessor_stage_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage_id": self.stage_id,
            "display_name": self.display_name,
            "build_pipeline_id": self.build_pipeline_id,
            "stage_type": self.stage_type,
            "compartment_id": self.compartment_id,
            "description": self.description,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "build_spec_file": self.build_spec_file,
            "image": self.image,
            "primary_build_source": self.primary_build_source,
            "stage_execution_timeout_in_seconds": self.stage_execution_timeout_in_seconds,
            "predecessor_stage_ids": self.predecessor_stage_ids,
        }


@dataclass
class BuildRunInfo:
    """Information about a build run."""

    build_run_id: str
    display_name: str
    build_pipeline_id: str
    compartment_id: Optional[str] = None
    project_id: Optional[str] = None
    lifecycle_state: Optional[str] = None
    lifecycle_details: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    time_started: Optional[str] = None
    time_finished: Optional[str] = None
    commit_info: Optional[dict[str, Any]] = None
    build_outputs: Optional[dict[str, Any]] = None
    build_run_source: Optional[dict[str, Any]] = None
    build_run_arguments: Optional[dict[str, Any]] = None
    build_run_progress: Optional[dict[str, Any]] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "build_run_id": self.build_run_id,
            "display_name": self.display_name,
            "build_pipeline_id": self.build_pipeline_id,
            "compartment_id": self.compartment_id,
            "project_id": self.project_id,
            "lifecycle_state": self.lifecycle_state,
            "lifecycle_details": self.lifecycle_details,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "time_started": self.time_started,
            "time_finished": self.time_finished,
            "commit_info": self.commit_info,
            "build_outputs": self.build_outputs,
            "build_run_source": self.build_run_source,
            "build_run_arguments": self.build_run_arguments,
            "build_run_progress": self.build_run_progress,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class DeployPipelineInfo:
    """Information about a deployment pipeline."""

    deploy_pipeline_id: str
    display_name: str
    project_id: str
    compartment_id: Optional[str] = None
    description: Optional[str] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    deploy_pipeline_parameters: Optional[dict[str, Any]] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "deploy_pipeline_id": self.deploy_pipeline_id,
            "display_name": self.display_name,
            "project_id": self.project_id,
            "compartment_id": self.compartment_id,
            "description": self.description,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "deploy_pipeline_parameters": self.deploy_pipeline_parameters,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class DeployStageInfo:
    """Information about a deployment stage."""

    stage_id: str
    display_name: str
    deploy_pipeline_id: str
    stage_type: str
    compartment_id: Optional[str] = None
    project_id: Optional[str] = None
    description: Optional[str] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    deploy_environment_id: Optional[str] = None
    predecessor_stage_ids: list[str] = field(default_factory=list)
    # OKE specific
    oke_cluster_id: Optional[str] = None
    kubernetes_manifest_artifact_ids: list[str] = field(default_factory=list)
    namespace: Optional[str] = None
    # Helm specific
    helm_chart_artifact_id: Optional[str] = None
    helm_command_artifact_ids: list[str] = field(default_factory=list)
    release_name: Optional[str] = None
    # Approval specific
    approval_policy: Optional[dict[str, Any]] = None
    # Wait specific
    wait_duration: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stage_id": self.stage_id,
            "display_name": self.display_name,
            "deploy_pipeline_id": self.deploy_pipeline_id,
            "stage_type": self.stage_type,
            "compartment_id": self.compartment_id,
            "project_id": self.project_id,
            "description": self.description,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "deploy_environment_id": self.deploy_environment_id,
            "predecessor_stage_ids": self.predecessor_stage_ids,
            "oke_cluster_id": self.oke_cluster_id,
            "kubernetes_manifest_artifact_ids": self.kubernetes_manifest_artifact_ids,
            "namespace": self.namespace,
            "helm_chart_artifact_id": self.helm_chart_artifact_id,
            "helm_command_artifact_ids": self.helm_command_artifact_ids,
            "release_name": self.release_name,
            "approval_policy": self.approval_policy,
            "wait_duration": self.wait_duration,
        }


@dataclass
class DeploymentInfo:
    """Information about a deployment."""

    deployment_id: str
    display_name: str
    deploy_pipeline_id: str
    compartment_id: Optional[str] = None
    project_id: Optional[str] = None
    deployment_type: Optional[str] = None
    lifecycle_state: Optional[str] = None
    lifecycle_details: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    deploy_stage_id: Optional[str] = None
    deployment_arguments: Optional[dict[str, Any]] = None
    deploy_artifact_override_arguments: Optional[dict[str, Any]] = None
    deployment_execution_progress: Optional[dict[str, Any]] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "deployment_id": self.deployment_id,
            "display_name": self.display_name,
            "deploy_pipeline_id": self.deploy_pipeline_id,
            "compartment_id": self.compartment_id,
            "project_id": self.project_id,
            "deployment_type": self.deployment_type,
            "lifecycle_state": self.lifecycle_state,
            "lifecycle_details": self.lifecycle_details,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "deploy_stage_id": self.deploy_stage_id,
            "deployment_arguments": self.deployment_arguments,
            "deploy_artifact_override_arguments": self.deploy_artifact_override_arguments,
            "deployment_execution_progress": self.deployment_execution_progress,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class DeployArtifactInfo:
    """Information about a deployment artifact."""

    artifact_id: str
    display_name: str
    project_id: str
    compartment_id: Optional[str] = None
    description: Optional[str] = None
    artifact_type: Optional[str] = None
    artifact_source_type: Optional[str] = None
    deploy_artifact_source: Optional[dict[str, Any]] = None
    argument_substitution_mode: Optional[str] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "display_name": self.display_name,
            "project_id": self.project_id,
            "compartment_id": self.compartment_id,
            "description": self.description,
            "artifact_type": self.artifact_type,
            "artifact_source_type": self.artifact_source_type,
            "deploy_artifact_source": self.deploy_artifact_source,
            "argument_substitution_mode": self.argument_substitution_mode,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class DeployEnvironmentInfo:
    """Information about a deployment environment."""

    environment_id: str
    display_name: str
    project_id: str
    compartment_id: Optional[str] = None
    description: Optional[str] = None
    environment_type: Optional[str] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    # OKE specific
    cluster_id: Optional[str] = None
    # Compute specific
    compute_instance_group_selectors: Optional[dict[str, Any]] = None
    # Function specific
    function_id: Optional[str] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "environment_id": self.environment_id,
            "display_name": self.display_name,
            "project_id": self.project_id,
            "compartment_id": self.compartment_id,
            "description": self.description,
            "environment_type": self.environment_type,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "cluster_id": self.cluster_id,
            "compute_instance_group_selectors": self.compute_instance_group_selectors,
            "function_id": self.function_id,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class DevOpsRepositoryInfo:
    """Information about a DevOps code repository."""

    repository_id: str
    name: str
    project_id: str
    compartment_id: Optional[str] = None
    description: Optional[str] = None
    namespace: Optional[str] = None
    project_name: Optional[str] = None
    default_branch: Optional[str] = None
    repository_type: Optional[str] = None
    ssh_url: Optional[str] = None
    http_url: Optional[str] = None
    mirror_repository_config: Optional[dict[str, Any]] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "repository_id": self.repository_id,
            "name": self.name,
            "project_id": self.project_id,
            "compartment_id": self.compartment_id,
            "description": self.description,
            "namespace": self.namespace,
            "project_name": self.project_name,
            "default_branch": self.default_branch,
            "repository_type": self.repository_type,
            "ssh_url": self.ssh_url,
            "http_url": self.http_url,
            "mirror_repository_config": self.mirror_repository_config,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class RepositoryBranchInfo:
    """Information about a repository branch."""

    ref_name: str
    ref_type: str
    full_ref_name: Optional[str] = None
    commit_id: Optional[str] = None
    repository_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ref_name": self.ref_name,
            "ref_type": self.ref_type,
            "full_ref_name": self.full_ref_name,
            "commit_id": self.commit_id,
            "repository_id": self.repository_id,
        }


@dataclass
class RepositoryCommitInfo:
    """Information about a repository commit."""

    commit_id: str
    commit_message: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    committer_name: Optional[str] = None
    committer_email: Optional[str] = None
    time_created: Optional[str] = None
    parent_commit_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "commit_id": self.commit_id,
            "commit_message": self.commit_message,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "committer_name": self.committer_name,
            "committer_email": self.committer_email,
            "time_created": self.time_created,
            "parent_commit_ids": self.parent_commit_ids,
        }


@dataclass
class TriggerInfo:
    """Information about a DevOps trigger."""

    trigger_id: str
    display_name: str
    project_id: str
    compartment_id: Optional[str] = None
    description: Optional[str] = None
    trigger_source: Optional[str] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    actions: list[dict[str, Any]] = field(default_factory=list)
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trigger_id": self.trigger_id,
            "display_name": self.display_name,
            "project_id": self.project_id,
            "compartment_id": self.compartment_id,
            "description": self.description,
            "trigger_source": self.trigger_source,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "actions": self.actions,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }


@dataclass
class ConnectionInfo:
    """Information about a DevOps connection (external SCM)."""

    connection_id: str
    display_name: str
    project_id: str
    compartment_id: Optional[str] = None
    description: Optional[str] = None
    connection_type: Optional[str] = None
    lifecycle_state: Optional[str] = None
    time_created: Optional[str] = None
    time_updated: Optional[str] = None
    freeform_tags: dict[str, str] = field(default_factory=dict)
    defined_tags: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "connection_id": self.connection_id,
            "display_name": self.display_name,
            "project_id": self.project_id,
            "compartment_id": self.compartment_id,
            "description": self.description,
            "connection_type": self.connection_type,
            "lifecycle_state": self.lifecycle_state,
            "time_created": self.time_created,
            "time_updated": self.time_updated,
            "freeform_tags": self.freeform_tags,
            "defined_tags": self.defined_tags,
        }

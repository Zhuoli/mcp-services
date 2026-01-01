"""Data models for Oracle Cloud MCP server."""

from dataclasses import dataclass, field
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


class BastionType(str, Enum):
    """Types of bastions."""

    STANDARD = "STANDARD"
    INTERNAL = "INTERNAL"


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

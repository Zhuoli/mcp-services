"""OCI client with session token support."""

import logging
import os
from typing import Any, Optional

import oci
from oci.pagination import list_call_get_all_results

from .auth import OCIAuthenticator
from .models import (
    BastionInfo,
    CompartmentInfo,
    InstanceInfo,
    LifecycleState,
    OCIConfig,
    OKEClusterInfo,
)

logger = logging.getLogger(__name__)


class OCIClient:
    """OCI client with session token support and lazy-loaded service clients."""

    def __init__(
        self,
        region: str,
        profile_name: str = "DEFAULT",
        config_file: Optional[str] = None,
    ):
        """
        Initialize OCI client with authentication.

        Args:
            region: OCI region name (e.g., 'us-phoenix-1')
            profile_name: OCI config profile name
            config_file: Optional path to config file
        """
        self.config = OCIConfig(
            region=region,
            profile_name=profile_name,
            config_file=config_file or os.environ.get("OCI_CONFIG_FILE"),
        )
        self.authenticator = OCIAuthenticator(self.config)
        self.oci_config: Optional[dict[str, Any]] = None
        self.signer: Optional[Any] = None

        # Lazy-loaded service clients
        self._compute_client: Optional[oci.core.ComputeClient] = None
        self._identity_client: Optional[oci.identity.IdentityClient] = None
        self._bastion_client: Optional[oci.bastion.BastionClient] = None
        self._network_client: Optional[oci.core.VirtualNetworkClient] = None
        self._container_engine_client: Optional[oci.container_engine.ContainerEngineClient] = None

        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with OCI."""
        self.oci_config, self.signer = self.authenticator.authenticate()

    @property
    def compute_client(self) -> oci.core.ComputeClient:
        """Lazy-load compute client."""
        if not self._compute_client:
            self._compute_client = oci.core.ComputeClient(self.oci_config, signer=self.signer)
        return self._compute_client

    @property
    def identity_client(self) -> oci.identity.IdentityClient:
        """Lazy-load identity client."""
        if not self._identity_client:
            self._identity_client = oci.identity.IdentityClient(self.oci_config, signer=self.signer)
        return self._identity_client

    @property
    def bastion_client(self) -> oci.bastion.BastionClient:
        """Lazy-load bastion client."""
        if not self._bastion_client:
            self._bastion_client = oci.bastion.BastionClient(self.oci_config, signer=self.signer)
        return self._bastion_client

    @property
    def network_client(self) -> oci.core.VirtualNetworkClient:
        """Lazy-load network client."""
        if not self._network_client:
            self._network_client = oci.core.VirtualNetworkClient(
                self.oci_config, signer=self.signer
            )
        return self._network_client

    @property
    def container_engine_client(self) -> oci.container_engine.ContainerEngineClient:
        """Lazy-load OKE container engine client."""
        if not self._container_engine_client:
            self._container_engine_client = oci.container_engine.ContainerEngineClient(
                self.oci_config, signer=self.signer
            )
        return self._container_engine_client

    def list_compartments(
        self, parent_compartment_id: str, include_root: bool = False
    ) -> list[CompartmentInfo]:
        """
        List all compartments under a parent compartment.

        Args:
            parent_compartment_id: Parent compartment OCID
            include_root: Whether to include the root compartment

        Returns:
            List of CompartmentInfo objects
        """
        compartments = []

        if include_root:
            root = self.identity_client.get_compartment(parent_compartment_id).data
            compartments.append(
                CompartmentInfo(
                    compartment_id=root.id,
                    name=root.name,
                    description=root.description,
                    lifecycle_state=root.lifecycle_state,
                )
            )

        response = self.identity_client.list_compartments(
            parent_compartment_id,
            compartment_id_in_subtree=True,
            lifecycle_state=LifecycleState.ACTIVE.value,
        )

        for comp in response.data:
            compartments.append(
                CompartmentInfo(
                    compartment_id=comp.id,
                    name=comp.name,
                    description=comp.description,
                    lifecycle_state=comp.lifecycle_state,
                )
            )

        return compartments

    def list_instances(
        self,
        compartment_id: str,
        lifecycle_state: Optional[str] = None,
    ) -> list[InstanceInfo]:
        """
        List compute instances in a compartment.

        Args:
            compartment_id: Compartment OCID
            lifecycle_state: Optional filter by lifecycle state

        Returns:
            List of InstanceInfo objects
        """
        instances = []

        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state

        response = list_call_get_all_results(self.compute_client.list_instances, **kwargs)

        for instance in response.data:
            vnic_info = self._get_instance_vnic(compartment_id, instance.id)
            private_ip, public_ip, subnet_id = vnic_info if vnic_info else (None, None, None)

            instances.append(
                InstanceInfo(
                    instance_id=instance.id,
                    display_name=instance.display_name,
                    private_ip=private_ip,
                    public_ip=public_ip,
                    subnet_id=subnet_id,
                    shape=instance.shape,
                    availability_domain=instance.availability_domain,
                    lifecycle_state=instance.lifecycle_state,
                    metadata=instance.metadata or {},
                )
            )

        return instances

    def list_oke_clusters(
        self,
        compartment_id: str,
        lifecycle_state: Optional[str] = None,
    ) -> list[OKEClusterInfo]:
        """
        List OKE clusters in a compartment.

        Args:
            compartment_id: Compartment OCID
            lifecycle_state: Optional filter by lifecycle state

        Returns:
            List of OKEClusterInfo objects
        """
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state

        response = list_call_get_all_results(
            self.container_engine_client.list_clusters, **kwargs
        )

        clusters = []
        for cluster in response.data or []:
            cluster_id = getattr(cluster, "id", None)
            if not cluster_id:
                continue

            available_upgrades = getattr(cluster, "available_kubernetes_upgrades", None)
            if available_upgrades is None:
                available_upgrades = getattr(cluster, "available_upgrades", None)

            clusters.append(
                OKEClusterInfo(
                    cluster_id=cluster_id,
                    name=getattr(cluster, "name", cluster_id),
                    kubernetes_version=getattr(cluster, "kubernetes_version", None),
                    lifecycle_state=getattr(cluster, "lifecycle_state", None),
                    compartment_id=getattr(cluster, "compartment_id", compartment_id),
                    available_upgrades=list(available_upgrades or []),
                )
            )

        return clusters

    def list_bastions(self, compartment_id: str) -> list[BastionInfo]:
        """
        List bastions in a compartment.

        Args:
            compartment_id: Compartment OCID

        Returns:
            List of BastionInfo objects
        """
        response = self.bastion_client.list_bastions(compartment_id=compartment_id)

        bastions = []
        for bastion in response.data:
            if hasattr(bastion, "lifecycle_state"):
                if bastion.lifecycle_state != "ACTIVE":
                    continue

            target_subnet_id = getattr(bastion, "target_subnet_id", "")
            if not target_subnet_id:
                continue

            max_session_ttl = None
            for attr_name in ["max_session_ttl_in_seconds", "max_session_ttl", "session_ttl"]:
                if hasattr(bastion, attr_name):
                    max_session_ttl = getattr(bastion, attr_name)
                    break

            bastions.append(
                BastionInfo(
                    bastion_id=bastion.id,
                    bastion_name=getattr(bastion, "name", None),
                    target_subnet_id=target_subnet_id,
                    bastion_type=getattr(bastion, "bastion_type", "INTERNAL"),
                    max_session_ttl=max_session_ttl or 10800,
                    lifecycle_state=getattr(bastion, "lifecycle_state", "ACTIVE"),
                )
            )

        return bastions

    def _get_instance_vnic(
        self, compartment_id: str, instance_id: str
    ) -> Optional[tuple[str, Optional[str], str]]:
        """Get VNIC information for an instance."""
        try:
            vnics = self.compute_client.list_vnic_attachments(
                compartment_id=compartment_id, instance_id=instance_id
            ).data

            for vnic_attachment in vnics:
                if vnic_attachment.lifecycle_state == "ATTACHED":
                    vnic = self.network_client.get_vnic(vnic_attachment.vnic_id).data

                    if vnic.lifecycle_state == "AVAILABLE" and vnic.private_ip:
                        return (vnic.private_ip, vnic.public_ip, vnic.subnet_id)

            return None
        except Exception as e:
            logger.warning(f"Failed to get VNIC for instance {instance_id}: {e}")
            return None

    def test_connection(self) -> bool:
        """Test if the connection to OCI is working."""
        try:
            regions = self.identity_client.list_regions()
            logger.info(f"Connection test successful. Found {len(regions.data)} regions.")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def __enter__(self) -> "OCIClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        pass

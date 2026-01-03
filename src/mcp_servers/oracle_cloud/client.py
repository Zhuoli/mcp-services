"""OCI client with session token support."""

import base64
import logging
import os
from typing import Any, Optional

import oci
from oci.pagination import list_call_get_all_results

from .auth import OCIAuthenticator
from .models import (
    BastionInfo,
    BuildPipelineInfo,
    BuildPipelineStageInfo,
    BuildRunInfo,
    CompartmentInfo,
    ConnectionInfo,
    DeployArtifactInfo,
    DeployEnvironmentInfo,
    DeploymentInfo,
    DeployPipelineInfo,
    DeployStageInfo,
    DevOpsProjectInfo,
    DevOpsRepositoryInfo,
    InstanceInfo,
    LifecycleState,
    NodeInfo,
    NodePoolInfo,
    OCIConfig,
    OKEClusterDetailsInfo,
    OKEClusterInfo,
    RepositoryBranchInfo,
    RepositoryCommitInfo,
    TriggerInfo,
    WorkRequestInfo,
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
        self._devops_client: Optional[oci.devops.DevopsClient] = None

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

    @property
    def devops_client(self) -> oci.devops.DevopsClient:
        """Lazy-load DevOps client."""
        if not self._devops_client:
            self._devops_client = oci.devops.DevopsClient(self.oci_config, signer=self.signer)
        return self._devops_client

    # =========================================================================
    # Identity & Compartment Operations
    # =========================================================================

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

    # =========================================================================
    # Compute Instance Operations
    # =========================================================================

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

    # =========================================================================
    # OKE Cluster Operations
    # =========================================================================

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

    def get_oke_cluster(self, cluster_id: str) -> OKEClusterDetailsInfo:
        """
        Get detailed information about an OKE cluster.

        Args:
            cluster_id: Cluster OCID

        Returns:
            OKEClusterDetailsInfo object
        """
        response = self.container_engine_client.get_cluster(cluster_id)
        cluster = response.data

        # Extract endpoint information
        endpoints = getattr(cluster, "endpoints", None)
        kubernetes_endpoint = None
        public_endpoint = None
        private_endpoint = None
        if endpoints:
            kubernetes_endpoint = getattr(endpoints, "kubernetes", None)
            public_endpoint = getattr(endpoints, "public_endpoint", None)
            private_endpoint = getattr(endpoints, "private_endpoint", None)

        # Extract options
        options = getattr(cluster, "options", None)
        is_public_ip_enabled = False
        is_dashboard_enabled = False
        is_tiller_enabled = False
        pods_cidr = None
        services_cidr = None
        if options:
            add_ons = getattr(options, "add_ons", None)
            if add_ons:
                is_dashboard_enabled = getattr(add_ons, "is_kubernetes_dashboard_enabled", False)
                is_tiller_enabled = getattr(add_ons, "is_tiller_enabled", False)
            kubernetes_network_config = getattr(options, "kubernetes_network_config", None)
            if kubernetes_network_config:
                pods_cidr = getattr(kubernetes_network_config, "pods_cidr", None)
                services_cidr = getattr(kubernetes_network_config, "services_cidr", None)

        # Extract network config
        endpoint_config = getattr(cluster, "endpoint_config", None)
        endpoint_subnet_id = None
        if endpoint_config:
            is_public_ip_enabled = getattr(endpoint_config, "is_public_ip_enabled", False)
            endpoint_subnet_id = getattr(endpoint_config, "subnet_id", None)

        available_upgrades = getattr(cluster, "available_kubernetes_upgrades", None)
        if available_upgrades is None:
            available_upgrades = getattr(cluster, "available_upgrades", None)

        return OKEClusterDetailsInfo(
            cluster_id=cluster.id,
            name=cluster.name,
            kubernetes_version=cluster.kubernetes_version,
            lifecycle_state=cluster.lifecycle_state,
            compartment_id=cluster.compartment_id,
            vcn_id=cluster.vcn_id,
            endpoint_subnet_id=endpoint_subnet_id,
            service_lb_subnet_ids=getattr(cluster, "options", {}).get("service_lb_subnet_ids", [])
            if hasattr(cluster, "options") and isinstance(cluster.options, dict)
            else [],
            available_upgrades=list(available_upgrades or []),
            kubernetes_endpoint=kubernetes_endpoint,
            public_endpoint=public_endpoint,
            private_endpoint=private_endpoint,
            is_public_ip_enabled=is_public_ip_enabled,
            is_kubernetes_dashboard_enabled=is_dashboard_enabled,
            is_tiller_enabled=is_tiller_enabled,
            pods_cidr=pods_cidr,
            services_cidr=services_cidr,
            created_by=getattr(cluster, "created_by_user_id", None),
            time_created=str(cluster.time_created) if cluster.time_created else None,
            time_updated=str(cluster.time_updated) if cluster.time_updated else None,
            freeform_tags=cluster.freeform_tags or {},
            defined_tags=cluster.defined_tags or {},
        )

    def get_kubeconfig(self, cluster_id: str, expiration: int = 2592000) -> str:
        """
        Generate kubeconfig for an OKE cluster.

        Args:
            cluster_id: Cluster OCID
            expiration: Token expiration in seconds (default 30 days)

        Returns:
            Kubeconfig content as string
        """
        response = self.container_engine_client.create_kubeconfig(
            cluster_id,
            oci.container_engine.models.CreateClusterKubeconfigContentDetails(
                token_version="2.0.0",
                expiration=expiration,
            ),
        )
        return response.data.text

    # =========================================================================
    # OKE Node Pool Operations
    # =========================================================================

    def list_node_pools(
        self,
        compartment_id: str,
        cluster_id: Optional[str] = None,
    ) -> list[NodePoolInfo]:
        """
        List node pools in a compartment or cluster.

        Args:
            compartment_id: Compartment OCID
            cluster_id: Optional cluster OCID to filter by

        Returns:
            List of NodePoolInfo objects
        """
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if cluster_id:
            kwargs["cluster_id"] = cluster_id

        response = list_call_get_all_results(
            self.container_engine_client.list_node_pools, **kwargs
        )

        node_pools = []
        for np in response.data or []:
            # Extract node source details
            node_source = getattr(np, "node_source", None)
            node_source_name = None
            node_source_type = None
            node_image_id = None
            node_image_name = None
            if node_source:
                node_source_type = getattr(node_source, "source_type", None)
                node_image_id = getattr(node_source, "image_id", None)
                node_image_name = getattr(node_source, "source_name", None)
                node_source_name = node_image_name

            # Extract shape config
            node_shape_config = getattr(np, "node_shape_config", None)
            ocpus = None
            memory_in_gbs = None
            if node_shape_config:
                ocpus = getattr(node_shape_config, "ocpus", None)
                memory_in_gbs = getattr(node_shape_config, "memory_in_gbs", None)

            # Calculate node count from placement configs
            node_count = 0
            subnet_ids = []
            node_config_details = getattr(np, "node_config_details", None)
            if node_config_details:
                placement_configs = getattr(node_config_details, "placement_configs", None)
                if placement_configs:
                    for pc in placement_configs:
                        subnet_ids.append(getattr(pc, "subnet_id", ""))
                size = getattr(node_config_details, "size", None)
                if size:
                    node_count = size

            node_pools.append(
                NodePoolInfo(
                    node_pool_id=np.id,
                    name=np.name,
                    cluster_id=np.cluster_id,
                    compartment_id=np.compartment_id,
                    kubernetes_version=np.kubernetes_version,
                    node_shape=np.node_shape,
                    node_source_name=node_source_name,
                    node_source_type=node_source_type,
                    node_image_id=node_image_id,
                    node_image_name=node_image_name,
                    initial_node_labels=[
                        {"key": label.key, "value": label.value}
                        for label in (np.initial_node_labels or [])
                    ],
                    quantity_per_subnet=getattr(np, "quantity_per_subnet", None),
                    subnet_ids=subnet_ids,
                    lifecycle_state=np.lifecycle_state,
                    node_count=node_count,
                    ocpus=ocpus,
                    memory_in_gbs=memory_in_gbs,
                    ssh_public_key=getattr(np, "ssh_public_key", None),
                    time_created=str(np.time_created) if np.time_created else None,
                    freeform_tags=np.freeform_tags or {},
                    defined_tags=np.defined_tags or {},
                )
            )

        return node_pools

    def get_node_pool(self, node_pool_id: str) -> NodePoolInfo:
        """
        Get details of a specific node pool.

        Args:
            node_pool_id: Node pool OCID

        Returns:
            NodePoolInfo object
        """
        response = self.container_engine_client.get_node_pool(node_pool_id)
        np = response.data

        # Extract node source details
        node_source = getattr(np, "node_source", None)
        node_source_name = None
        node_source_type = None
        node_image_id = None
        node_image_name = None
        if node_source:
            node_source_type = getattr(node_source, "source_type", None)
            node_image_id = getattr(node_source, "image_id", None)
            node_image_name = getattr(node_source, "source_name", None)
            node_source_name = node_image_name

        # Extract shape config
        node_shape_config = getattr(np, "node_shape_config", None)
        ocpus = None
        memory_in_gbs = None
        if node_shape_config:
            ocpus = getattr(node_shape_config, "ocpus", None)
            memory_in_gbs = getattr(node_shape_config, "memory_in_gbs", None)

        # Calculate node count from placement configs
        node_count = 0
        subnet_ids = []
        node_config_details = getattr(np, "node_config_details", None)
        if node_config_details:
            placement_configs = getattr(node_config_details, "placement_configs", None)
            if placement_configs:
                for pc in placement_configs:
                    subnet_ids.append(getattr(pc, "subnet_id", ""))
            size = getattr(node_config_details, "size", None)
            if size:
                node_count = size

        return NodePoolInfo(
            node_pool_id=np.id,
            name=np.name,
            cluster_id=np.cluster_id,
            compartment_id=np.compartment_id,
            kubernetes_version=np.kubernetes_version,
            node_shape=np.node_shape,
            node_source_name=node_source_name,
            node_source_type=node_source_type,
            node_image_id=node_image_id,
            node_image_name=node_image_name,
            initial_node_labels=[
                {"key": label.key, "value": label.value}
                for label in (np.initial_node_labels or [])
            ],
            quantity_per_subnet=getattr(np, "quantity_per_subnet", None),
            subnet_ids=subnet_ids,
            lifecycle_state=np.lifecycle_state,
            node_count=node_count,
            ocpus=ocpus,
            memory_in_gbs=memory_in_gbs,
            ssh_public_key=getattr(np, "ssh_public_key", None),
            time_created=str(np.time_created) if np.time_created else None,
            freeform_tags=np.freeform_tags or {},
            defined_tags=np.defined_tags or {},
        )

    def list_nodes(self, node_pool_id: str) -> list[NodeInfo]:
        """
        List nodes in a node pool.

        Args:
            node_pool_id: Node pool OCID

        Returns:
            List of NodeInfo objects
        """
        # First get the node pool to find compartment
        np = self.container_engine_client.get_node_pool(node_pool_id).data

        response = self.container_engine_client.list_work_requests(
            compartment_id=np.compartment_id
        )

        # Get nodes from node pool details
        nodes = []
        if hasattr(np, "nodes") and np.nodes:
            for node in np.nodes:
                node_error = None
                if hasattr(node, "node_error") and node.node_error:
                    node_error = getattr(node.node_error, "message", str(node.node_error))

                nodes.append(
                    NodeInfo(
                        node_id=node.id,
                        name=node.name,
                        node_pool_id=node_pool_id,
                        availability_domain=node.availability_domain,
                        subnet_id=node.subnet_id,
                        private_ip=node.private_ip,
                        public_ip=node.public_ip,
                        lifecycle_state=node.lifecycle_state,
                        lifecycle_details=getattr(node, "lifecycle_details", None),
                        kubernetes_version=node.kubernetes_version,
                        node_error=node_error,
                        fault_domain=node.fault_domain,
                        time_created=str(node.time_created) if node.time_created else None,
                    )
                )

        return nodes

    def scale_node_pool(self, node_pool_id: str, size: int) -> WorkRequestInfo:
        """
        Scale a node pool to a specific size.

        Args:
            node_pool_id: Node pool OCID
            size: Target number of nodes

        Returns:
            WorkRequestInfo for the scaling operation
        """
        update_details = oci.container_engine.models.UpdateNodePoolDetails(
            node_config_details=oci.container_engine.models.UpdateNodePoolNodeConfigDetails(
                size=size
            )
        )

        response = self.container_engine_client.update_node_pool(
            node_pool_id, update_details
        )

        work_request_id = response.headers.get("opc-work-request-id")
        return self._get_work_request(work_request_id)

    def _get_work_request(self, work_request_id: str) -> WorkRequestInfo:
        """Get work request details."""
        response = self.container_engine_client.get_work_request(work_request_id)
        wr = response.data

        resources = []
        if hasattr(wr, "resources") and wr.resources:
            for r in wr.resources:
                resources.append({
                    "action_type": r.action_type,
                    "entity_type": r.entity_type,
                    "identifier": r.identifier,
                    "entity_uri": getattr(r, "entity_uri", None),
                })

        return WorkRequestInfo(
            work_request_id=wr.id,
            operation_type=wr.operation_type,
            status=wr.status,
            compartment_id=wr.compartment_id,
            percent_complete=wr.percent_complete or 0.0,
            time_accepted=str(wr.time_accepted) if wr.time_accepted else None,
            time_started=str(wr.time_started) if wr.time_started else None,
            time_finished=str(wr.time_finished) if wr.time_finished else None,
            resources=resources,
        )

    def list_work_requests(
        self,
        compartment_id: str,
        cluster_id: Optional[str] = None,
        status: Optional[list[str]] = None,
    ) -> list[WorkRequestInfo]:
        """
        List work requests for OKE operations.

        Args:
            compartment_id: Compartment OCID
            cluster_id: Optional cluster OCID to filter by
            status: Optional list of statuses to filter by

        Returns:
            List of WorkRequestInfo objects
        """
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if cluster_id:
            kwargs["cluster_id"] = cluster_id
        if status:
            kwargs["status"] = status

        response = list_call_get_all_results(
            self.container_engine_client.list_work_requests, **kwargs
        )

        work_requests = []
        for wr in response.data or []:
            resources = []
            if hasattr(wr, "resources") and wr.resources:
                for r in wr.resources:
                    resources.append({
                        "action_type": r.action_type,
                        "entity_type": r.entity_type,
                        "identifier": r.identifier,
                        "entity_uri": getattr(r, "entity_uri", None),
                    })

            work_requests.append(
                WorkRequestInfo(
                    work_request_id=wr.id,
                    operation_type=wr.operation_type,
                    status=wr.status,
                    compartment_id=wr.compartment_id,
                    percent_complete=wr.percent_complete or 0.0,
                    time_accepted=str(wr.time_accepted) if wr.time_accepted else None,
                    time_started=str(wr.time_started) if wr.time_started else None,
                    time_finished=str(wr.time_finished) if wr.time_finished else None,
                    resources=resources,
                )
            )

        return work_requests

    # =========================================================================
    # Bastion Operations
    # =========================================================================

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

    # =========================================================================
    # DevOps Project Operations
    # =========================================================================

    def list_devops_projects(
        self,
        compartment_id: str,
        name: Optional[str] = None,
        lifecycle_state: Optional[str] = None,
    ) -> list[DevOpsProjectInfo]:
        """
        List DevOps projects in a compartment.

        Args:
            compartment_id: Compartment OCID
            name: Optional project name filter
            lifecycle_state: Optional lifecycle state filter

        Returns:
            List of DevOpsProjectInfo objects
        """
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if name:
            kwargs["name"] = name
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state

        response = list_call_get_all_results(self.devops_client.list_projects, **kwargs)

        projects = []
        for proj in response.data or []:
            projects.append(
                DevOpsProjectInfo(
                    project_id=proj.id,
                    name=proj.name,
                    compartment_id=proj.compartment_id,
                    description=proj.description,
                    namespace=getattr(proj, "namespace", None),
                    notification_config=None,  # Not in summary
                    lifecycle_state=proj.lifecycle_state,
                    time_created=str(proj.time_created) if proj.time_created else None,
                    time_updated=str(proj.time_updated) if proj.time_updated else None,
                    freeform_tags=proj.freeform_tags or {},
                    defined_tags=proj.defined_tags or {},
                )
            )

        return projects

    def get_devops_project(self, project_id: str) -> DevOpsProjectInfo:
        """
        Get details of a DevOps project.

        Args:
            project_id: Project OCID

        Returns:
            DevOpsProjectInfo object
        """
        response = self.devops_client.get_project(project_id)
        proj = response.data

        notification_config = None
        if hasattr(proj, "notification_config") and proj.notification_config:
            notification_config = {
                "topic_id": getattr(proj.notification_config, "topic_id", None),
            }

        return DevOpsProjectInfo(
            project_id=proj.id,
            name=proj.name,
            compartment_id=proj.compartment_id,
            description=proj.description,
            namespace=getattr(proj, "namespace", None),
            notification_config=notification_config,
            lifecycle_state=proj.lifecycle_state,
            time_created=str(proj.time_created) if proj.time_created else None,
            time_updated=str(proj.time_updated) if proj.time_updated else None,
            freeform_tags=proj.freeform_tags or {},
            defined_tags=proj.defined_tags or {},
        )

    # =========================================================================
    # Build Pipeline Operations
    # =========================================================================

    def list_build_pipelines(
        self,
        project_id: str,
        lifecycle_state: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> list[BuildPipelineInfo]:
        """
        List build pipelines in a project.

        Args:
            project_id: DevOps project OCID
            lifecycle_state: Optional lifecycle state filter
            display_name: Optional display name filter

        Returns:
            List of BuildPipelineInfo objects
        """
        kwargs: dict[str, Any] = {"project_id": project_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name:
            kwargs["display_name"] = display_name

        response = list_call_get_all_results(
            self.devops_client.list_build_pipelines, **kwargs
        )

        pipelines = []
        for bp in response.data or []:
            pipelines.append(
                BuildPipelineInfo(
                    build_pipeline_id=bp.id,
                    display_name=bp.display_name,
                    project_id=bp.project_id,
                    compartment_id=bp.compartment_id,
                    description=bp.description,
                    lifecycle_state=bp.lifecycle_state,
                    time_created=str(bp.time_created) if bp.time_created else None,
                    time_updated=str(bp.time_updated) if bp.time_updated else None,
                    build_pipeline_parameters=None,  # Not in summary
                    freeform_tags=bp.freeform_tags or {},
                    defined_tags=bp.defined_tags or {},
                )
            )

        return pipelines

    def get_build_pipeline(self, build_pipeline_id: str) -> BuildPipelineInfo:
        """
        Get details of a build pipeline.

        Args:
            build_pipeline_id: Build pipeline OCID

        Returns:
            BuildPipelineInfo object
        """
        response = self.devops_client.get_build_pipeline(build_pipeline_id)
        bp = response.data

        params = None
        if hasattr(bp, "build_pipeline_parameters") and bp.build_pipeline_parameters:
            params_obj = bp.build_pipeline_parameters
            if hasattr(params_obj, "items"):
                params = {
                    "items": [
                        {
                            "name": p.name,
                            "default_value": p.default_value,
                            "description": getattr(p, "description", None),
                        }
                        for p in params_obj.items
                    ]
                }

        return BuildPipelineInfo(
            build_pipeline_id=bp.id,
            display_name=bp.display_name,
            project_id=bp.project_id,
            compartment_id=bp.compartment_id,
            description=bp.description,
            lifecycle_state=bp.lifecycle_state,
            time_created=str(bp.time_created) if bp.time_created else None,
            time_updated=str(bp.time_updated) if bp.time_updated else None,
            build_pipeline_parameters=params,
            freeform_tags=bp.freeform_tags or {},
            defined_tags=bp.defined_tags or {},
        )

    def list_build_pipeline_stages(
        self, build_pipeline_id: str
    ) -> list[BuildPipelineStageInfo]:
        """
        List stages in a build pipeline.

        Args:
            build_pipeline_id: Build pipeline OCID

        Returns:
            List of BuildPipelineStageInfo objects
        """
        response = list_call_get_all_results(
            self.devops_client.list_build_pipeline_stages,
            build_pipeline_id=build_pipeline_id,
        )

        stages = []
        for stage in response.data or []:
            predecessor_ids = []
            if hasattr(stage, "build_pipeline_stage_predecessor_collection"):
                pred_collection = stage.build_pipeline_stage_predecessor_collection
                if hasattr(pred_collection, "items"):
                    predecessor_ids = [p.id for p in pred_collection.items]

            stages.append(
                BuildPipelineStageInfo(
                    stage_id=stage.id,
                    display_name=stage.display_name,
                    build_pipeline_id=stage.build_pipeline_id,
                    stage_type=stage.build_pipeline_stage_type,
                    compartment_id=stage.compartment_id,
                    description=stage.description,
                    lifecycle_state=stage.lifecycle_state,
                    time_created=str(stage.time_created) if stage.time_created else None,
                    build_spec_file=getattr(stage, "build_spec_file", None),
                    image=getattr(stage, "image", None),
                    primary_build_source=getattr(stage, "primary_build_source", None),
                    stage_execution_timeout_in_seconds=getattr(
                        stage, "stage_execution_timeout_in_seconds", None
                    ),
                    predecessor_stage_ids=predecessor_ids,
                )
            )

        return stages

    # =========================================================================
    # Build Run Operations
    # =========================================================================

    def list_build_runs(
        self,
        project_id: Optional[str] = None,
        build_pipeline_id: Optional[str] = None,
        compartment_id: Optional[str] = None,
        lifecycle_state: Optional[str] = None,
        limit: int = 50,
    ) -> list[BuildRunInfo]:
        """
        List build runs.

        Args:
            project_id: Optional project OCID filter
            build_pipeline_id: Optional build pipeline OCID filter
            compartment_id: Optional compartment OCID filter
            lifecycle_state: Optional lifecycle state filter
            limit: Maximum number of results

        Returns:
            List of BuildRunInfo objects
        """
        kwargs: dict[str, Any] = {"limit": limit}
        if project_id:
            kwargs["project_id"] = project_id
        if build_pipeline_id:
            kwargs["build_pipeline_id"] = build_pipeline_id
        if compartment_id:
            kwargs["compartment_id"] = compartment_id
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state

        response = self.devops_client.list_build_runs(**kwargs)

        runs = []
        for run in response.data.items or []:
            commit_info = None
            if hasattr(run, "commit_info") and run.commit_info:
                commit_info = {
                    "repository_url": getattr(run.commit_info, "repository_url", None),
                    "repository_branch": getattr(run.commit_info, "repository_branch", None),
                    "commit_hash": getattr(run.commit_info, "commit_hash", None),
                }

            runs.append(
                BuildRunInfo(
                    build_run_id=run.id,
                    display_name=run.display_name,
                    build_pipeline_id=run.build_pipeline_id,
                    compartment_id=run.compartment_id,
                    project_id=run.project_id,
                    lifecycle_state=run.lifecycle_state,
                    lifecycle_details=getattr(run, "lifecycle_details", None),
                    time_created=str(run.time_created) if run.time_created else None,
                    time_updated=str(run.time_updated) if run.time_updated else None,
                    time_started=str(run.time_started) if hasattr(run, "time_started") and run.time_started else None,
                    time_finished=str(run.time_finished) if hasattr(run, "time_finished") and run.time_finished else None,
                    commit_info=commit_info,
                    freeform_tags=run.freeform_tags or {},
                    defined_tags=run.defined_tags or {},
                )
            )

        return runs

    def get_build_run(self, build_run_id: str) -> BuildRunInfo:
        """
        Get details of a build run.

        Args:
            build_run_id: Build run OCID

        Returns:
            BuildRunInfo object
        """
        response = self.devops_client.get_build_run(build_run_id)
        run = response.data

        commit_info = None
        if hasattr(run, "commit_info") and run.commit_info:
            commit_info = {
                "repository_url": getattr(run.commit_info, "repository_url", None),
                "repository_branch": getattr(run.commit_info, "repository_branch", None),
                "commit_hash": getattr(run.commit_info, "commit_hash", None),
            }

        build_outputs = None
        if hasattr(run, "build_outputs") and run.build_outputs:
            outputs = run.build_outputs
            build_outputs = {
                "exported_variables": getattr(outputs, "exported_variables", None),
                "delivered_artifacts": getattr(outputs, "delivered_artifacts", None),
                "artifact_override_parameters": getattr(outputs, "artifact_override_parameters", None),
            }

        build_run_source = None
        if hasattr(run, "build_run_source") and run.build_run_source:
            source = run.build_run_source
            build_run_source = {
                "source_type": getattr(source, "source_type", None),
                "trigger_id": getattr(source, "trigger_id", None),
                "trigger_info": getattr(source, "trigger_info", None),
            }

        build_run_progress = None
        if hasattr(run, "build_run_progress") and run.build_run_progress:
            progress = run.build_run_progress
            build_run_progress = {
                "time_started": str(progress.time_started) if hasattr(progress, "time_started") and progress.time_started else None,
                "time_finished": str(progress.time_finished) if hasattr(progress, "time_finished") and progress.time_finished else None,
                "build_pipeline_stage_run_progress": {},
            }
            if hasattr(progress, "build_pipeline_stage_run_progress"):
                for stage_id, stage_progress in (progress.build_pipeline_stage_run_progress or {}).items():
                    build_run_progress["build_pipeline_stage_run_progress"][stage_id] = {
                        "stage_display_name": getattr(stage_progress, "stage_display_name", None),
                        "status": getattr(stage_progress, "status", None),
                        "time_started": str(stage_progress.time_started) if hasattr(stage_progress, "time_started") and stage_progress.time_started else None,
                        "time_finished": str(stage_progress.time_finished) if hasattr(stage_progress, "time_finished") and stage_progress.time_finished else None,
                    }

        return BuildRunInfo(
            build_run_id=run.id,
            display_name=run.display_name,
            build_pipeline_id=run.build_pipeline_id,
            compartment_id=run.compartment_id,
            project_id=run.project_id,
            lifecycle_state=run.lifecycle_state,
            lifecycle_details=getattr(run, "lifecycle_details", None),
            time_created=str(run.time_created) if run.time_created else None,
            time_updated=str(run.time_updated) if run.time_updated else None,
            time_started=str(run.time_started) if hasattr(run, "time_started") and run.time_started else None,
            time_finished=str(run.time_finished) if hasattr(run, "time_finished") and run.time_finished else None,
            commit_info=commit_info,
            build_outputs=build_outputs,
            build_run_source=build_run_source,
            build_run_progress=build_run_progress,
            freeform_tags=run.freeform_tags or {},
            defined_tags=run.defined_tags or {},
        )

    def trigger_build_run(
        self,
        build_pipeline_id: str,
        display_name: Optional[str] = None,
        commit_info: Optional[dict[str, str]] = None,
        build_run_arguments: Optional[dict[str, str]] = None,
    ) -> BuildRunInfo:
        """
        Trigger a new build run.

        Args:
            build_pipeline_id: Build pipeline OCID
            display_name: Optional display name for the build run
            commit_info: Optional commit information (repository_url, repository_branch, commit_hash)
            build_run_arguments: Optional build arguments as key-value pairs

        Returns:
            BuildRunInfo object for the new build run
        """
        create_details = oci.devops.models.CreateBuildRunDetails(
            build_pipeline_id=build_pipeline_id,
        )

        if display_name:
            create_details.display_name = display_name

        if commit_info:
            create_details.commit_info = oci.devops.models.CommitInfo(
                repository_url=commit_info.get("repository_url"),
                repository_branch=commit_info.get("repository_branch"),
                commit_hash=commit_info.get("commit_hash"),
            )

        if build_run_arguments:
            items = [
                oci.devops.models.BuildRunArgumentItem(name=k, value=v)
                for k, v in build_run_arguments.items()
            ]
            create_details.build_run_arguments = oci.devops.models.BuildRunArguments(items=items)

        response = self.devops_client.create_build_run(create_details)
        return self.get_build_run(response.data.id)

    def cancel_build_run(self, build_run_id: str, reason: Optional[str] = None) -> BuildRunInfo:
        """
        Cancel a running build.

        Args:
            build_run_id: Build run OCID
            reason: Optional cancellation reason

        Returns:
            Updated BuildRunInfo object
        """
        cancel_details = oci.devops.models.CancelBuildRunDetails(
            reason=reason or "Cancelled via MCP"
        )

        self.devops_client.cancel_build_run(build_run_id, cancel_details)
        return self.get_build_run(build_run_id)

    # =========================================================================
    # Deploy Pipeline Operations
    # =========================================================================

    def list_deploy_pipelines(
        self,
        project_id: str,
        lifecycle_state: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> list[DeployPipelineInfo]:
        """
        List deployment pipelines in a project.

        Args:
            project_id: DevOps project OCID
            lifecycle_state: Optional lifecycle state filter
            display_name: Optional display name filter

        Returns:
            List of DeployPipelineInfo objects
        """
        kwargs: dict[str, Any] = {"project_id": project_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name:
            kwargs["display_name"] = display_name

        response = list_call_get_all_results(
            self.devops_client.list_deploy_pipelines, **kwargs
        )

        pipelines = []
        for dp in response.data or []:
            pipelines.append(
                DeployPipelineInfo(
                    deploy_pipeline_id=dp.id,
                    display_name=dp.display_name,
                    project_id=dp.project_id,
                    compartment_id=dp.compartment_id,
                    description=dp.description,
                    lifecycle_state=dp.lifecycle_state,
                    time_created=str(dp.time_created) if dp.time_created else None,
                    time_updated=str(dp.time_updated) if dp.time_updated else None,
                    deploy_pipeline_parameters=None,  # Not in summary
                    freeform_tags=dp.freeform_tags or {},
                    defined_tags=dp.defined_tags or {},
                )
            )

        return pipelines

    def get_deploy_pipeline(self, deploy_pipeline_id: str) -> DeployPipelineInfo:
        """
        Get details of a deployment pipeline.

        Args:
            deploy_pipeline_id: Deploy pipeline OCID

        Returns:
            DeployPipelineInfo object
        """
        response = self.devops_client.get_deploy_pipeline(deploy_pipeline_id)
        dp = response.data

        params = None
        if hasattr(dp, "deploy_pipeline_parameters") and dp.deploy_pipeline_parameters:
            params_obj = dp.deploy_pipeline_parameters
            if hasattr(params_obj, "items"):
                params = {
                    "items": [
                        {
                            "name": p.name,
                            "default_value": p.default_value,
                            "description": getattr(p, "description", None),
                        }
                        for p in params_obj.items
                    ]
                }

        return DeployPipelineInfo(
            deploy_pipeline_id=dp.id,
            display_name=dp.display_name,
            project_id=dp.project_id,
            compartment_id=dp.compartment_id,
            description=dp.description,
            lifecycle_state=dp.lifecycle_state,
            time_created=str(dp.time_created) if dp.time_created else None,
            time_updated=str(dp.time_updated) if dp.time_updated else None,
            deploy_pipeline_parameters=params,
            freeform_tags=dp.freeform_tags or {},
            defined_tags=dp.defined_tags or {},
        )

    def list_deploy_stages(self, deploy_pipeline_id: str) -> list[DeployStageInfo]:
        """
        List stages in a deployment pipeline.

        Args:
            deploy_pipeline_id: Deploy pipeline OCID

        Returns:
            List of DeployStageInfo objects
        """
        response = list_call_get_all_results(
            self.devops_client.list_deploy_stages,
            deploy_pipeline_id=deploy_pipeline_id,
        )

        stages = []
        for stage in response.data or []:
            predecessor_ids = []
            if hasattr(stage, "deploy_stage_predecessor_collection"):
                pred_collection = stage.deploy_stage_predecessor_collection
                if hasattr(pred_collection, "items"):
                    predecessor_ids = [p.id for p in pred_collection.items]

            stages.append(
                DeployStageInfo(
                    stage_id=stage.id,
                    display_name=stage.display_name,
                    deploy_pipeline_id=stage.deploy_pipeline_id,
                    stage_type=stage.deploy_stage_type,
                    compartment_id=stage.compartment_id,
                    project_id=stage.project_id,
                    description=stage.description,
                    lifecycle_state=stage.lifecycle_state,
                    time_created=str(stage.time_created) if stage.time_created else None,
                    time_updated=str(stage.time_updated) if stage.time_updated else None,
                    deploy_environment_id=getattr(stage, "deploy_environment_id_for_update", None)
                    or getattr(stage, "oke_cluster_deploy_environment_id", None),
                    predecessor_stage_ids=predecessor_ids,
                    oke_cluster_id=getattr(stage, "oke_cluster_id", None),
                    kubernetes_manifest_artifact_ids=getattr(
                        stage, "kubernetes_manifest_deploy_artifact_ids", None
                    )
                    or [],
                    namespace=getattr(stage, "namespace", None),
                    helm_chart_artifact_id=getattr(stage, "helm_chart_deploy_artifact_id", None),
                    release_name=getattr(stage, "release_name", None),
                    approval_policy=None,  # Will be extracted if needed
                    wait_duration=getattr(stage, "wait_criteria", {}).get("wait_duration")
                    if hasattr(stage, "wait_criteria") and stage.wait_criteria
                    else None,
                )
            )

        return stages

    # =========================================================================
    # Deployment Operations
    # =========================================================================

    def list_deployments(
        self,
        project_id: Optional[str] = None,
        deploy_pipeline_id: Optional[str] = None,
        compartment_id: Optional[str] = None,
        lifecycle_state: Optional[str] = None,
        limit: int = 50,
    ) -> list[DeploymentInfo]:
        """
        List deployments.

        Args:
            project_id: Optional project OCID filter
            deploy_pipeline_id: Optional deploy pipeline OCID filter
            compartment_id: Optional compartment OCID filter
            lifecycle_state: Optional lifecycle state filter
            limit: Maximum number of results

        Returns:
            List of DeploymentInfo objects
        """
        kwargs: dict[str, Any] = {"limit": limit}
        if project_id:
            kwargs["project_id"] = project_id
        if deploy_pipeline_id:
            kwargs["deploy_pipeline_id"] = deploy_pipeline_id
        if compartment_id:
            kwargs["compartment_id"] = compartment_id
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state

        response = self.devops_client.list_deployments(**kwargs)

        deployments = []
        for dep in response.data.items or []:
            deployments.append(
                DeploymentInfo(
                    deployment_id=dep.id,
                    display_name=dep.display_name,
                    deploy_pipeline_id=dep.deploy_pipeline_id,
                    compartment_id=dep.compartment_id,
                    project_id=dep.project_id,
                    deployment_type=dep.deployment_type,
                    lifecycle_state=dep.lifecycle_state,
                    lifecycle_details=getattr(dep, "lifecycle_details", None),
                    time_created=str(dep.time_created) if dep.time_created else None,
                    time_updated=str(dep.time_updated) if dep.time_updated else None,
                    freeform_tags=dep.freeform_tags or {},
                    defined_tags=dep.defined_tags or {},
                )
            )

        return deployments

    def get_deployment(self, deployment_id: str) -> DeploymentInfo:
        """
        Get details of a deployment.

        Args:
            deployment_id: Deployment OCID

        Returns:
            DeploymentInfo object
        """
        response = self.devops_client.get_deployment(deployment_id)
        dep = response.data

        deployment_arguments = None
        if hasattr(dep, "deployment_arguments") and dep.deployment_arguments:
            args = dep.deployment_arguments
            if hasattr(args, "items"):
                deployment_arguments = {
                    "items": [
                        {"name": item.name, "value": item.value}
                        for item in args.items
                    ]
                }

        execution_progress = None
        if hasattr(dep, "deployment_execution_progress") and dep.deployment_execution_progress:
            progress = dep.deployment_execution_progress
            execution_progress = {
                "time_started": str(progress.time_started) if hasattr(progress, "time_started") and progress.time_started else None,
                "time_finished": str(progress.time_finished) if hasattr(progress, "time_finished") and progress.time_finished else None,
                "deploy_stage_execution_progress": {},
            }
            if hasattr(progress, "deploy_stage_execution_progress"):
                for stage_id, stage_progress in (progress.deploy_stage_execution_progress or {}).items():
                    execution_progress["deploy_stage_execution_progress"][stage_id] = {
                        "stage_display_name": getattr(stage_progress, "deploy_stage_display_name", None),
                        "status": getattr(stage_progress, "status", None),
                        "time_started": str(stage_progress.time_started) if hasattr(stage_progress, "time_started") and stage_progress.time_started else None,
                        "time_finished": str(stage_progress.time_finished) if hasattr(stage_progress, "time_finished") and stage_progress.time_finished else None,
                    }

        return DeploymentInfo(
            deployment_id=dep.id,
            display_name=dep.display_name,
            deploy_pipeline_id=dep.deploy_pipeline_id,
            compartment_id=dep.compartment_id,
            project_id=dep.project_id,
            deployment_type=dep.deployment_type,
            lifecycle_state=dep.lifecycle_state,
            lifecycle_details=getattr(dep, "lifecycle_details", None),
            time_created=str(dep.time_created) if dep.time_created else None,
            time_updated=str(dep.time_updated) if dep.time_updated else None,
            deploy_stage_id=getattr(dep, "deploy_stage_id", None),
            deployment_arguments=deployment_arguments,
            deployment_execution_progress=execution_progress,
            freeform_tags=dep.freeform_tags or {},
            defined_tags=dep.defined_tags or {},
        )

    def create_deployment(
        self,
        deploy_pipeline_id: str,
        display_name: Optional[str] = None,
        deployment_arguments: Optional[dict[str, str]] = None,
        deploy_stage_id: Optional[str] = None,
        previous_deployment_id: Optional[str] = None,
    ) -> DeploymentInfo:
        """
        Create a new deployment (trigger a deployment pipeline).

        Args:
            deploy_pipeline_id: Deploy pipeline OCID
            display_name: Optional display name
            deployment_arguments: Optional deployment arguments as key-value pairs
            deploy_stage_id: Optional specific stage to deploy (for single stage deployment)
            previous_deployment_id: Optional previous deployment ID (for redeployment)

        Returns:
            DeploymentInfo object
        """
        if previous_deployment_id:
            # Create a redeployment
            create_details = oci.devops.models.CreateDeployPipelineRedeploymentDetails(
                deploy_pipeline_id=deploy_pipeline_id,
                previous_deployment_id=previous_deployment_id,
            )
        elif deploy_stage_id:
            # Create a single stage deployment
            create_details = oci.devops.models.CreateSingleDeployStageDeploymentDetails(
                deploy_pipeline_id=deploy_pipeline_id,
                deploy_stage_id=deploy_stage_id,
            )
        else:
            # Create a full pipeline deployment
            create_details = oci.devops.models.CreateDeployPipelineDeploymentDetails(
                deploy_pipeline_id=deploy_pipeline_id,
            )

        if display_name:
            create_details.display_name = display_name

        if deployment_arguments:
            items = [
                oci.devops.models.DeploymentArgumentItem(name=k, value=v)
                for k, v in deployment_arguments.items()
            ]
            create_details.deployment_arguments = oci.devops.models.DeploymentArgumentCollection(
                items=items
            )

        response = self.devops_client.create_deployment(create_details)
        return self.get_deployment(response.data.id)

    def approve_deployment(
        self,
        deployment_id: str,
        stage_id: str,
        action: str = "APPROVE",
        reason: Optional[str] = None,
    ) -> DeploymentInfo:
        """
        Approve or reject a deployment stage waiting for approval.

        Args:
            deployment_id: Deployment OCID
            stage_id: Stage OCID requiring approval
            action: APPROVE or REJECT
            reason: Optional reason for the action

        Returns:
            Updated DeploymentInfo object
        """
        approve_details = oci.devops.models.ApproveDeploymentDetails(
            deploy_stage_id=stage_id,
            action=action,
            reason=reason,
        )

        self.devops_client.approve_deployment(deployment_id, approve_details)
        return self.get_deployment(deployment_id)

    def cancel_deployment(self, deployment_id: str, reason: Optional[str] = None) -> DeploymentInfo:
        """
        Cancel a running deployment.

        Args:
            deployment_id: Deployment OCID
            reason: Optional cancellation reason

        Returns:
            Updated DeploymentInfo object
        """
        cancel_details = oci.devops.models.CancelDeploymentDetails(
            reason=reason or "Cancelled via MCP"
        )

        self.devops_client.cancel_deployment(deployment_id, cancel_details)
        return self.get_deployment(deployment_id)

    # =========================================================================
    # Deploy Artifacts Operations
    # =========================================================================

    def list_deploy_artifacts(
        self,
        project_id: str,
        lifecycle_state: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> list[DeployArtifactInfo]:
        """
        List deployment artifacts in a project.

        Args:
            project_id: DevOps project OCID
            lifecycle_state: Optional lifecycle state filter
            display_name: Optional display name filter

        Returns:
            List of DeployArtifactInfo objects
        """
        kwargs: dict[str, Any] = {"project_id": project_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name:
            kwargs["display_name"] = display_name

        response = list_call_get_all_results(
            self.devops_client.list_deploy_artifacts, **kwargs
        )

        artifacts = []
        for art in response.data or []:
            source = None
            if hasattr(art, "deploy_artifact_source") and art.deploy_artifact_source:
                src = art.deploy_artifact_source
                source = {
                    "deploy_artifact_source_type": getattr(src, "deploy_artifact_source_type", None),
                }
                if hasattr(src, "image_uri"):
                    source["image_uri"] = src.image_uri
                if hasattr(src, "repository_id"):
                    source["repository_id"] = src.repository_id

            artifacts.append(
                DeployArtifactInfo(
                    artifact_id=art.id,
                    display_name=art.display_name,
                    project_id=art.project_id,
                    compartment_id=art.compartment_id,
                    description=art.description,
                    artifact_type=art.deploy_artifact_type,
                    artifact_source_type=getattr(art, "deploy_artifact_source", {}).deploy_artifact_source_type
                    if hasattr(art, "deploy_artifact_source") and art.deploy_artifact_source
                    else None,
                    deploy_artifact_source=source,
                    argument_substitution_mode=art.argument_substitution_mode,
                    lifecycle_state=art.lifecycle_state,
                    time_created=str(art.time_created) if art.time_created else None,
                    time_updated=str(art.time_updated) if art.time_updated else None,
                    freeform_tags=art.freeform_tags or {},
                    defined_tags=art.defined_tags or {},
                )
            )

        return artifacts

    # =========================================================================
    # Deploy Environments Operations
    # =========================================================================

    def list_deploy_environments(
        self,
        project_id: str,
        lifecycle_state: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> list[DeployEnvironmentInfo]:
        """
        List deployment environments in a project.

        Args:
            project_id: DevOps project OCID
            lifecycle_state: Optional lifecycle state filter
            display_name: Optional display name filter

        Returns:
            List of DeployEnvironmentInfo objects
        """
        kwargs: dict[str, Any] = {"project_id": project_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name:
            kwargs["display_name"] = display_name

        response = list_call_get_all_results(
            self.devops_client.list_deploy_environments, **kwargs
        )

        environments = []
        for env in response.data or []:
            cluster_id = None
            function_id = None
            compute_selectors = None

            env_type = env.deploy_environment_type
            if env_type == "OKE_CLUSTER":
                cluster_id = getattr(env, "cluster_id", None)
            elif env_type == "FUNCTION":
                function_id = getattr(env, "function_id", None)
            elif env_type == "COMPUTE_INSTANCE_GROUP":
                if hasattr(env, "compute_instance_group_selectors"):
                    compute_selectors = {
                        "items": [
                            {
                                "selector_type": s.selector_type,
                                "compute_instance_ids": getattr(s, "compute_instance_ids", None),
                                "query": getattr(s, "query", None),
                                "region": getattr(s, "region", None),
                            }
                            for s in (env.compute_instance_group_selectors.items or [])
                        ]
                    }

            environments.append(
                DeployEnvironmentInfo(
                    environment_id=env.id,
                    display_name=env.display_name,
                    project_id=env.project_id,
                    compartment_id=env.compartment_id,
                    description=env.description,
                    environment_type=env_type,
                    lifecycle_state=env.lifecycle_state,
                    time_created=str(env.time_created) if env.time_created else None,
                    time_updated=str(env.time_updated) if env.time_updated else None,
                    cluster_id=cluster_id,
                    compute_instance_group_selectors=compute_selectors,
                    function_id=function_id,
                    freeform_tags=env.freeform_tags or {},
                    defined_tags=env.defined_tags or {},
                )
            )

        return environments

    # =========================================================================
    # DevOps Repository Operations
    # =========================================================================

    def list_repositories(
        self,
        project_id: str,
        lifecycle_state: Optional[str] = None,
        name: Optional[str] = None,
    ) -> list[DevOpsRepositoryInfo]:
        """
        List code repositories in a DevOps project.

        Args:
            project_id: DevOps project OCID
            lifecycle_state: Optional lifecycle state filter
            name: Optional name filter

        Returns:
            List of DevOpsRepositoryInfo objects
        """
        kwargs: dict[str, Any] = {"project_id": project_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if name:
            kwargs["name"] = name

        response = list_call_get_all_results(self.devops_client.list_repositories, **kwargs)

        repositories = []
        for repo in response.data or []:
            mirror_config = None
            if hasattr(repo, "mirror_repository_config") and repo.mirror_repository_config:
                cfg = repo.mirror_repository_config
                mirror_config = {
                    "connector_id": getattr(cfg, "connector_id", None),
                    "repository_url": getattr(cfg, "repository_url", None),
                    "trigger_schedule": getattr(cfg, "trigger_schedule", None),
                }

            repositories.append(
                DevOpsRepositoryInfo(
                    repository_id=repo.id,
                    name=repo.name,
                    project_id=repo.project_id,
                    compartment_id=repo.compartment_id,
                    description=repo.description,
                    namespace=getattr(repo, "namespace", None),
                    project_name=getattr(repo, "project_name", None),
                    default_branch=repo.default_branch,
                    repository_type=repo.repository_type,
                    ssh_url=repo.ssh_url,
                    http_url=repo.http_url,
                    mirror_repository_config=mirror_config,
                    lifecycle_state=repo.lifecycle_state,
                    time_created=str(repo.time_created) if repo.time_created else None,
                    time_updated=str(repo.time_updated) if repo.time_updated else None,
                    freeform_tags=repo.freeform_tags or {},
                    defined_tags=repo.defined_tags or {},
                )
            )

        return repositories

    def get_repository(self, repository_id: str) -> DevOpsRepositoryInfo:
        """
        Get details of a code repository.

        Args:
            repository_id: Repository OCID

        Returns:
            DevOpsRepositoryInfo object
        """
        response = self.devops_client.get_repository(repository_id)
        repo = response.data

        mirror_config = None
        if hasattr(repo, "mirror_repository_config") and repo.mirror_repository_config:
            cfg = repo.mirror_repository_config
            mirror_config = {
                "connector_id": getattr(cfg, "connector_id", None),
                "repository_url": getattr(cfg, "repository_url", None),
                "trigger_schedule": getattr(cfg, "trigger_schedule", None),
            }

        return DevOpsRepositoryInfo(
            repository_id=repo.id,
            name=repo.name,
            project_id=repo.project_id,
            compartment_id=repo.compartment_id,
            description=repo.description,
            namespace=getattr(repo, "namespace", None),
            project_name=getattr(repo, "project_name", None),
            default_branch=repo.default_branch,
            repository_type=repo.repository_type,
            ssh_url=repo.ssh_url,
            http_url=repo.http_url,
            mirror_repository_config=mirror_config,
            lifecycle_state=repo.lifecycle_state,
            time_created=str(repo.time_created) if repo.time_created else None,
            time_updated=str(repo.time_updated) if repo.time_updated else None,
            freeform_tags=repo.freeform_tags or {},
            defined_tags=repo.defined_tags or {},
        )

    def list_repository_refs(
        self,
        repository_id: str,
        ref_type: Optional[str] = None,
        ref_name: Optional[str] = None,
    ) -> list[RepositoryBranchInfo]:
        """
        List refs (branches/tags) in a repository.

        Args:
            repository_id: Repository OCID
            ref_type: Optional ref type filter (BRANCH, TAG)
            ref_name: Optional ref name filter

        Returns:
            List of RepositoryBranchInfo objects
        """
        kwargs: dict[str, Any] = {"repository_id": repository_id}
        if ref_type:
            kwargs["ref_type"] = ref_type
        if ref_name:
            kwargs["ref_name"] = ref_name

        response = list_call_get_all_results(self.devops_client.list_refs, **kwargs)

        refs = []
        for ref in response.data or []:
            refs.append(
                RepositoryBranchInfo(
                    ref_name=ref.ref_name,
                    ref_type=ref.ref_type,
                    full_ref_name=getattr(ref, "full_ref_name", None),
                    commit_id=ref.commit_id,
                    repository_id=repository_id,
                )
            )

        return refs

    def list_repository_commits(
        self,
        repository_id: str,
        ref_name: Optional[str] = None,
        limit: int = 50,
    ) -> list[RepositoryCommitInfo]:
        """
        List commits in a repository.

        Args:
            repository_id: Repository OCID
            ref_name: Optional branch/tag name to list commits from
            limit: Maximum number of commits to return

        Returns:
            List of RepositoryCommitInfo objects
        """
        kwargs: dict[str, Any] = {"repository_id": repository_id, "limit": limit}
        if ref_name:
            kwargs["ref_name"] = ref_name

        response = self.devops_client.list_commits(**kwargs)

        commits = []
        for commit in response.data.items or []:
            commits.append(
                RepositoryCommitInfo(
                    commit_id=commit.commit_id,
                    commit_message=commit.commit_message,
                    author_name=getattr(commit, "author_name", None),
                    author_email=getattr(commit, "author_email", None),
                    committer_name=getattr(commit, "committer_name", None),
                    committer_email=getattr(commit, "committer_email", None),
                    time_created=str(commit.time_created) if commit.time_created else None,
                    parent_commit_ids=commit.parent_commit_ids or [],
                )
            )

        return commits

    # =========================================================================
    # Trigger Operations
    # =========================================================================

    def list_triggers(
        self,
        project_id: str,
        lifecycle_state: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> list[TriggerInfo]:
        """
        List triggers in a project.

        Args:
            project_id: DevOps project OCID
            lifecycle_state: Optional lifecycle state filter
            display_name: Optional display name filter

        Returns:
            List of TriggerInfo objects
        """
        kwargs: dict[str, Any] = {"project_id": project_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name:
            kwargs["display_name"] = display_name

        response = list_call_get_all_results(self.devops_client.list_triggers, **kwargs)

        triggers = []
        for trigger in response.data or []:
            actions = []
            if hasattr(trigger, "actions") and trigger.actions:
                for action in trigger.actions:
                    actions.append({
                        "type": action.type,
                        "build_pipeline_id": getattr(action, "build_pipeline_id", None),
                        "filter": getattr(action, "filter", None),
                    })

            triggers.append(
                TriggerInfo(
                    trigger_id=trigger.id,
                    display_name=trigger.display_name,
                    project_id=trigger.project_id,
                    compartment_id=trigger.compartment_id,
                    description=trigger.description,
                    trigger_source=trigger.trigger_source,
                    lifecycle_state=trigger.lifecycle_state,
                    time_created=str(trigger.time_created) if trigger.time_created else None,
                    time_updated=str(trigger.time_updated) if trigger.time_updated else None,
                    actions=actions,
                    freeform_tags=trigger.freeform_tags or {},
                    defined_tags=trigger.defined_tags or {},
                )
            )

        return triggers

    # =========================================================================
    # Connection Operations
    # =========================================================================

    def list_connections(
        self,
        project_id: str,
        lifecycle_state: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> list[ConnectionInfo]:
        """
        List external SCM connections in a project.

        Args:
            project_id: DevOps project OCID
            lifecycle_state: Optional lifecycle state filter
            display_name: Optional display name filter

        Returns:
            List of ConnectionInfo objects
        """
        kwargs: dict[str, Any] = {"project_id": project_id}
        if lifecycle_state:
            kwargs["lifecycle_state"] = lifecycle_state
        if display_name:
            kwargs["display_name"] = display_name

        response = list_call_get_all_results(self.devops_client.list_connections, **kwargs)

        connections = []
        for conn in response.data or []:
            connections.append(
                ConnectionInfo(
                    connection_id=conn.id,
                    display_name=conn.display_name,
                    project_id=conn.project_id,
                    compartment_id=conn.compartment_id,
                    description=conn.description,
                    connection_type=conn.connection_type,
                    lifecycle_state=conn.lifecycle_state,
                    time_created=str(conn.time_created) if conn.time_created else None,
                    time_updated=str(conn.time_updated) if conn.time_updated else None,
                    freeform_tags=conn.freeform_tags or {},
                    defined_tags=conn.defined_tags or {},
                )
            )

        return connections

    # =========================================================================
    # Utility Methods
    # =========================================================================

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

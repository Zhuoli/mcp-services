"""Unit tests for Oracle Cloud MCP server."""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from mcp_servers.oracle_cloud import tools
from mcp_servers.oracle_cloud.client import OCIClient
from mcp_servers.oracle_cloud.models import (
    CompartmentInfo,
    InstanceInfo,
    OKEClusterInfo,
    OKEClusterDetailsInfo,
    NodePoolInfo,
    NodeInfo,
    WorkRequestInfo,
    BastionInfo,
    DevOpsProjectInfo,
    BuildPipelineInfo,
    BuildRunInfo,
    DeployPipelineInfo,
    DeploymentInfo,
    DeployArtifactInfo,
    DeployEnvironmentInfo,
    DevOpsRepositoryInfo,
    TriggerInfo,
    ConnectionInfo,
)


class TestOCIClientInit:
    """Tests for OCIClient initialization."""

    @patch("mcp_servers.oracle_cloud.client.OCIAuthenticator")
    def test_client_init(self, mock_auth_class):
        """Test client initialization."""
        mock_auth = MagicMock()
        mock_auth.authenticate.return_value = ({"region": "us-phoenix-1"}, MagicMock())
        mock_auth_class.return_value = mock_auth

        client = OCIClient(region="us-phoenix-1", profile_name="DEFAULT")

        assert client.config.region == "us-phoenix-1"
        assert client.config.profile_name == "DEFAULT"
        mock_auth.authenticate.assert_called_once()


class TestCompartmentTools:
    """Tests for compartment-related tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_compartments(self, mock_get_client, mock_compartment_data):
        """Test list_compartments_tool."""
        mock_client = MagicMock()
        mock_client.list_compartments.return_value = [
            CompartmentInfo(
                compartment_id="ocid1.compartment.oc1..test",
                name="test-compartment",
                description="Test",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_compartments_tool({
            "region": "us-phoenix-1",
            "compartment_id": "ocid1.tenancy.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["compartments"][0]["name"] == "test-compartment"


class TestInstanceTools:
    """Tests for compute instance tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_instances(self, mock_get_client):
        """Test list_instances_tool."""
        mock_client = MagicMock()
        mock_client.list_instances.return_value = [
            InstanceInfo(
                instance_id="ocid1.instance.oc1..test",
                display_name="test-instance",
                private_ip="10.0.0.1",
                public_ip=None,
                subnet_id="ocid1.subnet.oc1..test",
                shape="VM.Standard.E4.Flex",
                availability_domain="AD-1",
                lifecycle_state="RUNNING",
                metadata={},
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_instances_tool({
            "region": "us-phoenix-1",
            "compartment_id": "ocid1.compartment.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["instances"][0]["display_name"] == "test-instance"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_instances_oke_only(self, mock_get_client):
        """Test list_instances_tool with oke_only filter."""
        mock_client = MagicMock()
        mock_client.list_instances.return_value = [
            InstanceInfo(
                instance_id="ocid1.instance.oc1..test1",
                display_name="oke-node-1",
                private_ip="10.0.0.1",
                public_ip=None,
                subnet_id="ocid1.subnet.oc1..test",
                shape="VM.Standard.E4.Flex",
                availability_domain="AD-1",
                lifecycle_state="RUNNING",
                metadata={"oke-cluster-display-name": "test-cluster"},
            ),
            InstanceInfo(
                instance_id="ocid1.instance.oc1..test2",
                display_name="regular-instance",
                private_ip="10.0.0.2",
                public_ip=None,
                subnet_id="ocid1.subnet.oc1..test",
                shape="VM.Standard.E4.Flex",
                availability_domain="AD-1",
                lifecycle_state="RUNNING",
                metadata={},
            ),
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_instances_tool({
            "region": "us-phoenix-1",
            "compartment_id": "ocid1.compartment.oc1..test",
            "oke_only": True,
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["oke_only"] is True


class TestOKEClusterTools:
    """Tests for OKE cluster tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_oke_clusters(self, mock_get_client):
        """Test list_oke_clusters_tool."""
        mock_client = MagicMock()
        mock_client.list_oke_clusters.return_value = [
            OKEClusterInfo(
                cluster_id="ocid1.cluster.oc1..test",
                name="test-cluster",
                kubernetes_version="v1.28.2",
                lifecycle_state="ACTIVE",
                compartment_id="ocid1.compartment.oc1..test",
                available_upgrades=["v1.29.0"],
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_oke_clusters_tool({
            "region": "us-phoenix-1",
            "compartment_id": "ocid1.compartment.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["clusters"][0]["name"] == "test-cluster"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_get_oke_cluster(self, mock_get_client):
        """Test get_oke_cluster_tool."""
        mock_client = MagicMock()
        mock_client.get_oke_cluster.return_value = OKEClusterDetailsInfo(
            cluster_id="ocid1.cluster.oc1..test",
            name="test-cluster",
            kubernetes_version="v1.28.2",
            lifecycle_state="ACTIVE",
            compartment_id="ocid1.compartment.oc1..test",
            vcn_id="ocid1.vcn.oc1..test",
            endpoint_subnet_id="ocid1.subnet.oc1..test",
            service_lb_subnet_ids=[],
            available_upgrades=["v1.29.0"],
            kubernetes_endpoint="https://cluster.oraclecloud.com",
            public_endpoint="https://public.cluster.oraclecloud.com",
            private_endpoint="https://private.cluster.oraclecloud.com",
            is_public_ip_enabled=True,
            is_kubernetes_dashboard_enabled=False,
            is_tiller_enabled=False,
            pods_cidr="10.244.0.0/16",
            services_cidr="10.96.0.0/16",
        )
        mock_get_client.return_value = mock_client

        result = await tools.get_oke_cluster_tool({
            "region": "us-phoenix-1",
            "cluster_id": "ocid1.cluster.oc1..test",
        })

        data = json.loads(result)
        assert data["cluster"]["name"] == "test-cluster"
        assert data["cluster"]["kubernetes_version"] == "v1.28.2"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_get_kubeconfig(self, mock_get_client):
        """Test get_kubeconfig_tool."""
        mock_client = MagicMock()
        mock_client.get_kubeconfig.return_value = "apiVersion: v1\nkind: Config\n..."
        mock_get_client.return_value = mock_client

        result = await tools.get_kubeconfig_tool({
            "region": "us-phoenix-1",
            "cluster_id": "ocid1.cluster.oc1..test",
        })

        data = json.loads(result)
        assert "kubeconfig" in data
        assert data["kubeconfig"].startswith("apiVersion")


class TestNodePoolTools:
    """Tests for node pool tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_node_pools(self, mock_get_client):
        """Test list_node_pools_tool."""
        mock_client = MagicMock()
        mock_client.list_node_pools.return_value = [
            NodePoolInfo(
                node_pool_id="ocid1.nodepool.oc1..test",
                name="test-pool",
                cluster_id="ocid1.cluster.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                kubernetes_version="v1.28.2",
                node_shape="VM.Standard.E4.Flex",
                lifecycle_state="ACTIVE",
                node_count=3,
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_node_pools_tool({
            "region": "us-phoenix-1",
            "compartment_id": "ocid1.compartment.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["node_pools"][0]["name"] == "test-pool"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_get_node_pool(self, mock_get_client):
        """Test get_node_pool_tool."""
        mock_client = MagicMock()
        mock_client.get_node_pool.return_value = NodePoolInfo(
            node_pool_id="ocid1.nodepool.oc1..test",
            name="test-pool",
            cluster_id="ocid1.cluster.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            kubernetes_version="v1.28.2",
            node_shape="VM.Standard.E4.Flex",
            lifecycle_state="ACTIVE",
            node_count=3,
            ocpus=2.0,
            memory_in_gbs=16.0,
        )
        mock_get_client.return_value = mock_client

        result = await tools.get_node_pool_tool({
            "region": "us-phoenix-1",
            "node_pool_id": "ocid1.nodepool.oc1..test",
        })

        data = json.loads(result)
        assert data["node_pool"]["name"] == "test-pool"
        assert data["node_pool"]["node_count"] == 3

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_nodes(self, mock_get_client):
        """Test list_nodes_tool."""
        mock_client = MagicMock()
        mock_client.list_nodes.return_value = [
            NodeInfo(
                node_id="ocid1.node.oc1..test",
                name="oke-node-1",
                node_pool_id="ocid1.nodepool.oc1..test",
                availability_domain="AD-1",
                subnet_id="ocid1.subnet.oc1..test",
                private_ip="10.0.0.1",
                lifecycle_state="ACTIVE",
                kubernetes_version="v1.28.2",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_nodes_tool({
            "region": "us-phoenix-1",
            "node_pool_id": "ocid1.nodepool.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["nodes"][0]["name"] == "oke-node-1"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_scale_node_pool(self, mock_get_client):
        """Test scale_node_pool_tool."""
        mock_client = MagicMock()
        mock_client.scale_node_pool.return_value = WorkRequestInfo(
            work_request_id="ocid1.workrequest.oc1..test",
            operation_type="UPDATE_NODE_POOL",
            status="IN_PROGRESS",
            compartment_id="ocid1.compartment.oc1..test",
            percent_complete=0.0,
        )
        mock_get_client.return_value = mock_client

        result = await tools.scale_node_pool_tool({
            "region": "us-phoenix-1",
            "node_pool_id": "ocid1.nodepool.oc1..test",
            "size": 5,
        })

        data = json.loads(result)
        assert data["target_size"] == 5
        assert "work_request" in data

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_work_requests(self, mock_get_client):
        """Test list_work_requests_tool."""
        mock_client = MagicMock()
        mock_client.list_work_requests.return_value = [
            WorkRequestInfo(
                work_request_id="ocid1.workrequest.oc1..test",
                operation_type="UPDATE_NODE_POOL",
                status="SUCCEEDED",
                compartment_id="ocid1.compartment.oc1..test",
                percent_complete=100.0,
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_work_requests_tool({
            "region": "us-phoenix-1",
            "compartment_id": "ocid1.compartment.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1


class TestBastionTools:
    """Tests for bastion tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_bastions(self, mock_get_client):
        """Test list_bastions_tool."""
        mock_client = MagicMock()
        mock_client.list_bastions.return_value = [
            BastionInfo(
                bastion_id="ocid1.bastion.oc1..test",
                bastion_name="test-bastion",
                target_subnet_id="ocid1.subnet.oc1..test",
                bastion_type="INTERNAL",
                max_session_ttl=10800,
                lifecycle_state="ACTIVE",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_bastions_tool({
            "region": "us-phoenix-1",
            "compartment_id": "ocid1.compartment.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["bastions"][0]["bastion_name"] == "test-bastion"


class TestDevOpsProjectTools:
    """Tests for DevOps project tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_devops_projects(self, mock_get_client):
        """Test list_devops_projects_tool."""
        mock_client = MagicMock()
        mock_client.list_devops_projects.return_value = [
            DevOpsProjectInfo(
                project_id="ocid1.devopsproject.oc1..test",
                name="test-project",
                compartment_id="ocid1.compartment.oc1..test",
                description="Test project",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_devops_projects_tool({
            "region": "us-phoenix-1",
            "compartment_id": "ocid1.compartment.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["projects"][0]["name"] == "test-project"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_get_devops_project(self, mock_get_client):
        """Test get_devops_project_tool."""
        mock_client = MagicMock()
        mock_client.get_devops_project.return_value = DevOpsProjectInfo(
            project_id="ocid1.devopsproject.oc1..test",
            name="test-project",
            compartment_id="ocid1.compartment.oc1..test",
            description="Test project",
            namespace="test-namespace",
            lifecycle_state="ACTIVE",
        )
        mock_get_client.return_value = mock_client

        result = await tools.get_devops_project_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["project"]["name"] == "test-project"


class TestBuildPipelineTools:
    """Tests for build pipeline tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_build_pipelines(self, mock_get_client):
        """Test list_build_pipelines_tool."""
        mock_client = MagicMock()
        mock_client.list_build_pipelines.return_value = [
            BuildPipelineInfo(
                build_pipeline_id="ocid1.buildpipeline.oc1..test",
                display_name="test-build-pipeline",
                project_id="ocid1.devopsproject.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_build_pipelines_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1
        assert data["build_pipelines"][0]["display_name"] == "test-build-pipeline"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_get_build_pipeline(self, mock_get_client):
        """Test get_build_pipeline_tool."""
        mock_client = MagicMock()
        mock_client.get_build_pipeline.return_value = BuildPipelineInfo(
            build_pipeline_id="ocid1.buildpipeline.oc1..test",
            display_name="test-build-pipeline",
            project_id="ocid1.devopsproject.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            lifecycle_state="ACTIVE",
        )
        mock_client.list_build_pipeline_stages.return_value = []
        mock_get_client.return_value = mock_client

        result = await tools.get_build_pipeline_tool({
            "region": "us-phoenix-1",
            "build_pipeline_id": "ocid1.buildpipeline.oc1..test",
        })

        data = json.loads(result)
        assert data["build_pipeline"]["display_name"] == "test-build-pipeline"


class TestBuildRunTools:
    """Tests for build run tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_build_runs(self, mock_get_client):
        """Test list_build_runs_tool."""
        mock_client = MagicMock()
        mock_client.list_build_runs.return_value = [
            BuildRunInfo(
                build_run_id="ocid1.buildrun.oc1..test",
                display_name="test-build-run",
                build_pipeline_id="ocid1.buildpipeline.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                project_id="ocid1.devopsproject.oc1..test",
                lifecycle_state="SUCCEEDED",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_build_runs_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_get_build_run(self, mock_get_client):
        """Test get_build_run_tool."""
        mock_client = MagicMock()
        mock_client.get_build_run.return_value = BuildRunInfo(
            build_run_id="ocid1.buildrun.oc1..test",
            display_name="test-build-run",
            build_pipeline_id="ocid1.buildpipeline.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            project_id="ocid1.devopsproject.oc1..test",
            lifecycle_state="SUCCEEDED",
        )
        mock_get_client.return_value = mock_client

        result = await tools.get_build_run_tool({
            "region": "us-phoenix-1",
            "build_run_id": "ocid1.buildrun.oc1..test",
        })

        data = json.loads(result)
        assert data["build_run"]["lifecycle_state"] == "SUCCEEDED"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_trigger_build_run(self, mock_get_client):
        """Test trigger_build_run_tool."""
        mock_client = MagicMock()
        mock_client.trigger_build_run.return_value = BuildRunInfo(
            build_run_id="ocid1.buildrun.oc1..new",
            display_name="new-build-run",
            build_pipeline_id="ocid1.buildpipeline.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            project_id="ocid1.devopsproject.oc1..test",
            lifecycle_state="ACCEPTED",
        )
        mock_get_client.return_value = mock_client

        result = await tools.trigger_build_run_tool({
            "region": "us-phoenix-1",
            "build_pipeline_id": "ocid1.buildpipeline.oc1..test",
        })

        data = json.loads(result)
        assert "message" in data
        assert data["build_run"]["lifecycle_state"] == "ACCEPTED"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_cancel_build_run(self, mock_get_client):
        """Test cancel_build_run_tool."""
        mock_client = MagicMock()
        mock_client.cancel_build_run.return_value = BuildRunInfo(
            build_run_id="ocid1.buildrun.oc1..test",
            display_name="test-build-run",
            build_pipeline_id="ocid1.buildpipeline.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            project_id="ocid1.devopsproject.oc1..test",
            lifecycle_state="CANCELING",
        )
        mock_get_client.return_value = mock_client

        result = await tools.cancel_build_run_tool({
            "region": "us-phoenix-1",
            "build_run_id": "ocid1.buildrun.oc1..test",
        })

        data = json.loads(result)
        assert "message" in data


class TestDeployPipelineTools:
    """Tests for deploy pipeline tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_deploy_pipelines(self, mock_get_client):
        """Test list_deploy_pipelines_tool."""
        mock_client = MagicMock()
        mock_client.list_deploy_pipelines.return_value = [
            DeployPipelineInfo(
                deploy_pipeline_id="ocid1.deploypipeline.oc1..test",
                display_name="test-deploy-pipeline",
                project_id="ocid1.devopsproject.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_deploy_pipelines_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_get_deploy_pipeline(self, mock_get_client):
        """Test get_deploy_pipeline_tool."""
        mock_client = MagicMock()
        mock_client.get_deploy_pipeline.return_value = DeployPipelineInfo(
            deploy_pipeline_id="ocid1.deploypipeline.oc1..test",
            display_name="test-deploy-pipeline",
            project_id="ocid1.devopsproject.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            lifecycle_state="ACTIVE",
        )
        mock_client.list_deploy_stages.return_value = []
        mock_get_client.return_value = mock_client

        result = await tools.get_deploy_pipeline_tool({
            "region": "us-phoenix-1",
            "deploy_pipeline_id": "ocid1.deploypipeline.oc1..test",
        })

        data = json.loads(result)
        assert data["deploy_pipeline"]["display_name"] == "test-deploy-pipeline"


class TestDeploymentTools:
    """Tests for deployment tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_deployments(self, mock_get_client):
        """Test list_deployments_tool."""
        mock_client = MagicMock()
        mock_client.list_deployments.return_value = [
            DeploymentInfo(
                deployment_id="ocid1.deployment.oc1..test",
                display_name="test-deployment",
                deploy_pipeline_id="ocid1.deploypipeline.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                project_id="ocid1.devopsproject.oc1..test",
                deployment_type="PIPELINE_DEPLOYMENT",
                lifecycle_state="SUCCEEDED",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_deployments_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_get_deployment(self, mock_get_client):
        """Test get_deployment_tool."""
        mock_client = MagicMock()
        mock_client.get_deployment.return_value = DeploymentInfo(
            deployment_id="ocid1.deployment.oc1..test",
            display_name="test-deployment",
            deploy_pipeline_id="ocid1.deploypipeline.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            project_id="ocid1.devopsproject.oc1..test",
            deployment_type="PIPELINE_DEPLOYMENT",
            lifecycle_state="SUCCEEDED",
        )
        mock_get_client.return_value = mock_client

        result = await tools.get_deployment_tool({
            "region": "us-phoenix-1",
            "deployment_id": "ocid1.deployment.oc1..test",
        })

        data = json.loads(result)
        assert data["deployment"]["lifecycle_state"] == "SUCCEEDED"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_create_deployment(self, mock_get_client):
        """Test create_deployment_tool."""
        mock_client = MagicMock()
        mock_client.create_deployment.return_value = DeploymentInfo(
            deployment_id="ocid1.deployment.oc1..new",
            display_name="new-deployment",
            deploy_pipeline_id="ocid1.deploypipeline.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            project_id="ocid1.devopsproject.oc1..test",
            deployment_type="PIPELINE_DEPLOYMENT",
            lifecycle_state="ACCEPTED",
        )
        mock_get_client.return_value = mock_client

        result = await tools.create_deployment_tool({
            "region": "us-phoenix-1",
            "deploy_pipeline_id": "ocid1.deploypipeline.oc1..test",
        })

        data = json.loads(result)
        assert "message" in data

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_approve_deployment(self, mock_get_client):
        """Test approve_deployment_tool."""
        mock_client = MagicMock()
        mock_client.approve_deployment.return_value = DeploymentInfo(
            deployment_id="ocid1.deployment.oc1..test",
            display_name="test-deployment",
            deploy_pipeline_id="ocid1.deploypipeline.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            project_id="ocid1.devopsproject.oc1..test",
            deployment_type="PIPELINE_DEPLOYMENT",
            lifecycle_state="IN_PROGRESS",
        )
        mock_get_client.return_value = mock_client

        result = await tools.approve_deployment_tool({
            "region": "us-phoenix-1",
            "deployment_id": "ocid1.deployment.oc1..test",
            "stage_id": "ocid1.stage.oc1..test",
            "action": "APPROVE",
        })

        data = json.loads(result)
        assert "message" in data

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_cancel_deployment(self, mock_get_client):
        """Test cancel_deployment_tool."""
        mock_client = MagicMock()
        mock_client.cancel_deployment.return_value = DeploymentInfo(
            deployment_id="ocid1.deployment.oc1..test",
            display_name="test-deployment",
            deploy_pipeline_id="ocid1.deploypipeline.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            project_id="ocid1.devopsproject.oc1..test",
            deployment_type="PIPELINE_DEPLOYMENT",
            lifecycle_state="CANCELING",
        )
        mock_get_client.return_value = mock_client

        result = await tools.cancel_deployment_tool({
            "region": "us-phoenix-1",
            "deployment_id": "ocid1.deployment.oc1..test",
        })

        data = json.loads(result)
        assert "message" in data


class TestArtifactTools:
    """Tests for artifact tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_deploy_artifacts(self, mock_get_client):
        """Test list_deploy_artifacts_tool."""
        mock_client = MagicMock()
        mock_client.list_deploy_artifacts.return_value = [
            DeployArtifactInfo(
                artifact_id="ocid1.artifact.oc1..test",
                display_name="test-artifact",
                project_id="ocid1.devopsproject.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                artifact_type="KUBERNETES_MANIFEST",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_deploy_artifacts_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1


class TestEnvironmentTools:
    """Tests for environment tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_deploy_environments(self, mock_get_client):
        """Test list_deploy_environments_tool."""
        mock_client = MagicMock()
        mock_client.list_deploy_environments.return_value = [
            DeployEnvironmentInfo(
                environment_id="ocid1.environment.oc1..test",
                display_name="test-environment",
                project_id="ocid1.devopsproject.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                environment_type="OKE_CLUSTER",
                lifecycle_state="ACTIVE",
                cluster_id="ocid1.cluster.oc1..test",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_deploy_environments_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1


class TestRepositoryTools:
    """Tests for repository tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_repositories(self, mock_get_client):
        """Test list_repositories_tool."""
        mock_client = MagicMock()
        mock_client.list_repositories.return_value = [
            DevOpsRepositoryInfo(
                repository_id="ocid1.repository.oc1..test",
                name="test-repo",
                project_id="ocid1.devopsproject.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                default_branch="main",
                repository_type="HOSTED",
                ssh_url="ssh://devops.oci.oraclecloud.com/test-repo",
                http_url="https://devops.oci.oraclecloud.com/test-repo",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_repositories_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_get_repository(self, mock_get_client):
        """Test get_repository_tool."""
        mock_client = MagicMock()
        mock_client.get_repository.return_value = DevOpsRepositoryInfo(
            repository_id="ocid1.repository.oc1..test",
            name="test-repo",
            project_id="ocid1.devopsproject.oc1..test",
            compartment_id="ocid1.compartment.oc1..test",
            default_branch="main",
            repository_type="HOSTED",
            ssh_url="ssh://devops.oci.oraclecloud.com/test-repo",
            http_url="https://devops.oci.oraclecloud.com/test-repo",
            lifecycle_state="ACTIVE",
        )
        mock_get_client.return_value = mock_client

        result = await tools.get_repository_tool({
            "region": "us-phoenix-1",
            "repository_id": "ocid1.repository.oc1..test",
        })

        data = json.loads(result)
        assert data["repository"]["name"] == "test-repo"

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_repository_refs(self, mock_get_client):
        """Test list_repository_refs_tool."""
        from mcp_servers.oracle_cloud.models import RepositoryBranchInfo

        mock_client = MagicMock()
        mock_client.list_repository_refs.return_value = [
            RepositoryBranchInfo(
                ref_name="main",
                ref_type="BRANCH",
                commit_id="abc123",
                repository_id="ocid1.repository.oc1..test",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_repository_refs_tool({
            "region": "us-phoenix-1",
            "repository_id": "ocid1.repository.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_repository_commits(self, mock_get_client):
        """Test list_repository_commits_tool."""
        from mcp_servers.oracle_cloud.models import RepositoryCommitInfo

        mock_client = MagicMock()
        mock_client.list_repository_commits.return_value = [
            RepositoryCommitInfo(
                commit_id="abc123",
                commit_message="Initial commit",
                author_name="Test User",
                author_email="test@example.com",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_repository_commits_tool({
            "region": "us-phoenix-1",
            "repository_id": "ocid1.repository.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1


class TestTriggerTools:
    """Tests for trigger tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_triggers(self, mock_get_client):
        """Test list_triggers_tool."""
        mock_client = MagicMock()
        mock_client.list_triggers.return_value = [
            TriggerInfo(
                trigger_id="ocid1.trigger.oc1..test",
                display_name="test-trigger",
                project_id="ocid1.devopsproject.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                trigger_source="GITHUB",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_triggers_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1


class TestConnectionTools:
    """Tests for connection tools."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_list_connections(self, mock_get_client):
        """Test list_connections_tool."""
        mock_client = MagicMock()
        mock_client.list_connections.return_value = [
            ConnectionInfo(
                connection_id="ocid1.connection.oc1..test",
                display_name="test-connection",
                project_id="ocid1.devopsproject.oc1..test",
                compartment_id="ocid1.compartment.oc1..test",
                connection_type="GITHUB_ACCESS_TOKEN",
                lifecycle_state="ACTIVE",
            )
        ]
        mock_get_client.return_value = mock_client

        result = await tools.list_connections_tool({
            "region": "us-phoenix-1",
            "project_id": "ocid1.devopsproject.oc1..test",
        })

        data = json.loads(result)
        assert data["count"] == 1


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    @patch("mcp_servers.oracle_cloud.tools._get_client")
    async def test_tool_error_handling(self, mock_get_client):
        """Test that tools properly handle exceptions."""
        mock_client = MagicMock()
        mock_client.list_oke_clusters.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        result = await tools.list_oke_clusters_tool({
            "region": "us-phoenix-1",
            "compartment_id": "ocid1.compartment.oc1..test",
        })

        data = json.loads(result)
        assert "error" in data
        assert "API Error" in data["error"]

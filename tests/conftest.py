"""Common test fixtures and utilities."""

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Any


@dataclass
class MockOCIResponse:
    """Mock OCI API response."""
    data: Any
    headers: dict = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class MockOCIListResponse:
    """Mock OCI list API response with items."""
    items: list

    @property
    def data(self):
        return self


@pytest.fixture
def mock_oci_config():
    """Mock OCI configuration."""
    return {
        "user": "ocid1.user.oc1..test",
        "fingerprint": "aa:bb:cc:dd:ee:ff",
        "tenancy": "ocid1.tenancy.oc1..test",
        "region": "us-phoenix-1",
        "key_file": "/path/to/key.pem",
    }


@pytest.fixture
def mock_compartment_data():
    """Mock compartment data."""
    mock = MagicMock()
    mock.id = "ocid1.compartment.oc1..test"
    mock.name = "test-compartment"
    mock.description = "Test compartment"
    mock.lifecycle_state = "ACTIVE"
    return mock


@pytest.fixture
def mock_cluster_data():
    """Mock OKE cluster data."""
    mock = MagicMock()
    mock.id = "ocid1.cluster.oc1..test"
    mock.name = "test-cluster"
    mock.kubernetes_version = "v1.28.2"
    mock.lifecycle_state = "ACTIVE"
    mock.compartment_id = "ocid1.compartment.oc1..test"
    mock.vcn_id = "ocid1.vcn.oc1..test"
    mock.available_kubernetes_upgrades = ["v1.29.0"]
    mock.time_created = None
    mock.time_updated = None
    mock.freeform_tags = {}
    mock.defined_tags = {}
    return mock


@pytest.fixture
def mock_node_pool_data():
    """Mock node pool data."""
    mock = MagicMock()
    mock.id = "ocid1.nodepool.oc1..test"
    mock.name = "test-pool"
    mock.cluster_id = "ocid1.cluster.oc1..test"
    mock.compartment_id = "ocid1.compartment.oc1..test"
    mock.kubernetes_version = "v1.28.2"
    mock.node_shape = "VM.Standard.E4.Flex"
    mock.lifecycle_state = "ACTIVE"
    mock.initial_node_labels = []
    mock.time_created = None
    mock.freeform_tags = {}
    mock.defined_tags = {}
    mock.node_source = None
    mock.node_shape_config = None
    mock.node_config_details = None
    return mock


@pytest.fixture
def mock_instance_data():
    """Mock compute instance data."""
    mock = MagicMock()
    mock.id = "ocid1.instance.oc1..test"
    mock.display_name = "test-instance"
    mock.shape = "VM.Standard.E4.Flex"
    mock.availability_domain = "AD-1"
    mock.lifecycle_state = "RUNNING"
    mock.metadata = {}
    return mock


@pytest.fixture
def mock_bastion_data():
    """Mock bastion data."""
    mock = MagicMock()
    mock.id = "ocid1.bastion.oc1..test"
    mock.name = "test-bastion"
    mock.target_subnet_id = "ocid1.subnet.oc1..test"
    mock.bastion_type = "INTERNAL"
    mock.max_session_ttl_in_seconds = 10800
    mock.lifecycle_state = "ACTIVE"
    return mock


@pytest.fixture
def mock_devops_project_data():
    """Mock DevOps project data."""
    mock = MagicMock()
    mock.id = "ocid1.devopsproject.oc1..test"
    mock.name = "test-project"
    mock.compartment_id = "ocid1.compartment.oc1..test"
    mock.description = "Test project"
    mock.namespace = "test-namespace"
    mock.lifecycle_state = "ACTIVE"
    mock.time_created = None
    mock.time_updated = None
    mock.freeform_tags = {}
    mock.defined_tags = {}
    return mock


@pytest.fixture
def mock_build_pipeline_data():
    """Mock build pipeline data."""
    mock = MagicMock()
    mock.id = "ocid1.buildpipeline.oc1..test"
    mock.display_name = "test-build-pipeline"
    mock.project_id = "ocid1.devopsproject.oc1..test"
    mock.compartment_id = "ocid1.compartment.oc1..test"
    mock.description = "Test build pipeline"
    mock.lifecycle_state = "ACTIVE"
    mock.time_created = None
    mock.time_updated = None
    mock.freeform_tags = {}
    mock.defined_tags = {}
    return mock


@pytest.fixture
def mock_build_run_data():
    """Mock build run data."""
    mock = MagicMock()
    mock.id = "ocid1.buildrun.oc1..test"
    mock.display_name = "test-build-run"
    mock.build_pipeline_id = "ocid1.buildpipeline.oc1..test"
    mock.compartment_id = "ocid1.compartment.oc1..test"
    mock.project_id = "ocid1.devopsproject.oc1..test"
    mock.lifecycle_state = "SUCCEEDED"
    mock.lifecycle_details = None
    mock.time_created = None
    mock.time_updated = None
    mock.time_started = None
    mock.time_finished = None
    mock.commit_info = None
    mock.freeform_tags = {}
    mock.defined_tags = {}
    return mock


@pytest.fixture
def mock_deploy_pipeline_data():
    """Mock deploy pipeline data."""
    mock = MagicMock()
    mock.id = "ocid1.deploypipeline.oc1..test"
    mock.display_name = "test-deploy-pipeline"
    mock.project_id = "ocid1.devopsproject.oc1..test"
    mock.compartment_id = "ocid1.compartment.oc1..test"
    mock.description = "Test deploy pipeline"
    mock.lifecycle_state = "ACTIVE"
    mock.time_created = None
    mock.time_updated = None
    mock.freeform_tags = {}
    mock.defined_tags = {}
    return mock


@pytest.fixture
def mock_deployment_data():
    """Mock deployment data."""
    mock = MagicMock()
    mock.id = "ocid1.deployment.oc1..test"
    mock.display_name = "test-deployment"
    mock.deploy_pipeline_id = "ocid1.deploypipeline.oc1..test"
    mock.compartment_id = "ocid1.compartment.oc1..test"
    mock.project_id = "ocid1.devopsproject.oc1..test"
    mock.deployment_type = "PIPELINE_DEPLOYMENT"
    mock.lifecycle_state = "SUCCEEDED"
    mock.lifecycle_details = None
    mock.time_created = None
    mock.time_updated = None
    mock.freeform_tags = {}
    mock.defined_tags = {}
    return mock


@pytest.fixture
def mock_repository_data():
    """Mock DevOps repository data."""
    mock = MagicMock()
    mock.id = "ocid1.repository.oc1..test"
    mock.name = "test-repo"
    mock.project_id = "ocid1.devopsproject.oc1..test"
    mock.compartment_id = "ocid1.compartment.oc1..test"
    mock.description = "Test repository"
    mock.default_branch = "main"
    mock.repository_type = "HOSTED"
    mock.ssh_url = "ssh://devops.us-phoenix-1.oci.oraclecloud.com/test-repo"
    mock.http_url = "https://devops.us-phoenix-1.oci.oraclecloud.com/test-repo"
    mock.lifecycle_state = "ACTIVE"
    mock.time_created = None
    mock.time_updated = None
    mock.freeform_tags = {}
    mock.defined_tags = {}
    return mock

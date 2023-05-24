# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Checks out charm repository into `charm_repo`. Updated metadata.yaml with reference to locally
# built ROCK. Executes integration tests.
#

from pathlib import Path

import logging
import pytest
import subprocess
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)
CHARM_REPO = "https://github.com/canonical/oidc-gatekeeper-operator.git"
CHARM_PATH = "./charm_repo"
CHARM_BRANCH = "main"

def read_rock_info():
    ROCKCRAFT = yaml.safe_load(Path("rockcraft.yaml").read_text())
    name = ROCKCRAFT["name"]
    version = ROCKCRAFT["version"]
    arch = list(ROCKCRAFT["platforms"].keys())[0]
    return f"{name}_{version}_{arch}:{version}"

@pytest.mark.abort_on_fail
def test_rock(ops_test: OpsTest):
    """Test rock."""
    LOCAL_ROCK_IMAGE = read_rock_info()

    # verify that all artifacts are in correct locations
    subprocess.run(["docker", "run", f"{LOCAL_ROCK_IMAGE}", "exec", "ls", "/home/authservice/web"], check=True)
    subprocess.run(["docker", "run", f"{LOCAL_ROCK_IMAGE}", "exec", "ls", "/home/authservice/oidc-authservice"], check=True)

    # checkout corresponding charm
    subprocess.run(["rm", "-rf", f"{CHARM_REPO}"])
    subprocess.run(["git", "clone", "--branch", f"{CHARM_BRANCH}", f"{CHARM_REPO}", f"{CHARM_PATH}"])

    # update metadata.yaml to point to rock
    METADATA = yaml.safe_load(Path(f"{CHARM_PATH}/metadata.yaml").read_text())
    METADATA["resources"]["oci-image"]["upstream-source"] = LOCAL_ROCK_IMAGE
    with open(f"{CHARM_PATH}/metadata.yaml", 'w') as file:
        documents = yaml.dump(METADATA, file)

    # run charm integration tests
    process = subprocess.Popen(
        ["tox", "-c", f"{CHARM_PATH}", "-e", "integration"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1
    )
    for line in iter(process.stdout.readline, b''):
        logger.info(f"{line}")
        if "FAILED" in f"{line}":
            # charm's integration test failed
            assert 0
    process.stdout.close()
    process.wait()


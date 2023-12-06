# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
#

from pathlib import Path

import os
import logging
import random
import pytest
import string
import subprocess
import yaml

from charmed_kubeflow_chisme.rock import CheckRock

@pytest.fixture()
def rock_test_env(tmpdir):
    """Yields a temporary directory and random docker container name, then cleans them up after."""
    container_name = "".join([str(i) for i in random.choices(string.ascii_lowercase, k=8)])
    yield tmpdir, container_name

    try:
        subprocess.run(["docker", "rm", container_name])
    except Exception:
        pass
    # tmpdir fixture we use here should clean up the other files for us

@pytest.mark.abort_on_fail
def test_rock(rock_test_env):
    """Test rock."""
    temp_dir, container_name = rock_test_env
    check_rock = CheckRock("rockcraft.yaml")
    rock_image = check_rock.get_image_name()
    rock_version = check_rock.get_version()
    print(f"{rock_image=}")
    print(f"{rock_version=}")
    LOCAL_ROCK_IMAGE = f"{check_rock.get_image_name()}:{check_rock.get_version()}"

    # TO-DO uncomment when updated chisme is published
    #rock_services = check_rock.get_services()
    #assert rock_services["mlserver-huggingface"]
    #assert rock_services["mlserver-huggingface"]["startup"] == "enabled"

    # create ROCK filesystem
    subprocess.run(["docker", "run", LOCAL_ROCK_IMAGE, "exec", "ls", "-la", "/bin/oidc-authservice"], check=True)

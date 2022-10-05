import logging
import os
import shutil
from pathlib import Path

import pytest

from quick_gist.credentials import _check_user_config_existance
from quick_gist.credentials import _create_default_user_config
from quick_gist.credentials import _create_user_config_dir
from quick_gist.credentials import _password_decrypt
from quick_gist.credentials import _password_encrypt
from quick_gist.credentials import crypto_iterations
from quick_gist.credentials import UserCredentialsError
from quick_gist.credentials import UserOsError

TEST_USER_CONFIG_PATH = Path("." + "/.config/quick-gist/")
TEST_USER_CONFIG_NAME = "quick-gist-config.yaml"
TEST_FULL_CONFIG_PATH = Path(f"{TEST_USER_CONFIG_PATH}{TEST_USER_CONFIG_NAME}")

TEST_ILLEGAL_USER_CONFIG_PATH = "." + "//.config/quick-gist/"
TEST_ILLEGAL_FULL_USER_CONFIG_PATH = Path(
    f"{TEST_ILLEGAL_USER_CONFIG_PATH}quick/-gist-config-yaml",
)


def test_password_encrypt_decrypt_valid_password():
    """Test password encryption and decryption of a string with the right password"""
    test_message = "secret test message"
    test_password = "testpassword42"

    encrypted_message = _password_encrypt(
        message=test_message.encode("utf-8"),
        password=test_password,
        iterations=crypto_iterations,
    )

    decrypted_message = _password_decrypt(
        token=encrypted_message,
        password=test_password,
    )

    assert decrypted_message.decode("utf-8") == test_message


def test_password_encrypt_decrypt_wrong_password():
    """Test password encryption and decryption of a string with the wrong password"""
    test_message = "secret test message"
    test_password = "testpassword42"
    wrong_password = "wrong_password"

    encrypted_message = _password_encrypt(
        message=test_message.encode("utf-8"),
        password=test_password,
        iterations=crypto_iterations,
    )
    with pytest.raises(UserCredentialsError) as exc_info:
        decrypted_message = _password_decrypt(
            token=encrypted_message,
            password=wrong_password,
        )

    assert str(exc_info.value) == "Invalid Password"


def test_check_user_config_existance():
    """Test the check of an existing user configuration file"""
    # check non existing user_configuration
    with pytest.raises(SystemExit) as exc_info_sys:
        _check_user_config_existance(path=TEST_FULL_CONFIG_PATH)

    assert exc_info_sys.errisinstance(UserOsError)
    assert (
        str(exc_info_sys.value)
        == "Could not find a user configuration (use add-user first)"
    )


def test_create_user_config_dir_illegal():
    """Test creatio of user configuration directory at a illegali path"""
    # with pytest.raises(SystemExit) as exc_info_sys:
    with pytest.raises(UserOsError) as exc_info_sys:
        _create_user_config_dir(path=TEST_ILLEGAL_USER_CONFIG_PATH)

    assert exc_info_sys.errisinstance(UserOsError)
    assert (
        str(exc_info_sys.value)
        == f"Could not create a new user configuraion dir at {TEST_ILLEGAL_USER_CONFIG_PATH}"
    )


def test_create_user_config_dir_legal(caplog):
    """Test creation of user configuation directory"""
    with caplog.at_level(logging.INFO):
        _create_user_config_dir(path=TEST_USER_CONFIG_PATH)

    assert f"Created directory at {TEST_USER_CONFIG_PATH}" in caplog.text
    # clean up directory
    shutil.rmtree(path=Path(".config"))


def test_create_user_config_illegal():
    """Test creation of a new user file at a illegal path"""
    # create legal config path first
    _create_user_config_dir(path=TEST_USER_CONFIG_PATH)

    with pytest.raises(SystemExit) as exc_info_sys:
        _create_default_user_config(path=TEST_ILLEGAL_FULL_USER_CONFIG_PATH)

    assert exc_info_sys.errisinstance(UserOsError)
    assert str(exc_info_sys.value) == f"Could not create a new user configuration file"
    # clean up test directory
    shutil.rmtree(path=Path(".config"))


def test_create_user_config(caplog):
    """Test creation of a new user configuration file"""
    # create legal config path first
    _create_user_config_dir(path=TEST_USER_CONFIG_PATH)
    with caplog.at_level(logging.INFO):
        _create_default_user_config(path=TEST_FULL_CONFIG_PATH)

    assert f"Created config file at {TEST_FULL_CONFIG_PATH}" in caplog.text

    # clean up test directory
    shutil.rmtree(path=Path(".config"))


def pytest_sessionfinish(session, exitstatus):
    """Called when whole test run is finished"""

    # clean up test directory in case anthing failed before
    shutil.rmtree(path=Path(".config"))

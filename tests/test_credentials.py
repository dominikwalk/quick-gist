from pathlib import Path

import pytest

from quick_gist.credentials import _check_user_config_existance
from quick_gist.credentials import _create_user_config_dir
from quick_gist.credentials import _password_decrypt
from quick_gist.credentials import _password_encrypt
from quick_gist.credentials import crypto_iterations
from quick_gist.credentials import UserCredentialsError
from quick_gist.credentials import UserOsError


TEST_USER_CONFIG_PATH = "." + "/.config/quick-gist/"
TEST_USER_CONFIG_NAME = "quick-gist-config.yaml"
TEST_FULL_CONFIG_PATH = Path(f"{TEST_USER_CONFIG_PATH}{TEST_USER_CONFIG_NAME}")

TEST_ILLEGAL_USER_CONFIG_PATH = "." + "//.config/quick-gist/"


def test_password_encrypt_decrypt_valid_password():

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

    # check non existing user_configuration
    with pytest.raises(SystemExit) as exc_info_sys:
        with pytest.raises(UserOsError) as exc_info_custom:
            _check_user_config_existance(path=TEST_FULL_CONFIG_PATH)

        assert (
            str(exc_info_custom.value)
            == "Could not find a user configuration (use add-user first)"
        )
    assert exc_info_sys.value.code == 1


def test_create_user_config_dir_illegal():
    with pytest.raises(SystemExit) as exc_info_sys:
        with pytest.raises(UserOsError) as exc_info_custom:
            _create_user_config_dir(path=TEST_ILLEGAL_USER_CONFIG_PATH)

        assert (
            str(exc_info_custom.value)
            == f"Could not create a new user configuraion dir at {ILLEGAL_USER_CONFIG_PATH}"
        )
    assert exc_info_sys.value.code == 1

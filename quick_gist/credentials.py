import logging
import os
import pathlib
import secrets
from base64 import urlsafe_b64decode as b64d
from base64 import urlsafe_b64encode as b64e
from typing import Union

import yaml
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

crypto_backend = default_backend()
# https://github.com/django/django/blob/main/django/contrib/auth/hashers.py
crypto_iterations = 390000


class UserOsError(Exception):
    def __init__(self, msg=""):
        logging.error(f"UserOsError: {msg}")
        exit(1)


class UserCredentialsError(Exception):
    def __init__(self, msg="", exit=False):
        logging.error(f"UserCredentialsError: {msg}")
        if exit:
            exit(1)


def _crypto_derive_key(
    password: bytes,
    salt: bytes,
    iterations: int = crypto_iterations,
) -> bytes:
    """Derive a secret key from a given password and salt"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=crypto_backend,
    )

    return b64e(kdf.derive(password))


def _password_encrypt(
    message: bytes,
    password: str,
    iterations: int = crypto_iterations,
) -> bytes:
    """Encrypt a message using a given password"""
    salt = secrets.token_bytes(16)
    key = _crypto_derive_key(password.encode(), salt, iterations)
    return b64e(
        b"%b%b%b"
        % (
            salt,
            iterations.to_bytes(4, "big"),
            b64d(Fernet(key).encrypt(message)),
        ),
    )


def _password_decrypt(token: bytes, password: str) -> bytes:
    """Decrypt a message using a given password"""
    decoded = b64d(token)
    salt, iter, token = decoded[:16], decoded[16:20], b64e(decoded[20:])
    iterations = int.from_bytes(iter, "big")
    key = _crypto_derive_key(password.encode(), salt, iterations)

    try:
        token = Fernet(key).decrypt(token)
    except InvalidToken:
        raise UserCredentialsError("Invalid Password", exit=False)

    return token


def _check_user_config_existance(path: pathlib.Path) -> None:
    """Check if a user configuration file exists and report status"""
    if not path.is_file():
        raise UserOsError("Could not find a user configuration (use add-user first)")


def _create_user_config_dir(path: pathlib.Path) -> None:
    """Create the default directory where the user configuration is stored"""
    try:
        os.mkdir(path)
    except:
        raise UserOsError(f"Could not create a new user configuraion dir at {path}")
    else:
        logging.info(f"Created directory at {path}")


def _create_default_user_config(path: pathlib.Path) -> None:
    """Create a new blank configuraton file"""
    try:
        with open(path, "w") as f:
            f.write(
                """
    default:
        publish: private # (private/public) default publish mode
    user:
    """,
            )
    except:
        raise UserOsError(f"Could not create a new user configuration file")
    else:
        logging.info(f"Created config file at {path}")


def _read_user_config(path: pathlib.Path) -> dict:
    """Read the user configuration file and return keys and values"""
    with open(path, "r") as f:
        config_data = yaml.load(f, Loader=yaml.FullLoader)

        return config_data


def _write_user_config(path: pathlib.Path, data: dict) -> None:
    """Write confiiguration in user configuration file"""
    with open(path, "w") as f:
        yaml.dump(data, f)

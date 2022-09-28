import argparse
import getpass
import itertools
import logging
import os
import pathlib
import re
from collections import OrderedDict
from pathlib import Path
from typing import Callable
from typing import List
from typing import NamedTuple
from typing import Tuple

from quick_gist.api import _post_github_gist
from quick_gist.api import _validate_github_user_apitoken
from quick_gist.api import _validate_github_username
from quick_gist.api import GistContent
from quick_gist.credentials import _check_user_config_existance
from quick_gist.credentials import _create_default_user_config
from quick_gist.credentials import _create_user_config_dir
from quick_gist.credentials import _password_decrypt
from quick_gist.credentials import _password_encrypt
from quick_gist.credentials import _read_user_config
from quick_gist.credentials import _write_user_config
from quick_gist.credentials import UserCredentialsError

USER_CONFIG_PATH = str(os.getenv("HOME")) + "/.config/quick-gist/"
USER_CONFIG_NAME = "quick-gist-config.yaml"
FULL_CONFIG_PATH = Path(f"{USER_CONFIG_PATH}{USER_CONFIG_NAME}")

NEW_SUBFILE_PATTERN = re.compile(r"^(\w+?.\w+)\[([\d+\-\d+?,]+)\]$")


class term_colors:
    GREEN = "\033[92m"
    RESET = "\033[0m"


class UserCommandError(Exception):
    def __init__(self, msg=""):
        logging.error(f"UserCommandError: {msg}")
        exit(1)


class FileDescriptor(NamedTuple):
    path: pathlib.Path
    line_descriptor: List[Tuple[int, int]]


def _get_user_input(msg: str, validation_function: Callable[..., bool]) -> str:
    """Get user input and validate it and try again if it fails"""
    while True:
        inp = input(msg)
        if validation_function(inp):
            return inp
        else:
            print("Invalid input, please try again")


def command_add_user(args: argparse.Namespace) -> None:
    """Add a new github user to the quick-gist configuration"""
    # check if the config directory exists
    config_path_dir = Path(USER_CONFIG_PATH)
    if not config_path_dir.is_dir():
        # create config path
        _create_user_config_dir(config_path_dir)
    # check if a confiuration file exists
    if not FULL_CONFIG_PATH.is_file():
        # create user default configuration
        _create_default_user_config(FULL_CONFIG_PATH)

    user_configuration = _read_user_config(path=FULL_CONFIG_PATH)

    # ask for github username
    user_name = _get_user_input(
        msg="Github username: ",
        validation_function=lambda x: isinstance(x, str),
    )
    if user_configuration["user"] is not None:
        existing_users = list(
            itertools.chain.from_iterable(
                [list(x.keys()) for x in user_configuration["user"]],
            ),
        )
        if user_name in existing_users:
            raise UserCommandError(msg="Username alreay exists in user configuration")

    # check if user exists on github
    _validate_github_username(username=user_name)
    api_token_selection = _get_user_input(
        msg="""
The following options for getting your API token are available:
- from environment variable [1]
- from configuration file [2]""",
        validation_function=lambda x: x in ["1", "2"],
    )
    if api_token_selection == "1":
        api_token = "env"
        user_encryption = False
    elif api_token_selection == "2":
        user_token_source = "config"
        encryption_selection = _get_user_input(
            msg="Do you want to save your API token password encrypted? (Y/n)",
            validation_function=lambda x: x in ["y", "Y", "n", "N"],
        )
        user_encryption = True if encryption_selection.lower() == "y" else False

        api_token = _get_user_input(
            msg="Your GitHub API token: ",
            validation_function=lambda x: isinstance(x, str),
        )

        _validate_github_user_apitoken(username=user_name, api_token=api_token)

        if user_encryption:
            # encrypt user api token
            psw = getpass.getpass(prompt="Password: ")
            api_token = _password_encrypt(
                message=api_token.encode("utf-8"),
                password=psw,
            ).decode("utf-8")

    # create new user with given properties
    new_user = dict()
    new_user[user_name] = {
        "auth": api_token,
        "encrypted": user_encryption,
    }

    # if there is no user yet, create a new list of users
    all_users = user_configuration["user"]
    if all_users == None:
        all_users = [new_user]
    else:
        # if there already exists a list of users, append to them
        all_users.append(new_user)
    user_configuration["user"] = all_users

    # write down the new user configuration
    _write_user_config(FULL_CONFIG_PATH, user_configuration)
    logging.info(f"Successfully added user '{user_name}' to configuration")


def command_new(args: argparse.Namespace) -> None:
    """Create a new github gist"""

    def _read_files(files: List[FileDescriptor]) -> dict:
        """Read in file content as described in the list of FileDescriptors"""
        parsed_files = OrderedDict()
        for file, line_blocks in files:
            # create a new empty content field for each new file
            content = ""
            file_path = file.resolve()
            try:
                with open(file_path, "r") as f:
                    if len(line_blocks) == 0:
                        content = f.read()
                        logging.debug("Including all lines from file '{file.name}'")
                    else:
                        all_lines = f.readlines()
                        for line_pair in line_blocks:
                            first_line, second_line = line_pair[0], line_pair[1]
                            # wrong order of line numbers
                            if second_line < first_line:
                                logging.warning(
                                    f"First line number must be lower "
                                    f"then the second one (skipping "
                                    f"'{file.name}',{line_pair})",
                                )
                            elif first_line <= 0:
                                logging.warning(
                                    f"Line {first_line} does not exist in "
                                    f"'{file.name}' (skipping)",
                                )
                            # line number does not exist
                            elif second_line > len(all_lines):
                                logging.warning(
                                    f"Line {second_line} does not exist in file "
                                    f"'{file.name}' (skipping lines [{first_line}-{second_line}])",
                                )
                            # if both lines are the same, include exactly that line
                            elif first_line == second_line:
                                content += all_lines[first_line - 1]
                                logging.debug(
                                    f"Including line {first_line} in file {file.name}",
                                )
                            # otherwise read specific lines
                            else:
                                content += "".join(
                                    all_lines[first_line - 1 : second_line],
                                )
                                logging.debug(
                                    "Including lines {first_line}-"
                                    f"{second_line} in file '{file.name}'",
                                )
                            # otherwise read specific lines
                    # create content object for api request
                    file_descriptor = {"content": content}
                    parsed_files[file.name] = file_descriptor
            except IOError:
                if args.softfail:
                    logging.warning(
                        f"Failed to open/read file '{file.name}' (skipping)",
                    )
                else:
                    raise UserCommandError(
                        f"Failed to open/read file '{file.name}'(aborting)",
                    )

        return parsed_files

    files_argument = args.files
    # parse the file argument to create a list of files to parse
    # and remember which lines to include
    files_to_parse: List[FileDescriptor] = []
    for file_descriptor in files_argument:
        line_numbers = []
        m = re.match(NEW_SUBFILE_PATTERN, file_descriptor)
        if m:
            # if there are no line numbers given, this section will be skipped
            # first group of the matched string is the filename
            file_name = m.group(1)
            # second group of the matched string are the line numbers to include
            seperated_line_numbers = str(m.group(2)).split(",")
            for section in seperated_line_numbers:
                # extract the line numbers from the matched string
                try:
                    a, b = map(int, section.split("-"))
                except ValueError:
                    # case when user typed in only one line number e.g. file.txt[10]
                    a = b = int(section)
                # add the line numbers to a list of sections that should be included
                line_numbers.append((a, b))
        else:
            # remember only the file name, if there are no line numbers given in the argument
            file_name = file_descriptor
            # list of line numbers stays empty
        # get full file path
        file_path = Path(file_name)
        # create a new FileDescriptor to remember the full file path and all lines to include
        new_file_desc = FileDescriptor(file_path, line_numbers)
        # add the new FileDescriptor to the list of descriptions of files to parse
        files_to_parse.append(new_file_desc)

    parsed_files = _read_files(files_to_parse)

    for parsed_file in parsed_files.items():
        if len(parsed_file[1]["content"]) != 0:
            break
        else:
            raise UserCommandError("All files were skipped, noting to create")

    # check if user configuration file exists
    _check_user_config_existance(path=FULL_CONFIG_PATH)

    # read user configuration
    user_configuration = _read_user_config(FULL_CONFIG_PATH)

    # get public option either from command line argument or from user configuration file
    if not args.public:
        publish_type = (
            False if (user_configuration["default"]["publish"] == "private") else True
        )
    else:
        publish_type = args.public

    # create new gist object
    new_gist_content = GistContent(
        description=args.description,
        files=parsed_files,
        public=publish_type,
    )

    number_of_users = len(user_configuration["user"])

    if number_of_users == 0:
        raise UserCommandError(
            "No github user is configured (use command 'add-user' first)",
        )
    elif number_of_users == 1:
        user = user_configuration["user"][0]
        user_name = list(user.keys())[0]
    else:
        # if more then one user is configured, use the one from the command line argume
        user_name = args.user
        if user_name == None:
            raise UserCommandError(
                """Found more then one user in user configuration file
                (use '-u/--user' to select one user)""",
            )
        # check if username exists in user configuration file
        for user in user_configuration["user"]:
            if list(user.keys())[0] == user_name:
                # found user in user configuration file
                break
        else:
            raise UserCommandError(
                f"Given user '{user_name}' does not exist in user configuration file",
            )
    # get user api token
    for user in user_configuration["user"]:
        if list(user.keys())[0] == user_name:
            # check if api token is encrypted
            if user[user_name]["encrypted"] == False:
                user_token = user[user_name]["auth"]
            else:
                # ask for password to decrypt the user api token
                while True:
                    psw = getpass.getpass(prompt="Password: ")
                    try:
                        user_token = _password_decrypt(
                            token=user[user_name]["auth"].encode("utf-8"),
                            password=psw,
                        ).decode("utf-8")
                        # valid password, break out of loop
                        break
                    except UserCredentialsError:
                        # invalid password, stay in loop and ask again
                        pass
            break

    # try to post gist on github
    gist_url = _post_github_gist(gist_content=new_gist_content, api_token=user_token)

    # print out information about which lines files/lines did get included in the gist
    secret_public_str = "public" if args.public else "secret"
    print(f"Created new {secret_public_str} github gist!✨")
    for file in files_to_parse:
        if file.path.name in parsed_files.keys():
            line_descriptor_str = ""
            for i, line_pair in enumerate(file.line_descriptor):
                line_descriptor_str += f"[{line_pair[0]}-{line_pair[1]}]"
                if i < len(file.line_descriptor) - 1:
                    line_descriptor_str += ", "
            print(
                term_colors.GREEN,
                f"  - {file.path.resolve()} {line_descriptor_str}",
                term_colors.RESET,
            )
    print(f"-> {gist_url}")

    return

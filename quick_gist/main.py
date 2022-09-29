import argparse
import logging
from typing import Optional
from typing import Sequence

from quick_gist.commands import command_add_user
from quick_gist.commands import command_list_user
from quick_gist.commands import command_new
from quick_gist.commands import command_remove_user


def main(argv: Optional[Sequence[str]] = None) -> int:

    # configure logging
    logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

    # configure argument parser
    parser = argparse.ArgumentParser(
        description="""
                A tool that allows yout to quickly create
                github gists from local files
                """,
    )

    # add subparser
    subparser = parser.add_subparsers(dest="command")

    # subparser to add a new github user to user confiuration
    parser_adduser = subparser.add_parser(
        "add-user",
        help="Add a new Github user to the configuration",
    )

    # subparser to remove a github user from the user confiuration
    parser_removeuser = subparser.add_parser(
        "remove-user",
        help="Remove a Github user from the configuration",
    )

    # subparser to list all github users from user configuration file
    parser_listuser = subparser.add_parser(
        "list-user",
        help="List all Github users from the configuration",
    )

    # subparser to create a new github gist
    parser_new = subparser.add_parser("new", help="Create a new github gist")

    parser_new.add_argument(
        "-f",
        "--files",
        type=str,
        nargs="+",
        help="Files to include into the gist",
        required=True,
    )

    parser_new.add_argument(
        "-d",
        "--description",
        type=str,
        help="Description of the gist",
        default="gist created via quick-gist",
        required=False,
    )

    parser_new.add_argument(
        "-p",
        "--public",
        action="store_true",
        help="Make the new gist public",
        required=False,
    )

    parser_new.add_argument(
        "-sf",
        "--softfail",
        action="store_true",
        help="Softfail will skip files that can not be read, instead of failing",
        required=False,
    )

    parser_new.add_argument(
        "-u",
        "--user",
        type=str,
        help="Github username",
        required=False,
    )

    # parse arguments
    args = parser.parse_args(argv)

    if not args.command:
        # error if the user did not pass a positional argument
        parser.error("quick-gist needs at least one positional argument (see -h)")

    if args.command == "add-user":
        command_add_user(args=args)
    elif args.command == "remove-user":
        command_remove_user(args=args)
    elif args.command == "list-user":
        command_list_user(args=args)
    elif args.command == "new":
        command_new(args=args)
    return 0


if __name__ == "__main__":

    exit(main())

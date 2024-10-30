"""Parsers for command strings"""

import argparse
import shlex
from textwrap import dedent
import dateparser

from data_models import Mute, MuteMatcher


mute_parser = argparse.ArgumentParser(
    description="Mute command",
    exit_on_error=False,
    add_help=False
)

mute_parser.add_argument("-l", "--label",
  type=str,
  default=[],
  action="append",
  help="label from which the silence will be created"
)

mute_parser.add_argument("-b", "--created_by",
  type=str,
  default="",
  help="who create that silence"
)

mute_parser.add_argument("-c", "--comment",
  type=str,
  default="",
  help="comment for silence"
)

mute_parser.add_argument("-t", "--ends_at",
  type=str,
  nargs="?",
  default="",
  help="end time for silence"
)


def parse_mute_command(command: str) -> Mute:
    """
    Parse mute comand into Mute data model
    args:
        command: mute alert command
    """
    args, unknown = mute_parser.parse_known_args(shlex.split(command))

    if "/mute" in command or "/silence" in command:
        command = command.replace("/mute", "")
        command = command.replace("/silence", "")

    args, unknown = mute_parser.parse_known_args(shlex.split(command))

    if unknown:
        raise UnknownArguments(command=command, unknown=' '.join(unknown))

    args = vars(args)

    if len(args['label']) == 0:
        raise MissingLabels(command=command)

    if args["ends_at"]:
        args["ends_at"] = dateparser.parse(
            args["ends_at"],
            settings={'SKIP_TOKENS': ['-'],
                      'PREFER_DATES_FROM': 'future'
            }
        ).isoformat()

    matchers = []
    for label in args["label"]:
        name, value = label.split("=")
        matchers.append(
            MuteMatcher(
                name=name,
                value=value
            )
        )

    result = Mute(
        matchers=matchers,
        createdBy=args["created_by"],
        comment=args["comment"],
        endsAt=args["ends_at"]
    )

    return result


# Module Exceptions


class UnknownArguments(Exception):
    """
    Exception for cases when user provide unknown args in command
    args:
        command: Original command
        unknown: Arguments thats unknown for parser
    """
    def __init__(self, command: str, unknown: str):
        self.command = command
        self.unknown = unknown
        super().__init__(
            dedent(f"""failed to parse provided command {self.command}
            unknown arguments - {self.unknown}""")
        )


class MissingLabels(Exception):
    """
    Exception for cases when user was not provide any labels in command
    args:
        command: Original command
    """
    def __init__(self, command: str):
        self.command = command
        super().__init__(
            dedent(f"""failed to parse provided command {self.command}
            you must provide one or more labels""")
        )

"""Parsers for command strings"""

import argparse
import shlex
from textwrap import dedent
import dateparser

from data_models import Mute, MuteMatcher, BaseAlert


silence_parser = argparse.ArgumentParser(
    prog='/silence',
    description="""Mute command""",
    exit_on_error=False,
    add_help=False
)

silence_parser.add_argument("-l", "--label",
  type=str,
  default=[],
  action="append",
  help="label from which the silence will be created"
)

silence_parser.add_argument("-b", "--created_by",
  type=str,
  default="",
  help="who create that silence"
)

silence_parser.add_argument("-c", "--comment",
  type=str,
  default="",
  help="comment for silence"
)

silence_parser.add_argument("-t", "--ends_at",
  type=str,
  nargs="?",
  default="",
  help="end time for silence"
)


def parse_silence_command(command: str) -> Mute:
    """
    Parse silence command into Mute data model
    args:
        command: silence alert command
    """
    args, unknown = silence_parser.parse_known_args(shlex.split(command))

    if "/silence" in command:
        command = command.replace("/silence", "")
        command = command.replace("/silence", "")

    args, unknown = silence_parser.parse_known_args(shlex.split(command))

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


mute_parser = argparse.ArgumentParser(
    prog='/mute',
    description=dedent("""
    Forward one or more alerts from an active chat here and add this command.
    """),
    exit_on_error=False,
    add_help=False
)

mute_parser.add_argument("ends_at",
  type=str,
  nargs="?",
  default="",
  help="end time for mute"
)


mute_parser.add_argument("-c", "--comment",
  type=str,
  default="",
  help="comment for mute"
)


def parse_mute_command(command: str, alert: BaseAlert) -> Mute:
    """
    Parse mute command into Mute data model
    args:
        command: mute alert command
        alert: alert that requires mute
    """
    args, unknown = mute_parser.parse_known_args(shlex.split(command))

    if "/mute" in command:
        command = command.replace("/mute", "")
        command = command.replace("/mute", "")

    args, unknown = mute_parser.parse_known_args(shlex.split(command))

    if unknown:
        raise UnknownArguments(command=command, unknown=' '.join(unknown))

    args = vars(args)

    if args["ends_at"]:
        args["ends_at"] = dateparser.parse(
            args["ends_at"],
            settings={'SKIP_TOKENS': ['-'],
                      'PREFER_DATES_FROM': 'future'
            }
        ).isoformat()

    mute_matchers = []
    for label in alert.labels:
        if "pane-" not in label:
            mute_matchers.append(
                MuteMatcher(
                    name=label,
                    value=alert.labels[label]
                )
            )

    if args["ends_at"] != "":
        result = Mute(
            matchers=mute_matchers,
            createdBy='',
            comment=args["comment"],
            endsAt=args["ends_at"]
        )
    else:
        result = Mute(
            matchers=mute_matchers,
            createdBy='',
            comment=args["comment"],
        )

    return result


unmute_parser = argparse.ArgumentParser(
    prog='/unmute',
    description=dedent("""
    Forward one or more muted alerts from an active chat here and add this command.
    """),
    exit_on_error=False,
    add_help=False
)


def get_help() -> str:
    """
    Get help for all parsers
    """
    help_message = ""

    silence_help = silence_parser.format_help()
    silence_help = silence_help.replace("\n\n", "\n")
    silence_help = silence_help.replace("/silence", "**/silence**")
    help_message += silence_help + "\n\n"

    mute_help = mute_parser.format_help()
    mute_help = mute_help.replace("\n\n", "\n")
    mute_help = mute_help.replace("/mute", "**/mute**")
    help_message += mute_help + "\n\n"

    unmute_help = unmute_parser.format_help()
    unmute_help = unmute_help.replace("\n\n", "\n")
    unmute_help = unmute_help.replace("/unmute", "**/unmute**")
    help_message += unmute_help + "\n\n"

    return help_message


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

import argparse
import logging
import textwrap
from typing import Protocol

from tests.commands.evaluate_classification import EvaluateClassificationCommand
from tests.commands.evaluate_identification import EvaluateIdentificationCommand
from tests.commands.evaluate_merge import EvaluateMergeCommand
from tests.commands.evaluate_temperature import EvaluateTemperatureCommand
from tests.commands.evaluate_postmortem import EvaluatePostmortemCommand
from tests.commands.sample_dataset_creation import SampleDatasetCreationCommand
from tests.commands.exp_runQueries import exp_RunQueriesCommand
from tests.commands.evaluate_taxonomy import EvaluateTaxonomyCommand
from tests.commands.fetch_data import FetchDataCommand



_EPILOG = textwrap.dedent(
    """\
    Please submit feedback, ideas, and bug reports by filing a new issue at
    https://github.com/d57montes/failures/issues.
    """
)

_DESCRIPTION = textwrap.dedent(
    """\
    failures is a tool for scraping and analyzing software failures in the news.
    """
)


class Command(Protocol):
    def prepare_parser(self, parser: argparse.ArgumentParser) -> None:
        ...

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
        ...


_COMMANDS: list[Command] = [EvaluateClassificationCommand(), EvaluateIdentificationCommand(), EvaluateMergeCommand(), EvaluateTemperatureCommand(), EvaluatePostmortemCommand(), SampleDatasetCreationCommand(), exp_RunQueriesCommand(), EvaluateTaxonomyCommand(), FetchDataCommand()]


def get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=_DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=_EPILOG,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=1,
        help="Increase verbosity. Option is additive and can be specified up to 3 times.",
    )

    subparsers = parser.add_subparsers(
        help="Subcommand to run. See `python3.9 -m failures <command> --help` for more information.",
        dest="command",
        required=True,
    )

    for command in _COMMANDS:
        assert command.__class__.__name__.endswith("Command")
        name = command.__class__.__name__[: -len("Command")].lower()

        command_parser = subparsers.add_parser(
            name,
            help=command.__doc__,
            epilog=_EPILOG,
        )
        command_parser.set_defaults(entrypoint=command.run)
        command.prepare_parser(command_parser)

    return parser


def determine_logging_level(verbose_level: int) -> int:
    if verbose_level == 0:
        return logging.WARNING
    elif verbose_level == 1:
        return logging.INFO
    else:
        return logging.DEBUG


def main():
    parser = get_argument_parser()
    args = parser.parse_args()

    logging.basicConfig(
        filename="merge_manual.log",
        filemode='a',
        level=determine_logging_level(args.verbose),
        format="%(asctime)s %(levelname)s: %(message)s",
        force=True,
    )

    args.entrypoint(args, parser)

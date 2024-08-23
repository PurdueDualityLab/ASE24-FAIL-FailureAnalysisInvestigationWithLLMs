import argparse
import logging
import textwrap
from typing import Protocol

from failures.commands.scrape import ScrapeCommand
from failures.commands.outdated.summarize import SummarizeCommand
from failures.commands.classifyFailure import ClassifyFailureCommand
from failures.commands.classifyAnalyzable import ClassifyAnalyzableCommand
from failures.commands.postmortemIncidentAutoVDB import PostmortemIncidentAutoVDBCommand
from failures.commands.cluster import ClusterCommand
from failures.commands.merge import MergeCommand
from failures.commands.fixes import FixesCommand
from failures.commands.cleanup import CleanUpCommand

from failures.commands.outdated.stats import StatsCommand
from failures.commands.results import ResultsCommand

'''
from failures.commands.outdated.summarize import SummarizeCommand
from failures.commands.outdated.embed import EmbedCommand
from failures.commands.outdated.postmortemArticle import PostmortemArticleCommand
from failures.commands.outdated.postmortemIncidentVDB import PostmortemIncidentVDBCommand
from failures.commands.outdated.vectordb import VectordbCommand
'''

_EPILOG = textwrap.dedent(
    """\
    Please submit feedback, ideas, and bug reports by filing a new issue at
    https://github.com/Dharun-Anand/failures/issues.
    """
)

_DESCRIPTION = textwrap.dedent(
    """\
    failures is a pipeline for scraping and analyzing software failures in the news.
    """
)


class Command(Protocol):
    def prepare_parser(self, parser: argparse.ArgumentParser) -> None:
        ...

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
        ...


_COMMANDS: list[Command] = [ScrapeCommand(), ClassifyFailureCommand(), ClassifyAnalyzableCommand(), MergeCommand(), PostmortemIncidentAutoVDBCommand(), ClusterCommand(), FixesCommand(), CleanUpCommand(), StatsCommand(), ResultsCommand()]


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
        filename="PaperResults.log",
        filemode='a',
        level=determine_logging_level(args.verbose),
        format="%(asctime)s %(levelname)s: %(message)s",
        force=True, 
    )

    args.entrypoint(args, parser)

#!/usr/bin/env python

import argparse
import os

import leat
from leat.search import Search
from leat.search.config import ConfigData, PredefinedConfigurations
from leat.search.pattern import PatternBuilder

CLI_COMMANDS = ["list", "search", "show"]


def init_args(parser=""):
    parser = argparse.ArgumentParser(description="Command line interface for LEAT")
    parser.add_argument(
        dest="command", default="", choices=CLI_COMMANDS, help="Commands to execute"
    )
    parser.add_argument(
        dest="arg", nargs="*", default="", help="Argument for show or list command"
    )
    parser.add_argument(
        "--arg",
        dest="arg",
        default="",
        help="Argument for show or list command",
    )
    parser.add_argument(
        "--cmd",
        "--command",
        dest="command",
        default="",
        choices=CLI_COMMANDS,
        help="Commands to execute",
    )
    parser.add_argument(
        "--config",
        "--config-file",
        dest="config_file",
        default="",
        help="Configuration file for search patterns",
    )
    parser.add_argument(
        "--config-name",
        "--predefined-config",
        dest="predefined_configuration",
        default="",
        help="Predefined configuration for search patterns",
    )
    parser.add_argument(
        "--sect-sep",
        dest="section_sep",
        type=int,
        help="Length of text without patterns that is sufficient to create a new section or results",
    )
    parser.add_argument(
        "--sect-max", dest="section_max", type=int, help="Maximum length of a section"
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["txt", "text", "html"],
        help="Format of output file (default: file extension or text)",
    )
    parser.add_argument("-o", "--output", dest="output_file", help="Output file name")
    args = parser.parse_args()
    if not args.output_format:
        if args.output_file is not None:
            _, ext = os.path.splitext(args.output_file)
            if ext == ".html":
                args.output_format = "html"
            else:
                args.output_format = "text"
        else:
            args.output_format = "text"
    if args.output_format == "txt":
        args.output_format = "text"
    return args


def handle_list_command(args):
    "List files from store"
    pass

def handle_show_command(args):
    "Show aspect of leat configuration"
    construct = args.arg[0]
    if construct == "concepts":
        config_data = get_config_data(args)
        match_patterns = PatternBuilder.build(config_data)
        all_concepts = sorted(set(mp.concept for mp in match_patterns))
        for c in all_concepts:
            print(c)
    elif construct == "configs":
        for c in PredefinedConfigurations.list():
            print(c)

def handle_search_command(args):
    "Search using leat"
    pass

    
def get_config_data(args):
    "Get ConfigData from args"
    if args.config_file:
        return ConfigData(config_file=args.config_file)
    if args.predefined_configuration:
        return ConfigData(predefined_configuration=args.predefined_configuration)
    print('No configuration data specified')

def cli():
    "Command line interface for LEAT"
    args = init_args()
    #print(args)
    if args.command == "search":
        handle_search_command(args)
    elif args.command == "show":
        handle_show_command(args)
    elif args.command == "list":
        handle_list_command(args)
    else:
        print("Unknown Command. Try `leat --help`")


if __name__ == "__main__":
    cli()

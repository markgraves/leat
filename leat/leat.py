#!/usr/bin/env python

import argparse
import os

import leat
from leat.search import Search
from leat.search.config import ConfigData, PredefinedConfigurations
from leat.search.pattern import PatternBuilder
from leat.store.filesys import LocalFileSys
from leat.store.core import DocStore
from leat.search import Search
from leat.search.writer import TextWriter, HTMLWriter

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
    parser.add_argument(
        "-d", "--dir", nargs="*", dest="dir", help="Directory to search"
    )
    parser.add_argument(
        "-i",
        "--include",
        nargs="*",
        dest="include",
        help="Glob patterns for files to include in any directory search (default: *)",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        nargs="*",
        dest="exclude",
        help="Glob patterns for files to exclude from any directory search",
    )

    args = parser.parse_args()
    if not args.dir:
        args.dir = ["."]
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
    if not args.arg:
        print("List commands requires additional argument: all, matches, counts")
        return
    construct = args.arg[0]
    if construct == "all":
        fs = get_filesys(args)
        if fs is None:
            print("No directories specified")
            return
        for f in fs:
            print(f)
    elif construct == "matches":
        search = get_search(args)
        for doc_result in search:
            print(doc_result.doc.name)
    elif construct == "counts":
        search = get_search(args)
        for doc_result in search:
            print(len(doc_result.all_results()), doc_result.doc.name)


def handle_show_command(args):
    "Show aspect of leat configuration"
    if not args.arg:
        print("Show commands requires additional argument: concepts, configs")
        return
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
    search = get_search(args)
    with open(args.output_file, "w") as ofp:
        if args.output_format == "text":
            w = TextWriter(stream=ofp)
        elif args.output_format == "html":
            w = HTMLWriter(stream=ofp)
        else:
            print("Unknown format specified")
            return
        for doc_result in search:
            w.write_doc_result(doc_result)


def get_search(args):
    "Get Search from args"
    config_data = get_config_data(args)
    filesys = get_filesys(args)
    doc_store = DocStore(filesys)
    search = Search(
        config=config_data,
        doc_store=doc_store,
        default_section_sep=args.section_sep,
        default_section_max=args.section_max,
    )
    return search


def get_config_data(args):
    "Get ConfigData from args"
    if args.config_file:
        return ConfigData(config_file=args.config_file)
    if args.predefined_configuration:
        return ConfigData(predefined_configuration=args.predefined_configuration)
    print("No configuration data specified")


def get_filesys(args):
    "Get LocalFileSys for directories"
    if args.dir is None:
        return
    fs = LocalFileSys()
    for d in args.dir:
        # Note: include and exclude patterns are used for all directories
        fs.add_directory(d, include=args.include, exclude=args.exclude)
    return fs


def cli():
    "Command line interface for LEAT"
    args = init_args()
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

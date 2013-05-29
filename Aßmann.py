#!/usr/bin/python3

import re
import sys
import pickle
import functools
import operator

import argparse

def positive_int(s):
    i = int(s)
    if i <= 0:
        raise ValueError("Out of bounds: {}".format(i))
    return i

class LearnWords:
    pattern = """(\w+|\s+|,|\.|\?|!|"|'|\[|\]|\(|\)|\n)"""

    def __init__(self, args):
        self._infile = open(args.infile, "r", encoding=args.encoding)
        self._order = args.order
        self._chainfile = args.chainfile
        if self._chainfile is None and args.save:
            print("Chainfile argument omitted, but --no-save is not set.")
            sys.exit(1)

        if args.fold_whitespace:
            self._filter = self.filter_fold_whitespace
        else:
            self._filter = self.filter_pass

        if args.fold_case:
            old_filter = self._filter
            self._filter = lambda x: str.lower(old_filter(x))

    @staticmethod
    def filter_fold_whitespace(x):
        return x.replace("\t", " ").replace("\n", " ")

    @staticmethod
    def filter_pass(x):
        return x

    def source(self):
        with self._infile as f:
            yield from map(self._filter,
                           (m.group(0)
                            for m in re.finditer(self.pattern, f.read())
                           ))

    def __call__(self):
        print("learning ... ", end="")
        sys.stdout.flush()
        chain = MarkovChain.MarkovChain(self._order)
        chain.learn(self.source())
        print("done.")

        if self._chainfile is not None:
            with open(self._chainfile, "wb") as f:
                pickle.dump(chain, f)

class Produce:
    def __init__(self, args):
        with open(args.chainfile, "rb") as f:
            self._chain = pickle.load(f)
        self._units = args.units

    def __call__(self):
        iterable = self._chain.emit()
        try:
            for i in range(self._units):
                print(next(iterable), end="")
        except StopIteration:
            pass
        print()



if __name__ == "__main__":
    import MarkovChain
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()
    learn_parser = subparsers.add_parser(
        "learn-words",
        help="Learn the markov chain from a source file"
    )
    learn_parser.set_defaults(cls=LearnWords)
    learn_parser.add_argument(
        "infile",
        metavar="INFILE",
        help="File to learn from. Must be plaintext"
    )
    learn_parser.add_argument(
        "order",
        type=positive_int,
        help="Order of the markov chain. Must be a positive integer."
    )
    learn_parser.add_argument(
        "chainfile",
        metavar="OUTFILE",
        default=None,
        nargs="?",
        help="File to store the learned data to. Can be omitted if --no-save is set."
    )
    learn_parser.add_argument(
        "--no-save",
        dest="save",
        action="store_false",
        default="True",
        help="Must be set to omit the chainfile argument"
    )
    learn_parser.add_argument(
        "--encoding",
        metavar="CODING",
        default="utf-8",
        help="Encoding used for the input file, defaults to utf-8"
    )
    learn_parser.add_argument(
        "--fold-whitespace",
        action="store_true",
        help="Map all whitespace to plain spaces"
    )
    learn_parser.add_argument(
        "--fold-case",
        action="store_true",
        help="Map all characters to lower case"
    )

    produce_parser = subparsers.add_parser(
        "produce",
        help="Load a saved markov chain and produce data from it"
    )
    produce_parser.set_defaults(cls=Produce)
    produce_parser.add_argument(
        "chainfile",
        help="Chain file to load"
    )
    produce_parser.add_argument(
        "units",
        metavar="NUMBER",
        type=positive_int,
        help="Produce NUMBER units of output"
    )

    args = parser.parse_args()

    try:
        cls = args.cls
    except AttributeError:
        parser.print_help()
        sys.exit(0)

    instance = args.cls(args)
    instance()

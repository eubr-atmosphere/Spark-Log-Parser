#!/usr/bin/env python3

## Copyright 2017-2018 Eugenio Gianniti
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

import argparse
import csv
import os
import sys

from collections import defaultdict
from pathlib import PurePath


def parse_dir_name (directory):
    experiment = query = None
    path = PurePath (directory)
    pieces = path.parts

    if len (pieces) >= 2:
        experiment = pieces[-2]
        query = pieces[-1]

    return experiment, query


def process_simulations (filename):
    results = defaultdict (dict)

    with open (filename, newline = '') as csvfile:
        reader = csv.DictReader (csvfile)

        for row in reader:
            query = row["Query"]

            if query == row["Run"]:
                experiment = row["Experiment"]
                results[experiment][query] = float (row["SimAvg"])

    return results


def process_summary (filename):
    cumsum = 0.
    count = 0

    with open (filename, newline = '') as csvfile:
        # Skip first line with application class
        try:
            next (csvfile)
        except StopIteration:
            pass

        reader = csv.DictReader (csvfile)

        try:
            for row in reader:
                cumsum += (float (row["applicationCompletionTime"]) -
                           float (row["applicationDeltaBeforeComputing"]))
                count += 1
        except KeyError as e:
            print ("warning: '{csv}' lacks key {key}".format (csv = filename, key = e),
                   file = sys.stderr)

    return cumsum / count


def parse_arguments (args = None):
    descr = "Build a CSV table comparing real data and empirical simulations"
    parser = argparse.ArgumentParser (description = descr)
    parser.add_argument ("root", help = "directory with processed and simulated logs")
    return parser.parse_args (args)


def main (args):
    avg_R = defaultdict (dict)

    for directory, _, files in os.walk (args.root):
        if "failed" not in directory:
            for filename in files:
                full_path = os.path.join (directory, filename)

                if filename == "summary.csv":
                    experiment, query = parse_dir_name (directory)
                    result = process_summary (full_path)
                    avg_R[experiment][query] = result
                elif filename == "simulations.csv":
                    sim_R = process_simulations (full_path)

    errors = {experiment:
              {query:
               {"measured": real,
                "simulated": sim_R[experiment][query],
                "error": (sim_R[experiment][query] - real) / real}
               for query, real in inner.items ()}
              for experiment, inner in avg_R.items ()}

    fields = ["Experiment", "Query", "Measured", "Simulated", "Error[1]"]
    rows = ({"Experiment": experiment,
             "Query": query,
             "Error[1]": data["error"],
             "Measured": data["measured"],
             "Simulated": data["simulated"]}
            for experiment, inner in errors.items ()
            for query, data in inner.items())

    writer = csv.DictWriter (sys.stdout, fieldnames = fields)
    writer.writeheader ()
    writer.writerows (rows)


if __name__ == "__main__":
    args = parse_arguments ()
    main (args)

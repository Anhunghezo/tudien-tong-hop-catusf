"""
Verify tab file


"""

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a tab file for errors", usage="Usage: python verify_tab_file.py --input data.tab --output data.stats")

    parser.add_argument("-i", "--input", required=True, help="Input file ")
    parser.add_argument("-o", "--output", help="Output report file")
    args, array = parser.parse_known_args()
    inputfile = args.input
    outputfile = args.output

    if not outputfile:
        outputfile = inputfile + ".cleaned"

    issuefile = inputfile + ".issued"

    outfile = open(outputfile, "w", encoding="utf-8")

    if not outfile:
        print(f"Couldnot open output file {outputfile}")

    issfile = open(issuefile, "w", encoding="utf-8")

    if not issfile:
        print(f"Couldnot open output file {issuefile}")

    skipped = 0

    with open(inputfile, "r", encoding="utf-8", errors="replace") as infile:  # , errors='replace'
        count = 0
        count_issues = 0

        while True:
            count += 1
            # print(f'Reading line {count}')
            line = infile.readline().strip()

            if not line:
                break

            tabs = line.count("\t")

            if tabs == 0:
                skipped += 1
                print(f"Line {count} has {tabs} tabs")
                issfile.write(f"{line}\n")
                count_issues += 1

            elif tabs > 1:
                skipped += 1
                print(f"Line {count} has {tabs} tabs")
                issfile.write(f"{line}\n")
                count_issues += 1
            else:
                items = line.split("\t")

                headword = items[0].strip()
                definition = items[1].strip()
                found_pos = definition.find(headword)

                if not headword:
                    print(f"Line {count} has empty headword")
                    skipped += 1
                    issfile.write(f"{headword}\t{definition}\n")
                    count_issues += 1
                    continue

                if not definition:
                    print(f"Line {count} has empty definition")
                    issfile.write(f"{headword}\t{definition}\n")
                    count_issues += 1

                    skipped += 1
                    continue

                if headword == definition[: len(headword)]:
                    print(f"Line {count} has duplicated headword")
                    issfile.write(f"{headword}\t{definition}\n")

                    definition = definition[len(headword) :].strip()
                    count_issues += 1

                outfile.write(f"{headword}\t{definition}\n")
                # print(f'{headword}\t{definition}')
                outfile.flush()

        if not count_issues:  # Nothing was written
            os.remove(issuefile)

        print(f"Original lines: {count}, skipped: {skipped}")

    outfile.close()
    issfile.close()


if __name__ == "__main__":
    main()

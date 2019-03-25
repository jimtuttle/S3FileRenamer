#!/usr/bin/env python3

"""Find and remove characters from directories and files that pose difficulty in Amazon S3.
    See https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingMetadata.html for a list of characters.
    This will generate a double pipe-delimited file for review.
    Default behavior is to only generate the log file for review.  Pass the "--rename" or "-r" flag to rename files.
 """

from os import rename, walk
from os.path import dirname, basename, exists, join
import argparse
import re


def contains_bad_characters(string, badchars):
    """Search input string for illegal characters.  Return True, list of characters found, if any found."""
    found_bad_characters = []
    for char in string:
        if char in badchars:
            found_bad_characters.append(char)
    if len(found_bad_characters) > 0:
        return True, found_bad_characters
    else:
        return False, ""


def perform_rename(old_name, root_path, found_bad_characters, rename_do):
    """Remove illegal characters if rename argument was passed to program."""
# Replaced "re.sub" because of conflict with regular expression wildcards
#   corrected_name = re.sub("|".join(found_bad_characters), "", old_name)
    corrected_name = ""
    for c in old_name:
        if c in found_bad_characters:
            c = "_"                     # Replacement character can be ""
        corrected_name += c
    # Avoid overwriting files that already exist.
    n = 0
    done = False
    check_name = corrected_name
    while not done:
        if exists(join(root_path, check_name)):
            n += 1
            check_name = re.sub(check_name.split(".")[0], corrected_name.split(".")[0] + str(n), check_name)
        else:
            done = True
            corrected_name = check_name
    if rename_do:
        print("Renaming {} to {}".format(join(root_path, old_name), join(root_path, corrected_name)))
        rename(join(root_path, old_name), join(root_path, corrected_name))
    else:
        print(corrected_name)
    return corrected_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and replace S3-illegal characters")
    parser.add_argument("-r", "--rename", help="Perform rename action.", action="store_true", default=False)
    parser.add_argument("-p", '--path', help="Path to data directory", required=True)
    parser.add_argument("-l", '--log', help="Path to log file directory", required=True)
    args = vars(parser.parse_args())
    path = args["path"]
    do_rename = args["rename"]
    log_directory = args["log"]
    log_file = open(join(log_directory, "rename.log"), "w")
    log_file.write("CHARACTERS || ORIGINAL NAME || NEW NAME\n")
    bad_characters = ["&", "$", "@", "=", ";", "+", ",", "?", "\\", "{", "^", "}", "%", "`", "]", "\"", ">", "[", "~",
                      "<", "#", "|"]
    for root, dirs, files in walk(path, topdown=False):
        for name in files:
            found, characters_found = contains_bad_characters(name, bad_characters)
            if found is True:
                new_name = perform_rename(name, root, characters_found, do_rename)
                log_line = "{} || {} || {}\n".format(" ".join(characters_found), join(root, name), join(root, new_name))
                print(log_line)
                log_file.write(log_line)
    log_file.close()

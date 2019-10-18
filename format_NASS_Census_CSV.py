# This script inputs National Agricultural Statistics Service (NASS) census
# data in the form of CSV files and adds a FIPS code field.
# Download census data here: https://quickstats.nass.usda.gov/

import os
import pandas

files = [r'C:/example.csv',]  # Replace this with the relevant file paths.

def add_FIPS(csv_files):
    """

    :param csv_files: List of one or more file paths to CSVs.
    :return: file path to new CSV
    """
    def fn(csv):
        df = pd.read_csv(csv, dtype=str)
        df['FIPS']=df['State ANSI']+df['County ANSI']
        return df

    for thing in csv_files:
        new_df = fn(thing)
        new_file_path = thing[:-4]+'_FIPS.csv'
        new_df.to_csv(new_file_path, index_label=False)


def match_format(csv_files, field):
    """
    Capatalizes first letter, all other letters lowercase. Used like this:
        match_format(state_files, 'State')
    :param csv_files:
    :param field: string name of field to be capitalized
    :return: None
    """
    for thing in csv_files:
        df = pd.read_csv(thing, dtype=str)
        df[field] = df[field].str.title()
        df.to_csv(thing, index_label=False)
        print ("Capitalized the '", field + "' field for", thing)


def remove_codes(csv_files, field, codes=["(D)", "(L)", "(H)"]):
    """
    NASS Census data come with all sorts of codes like (L) that make data processing
    difficult. This removes (D), (L), and (H) from a specific field.
    :param csv_files: list of file paths to csv's
    :param field: the string name of the field
    :return:
    """

    if isinstance(codes, str):
        raise TypeError("The codes parameter must be a list, not a string."
                        "Put some brackets around that string, honey.")

    for thing in csv_files:
        df = pd.read_csv(thing, dtype=str)
        # Replace (D), (L), and (H) with an empty string.
        for code in codes:
            df[field] = df[field].replace(code, "")

        df.to_csv(thing, index_label=False)
        print ("Removed weird characters for", thing)


if __name__ == '__main__':
    add_FIPS(files)

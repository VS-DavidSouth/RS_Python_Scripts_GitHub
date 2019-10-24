# This script inputs National Agricultural Statistics Service (NASS) census
# data in the form of CSV files and adds a FIPS code field.
# Download census data here: https://quickstats.nass.usda.gov/

# This is meant to be used with Python 3 (ArcGIS Pro)

import os
import pandas as pd

files = [r'C:/example.csv',]  # Replace this with the relevant file paths.

def convert_FIPS(csv_files):
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
        new_df.to_csv(new_file_path, index=False)


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
        df.to_csv(thing, index=False)
        print ("Capitalized the '", field + "' field for", thing)


def replace_codes(csv_files, field, codes=["(D)", "(L)", "(H)"], replace_value=0):
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
        # Replace (D), (L), and (H) with 0, and move the code to a new field
        for code in codes:
            df[field] = df[field].replace(
                code, replace_value).replace(
                    " " + code, replace_value)

        # Overwrite CSV
        df.to_csv(thing, index=False)
        print ("Replaced weird characters with", replace_value, "for", thing)


if __name__ == '__main__':
    csvs = (r'O:\MapRequests\Meg_Parker\Bison_StoryMap\NASS_2012_Census_Bison_operations_with_inventory_by_county.csv', r'O:\MapRequests\Meg_Parker\Bison_StoryMap\NASS_2012_Census_Bison_inventory_by_county.csv')
    replace_codes(csvs, "Value")

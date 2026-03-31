import os
import hashlib
import pandas as pd

def hash(*args):
    combined = ''.join(args)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def read_table(filepath):
    """
    Load a CSV or Excel file into a df, depending on the file extension

    :param filepath:
    :return:
    """
    _, file_extension = os.path.splitext(filepath)
    if file_extension == '.csv':
        df = pd.read_csv(filepath, encoding='utf-8')
    elif file_extension in ['.xls', '.xlsx']:
        df = pd.read_excel(filepath)
    else:
        raise ValueError("Unsupported file format")

    return df

def write_table(df, filepath):
    """
    Write a df into a CSV or Excel file, depending on the file extension

    :param filepath:
    :return:
    """
    _, file_extension = os.path.splitext(filepath)
    if file_extension == '.csv':
        df.to_csv(filepath, index=False, encoding='utf-8')
    elif file_extension in ['.xls', '.xlsx']:
        df.to_excel(filepath, index=False)
    else:
        raise ValueError("Unsupported file format")

    return df

def clean_name(value):
    value = value.strip().lower()
    return value.replace(' ', '_').replace('.', '-')


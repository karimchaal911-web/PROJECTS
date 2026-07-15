import pandas as pd
import re
def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    cleaned_columns = []


    for column in df.columns:
        column = str(column).strip().lower()
        column = re.sub(r"[^\w\s]", "_", column)
        column = re.sub(r"\s+", "_", column)
        column = re.sub(r"_+", "_", column)
    
        column = column.strip("_")

        cleaned_columns.append(column)

    df.columns = cleaned_columns

    # Prevent duplicate column names
    counts = {}
    unique_columns = []

    for column in df.columns:
        if column not in counts:
            counts[column] = 0
            unique_columns.append(column)
        else:
            counts[column] += 1
            unique_columns.append(f"{column}_{counts[column]}")

    df.columns = unique_columns

    return df
    




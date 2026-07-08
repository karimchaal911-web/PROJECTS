"""Data cleaning utilities for handling common data quality issues."""
import pandas as pd
import numpy as np
from pathlib import Path


def save_processed_data(df, filepath, format="csv", include_index=False, **kwargs):
    """
    Save processed data to the processed folder.
    
    IMPORTANT: This saves to the processed folder to preserve raw data.
    Never overwrite raw files - keep them as the single source of truth.
    
    Args:
        df: Dataframe to save
        filepath: Path or filename for the processed data
        format: 'csv' (default), 'parquet', 'json', 'xlsx'
        include_index: Whether to include dataframe index (default False)
        **kwargs: Additional arguments passed to save function
        
    Returns:
        Path object of saved file
        
    Example:
        save_processed_data(cleaned_df, "players_cleaned.csv")
        save_processed_data(cleaned_df, "DATA_PROCESSED / players_cleaned.parquet", format="parquet")
    """
    # Convert string path to Path object if needed
    if isinstance(filepath, str):
        filepath = Path(filepath)
    
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Save based on format
    if format.lower() == "csv":
        df.to_csv(filepath, index=include_index, **kwargs)
    elif format.lower() == "parquet":
        df.to_parquet(filepath, index=include_index, **kwargs)
    elif format.lower() == "json":
        df.to_json(filepath, index=include_index, **kwargs)
    elif format.lower() == "xlsx":
        df.to_excel(filepath, index=include_index, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    print(f"✓ Saved processed data to: {filepath}")
    return filepath


def load_raw_data(filepath):
    """
    Load raw data from the raw folder.
    
    Args:
        filepath: Path to raw data file
        
    Returns:
        Dataframe with loaded data
    """
    filepath = Path(filepath)
    
    if filepath.suffix.lower() == ".csv":
        return pd.read_csv(filepath)
    elif filepath.suffix.lower() == ".parquet":
        return pd.read_parquet(filepath)
    elif filepath.suffix.lower() == ".json":
        return pd.read_json(filepath)
    elif filepath.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")


def handle_missing_values(df, strategy="drop", fill_value=None, columns=None):
    """
    Handle missing values in a dataframe.
    
    Args:
        df: Input dataframe
        strategy: 'drop' (remove rows), 'fill' (fill with value), 'mean', 'median', 'mode', 'forward_fill', 'backward_fill'
        fill_value: Value to fill with (used if strategy='fill')
        columns: Specific columns to apply strategy to. If None, applies to all columns
        
    Returns:
        Dataframe with missing values handled
    """
    df = df.copy()
    
    if columns is None:
        columns = df.columns
    
    if strategy == "drop":
        return df.dropna(subset=columns)
    
    elif strategy == "fill":
        if fill_value is None:
            raise ValueError("fill_value must be provided when strategy='fill'")
        return df.fillna({col: fill_value for col in columns if col in df.columns})
    
    elif strategy == "mean":
        numeric_cols = df[columns].select_dtypes(include=[np.number]).columns
        return df.fillna(df[numeric_cols].mean())
    
    elif strategy == "median":
        numeric_cols = df[columns].select_dtypes(include=[np.number]).columns
        return df.fillna(df[numeric_cols].median())
    
    elif strategy == "mode":
        for col in columns:
            if col in df.columns:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col].fillna(mode_val[0], inplace=True)
        return df
    
    elif strategy == "forward_fill":
        return df.fillna(method="ffill")
    
    elif strategy == "backward_fill":
        return df.fillna(method="bfill")
    
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def remove_duplicates(df, subset=None, keep="first"):
    """
    Remove duplicate rows.
    
    Args:
        df: Input dataframe
        subset: Columns to consider for identifying duplicates. If None, uses all columns
        keep: 'first', 'last', or False (remove all duplicates)
        
    Returns:
        Dataframe with duplicates removed
    """
    return df.drop_duplicates(subset=subset, keep=keep)


def remove_outliers(df, columns, method="iqr", threshold=1.5):
    """
    Remove or flag outliers in specified columns.
    
    Args:
        df: Input dataframe
        columns: Column names to check for outliers
        method: 'iqr' (Interquartile Range) or 'zscore'
        threshold: IQR multiplier (default 1.5) or z-score threshold (default 3)
        
    Returns:
        Dataframe with outliers removed
    """
    df = df.copy()
    
    if isinstance(columns, str):
        columns = [columns]
    
    for col in columns:
        if col not in df.columns:
            continue
            
        if method == "iqr":
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        
        elif method == "zscore":
            z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
            df = df[z_scores < threshold]
    
    return df.reset_index(drop=True)


def standardize_dtypes(df, type_mapping=None):
    """
    Standardize data types in dataframe.
    
    Args:
        df: Input dataframe
        type_mapping: Dictionary mapping column names to desired dtypes
        
    Returns:
        Dataframe with standardized dtypes
    """
    df = df.copy()
    
    if type_mapping is None:
        type_mapping = {}
    
    for col, dtype in type_mapping.items():
        if col in df.columns:
            try:
                df[col] = df[col].astype(dtype)
            except ValueError:
                print(f"Warning: Could not convert {col} to {dtype}")
    
    return df


def clean_text_column(df, column, lowercase=True, strip=True, remove_extra_spaces=True):
    """
    Clean text in a specific column.
    
    Args:
        df: Input dataframe
        column: Column name containing text
        lowercase: Convert to lowercase
        strip: Remove leading/trailing whitespace
        remove_extra_spaces: Replace multiple spaces with single space
        
    Returns:
        Dataframe with cleaned text
    """
    df = df.copy()
    
    if column not in df.columns:
        return df
    
    if lowercase:
        df[column] = df[column].str.lower()
    
    if strip:
        df[column] = df[column].str.strip()
    
    if remove_extra_spaces:
        df[column] = df[column].str.replace(r'\s+', ' ', regex=True)
    
    return df


def remove_columns(df, columns):
    """
    Remove specified columns from dataframe.
    
    Args:
        df: Input dataframe
        columns: Column name(s) to remove (string or list)
        
    Returns:
        Dataframe with columns removed
    """
    if isinstance(columns, str):
        columns = [columns]
    
    return df.drop(columns=[col for col in columns if col in df.columns])


def rename_columns(df, mapping):
    """
    Rename columns using a mapping dictionary.
    
    Args:
        df: Input dataframe
        mapping: Dictionary mapping old column names to new names
        
    Returns:
        Dataframe with renamed columns
    """
    return df.rename(columns=mapping)


def validate_data_quality(df, print_report=True):
    """
    Validate and report on data quality.
    
    Args:
        df: Input dataframe
        print_report: Whether to print quality report
        
    Returns:
        Dictionary with quality metrics
    """
    quality_report = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "missing_percentage": (df.isnull().sum() / len(df) * 100).to_dict(),
        "duplicate_rows": df.duplicated().sum(),
        "dtypes": df.dtypes.to_dict()
    }
    
    if print_report:
        print("\n================ DATA QUALITY REPORT ================")
        print(f"Total Rows: {quality_report['total_rows']}")
        print(f"Total Columns: {quality_report['total_columns']}")
        print(f"Duplicate Rows: {quality_report['duplicate_rows']}")
        print("\nMissing Values:")
        for col, count in quality_report['missing_values'].items():
            if count > 0:
                pct = quality_report['missing_percentage'][col]
                print(f"  {col}: {count} ({pct:.2f}%)")
        print("\nData Types:")
        for col, dtype in quality_report['dtypes'].items():
            print(f"  {col}: {dtype}")
    
    return quality_report


def clean_numeric_column(df, column, handle_negative=False, handle_zero=False, round_decimals=None):
    """
    Clean numeric column by handling negative/zero values and rounding.
    
    Args:
        df: Input dataframe
        column: Column name
        handle_negative: If True, remove negative values
        handle_zero: If True, remove zero values
        round_decimals: Number of decimal places to round to
        
    Returns:
        Dataframe with cleaned numeric column
    """
    df = df.copy()
    
    if column not in df.columns:
        return df
    
    if handle_negative:
        df = df[df[column] >= 0]
    
    if handle_zero:
        df = df[df[column] != 0]
    
    if round_decimals is not None:
        df[column] = df[column].round(round_decimals)
    
    return df.reset_index(drop=True)


def filter_by_condition(df, conditions):
    """
    Filter dataframe by multiple conditions.
    
    Args:
        df: Input dataframe
        conditions: Dictionary of column -> (operator, value) pairs
                   operator can be: '==', '!=', '>', '<', '>=', '<=', 'in', 'not_in'
        
    Returns:
        Filtered dataframe
    """
    result = df.copy()
    
    for col, (operator, value) in conditions.items():
        if col not in result.columns:
            continue
        
        if operator == "==":
            result = result[result[col] == value]
        elif operator == "!=":
            result = result[result[col] != value]
        elif operator == ">":
            result = result[result[col] > value]
        elif operator == "<":
            result = result[result[col] < value]
        elif operator == ">=":
            result = result[result[col] >= value]
        elif operator == "<=":
            result = result[result[col] <= value]
        elif operator == "in":
            result = result[result[col].isin(value)]
        elif operator == "not_in":
            result = result[~result[col].isin(value)]
    
    return result.reset_index(drop=True)


def consolidate_pipeline(df, operations):
    """
    Run multiple cleaning operations in sequence.
    
    Args:
        df: Input dataframe
        operations: List of tuples (function_name, kwargs)
                   Example: [('remove_duplicates', {}), 
                            ('handle_missing_values', {'strategy': 'drop'})]
        
    Returns:
        Cleaned dataframe
    """
    result = df.copy()
    
    operation_map = {
        'handle_missing_values': handle_missing_values,
        'remove_duplicates': remove_duplicates,
        'remove_outliers': remove_outliers,
        'standardize_dtypes': standardize_dtypes,
        'clean_text_column': clean_text_column,
        'remove_columns': remove_columns,
        'rename_columns': rename_columns,
        'clean_numeric_column': clean_numeric_column,
        'filter_by_condition': filter_by_condition,
    }
    
    for op_name, kwargs in operations:
        if op_name not in operation_map:
            print(f"Warning: Unknown operation '{op_name}'")
            continue
        
        result = operation_map[op_name](result, **kwargs)
        print(f"✓ Applied: {op_name}")
    
    return result

import pandas as pd
import numpy as np


def process_data(file_path: str):
    df = pd.read_csv(file_path)
    df.fillna(0, inplace=True)

    process_file_path = f"ds_files/processed_data/{file_path.split('/')[-1]}"
    df.to_csv(process_file_path, index=False)
    return process_file_path



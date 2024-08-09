from datetime import datetime
import os
import pandas as pd
from src import DATA_PATH


def get_latest_file(prefix) -> str:
    dt_max = datetime(1970, 1, 1)
    f_max = ''
    for f in os.listdir(DATA_PATH):
        try:
            if not f.startswith(prefix):
                continue
            dt = f.split(prefix)[1].split('.')[0].strip('_')
            dt = datetime.strptime(dt, '%Y_%m_%d_%H_%M_%S')
            if dt > dt_max:
                dt_max = dt
                f_max = f
        except (IndexError, ValueError):
            continue
    print(f'Loading {f_max}')
    return os.path.join(DATA_PATH, f_max)


def load_data(model_name: str) -> pd.DataFrame:
    df = pd.read_csv(get_latest_file(model_name))
    return df

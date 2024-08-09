"""Geomagnetic Data
We use the Kp index to measure the Earth's magnetic force.
It is thought that this feature affects pigeons' homing ability.
"""
import requests
import pandas as pd

BASE_URL = 'https://kp.gfz-potsdam.de/app/json/'
index = 'Kp'
start = '2010-01-01T00:00:00Z'
end = '2025-01-01T00:00:00Z'
url = f'{BASE_URL}?start={start}&end={end}&index={index}&status=def'

res = requests.get(url).json()
df_mag = pd.DataFrame({k: v for k, v in res.items() if k in ['datetime', 'Kp']})
df_mag.datetime = df_mag.datetime.apply(pd.Timestamp)

df_mag[df_mag.datetime >= '2024-01-01'].set_index('datetime').rolling(10).mean().plot(title='Planetory Kp Index')

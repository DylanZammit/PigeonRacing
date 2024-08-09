import asyncio
from functools import partial

from datetime import datetime
import pandas as pd
import itertools
import os
from src import DATA_PATH
from src.data_load.loaders.malta_pigeon_federation import MaltaPigeonFederationAPI
from src.data_load.loaders.meteostat import get_geo_weather, get_all_locations
from src.data_load.utils import camel_to_snake, deg_to_compass, wind_speed_to_beaufort


async def get_raw_pigeon_list_club(club_id: int, mpr: MaltaPigeonFederationAPI):
    return [res async for res in mpr.get_pigeon_list(club=club_id)]


async def get_raw_pigeon_list(mpr: MaltaPigeonFederationAPI, club_list: list[int]):
    print(f'Getting pigeons for clubs {club_list}...')
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(get_raw_pigeon_list_club(club_id=club_id, mpr=mpr)) for club_id in club_list]

    pigeons = itertools.chain.from_iterable(x for task in tasks for x in task.result())
    return pigeons


async def get_raw_race_results(race_id: int, mpr: MaltaPigeonFederationAPI) -> list[dict]:

    race_results = await mpr.get_race_results(race_id=race_id)

    for pigeon_stats in race_results.get('results', []):
        pigeon_stats['race_id'] = race_id
        pigeon_stats['participants'] = race_results['participants']
        pigeon_stats['memberParticipants'] = race_results['memberParticipants']

    return race_results.get('results', [])


async def get_raw_race_club_stats(race_id: int, mpr: MaltaPigeonFederationAPI) -> list[dict]:
    race_club_stats = await mpr.get_race_club_stats(race_id=race_id)
    return race_club_stats


async def get_raw_race_participants(race_id: int, mpr: MaltaPigeonFederationAPI):
    gen = [res async for res in mpr.get_race_participants(race_id=race_id)]
    race_participants = itertools.chain.from_iterable(gen)
    return race_participants


def get_weather_columns_location(loc: str) -> list[str]:
    return [
        f'temperature_{loc}',
        f'dew_point_{loc}',
        f'relative_humidity_{loc}',
        f'precipitation_{loc}',
        f'wind_direction_degrees_{loc}',
        f'wind_speed_kph_{loc}',
        f'air_pressure_{loc}',
    ]


def include_weather_stats(df_races: pd.DataFrame) -> pd.DataFrame:

    location_metadata = get_all_locations()
    location_metadata.update({'departure': None})

    for location, lat_lon in location_metadata.items():

        df_races[get_weather_columns_location(location)] = df_races.apply(
            partial(get_geo_weather, lat_lon=lat_lon), axis=1, result_type='expand'
        )

        col_compass = f'wind_direction_compass_{location}'
        col_degrees = f'wind_direction_degrees_{location}'

        col_beafort = f'wind_speed_beaufort_{location}'
        col_speed = f'wind_speed_kph_{location}'

        df_races[col_compass] = df_races[col_degrees].apply(deg_to_compass)
        df_races[col_beafort] = df_races[col_speed].apply(wind_speed_to_beaufort)

    return df_races


def clean_race_results(races: pd.DataFrame, race_points: pd.DataFrame, race_club_stats: pd.DataFrame) -> pd.DataFrame:
    df_races_partial = pd.DataFrame(races).rename(columns=camel_to_snake)
    df_race_points = pd.DataFrame(race_points).rename(columns=camel_to_snake)
    df_race_club_stats = pd.DataFrame(race_club_stats).rename(columns=camel_to_snake)

    df_races = df_races_partial.merge(
        df_race_points,
        left_on='race_point_id',
        right_on='id',
        how='left',
        suffixes=('_race', '_race_points')
    ).merge(
        df_race_club_stats,
        right_on='race_id',
        left_on='id_race',
        how='right',
    )

    df_races['arrival_rate'] = df_races['arrived_pigeons'] / df_races['registered_pigeons']
    df_races['race_point_types'] = df_races['race_point_types'].apply(lambda x: x[0])
    df_races = df_races.rename({'release_datetime': 'release_epoch'}, axis=1)
    df_races['release_datetime'] = pd.to_datetime(df_races['release_epoch'], unit='ms')
    df_races['release_month'] = df_races.release_datetime.dt.month
    df_races['release_hour'] = df_races.release_datetime.dt.hour
    return df_races


async def get_all_data(club_list: list[int] = None) -> tuple[pd.DataFrame, ...]:

    club_list = club_list if club_list else range(1, 27)
    async with MaltaPigeonFederationAPI() as mpr:

        pigeons = await get_raw_pigeon_list(mpr, club_list=club_list)
        print('Getting members, race_points, races...')
        members = await mpr.get_members_list()
        race_points = await mpr.get_race_points()
        races = await mpr.get_race_list()
        async with asyncio.TaskGroup() as tg:
            race_club_stats = [tg.create_task(get_raw_race_club_stats(race['id'], mpr)) for race in races]
            race_participants = [tg.create_task(get_raw_race_participants(race['id'], mpr)) for race in races]
            raw_race_results = [tg.create_task(get_raw_race_results(race['id'], mpr)) for race in races]

    race_club_stats = itertools.chain.from_iterable(task.result() for task in race_club_stats)
    race_participants = itertools.chain.from_iterable(task.result() for task in race_participants)
    race_results_final = itertools.chain.from_iterable(task.result() for task in raw_race_results)

    df_pigeons = pd.DataFrame(pigeons).rename(columns=camel_to_snake)
    df_members = pd.DataFrame(members).rename(columns=camel_to_snake)
    df_race_results = pd.DataFrame(race_results_final).rename(columns=camel_to_snake)
    df_race_participants = pd.DataFrame(race_participants).rename(columns=camel_to_snake)

    df_races = clean_race_results(races, race_points, race_club_stats)
    df_races = include_weather_stats(df_races)

    df_race_results_final = df_race_participants.merge(
        df_pigeons,
        left_on='pigeon_id',
        right_on='id',
        how='left',
        suffixes=('_race_results', '_pigeon')
    ).merge(
        df_races,
        left_on=('race_id', 'club_number_race_results'),
        right_on=('race_id', 'club_number'),
        how='left',
        suffixes=('_pigeon', '_race')
    )

    cols_fillna_0 = ['club_points', 'section_points', 'federation_points', 'velocity']
    df_race_results_final = df_race_results_final.fillna({col: 0 for col in cols_fillna_0})

    return df_races, df_pigeons, df_members, df_race_results, df_race_participants, df_race_results_final


def save_data(df_list: tuple[pd.DataFrame, ...]) -> None:

    dt = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    df_races, df_pigeons, df_members, df_race_results, df_race_participants, df_race_results_final = df_list

    df_races.to_csv(os.path.join(DATA_PATH, f'df_race_results_{dt}.csv'), index=False)
    df_pigeons.to_csv(os.path.join(DATA_PATH, f'df_pigeons_{dt}.csv'), index=False)
    df_members.to_csv(os.path.join(DATA_PATH, f'df_members_{dt}.csv'), index=False)
    df_race_results.to_csv(os.path.join(DATA_PATH, f'df_race_results_{dt}.csv'), index=False)
    df_race_participants.to_csv(os.path.join(DATA_PATH, f'df_race_participants_{dt}.csv'), index=False)
    df_race_results_final.to_csv(os.path.join(DATA_PATH, f'df_race_results_final_{dt}.csv'), index=False)


if __name__ == '__main__':
    club_list = None
    df_list_out = asyncio.run(get_all_data(club_list=club_list))
    save_data(df_list_out)

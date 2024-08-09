from typing import AsyncGenerator

import os
import itertools
import aiohttp


class MaltaPigeonFederationAPI:

    def __init__(self, timeout: int = None, session_limit: int = 5):
        self.base_url = os.environ['BASE_URL']
        self.timeout = timeout
        self.session = None
        self.session_limit = session_limit

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=self.session_limit)
        self.session = aiohttp.ClientSession(connector=connector, base_url=self.base_url, timeout=self.timeout)
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.session.close()

    @staticmethod
    def params(**kwargs):
        return {k: v for k, v in kwargs.items() if v is not None}

    async def get_race_results(
            self,
            race_id: int,
            club: int = None,
            section: int = None,
            limit: int = None,
    ) -> dict:
        url = f'/unprot/races/related/{race_id}/results/federation.json'
        limit = limit or 10e100
        print(f'Getting race results for {race_id}')
        params = self.params(**{'club': club, 'section': section, 'limit': limit})
        res = await self.session.get(url, params=params)
        res_json = await res.json()

        return res_json

    async def get_race_list(
            self,
            limit: int = None,
            current_season: bool = False,
    ) -> list[dict]:
        limit = limit or 1_000
        url = '/unprot/races/list/currentseason.json' if current_season else '/unprot/races/list.json'
        params = self.params(**{'limit': limit})
        res = await self.session.get(url, params=params)
        res_json = await res.json()
        return res_json

    async def get_pigeon_list(
            self,
            club: int = None,
            section: int = None,
            state: str = None,
            limit: int = None,
            offset: int = 0,
            batch: int = 10_000,
    ) -> AsyncGenerator:

        url = '/unprot/pigeons/list.json'
        limit = limit or 10e100
        batch = min(batch, limit) if batch else limit

        tot_returned = 0
        prepend = f'of club {club}' if club else ''
        print(f' Loading pigeons {prepend}...')
        for req_num in itertools.count():
            params = self.params(**{'club': club, 'section': section, 'state': state, 'limit': batch,
                                    'offset': offset + req_num * batch})

            res_partial = await self.session.get(url, params=params)
            res_json = await res_partial.json()
            tot_returned += len(res_json)

            is_exhausted = len(res_json) == 0
            is_limit_reached = tot_returned >= limit
            if is_exhausted or is_limit_reached:
                if is_limit_reached:
                    yield res_json
                print(f'[Request {req_num + 1}] Loaded {tot_returned} pigeons {prepend}...')
                return

            yield res_json

    async def get_all_pigeons(self) -> list[dict]:
        return [res for club in range(1, 27) async for res in self.get_pigeon_list(club=club)]

    async def get_members_list(
            self,
            club: int = None,
            section: int = None,
            limit: int = None,
    ) -> list[dict]:
        url = '/unprot/members/list.json'
        params = self.params(**{'club': club, 'section': section, 'limit': limit})
        res = await self.session.get(url, params=params)
        res_json = await res.json()
        return res_json

    async def get_pigeon_races(
            self,
            pigeon_id: int,
            limit: int = None,
    ) -> list[dict]:
        limit = limit or 10e100
        url = f'/unprot/pigeons/related/{pigeon_id}/races.json'
        params = self.params(**{'limit': limit})
        res = await self.session.get(url, params=params)
        res_json = await res.json()
        return res_json

    async def get_race_club_stats(
            self,
            race_id: int,
            club: int = None,
    ) -> list[dict]:
        url = f'/unprot/races/related/{race_id}/bookings.json'
        params = self.params(**{'club': club})
        res = await self.session.get(url, params=params)
        res_json = await res.json()
        return res_json

    async def get_race_participants(
            self,
            race_id: int,
            club: int = None,
            limit: int = None,
            offset: int = 0,
            batch: int = 1_000,
    ) -> AsyncGenerator:

        limit = limit or 10e100
        batch = min(batch, limit) if batch else limit

        tot_returned = 0
        print(f'Load race participants for {race_id=}')
        for req_num in itertools.count():
            url = f'/unprot/races/related/{race_id}/registers.json'
            params = self.params(**{'club': club, 'limit': batch, 'offset': offset + req_num * batch})
            res_partial = await self.session.get(url, params=params)
            res = await res_partial.json()
            tot_returned += len(res)

            is_exhausted = len(res) == 0
            is_limit_reached = tot_returned >= limit
            if is_exhausted or is_limit_reached:
                if is_limit_reached:
                    yield res
                print(f'[Request {req_num + 1}] Loaded {tot_returned} race participants for {race_id=}...')
                return

            yield res

    async def get_race_points(self) -> list[dict]:
        url = f'/unprot/racepoints/list.json'
        res = await self.session.get(url)
        res_json = await res.json()
        return res_json

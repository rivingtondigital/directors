from collections import namedtuple
import pandas as pd
import requests
import json

from directors.orm.models import Company


Listing = namedtuple('Listing', ['name', 'symbol', 'market'])


class Market:
    def __init__(self, link, name_col, symbol_col, source):
        self.link = link
        self.name_col = name_col
        self.symbol_col = symbol_col
        self.source = source
        self._data = None

    @property
    def listings(self):
        if self._data is None:
            self._data = self._fetch_data()
        return self._data

    def _fetch_data(self):
        ret = []
        resp = requests.get(self.link)
        blob = resp.content.decode()
        data = json.loads(blob)
        for line in data:
            try:
                ret.append(
                    Listing(
                        line[self.name_col],
                        line[self.symbol_col],
                        self.source)
                )
            except Exception as e:
                print("Problem encountered with {} on line:\n{}\n{}".format(self.source, line, e))
        return ret

    def to_pandas(self):
        return pd.DataFrame(self.listings)

    def to_orm(self):
        companies = Company.batch_update(self.listings, market=self.source)
        return companies


nyse = Market(
    link='https://datahub.io/core/nyse-other-listings/r/nyse-listed.json',
    name_col='Company Name',
    symbol_col='ACT Symbol',
    source='nyse')


nasdaq = Market(
    link='https://datahub.io/core/nasdaq-listings/r/nasdaq-listed-symbols.json',
    name_col='Company Name',
    symbol_col='Symbol',
    source='nasdaq')




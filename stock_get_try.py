"""import requests

import alpha_vantage

API_URL = "https://www.alphavantage.co/query"

data = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "AAPL",
    "outputsize": "compact",
    "datatype": "csv",
    "apikey": "XA3RBMF2EOR78ND2",
    }
response = requests.get(API_URL, params=data)
print(response.json())"""

from alpha_vantage.timeseries import TimeSeries
import pandas as pd
def lookup2():
    ts = TimeSeries(key='XA3RBMF2EOR78ND2', output_format='pandas')
    data, meta_data = ts.get_intraday(symbol='AAPL', interval='60min', outputsize='full')

    data.to_csv("data.csv")
    data = pd.read_csv("data.csv")
    # data = pd.DataFrame(data)
    s = data['date'].apply(lambda x: x.split())
    data['Date'] = s.apply(lambda x: x[0])
    data['Time'] = s.apply(lambda x: x[1])
    data.to_csv("data.csv")


# lookup2()
# data['4. close'].plot()
# plt.title('Intraday TimeSeries Google')
# plt.show()

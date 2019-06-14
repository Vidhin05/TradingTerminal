from functools import wraps

from alpha_vantage.timeseries import TimeSeries
from flask import redirect, render_template, request, session, url_for


def apology(top="", bottom=""):
    """Renders message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=escape(top), bottom=escape(bottom))


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


"""def lookup(symbol):
    # Look up quote for symbol.

    # reject symbol if it starts with caret
    if symbol.startswith("^"):
        return None

    # reject symbol if it contains comma
    if "," in symbol:
        return None

    # query Yahoo for quote
    # http://stackoverflow.com/a/21351911
    try:
        url = "http://download.finance.yahoo.com/d/quotes.csv?f=snl1&s={}".format(symbol)
        webpage = urllib.request.urlopen(url)
        datareader = csv.reader(webpage.read().decode("utf-8").splitlines())
        row = next(datareader)
    except:
        return None

    # ensure stock exists
    try:
        price = float(row[2])
    except:
        return None

    # return stock's name (as a str), price (as a float), and (uppercased) symbol (as a str)
    return {
        "name": row[1],
        "price": price,
        "symbol": row[0].upper()
    }"""


def stock_hist(symbol):
    ts = TimeSeries(key='QRXN341LEPEKC3DN', output_format='pandas')
    # data, meta_data = ts.get_daily(symbol='AAPL')
    data, meta_data = ts.get_intraday(symbol='AAPL', interval='60min')
    data.to_csv("data.csv")
    return

# XA3RBMF2EOR78ND2
def lookup(symbol):
    ts = TimeSeries(key='QRXN341LEPEKC3DN')
    data = ts.get_quote_endpoint(symbol='AAPL')
    return {
        "name": symbol,
        "price": float(data[0]['05. price']),
        "symbol": symbol
    }


# def lookup(symbol):
#     API_URL = "https://www.alphavantage.co/query"
#     data = {
#         "function": "GLOBAL_QUOTE",
#         "symbol": "AAPL",
#         "datatype": "json",
#         "apikey": "XA3RBMF2EOR78ND2",
#     }
#     response = requests.get(API_URL, params=data)
#     data = response.json()
#     return {
#         "name": symbol,
#         "price": float(data['Global Quote']['05. price']),
#         "symbol": symbol
#     }


def usd(value):
    """Formats value as USD."""
    return "${:,.2f}".format(value)

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


def stock_hist(symbol):
    ts = TimeSeries(key='QRXN341LEPEKC3DN', output_format='pandas')
    # data, meta_data = ts.get_daily(symbol='AAPL')
    data, meta_data = ts.get_intraday(symbol=symbol, interval='60min')
    return data


# XA3RBMF2EOR78ND2
def lookup(symbol):
    ts = TimeSeries(key='XA3RBMF2EOR78ND2')
    data = ts.get_quote_endpoint(symbol=symbol)
    return {
        "name": symbol,
        "price": float(data[0]['05. price']),
        "symbol": symbol
    }


def usd(value):
    """Formats value as USD."""
    return "${:,.2f}".format(value)

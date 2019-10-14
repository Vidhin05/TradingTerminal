import base64
import io
import itertools
import math
import os
import time
from datetime import datetime
from tempfile import gettempdir

import matplotlib.pyplot as plt
import psycopg2
from flask import Flask
from flask_session import Session
from matplotlib import style
from passlib.hash import sha256_crypt

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# for local run change sslmode to allow and add environment variable DATABASE_URL=postgresql://localhost/tradingterminal
DATABASE_URL = os.environ['DATABASE_URL']
db = psycopg2.connect(DATABASE_URL, sslmode='allow')
c = db.cursor()

start = 1572892200.0


@app.route("/")
@login_required
def index():
    refresh()

    c.execute("SELECT username, cash FROM users WHERE id = %s", [session["user_id"]])
    username, current_cash = c.fetchall()[0]

    c.execute("SELECT symbol, sum(quantity) FROM transactions WHERE user_id = %s GROUP BY symbol",
              [session["user_id"]])
    available = c.fetchall()

    c.execute(
        "SELECT option_id, stock_symbol, option_type, strike_price, shares , expiry_date FROM option_transaction"
        " WHERE writer_id=%s GROUP BY option_id, stock_symbol, option_type, strike_price, shares , expiry_date",
        [session["user_id"]])
    written_options = c.fetchall()

    c.execute(
        "SELECT option_id, stock_symbol, option_type, strike_price, shares , expiry_date"
        " FROM option_chain WHERE writer_id=%s GROUP BY option_id", [session["user_id"]])
    unsold_options = c.fetchall()

    c.execute("SELECT * FROM option_transaction WHERE holder_id=%s AND is_available='Yes'",
              [session["user_id"]])
    available_options = c.fetchall()

    stocks_value = 0
    for stock in available:
        stocks_value += (stock[1] * lookup(stock[0])["price"])
    c.execute("UPDATE users SET assets = %s WHERE id = %s", [stocks_value, session["user_id"]])
    db.commit()
    return render_template("index.html", username=username, current_cash=current_cash, available=available,
                           lookup=lookup, usd=usd, stocks_value=stocks_value, available_options=available_options,
                           written_options=written_options, unsold_options=unsold_options)


@app.route("/quote/", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    refresh()

    c.execute("SELECT username FROM users WHERE id = %s", [session["user_id"]])
    username = c.fetchall()[0][0]
    if request.method == "GET" and request.args.get('stock_symbol', None) is None:
        return render_template("quote.html", username=username)
    elif request.method == "POST" or request.args.get('stock_symbol', None) is not None:
        if request.args.get('stock_symbol', None) is not None:
            stock = lookup(request.args.get('stock_symbol', None))
        else:
            if not request.form.get("stock-symbol"):
                return apology("Error", "Forgot to enter a stock")
            stock = lookup(request.form.get("stock-symbol"))
        if not stock:
            return apology("ERROR", "INVALID STOCK")
        df = stock_hist(stock['symbol'])
        c.execute("SELECT symbol, sum(quantity) FROM transactions WHERE user_id = %s AND symbol = %s GROUP BY symbol",
                  [session["user_id"], stock["symbol"]])
        available = c.fetchall()
        # style.use('ggplot')
        # style.use('seaborn-deep')
        style.use('fivethirtyeight')
        img = io.BytesIO()
        df['Close'].plot()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(img, format='png', transparent=True)
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        c.execute("SELECT price, sum(shares), buy_sell FROM order_book where stock_symbol=%s and shares>0 "
                  "group by price, buy_sell ORDER BY price",
                  [stock['symbol']])
        orders = c.fetchall()
        order_book = []
        total_buy = 0
        total_sell = 0
        for row in orders:
            if row[2] == 'buy':
                order_book.append([int(row[1]), row[0], '-'])
                total_buy += row[1]
            else:
                order_book.append(['-', row[0], int(row[1])])
                total_sell += row[1]

        return render_template("quoted.html", stock=stock, url='data:image/png;base64,{}'.format(graph_url),
                               username=username, order_book=order_book, total_buy=total_buy, total_sell=total_sell,
                               available=available, stock_symbol=stock["symbol"], usd=usd)


@app.route("/buy/", methods=["POST"])
@login_required
def buy():
    c.execute("SELECT username, cash FROM users WHERE id = %s", [session["user_id"]])
    username, current_cash = c.fetchall()[0]
    """Buy shares of stock."""

    stock_symbol = request.args.get('stock_symbol', None)
    price = float(request.form.get("price"))
    try:
        stock_quantity = int(request.form.get("stock-quantity"))

    except ValueError:
        return apology("ERROR", "ENTER QUANTITY IN WHOLE NUMBERS ONLY")
    if not stock_symbol:
        return apology("ERROR", "FORGOT STOCK SYMBOL")
    elif not stock_quantity:
        return apology("ERROR", "FORGOT DESIRED QUANTITY")

    stock_info = lookup(stock_symbol)
    if not stock_info:
        return apology("ERROR", "INVALID STOCK")

    transaction_cost = price * stock_quantity
    if transaction_cost <= current_cash:
        c.execute("INSERT INTO order_book(writer_id, stock_symbol, price, shares, buy_sell, order_time)"
                  " VALUES(%s, %s, %s, %s,'buy', %s)",
                  [session["user_id"], stock_info["symbol"], price, stock_quantity, time.strftime("%c")])
        db.commit()
        c.execute("SELECT last_value FROM order_book_order_id_seq;")
        order_id = c.fetchall()[0][0]
        order_book_execute(order_id)
    else:
        return apology("ERROR", "INSUFFICIENT FUNDS")
    return redirect(url_for("quote", stock_symbol=stock_symbol))


@app.route("/sell/", methods=["POST"])
@login_required
def sell():
    """Sell shares of stock."""
    stock_symbol = request.args.get('stock_symbol', None)
    price = float(request.form.get("price"))
    c.execute("SELECT sum(quantity) FROM transactions WHERE user_id = %s AND symbol = %s",
              [session["user_id"], stock_symbol])
    stock_available = c.fetchall()
    try:
        stock_quantity = int(request.form.get("stock-quantity"))
    except ValueError:
        return apology("ERROR", "ENTER QUANTITY IN WHOLE NUMBERS ONLY")

    if not stock_symbol:
        return apology("ERROR", "Missing stock symbol")
    if not stock_available[0][0]:
        return apology("ERROR", "You don't own this security")

    if stock_quantity <= stock_available[0][0]:
        c.execute("INSERT INTO order_book(writer_id, stock_symbol, price, shares, buy_sell, order_time)"
                  " VALUES(%s, %s, %s, %s,'sell', %s)",
                  [session["user_id"], stock_symbol, price, stock_quantity, time.strftime("%c")])
        c.execute("SELECT last_value FROM order_book_order_id_seq;")
        order_id = c.fetchall()[0][0]
        db.commit()
        order_book_execute(order_id)
    else:
        return apology("ERROR", "You don't own that much!")
    return redirect(url_for("quote", stock_symbol=stock_symbol))


@app.route("/option_quote/", methods=["GET", "POST"])
@login_required
def option_quote():
    """Get stock option quote."""
    refresh()

    c.execute("SELECT username FROM users WHERE id = %s", [session["user_id"]])
    username = c.fetchall()[0][0]
    if request.method == "GET" and request.args.get('stock_symbol', None) is None:
        return render_template("option_quote.html", username=username)
    elif request.method == "POST" or request.args.get('stock_symbol', None) is not None:
        if request.args.get('stock_symbol', None) is not None:
            stock = lookup(request.args.get('stock_symbol', None))
        else:
            if not request.form.get("stock-symbol"):
                return apology("Error", "Forgot to enter a stock")
            stock = lookup(request.form.get("stock-symbol"))
        if not stock:
            return apology("ERROR", "INVALID STOCK")

        days = ((datetime(datetime.now().year, datetime.now().month,
                          datetime.now().day).timestamp() - start) / 86400)
        offset = 7 - days % 7
        option_dates = [(days + offset) * 86400, (days + offset + 7) * 86400, (days + offset + 14) * 86400]
        option_dates = [datetime.fromtimestamp(start + x).strftime('%c') for x in option_dates]

        df = stock_hist(stock['symbol'])
        c.execute("SELECT symbol, sum(quantity) FROM transactions WHERE user_id = %s AND symbol = %s GROUP BY symbol",
                  [session["user_id"], stock["symbol"]])
        available = c.fetchall()
        # style.use('ggplot')
        # style.use('seaborn-deep')
        style.use('fivethirtyeight')
        img = io.BytesIO()
        df['Close'].plot()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(img, format='png', transparent=True)
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        c.execute(
            "SELECT option_price, sum(shares), buy_sell, option_type, expiry_date, strike_price "
            "FROM option_chain where stock_symbol=%s and shares>0 "
            "group by option_price, buy_sell, option_type, expiry_date, strike_price"
            " ORDER BY expiry_date, strike_price, option_price",
            [stock['symbol']])

        orders = c.fetchall()
        exp_str = sorted(list(set([(item[4], item[5]) for item in orders])))
        option_order_book = []
        total_call_buy = 0
        total_call_sell = 0
        total_put_buy = 0
        total_put_sell = 0
        for row in orders:
            if row[3] == 'CALL':
                if row[2] == 'buy':
                    total_call_buy += row[1]
                else:
                    total_call_sell += row[1]
            if row[3] == 'PUT':
                if row[2] == 'buy':
                    total_put_buy += row[1]
                else:
                    total_put_sell += row[1]

        for item in exp_str:
            call_list = []
            put_list = []
            for row in orders:
                if (row[4], row[5]) == item and row[3] == 'CALL':
                    call_list.append(list(row))
                elif (row[4], row[5]) == item and row[3] == 'PUT':
                    put_list.append(list(row))
            call_list_order_price = set([item[0] for item in call_list])
            put_list_order_price = set([item[0] for item in put_list])
            new_call_list = []
            new_put_list = []
            for x in call_list_order_price:
                buy_qty = 0
                sell_qty = 0
                for row in call_list:
                    if row[0] == x:
                        if row[2] == 'buy':
                            buy_qty += row[1]
                        else:
                            sell_qty += row[1]
                new_call_list.append([buy_qty, x, sell_qty])
            for x in put_list_order_price:
                buy_qty = 0
                sell_qty = 0
                for row in call_list:
                    if row[0] == x:
                        if row[2] == 'buy':
                            buy_qty += row[1]
                        else:
                            sell_qty += row[1]
                new_put_list.append([buy_qty, x, sell_qty])
            call_put = list(itertools.zip_longest(new_call_list, new_put_list))
            for row in call_put:
                if row[0] is None:
                    option_order_book.append(['-', '-', '-', item[1], item[0], row[1][0], row[1][1], row[1][2]])
                elif row[1] is None:
                    option_order_book.append([row[0][0], row[0][1], row[0][2], item[1], item[0], '-', '-', '-'])
                else:
                    option_order_book.append(
                        [row[0][0], row[0][1], row[0][2], item[1], item[0], row[1][0], row[1][1], row[1][2]])

        return render_template("option_quoted.html", stock=stock, url='data:image/png;base64,{}'.format(graph_url),
                               username=username, option_order_book=option_order_book,
                               total_put_buy=total_put_buy, total_put_sell=total_put_sell,
                               total_call_buy=total_call_buy, total_call_sell=total_call_sell,
                               available=available, stock_symbol=stock["symbol"], option_dates=option_dates)


@app.route("/option_buy/", methods=["POST"])
@login_required
def option_buy():
    refresh()
    stock_symbol = request.args.get('stock_symbol', None)

    c.execute("SELECT cash FROM users WHERE id = %s", [session["user_id"]])
    current_cash = float(c.fetchall()[0][0])
    option_price = float(request.form.get("option_price"))
    shares = int(request.form.get("shares"))
    option_type = request.form.get("option_type")
    strike_price = float(request.form.get("strike_price"))
    expiry_date = request.form.get("expiry_date_buy")

    transaction_cost = option_price * shares
    if transaction_cost <= current_cash:
        c.execute(
            "INSERT INTO option_chain(writer_id, holder_id, stock_symbol, option_type, option_price, strike_price,"
            " shares, transaction_date,expiry_date, buy_sell) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, 'buy')",
            [session["user_id"], session["user_id"], stock_symbol, option_type, option_price, strike_price,
             shares,
             time.strftime("%c"), expiry_date])
        db.commit()
        print("Transaction sent.")
        c.execute("SELECT last_value FROM option_chain_option_id_seq;")
        order_id = c.fetchall()[0][0]
        option_chain_execute(order_id)
    else:
        return apology("ERROR", "INSUFFICIENT FUNDS")
    return redirect(url_for("option_quote", stock_symbol=stock_symbol))


@app.route("/option_sell/", methods=["POST"])
@login_required
def option_sell():
    refresh()
    stock_symbol = request.args.get('stock_symbol', None)

    c.execute("SELECT username FROM users WHERE id = %s", [session["user_id"]])
    c.execute("SELECT * FROM option_transaction WHERE holder_id=%s AND is_available='Yes'",
              [session["user_id"]])
    transactions = c.fetchall()

    option_id = request.form.get("option_id")
    option_price = request.form.get("option_price")

    if not option_id:
        strike_price = request.form.get("strike_price")
        option_type = request.form.get("option_type")
        shares = request.form.get("shares")
        expiry_date = request.form.get("expiry_date_sell")
        c.execute(
            "INSERT INTO option_chain(writer_id, holder_id, stock_symbol, option_type, option_price, strike_price,"
            " shares, transaction_date,expiry_date,buy_sell) "
            "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s,'sell')",
            [session["user_id"], session["user_id"], stock_symbol, option_type, option_price, strike_price,
             shares,
             time.strftime("%c"), expiry_date])
        db.commit()
        c.execute("SELECT last_value FROM option_chain_option_id_seq;")
        order_id = c.fetchall()[0][0]
        option_chain_execute(order_id)

    elif int(option_id) in [row[0] for row in transactions]:
        writer_id, holder_id, stock_symbol, option_type, strike_price, shares, expiry_date = \
            c.execute(
                "SELECT writer_id, holder_id, stock_symbol, option_type, strike_price, shares, expiry_date "
                "FROM option_transaction WHERE option_id = %s", [option_id]).fetchall()[0]

        c.execute("UPDATE option_transaction SET is_available = 'No' WHERE holder_id = %s and option_id = %s",
                  [holder_id, option_id])
        c.execute("UPDATE option_chain SET option_price= %s, shares = %s where option_id=%s",
                  [option_price, shares, option_id])
        db.commit()
        print("Transaction sent.")
        option_chain_execute(option_id)
    else:
        return apology("ERROR", "No such option")

    return redirect(url_for("option_quote", stock_symbol=stock_symbol))


@app.route("/history/")
@login_required
def history():
    refresh()
    """Show history of transactions."""

    c.execute("SELECT username FROM users WHERE id = %s", [session["user_id"]])
    username = c.fetchall()[0][0]
    c.execute("SELECT * FROM transactions WHERE user_id = %s", [session["user_id"]])
    transactions = c.fetchall()
    c.execute("SELECT * FROM option_transaction WHERE holder_id = %s AND is_available = 'Yes'",
              [session["user_id"]])
    option_transactions = c.fetchall()
    return render_template("history.html", transactions=transactions, option_transactions=option_transactions,
                           lookup=lookup, usd=usd, username=username)


@app.route("/leaderboard/")
@login_required
def leaderboard():
    refresh()

    c.execute("SELECT username FROM users WHERE id = %s", [session["user_id"]])
    username = c.fetchall()[0][0]
    c.execute("SELECT username, cash, assets FROM users ORDER BY cash + assets DESC")
    leaders = c.fetchall()
    return render_template("leaderboard.html", leaders=leaders, usd=usd, username=username)


@app.route("/login/", methods=["GET", "POST"])
def login():
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        c.execute("SELECT * FROM users WHERE username = %s", [request.form.get("username")])
        all_rows = c.fetchall()

        # ensure username exists and password is correct
        if len(all_rows) != 1 or not sha256_crypt.verify(request.form.get("password"), all_rows[0][2]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = all_rows[0][0]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout/")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/register/", methods=["GET", "POST"])
def register():
    """Register user."""
    username = request.form.get("username")
    password = request.form.get("password")
    password_confirm = request.form.get("password-confirm")
    # if get request return register template
    if request.method == "GET":
        return render_template("register.html")
    # if post request
    elif request.method == "POST":
        # check fields for completion
        if not request.form.get("username"):
            return apology("Error", "Forgot Username")
        elif not request.form.get("password"):
            return apology("Error", "Forgot Password")
        elif not request.form.get("password-confirm"):
            return apology("Error", "Forgot Confirmation")

        # if passwords match
        if password == password_confirm:
            # encrypt password
            hashed = sha256_crypt.encrypt(password)
            try:
                # send user details to database
                c.execute("INSERT INTO users(username, hash) VALUES(%s, %s)", [username, hashed])
                db.commit()

                # immediately log user in
                c.execute("SELECT * FROM users WHERE username = %s", [username])
                session["user_id"] = c.fetchall()[0][0]

                # send user to index
                return redirect(url_for("index"))

            # if username is not unique alert user
            # except sqlite3.IntegrityError:
            except psycopg2.IntegrityError:
                return apology("Error", "Username taken")
        else:
            return apology("Passwords don't match")


# noinspection PyUnusedLocal
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


def refresh():
    c.execute("SELECT id, cash, last_update_time FROM users")
    rows = c.fetchall()
    users, current_cash = [item[0] for item in rows], [item[1] for item in rows]
    last_update_time = [item[2] for item in rows]

    current_time = time.time()
    time_elapsed = current_time - datetime.strptime(last_update_time[0], '%c').timestamp()
    if time_elapsed > 300:
        c.execute("SELECT * FROM option_chain WHERE shares>0")
        available_options = c.fetchall()
        for option in available_options:
            if current_time > datetime.strptime(option[9], '%c').timestamp():
                try:
                    c.execute("SELECT * FROM option_transaction WHERE option_id = %s", [option[0]])
                    current_option = c.fetchall()[-1]
                    c.execute("UPDATE option_chain SET shares=0  WHERE option_id=%s", [option[0]])
                    c.execute(
                        "UPDATE option_transaction SET is_available='Yes' "
                        "WHERE option_id=%s AND holder_id=%s AND transaction_date=%s",
                        [current_option[0], current_option[2], current_option[8]])
                    db.commit()
                except IndexError:
                    c.execute("UPDATE option_chain SET shares=0 WHERE option_id=%s", [option[0]])
                    db.commit()
        cash_update(users, current_cash, time_elapsed)
        option_update(current_time)
    # noinspection SqlWithoutWhere
    c.execute("UPDATE users SET last_update_time = %s", [time.strftime('%c')])


def cash_update(users, current_cash, time_elapsed):
    factor = math.exp(0.1 * (time_elapsed / 31557600))
    for i in range(len(users)):
        new_cash = current_cash[i] * factor
        c.execute("UPDATE users SET cash = %s WHERE id = %s", [new_cash, users[i]])
    db.commit()


def option_update(current_time):
    c.execute("SELECT * FROM option_transaction WHERE is_available='Yes'")
    available_options = c.fetchall()
    for option in available_options:
        if current_time > datetime.strptime(option[10], '%c').timestamp():  # expiry_date
            if option[4] == "CALL":  # option_type
                if option[6] < lookup(option[3])["price"]:  # strike_price
                    writer_id, holder_id = option[1], option[2]
                    c.execute("SELECT cash FROM users WHERE id = %s", [holder_id])
                    holder_cash = float(c.fetchall()[0][0])
                    c.execute("SELECT cash FROM users WHERE id = %s", [writer_id])
                    writer_cash = float(c.fetchall()[0][0])
                    strike_price = option[6]
                    stock_symbol = option[3]
                    stock_quantity = int(option[7])
                    stock_price = lookup(stock_symbol)["price"]
                    transaction_cost = stock_price * stock_quantity
                    if transaction_cost <= writer_cash:
                        writer_cash -= transaction_cost
                        c.execute("UPDATE users SET cash = %s WHERE id = %s", [writer_cash, writer_id])
                        c.execute(
                            "INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date) "
                            "VALUES(%s, %s, %s, %s, %s)",
                            [writer_id, stock_symbol, stock_price, stock_quantity,
                             time.strftime("%c")])
                        c.execute(
                            "INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date) "
                            "VALUES(%s, %s, %s, %s, %s)",
                            [writer_id, stock_symbol, stock_price, -stock_quantity,
                             time.strftime("%c")])
                        db.commit()
                        print("Transaction sent.")

                    transaction_cost = strike_price * stock_quantity
                    if transaction_cost <= holder_cash:
                        holder_cash -= transaction_cost
                        c.execute("UPDATE users SET cash = %s WHERE id = %s", [holder_cash, holder_id])
                        c.execute(
                            "INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date) "
                            "VALUES(%s, %s, %s, %s, %s)",
                            [holder_id, stock_symbol, strike_price, stock_quantity,
                             time.strftime("%c")])
                        c.execute("UPDATE option_transaction SET is_available='No' WHERE option_id = %s ",
                                  [option[0]])
                        db.commit()
                        print("Transaction sent.")

            elif option[4] == "PUT":
                if option[6] > lookup(option[3])["price"]:  # strike_price
                    writer_id, holder_id = option[1], option[2]
                    c.execute("SELECT cash FROM users WHERE id = %s", [holder_id])
                    holder_cash = c.fetchall()[0][0]
                    c.execute("SELECT cash FROM users WHERE id = %s", [writer_id])
                    writer_cash = c.fetchall()[0][0]
                    strike_price = option[3]
                    stock_symbol = option[3]
                    stock_quantity = option[7]
                    stock_price = lookup(stock_symbol)["price"]

                    transaction_cost = (strike_price - stock_price) * stock_quantity
                    if transaction_cost <= holder_cash:
                        holder_cash += transaction_cost
                        c.execute("UPDATE users SET cash = %s WHERE id = %s", [holder_cash, holder_id])
                        c.execute(
                            "INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date) "
                            "VALUES(%s, %s, %s, %s, %s)",
                            [holder_id, stock_symbol, stock_price, stock_quantity,
                             time.strftime("%c")])
                        c.execute(
                            "INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date) "
                            "VALUES(%s, %s, %s, %s, %s)",
                            [holder_id, stock_symbol, strike_price, -stock_quantity,
                             time.strftime("%c")])
                        db.commit()
                        print("Transaction sent.")

                    transaction_cost = strike_price * stock_quantity
                    writer_cash -= transaction_cost
                    c.execute("UPDATE users SET cash = %s WHERE id = %s", [writer_cash, writer_id])
                    c.execute(
                        "INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)"
                        "VALUES(%s, %s, %s, %s, %s)",
                        [writer_id, stock_symbol, strike_price, stock_quantity,
                         time.strftime("%c")])
                    c.execute("UPDATE option_transaction SET is_available='No' WHERE option_id = %s ", [option[0]])
                    db.commit()
                    print("Transaction sent.")


def order_book_execute(order_id):
    c.execute("SELECT * FROM order_book where order_id=%s", [order_id])
    _, writer_id, stock_symbol, price, shares, buy_sell, _ = c.fetchall()[0]

    if buy_sell == "buy":
        c.execute("SELECT order_id, writer_id, price, shares FROM order_book where stock_symbol=%s "
                  "AND buy_sell='sell'  ORDER BY price", [stock_symbol])
        orders = c.fetchall()

        i = 0
        while shares > 0 and orders and orders[i] and price >= orders[i][2]:
            exchanged = min(orders[i][3], shares)
            shares -= exchanged
            transaction_cost = exchanged * orders[i][2]

            c.execute("SELECT cash FROM users WHERE id = %s", [writer_id])
            buyer_cash = c.fetchall()[0][0]
            buyer_cash -= transaction_cost
            c.execute("SELECT cash FROM users WHERE id = %s", [orders[i][1]])
            seller_cash = c.fetchall()[0][0]
            seller_cash += transaction_cost
            c.execute("UPDATE users SET cash = %s WHERE id = %s", [buyer_cash, writer_id])
            c.execute("UPDATE users SET cash = %s WHERE id = %s", [seller_cash, orders[i][1]])
            c.execute("UPDATE order_book SET shares = %s WHERE order_id = %s", [shares, order_id])
            c.execute("UPDATE order_book SET shares = %s WHERE order_id = %s",
                      [orders[i][3] - exchanged, orders[i][0]])
            c.execute("INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)"
                      "VALUES(%s, %s, %s, %s, %s)",
                      [writer_id, stock_symbol, orders[i][2], exchanged, time.strftime("%c")])
            c.execute("INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)"
                      "VALUES(%s, %s, %s, %s, %s)",
                      [orders[i][1], stock_symbol, orders[i][2], -exchanged, time.strftime("%c")])
            db.commit()
            i += 1

    elif buy_sell == "sell":
        c.execute("SELECT order_id, writer_id, price, shares FROM order_book where stock_symbol=%s "
                  "AND buy_sell='buy'  ORDER BY price DESC", [stock_symbol])
        orders = c.fetchall()

        i = 0
        while shares > 0 and orders and orders[i] and price <= orders[i][2]:
            exchanged = min(orders[i][3], shares)
            shares -= exchanged
            transaction_cost = exchanged * price

            c.execute("SELECT cash FROM users WHERE id = %s", [orders[i][1]])
            buyer_cash = c.fetchall()[0][0]
            buyer_cash -= transaction_cost
            c.execute("SELECT cash FROM users WHERE id = %s", [writer_id])
            seller_cash = c.fetchall()[0][0]
            seller_cash += transaction_cost
            c.execute("UPDATE users SET cash = %s WHERE id = %s", [buyer_cash, writer_id])
            c.execute("UPDATE users SET cash = %s WHERE id = %s", [seller_cash, orders[i][1]])
            c.execute("UPDATE order_book SET shares = %s WHERE order_id = %s", [shares, order_id])
            c.execute("UPDATE order_book SET shares = %s WHERE order_id = %s",
                      [orders[i][3] - exchanged, orders[i][0]])
            c.execute("INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)"
                      "VALUES(%s, %s, %s, %s, %s)",
                      [writer_id, stock_symbol, price, -exchanged, time.strftime("%c")])
            c.execute("INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)"
                      "VALUES(%s, %s, %s, %s, %s)",
                      [orders[i][1], stock_symbol, price, exchanged, time.strftime("%c")])
            db.commit()
            i += 1


def option_chain_execute(option_id):
    c.execute("SELECT * FROM option_chain where option_id=%s", [option_id])
    _, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, shares, transaction_date, \
    expiry_date, buy_sell = c.fetchall()[0]

    if buy_sell == "buy":
        c.execute("SELECT * FROM option_chain where stock_symbol=%s "
                  "AND buy_sell='sell' AND strike_price=%s AND option_type=%s AND expiry_date= %s "
                  "ORDER BY option_price", [stock_symbol, strike_price, option_type, expiry_date])
        orders = c.fetchall()

        i = 0
        while shares > 0 and orders and orders[i] and option_price >= orders[i][5]:
            exchanged = min(orders[i][7], shares)
            shares -= exchanged
            transaction_cost = exchanged * orders[i][5]

            c.execute("SELECT cash FROM users WHERE id = %s", [writer_id])
            buyer_cash = c.fetchall()[0][0]
            buyer_cash -= transaction_cost
            c.execute("SELECT cash FROM users WHERE id = %s", [orders[i][1]])
            seller_cash = c.fetchall()[0][0]
            seller_cash += transaction_cost
            c.execute("UPDATE users SET cash = %s WHERE id = %s", [buyer_cash, writer_id])
            c.execute("UPDATE users SET cash = %s WHERE id = %s", [seller_cash, orders[i][1]])

            c.execute("UPDATE option_chain SET shares = %s WHERE option_id = %s", [shares, option_id])
            c.execute("UPDATE option_chain SET shares = %s WHERE option_id = %s", [orders[i][7] - exchanged,
                                                                                   orders[i][0]])
            c.execute("INSERT INTO option_transaction VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Yes', %s)",
                      [option_id, orders[i][1], holder_id, stock_symbol, option_type, orders[i][5],
                       strike_price, exchanged, time.strftime("%c"), expiry_date])
            db.commit()
            i += 1

    elif buy_sell == "sell":
        c.execute("SELECT * FROM option_chain where stock_symbol=%s "
                  "AND buy_sell='buy' AND strike_price=%s AND option_type=%s AND expiry_date= %s "
                  "ORDER BY option_price", [stock_symbol, strike_price, option_type, expiry_date])
        orders = c.fetchall()

        i = 0
        while shares > 0 and orders and orders[i] and option_price <= orders[i][5]:
            exchanged = min(orders[i][7], shares)
            shares -= exchanged
            transaction_cost = exchanged * option_price

            c.execute("SELECT cash FROM users WHERE id = %s", [orders[i][1]])
            buyer_cash = c.fetchall()[0][0]
            buyer_cash -= transaction_cost
            c.execute("SELECT cash FROM users WHERE id = %s", [writer_id])
            seller_cash = c.fetchall()[0][0]
            seller_cash += transaction_cost
            c.execute("UPDATE users SET cash = %s WHERE id = %s", [buyer_cash, writer_id])
            c.execute("UPDATE users SET cash = %s WHERE id = %s", [seller_cash, orders[i][1]])
            c.execute("UPDATE option_chain SET shares = %s WHERE option_id = %s", [shares, option_id])
            c.execute("UPDATE option_chain SET shares = %s WHERE option_id = %s",
                      [orders[i][7] - exchanged, orders[i][0]])
            c.execute("INSERT INTO option_transaction VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Yes', %s)",
                      [option_id, writer_id, orders[i][1], stock_symbol, option_type, option_price, strike_price,
                       exchanged, time.strftime("%c"), expiry_date])
            db.commit()
            i += 1


if __name__ == "__main__":
    # app.run(debug=False)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

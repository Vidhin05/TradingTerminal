import base64
import io
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
        "SELECT option_id, stock_symbol, option_type, strike_price, num_of_shares , expiry_date FROM option_transaction"
        " WHERE writer_id=%s GROUP BY option_id, stock_symbol, option_type, strike_price, num_of_shares , expiry_date",
        [session["user_id"]])
    written_options = c.fetchall()

    c.execute(
        "SELECT option_id, stock_symbol, option_type, strike_price, num_of_shares , expiry_date, is_available"
        " FROM option_post WHERE writer_id=%s GROUP BY option_id", [session["user_id"]])
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
        plt.savefig(img, format='png')
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        c.execute("SELECT price, sum(shares), buy_sell FROM order_book where stock_symbol=%s "
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
        order_book_execute()
    else:
        return apology("ERROR", "INSUFFICIENT FUNDS")
    return redirect(url_for("quote", stock_symbol=stock_symbol))


@app.route("/sell/", methods=["POST"])
@login_required
def sell():
    """Sell shares of stock."""

    c.execute("SELECT username FROM users WHERE id = %s", [session["user_id"]])
    username = c.fetchall()[0][0]

    stock_symbol = request.args.get('stock_symbol', None)
    price = float(request.form.get("price"))
    c.execute("SELECT cash FROM users WHERE id = %s", [session["user_id"]])
    current_cash = c.fetchall()[0][0]
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
        db.commit()
        order_book_execute()
    else:
        return apology("ERROR", "You don't own that much!")
    return redirect(url_for("quote", stock_symbol=stock_symbol))


@app.route("/option_buy/", methods=["GET", "POST"])
@login_required
def option_buy():
    refresh()

    c.execute("SELECT username, cash FROM users WHERE id = %s", [session["user_id"]])
    username, current_cash = c.fetchall()[0]
    c.execute("SELECT * FROM option_post WHERE is_available='Yes'")
    options = c.fetchall()
    if request.method == "GET":
        c.execute("SELECT * FROM option_post where is_available='Yes'")
        transactions = c.fetchall()
        return render_template("option_buy.html", transactions=transactions, username=username)

    elif request.method == "POST":

        option_id = request.form.get("option_id")

        if not option_id:
            return apology("ERROR", "FORGOT OPTION ID")

        elif int(option_id) in [row[0] for row in options]:
            c.execute("SELECT * FROM option_post WHERE option_id = %s", [option_id])
            option = c.fetchall()[0]

            transaction_cost = option[5]
            if transaction_cost <= current_cash:
                current_cash -= transaction_cost
                c.execute("SELECT cash FROM users WHERE id = %s", [option[2]])
                seller_cash = c.fetchall()[0][0]
                seller_cash += transaction_cost

                c.execute("UPDATE users SET cash = %s WHERE id = %s", [current_cash, session["user_id"]])
                c.execute("UPDATE users SET cash = %s WHERE id = %s", [seller_cash, option[2]])

                c.execute(
                    "INSERT INTO option_transaction VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Yes', %s)",
                    [option[:8], time.strftime("%c"), option[-1]])

                c.execute("DELETE FROM option_post WHERE option_id=%s", [option_id])
                db.commit()
                print("Transaction sent.")
            else:
                return apology("ERROR", "INSUFFICIENT FUNDS")
            return redirect(url_for("index"))
        else:
            return apology("ERROR", "No such option")


@app.route("/option_sell/", methods=["GET", "POST"])
@login_required
def option_sell():
    refresh()

    c.execute("SELECT username FROM users WHERE id = %s", [session["user_id"]])
    username = c.fetchall()[0][0]
    c.execute("SELECT * FROM option_transaction WHERE holder_id=%s AND is_available='Yes'",
              [session["user_id"]])
    transactions = c.fetchall()
    if request.method == "GET":
        return render_template("option_sell.html", transactions=transactions, username=username)

    elif request.method == "POST":

        option_id = request.form.get("option_id")
        stock_symbol = request.form.get("stock_symbol")
        option_price = request.form.get("option_price")

        if not option_id:
            strike_price = request.form.get("strike_price")
            option_type = request.form.get("option_type")
            num_of_shares = request.form.get("num_of_shares")
            expiry = int(request.form.get("days_to_expiry"))
            expiry_date = datetime.fromtimestamp(time.time() + expiry * 86400).strftime('%c')
            c.execute(
                "INSERT INTO option_post(writer_id, holder_id, stock_symbol, option_type, option_price, strike_price,"
                " num_of_shares, transaction_date,is_available,expiry_date) "
                "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [session["user_id"], session["user_id"], stock_symbol, option_type, option_price, strike_price,
                 num_of_shares,
                 time.strftime("%c"), 'Yes', expiry_date])
            db.commit()

        elif int(option_id) in [row[0] for row in transactions]:
            writer_id, holder_id, stock_symbol, option_type, strike_price, num_of_shares, expiry_date = \
                c.execute(
                    "SELECT writer_id, holder_id, stock_symbol, option_type, strike_price, num_of_shares, expiry_date"
                    "FROM option_transaction WHERE option_id = %s", [option_id]).fetchall()[0]

            c.execute("UPDATE option_transaction SET is_available = %s WHERE holder_id = %s and option_id = %s",
                      ["No", holder_id, option_id])
            c.execute(
                "INSERT INTO option_post VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [option_id, writer_id, session["user_id"], stock_symbol, option_type, option_price, strike_price,
                 num_of_shares, time.strftime("%c"), 'Yes', expiry_date])
            db.commit()
            print("Transaction sent.")
        else:
            return apology("ERROR", "No such option")

        return redirect(url_for("index"))


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
        c.execute("SELECT * FROM option_post WHERE is_available='Yes'")
        available_options = c.fetchall()
        for option in available_options:
            if current_time > datetime.strptime(option[10], '%c').timestamp():
                try:
                    c.execute("SELECT * FROM option_transaction WHERE option_id = %s", [option[0]])
                    current_option = c.fetchall()[-1]
                    c.execute("UPDATE option_post SET is_available='No' WHERE option_id=%s", [option[0]])
                    c.execute(
                        "UPDATE option_transaction SET is_available='Yes' "
                        "WHERE option_id=%s AND holder_id=%s AND transaction_date=%s",
                        [current_option[0], current_option[2], current_option[8]])
                    db.commit()
                except IndexError:
                    c.execute("UPDATE option_post SET is_available='No' WHERE option_id=%s", [option[0]])
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
                        c.execute("UPDATE option_transaction SET is_available='No' WHERE option_id = %s ", [option[0]])
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


def order_book_execute():
    return 0


# buy
#     transaction_cost = stock_info["price"] * stock_quantity
#     if transaction_cost <= current_cash:
#         current_cash -= transaction_cost
#         c.execute("UPDATE users SET cash = %s WHERE id = %s", [current_cash, session["user_id"]])
#         c.execute("INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)"
#                   "VALUES(%s, %s, %s, %s, %s)",
#                   [session["user_id"], stock_info["symbol"], stock_info["price"], stock_quantity, time.strftime("%c")])
#         db.commit()
#         print("Transaction sent.")
#
# sell
#         if stock_quantity <= stock_available[0][0]:
#             print("transaction possible")
#             stock_info = lookup(stock_symbol)
#             if not stock_info:
#                 return apology("ERROR", "INVALID STOCK")
#             current_cash += stock_info["price"] * stock_quantity
#             c.execute("UPDATE users SET cash = %s WHERE id = %s", [current_cash, session["user_id"]])
#             c.execute(
#                 "INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)"
#                 "VALUES(%s, %s, %s, %s, %s)",
#                 [session["user_id"], stock_info["symbol"], stock_info["price"], 0 - stock_quantity, time.strftime("%c")])
#             db.commit()
#             print("Transaction sent.")
#         else:
#             return apology("ERROR", "You don't own that much!")


if __name__ == "__main__":
    # app.run(debug=False)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

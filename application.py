import base64
import io
import sqlite3
import time
from tempfile import gettempdir
import time
import matplotlib.pyplot as plt
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

# connect sqlite3 with database
file = "finance.db"
db = sqlite3.connect(file, check_same_thread=False)
c = db.cursor()


@app.route("/")
@login_required
def index():
    current_user = session["user_id"]
    username, current_cash = c.execute("SELECT username, cash FROM users WHERE id = ?", [current_user]).fetchall()[0]
    cash_update()

    available = c.execute("SELECT symbol, sum(quantity) FROM transactions WHERE user_id = ? GROUP BY symbol",
                          [current_user]).fetchall()
    written_options = c.execute(
        "SELECT option_id, option_type, strike_price, num_of_shares, stock_symbol FROM option_transaction"
        " WHERE writer_id=? GROUP BY option_id", [current_user]).fetchall()
    unsold_options = c.execute(
        "SELECT option_id, option_type, strike_price, num_of_shares, stock_symbol FROM option_post WHERE writer_id=?"
        " GROUP BY option_id",
        [current_user]).fetchall()
    available_options = c.execute("SELECT * FROM option_transaction WHERE holder_id=? AND is_available='Yes'",
                                  [current_user]).fetchall()
    stocks_value = 0
    for stock in available:
        stocks_value += (stock[1] * lookup(stock[0])["price"])
    c.execute("UPDATE users SET assets = ? WHERE id = ?", [stocks_value, current_user])
    db.commit()
    return render_template("index.html", username=username, current_cash=current_cash, available=available,
                           lookup=lookup, usd=usd, stocks_value=stocks_value, available_options=available_options,
                           written_options=written_options, unsold_options=unsold_options)


@app.route("/buy/", methods=["GET", "POST"])
@login_required
def buy():
    current_user = session["user_id"]
    current_cash = c.execute("SELECT cash FROM users WHERE id = ?", [current_user]).fetchall()[0][0]
    """Buy shares of stock."""
    if request.method == "GET":
        return render_template("buy.html", current_cash=usd(current_cash))
    elif request.method == "POST":

        stock_symbol = request.form.get("stock-symbol")
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
        transaction_cost = stock_info["price"] * stock_quantity
        if transaction_cost <= current_cash:
            current_cash -= transaction_cost
            c.execute("UPDATE users SET cash = ? WHERE id = ?", [current_cash, current_user])
            c.execute(
                "INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)VALUES(?, ?, ?, ?, ?)",
                [current_user, stock_info["symbol"], stock_info["price"], stock_quantity, time.strftime("%c")])
            db.commit()
            print("Transaction sent.")
        else:
            return apology("ERROR", "INSUFFICIENT FUNDS")
        return redirect(url_for("index"))


@app.route("/history/")
@login_required
def history():
    """Show history of transactions."""
    current_user = session["user_id"]
    transactions = c.execute("SELECT * FROM transactions WHERE user_id = ?", [current_user]).fetchall()
    option_transactions = c.execute("SELECT * FROM option_transaction WHERE holder_id = ?", [current_user]).fetchall()
    return render_template("history.html", transactions=transactions, option_transactions=option_transactions,
                           lookup=lookup, usd=usd)


# test

@app.route("/leaderboard/")
@login_required
def leaderboard():
    cash_update()

    leaders = c.execute("SELECT username, cash, assets FROM users ORDER BY cash + assets DESC").fetchall()
    return render_template("leaderboard.html", leaders=leaders, usd=usd)


@app.route("/login/", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
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
        c.execute("SELECT * FROM users WHERE username = ?", [request.form.get("username")])
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


@app.route("/quote/", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    elif request.method == "POST":
        if not request.form.get("stock-symbol"):
            return apology("Error", "Forgot to enter a stock")
        stock = lookup(request.form.get("stock-symbol"))
        df = stock_hist(stock['symbol'])

        style.use('ggplot')
        img = io.BytesIO()
        df['Close'].plot()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(img, format='png')
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        if not stock:
            return apology("ERROR", "INVALID STOCK")
        return render_template("quoted.html", stock=stock, url='data:image/png;base64,{}'.format(graph_url))


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
                c.execute("INSERT INTO users(username, hash) VALUES(?, ?)", [username, hashed])
                db.commit()

                # immediately log user in
                session["user_id"] = c.execute("SELECT * FROM users WHERE username = ?", [username]).fetchall()[0][0]

                # send user to index
                return redirect(url_for("index"))

            # if username is not unique alert user
            except sqlite3.IntegrityError:
                return apology("Error", "Username taken")
        else:
            return apology("Passwords don't match")


@app.route("/sell/", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method == "GET":
        available = c.execute("SELECT symbol, sum(quantity) FROM transactions WHERE user_id = ? GROUP BY symbol",
                              [session["user_id"]]).fetchall()
        return render_template("sell.html", available=available)
    elif request.method == "POST":

        current_user = session["user_id"]
        stock_symbol = request.form.get("stock-symbol")
        current_cash = c.execute("SELECT cash FROM users WHERE id = ?", [current_user]).fetchall()[0][0]
        stock_available = c.execute("SELECT sum(quantity) FROM transactions WHERE user_id = ? AND symbol = ?",
                                    [current_user, stock_symbol]).fetchall()
        try:
            stock_quantity = int(request.form.get("stock-quantity"))
        except ValueError:
            return apology("ERROR", "ENTER QUANTITY IN WHOLE NUMBERS ONLY")

        if not stock_symbol:
            return apology("ERROR", "Missing stock symbol")
        if not stock_available[0][0]:
            return apology("ERROR", "You don't own this security")

        if stock_quantity <= stock_available[0][0]:
            print("transaction possible")
            stock_info = lookup(stock_symbol)
            if not stock_info:
                return apology("ERROR", "INVALID STOCK")
            current_cash += stock_info["price"] * stock_quantity
            c.execute("UPDATE users SET cash = ? WHERE id = ?", [current_cash, current_user])
            c.execute(
                "INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)VALUES(?, ?, ?, ?, ?)",
                [current_user, stock_info["symbol"], stock_info["price"], 0 - stock_quantity, time.strftime("%c")])
            db.commit()
            print("Transaction sent.")
        else:
            return apology("ERROR", "You don't own that much!")
        return redirect(url_for("index"))


@app.route("/option_buy/", methods=["GET", "POST"])
@login_required
def option_buy():
    current_user = session["user_id"]
    current_cash = c.execute("SELECT cash FROM users WHERE id = ?", [current_user]).fetchall()[0][0]
    if request.method == "GET":
        transactions = c.execute("SELECT * FROM option_post").fetchall()
        return render_template("option_buy.html", transactions=transactions)

    elif request.method == "POST":

        option_id = request.form.get("option_id")

        if not option_id:
            return apology("ERROR", "FORGOT OPTION ID")

        option_id, writer_id, holder_id, stock_symbol, option_type, option_price, strike_price, num_of_shares, \
        option_time = c.execute("SELECT * FROM option_post WHERE option_id = ?", [option_id]).fetchall()[0]

        transaction_cost = option_price
        if transaction_cost <= current_cash:
            current_cash -= transaction_cost
            seller_cash = c.execute("SELECT cash FROM users WHERE id = ?", [holder_id]).fetchall()[0][0]
            seller_cash += transaction_cost

            c.execute("UPDATE users SET cash = ? WHERE id = ?", [current_cash, current_user])
            c.execute("UPDATE users SET cash = ? WHERE id = ?", [seller_cash, holder_id])

            c.execute(
                "INSERT INTO option_transaction VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 'Yes')",
                [option_id, writer_id, current_user, stock_symbol, option_type, option_price, strike_price,
                 num_of_shares, time.strftime("%c")])

            c.execute("DELETE FROM option_post WHERE option_id=?", [option_id])
            db.commit()
            print("Transaction sent.")
        else:
            return apology("ERROR", "INSUFFICIENT FUNDS")
        return redirect(url_for("index"))


@app.route("/option_sell/", methods=["GET", "POST"])
@login_required
def option_sell():
    current_user = session["user_id"]
    transactions = c.execute("SELECT * FROM option_transaction WHERE holder_id=? AND is_available='Yes'",
                             [current_user]).fetchall()
    if request.method == "GET":
        return render_template("option_sell.html", transactions=transactions)

    elif request.method == "POST":

        option_id = request.form.get("option_id")
        stock_symbol = request.form.get("stock_symbol")
        option_price = request.form.get("option_price")

        if not option_id:
            strike_price = request.form.get("strike_price")
            option_type = request.form.get("option_type")
            num_of_shares = request.form.get("num_of_shares")
            c.execute(
                "INSERT INTO option_post(writer_id, holder_id, stock_symbol, option_type, option_price, strike_price,"
                " num_of_shares, transaction_date) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                [current_user, current_user, stock_symbol, option_type, option_price, strike_price, num_of_shares,
                 time.strftime("%c")])
            db.commit()
            print("Transaction sent.")

        elif int(option_id) in [row[0] for row in transactions]:
            writer_id, holder_id, stock_symbol, option_type, strike_price, num_of_shares, is_available = c.execute(
                "SELECT writer_id, holder_id, stock_symbol, option_type, strike_price, num_of_shares, is_available "
                "FROM option_transaction WHERE option_id = ?", [option_id]).fetchall()[0]

            c.execute("UPDATE option_transaction SET is_available = ? WHERE holder_id = ? and option_id = ?",
                      ["No", holder_id, option_id])
            c.execute(
                "INSERT INTO option_post VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [option_id, writer_id, current_user, stock_symbol, option_type, option_price, strike_price,
                 num_of_shares, time.strftime("%c")])
            db.commit()
            print("Transaction sent.")
        else:
            return apology("ERROR", "No such option")

        return redirect(url_for("index"))


def cash_update():
    users, last_update_time, current_cash = c.execute("SELECT ID, start_time, cash FROM users").fetchall()
    current_time = time.time()
    time_elapsed = current_time - last_update_time[0]
    if time_elapsed > 300:
        for i in range(len(users)):
            current_cash[i] *= pow(e, 0.1 * (time_elapsed / 31557600))
            c.execute("UPDATE cash SET cash = ? WHERE id = ?", [current_cash[i], users[i]])
        db.commit()


if __name__ == "__main__":
    app.run(debug=False)

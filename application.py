import sqlite3
import re
import time

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.hash import sha256_crypt
from tempfile import gettempdir
import pandas as pd
import matplotlib.pyplot as plt
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
    current_cash = c.execute("SELECT cash FROM users WHERE id = :CURRENT_USER", [current_user]).fetchall()[0][0]
    available = c.execute("SELECT symbol, sum(quantity) FROM transactions WHERE user_id = :user_id GROUP BY symbol",
                          [session["user_id"]]).fetchall()
    stocks_value = 0
    for stock in available:
        stocks_value += (stock[1] * lookup(stock[0])["price"])
    c.execute("UPDATE users SET assets = :assets WHERE id = :user_id", [stocks_value, current_user])
    db.commit()
    return render_template("index.html", current_cash=current_cash, available=available, lookup=lookup, usd=usd, stocks_value=stocks_value)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    current_user = session["user_id"]
    current_cash = c.execute("SELECT cash FROM users WHERE id = :CURRENT_USER", [current_user]).fetchall()[0][0]
    """Buy shares of stock."""
    if request.method == "GET":
        return render_template("buy.html", current_cash=usd(current_cash))
    elif request.method == "POST":
        now = time.strftime("%c")
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
            c.execute("UPDATE users SET cash = :cash WHERE id = :id", [current_cash, current_user])
            c.execute("INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)"
                      "VALUES(:user_id, :symbol, :price, :quantity, :transaction_date)",
                      [current_user, stock_info["symbol"], stock_info["price"], stock_quantity, now])
            db.commit()
            print("Transaction sent.")
        else:
            return apology("ERROR", "INSUFFICIENT FUNDS")
        return redirect(url_for("index"))

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    current_user = session["user_id"]
    transactions = c.execute("SELECT * FROM transactions WHERE user_id = :user_id", [current_user]).fetchall()
    return render_template("history.html", transactions=transactions, lookup=lookup, usd=usd)
#test

@app.route("/leaderboard")
@login_required
def leaderboard():
    leaders = c.execute("SELECT username, cash, assets FROM users ORDER BY cash + assets DESC").fetchall()
    return render_template("leaderboard.html", leaders=leaders, usd=usd)

@app.route("/login", methods=["GET", "POST"])
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
        c.execute("SELECT * FROM users WHERE username = :username", [request.form.get("username").lower()])
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

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    elif request.method == "POST":

        ## here we can display our local GBM simulation
        df = pd.read_csv('TCS.NS.csv')

        plt.plot(df['Date'],df['Adj Close'])
        fig.savefig('stock_plot.png')
        return render_template("quoted.html", stock=stock)

@app.route("/register", methods=["GET", "POST"])
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
            return apology("Error","Forgot Username")
        elif not request.form.get("password"):
            return apology("Error", "Forgot Password")
        elif not request.form.get("password-confirm"):
            return apology("Error", "Forgot Confirmation")

        # if passwords match
        if password == password_confirm:
            # encrypt password
            hashed = sha256_crypt.encrypt(password)
            username = re.sub(r'\W+', '', username.lower())
            try:
                # send user details to database
                c.execute("INSERT INTO users(username, hash) VALUES(:username, :hash)", [username, hashed])
                db.commit()

                # immediately log user in
                session["user_id"] = c.execute("SELECT * FROM users WHERE username = :username", [username]).fetchall()[0][0]

                # send user to index
                return redirect(url_for("index"))

            # if username is not unique alert user
            except sqlite3.IntegrityError:
                return apology("Error", "Username taken")
        else:
            return apology("Passwords don't match")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method == "GET":
        available = c.execute("SELECT symbol, sum(quantity) FROM transactions WHERE user_id = :user_id GROUP BY symbol", [session["user_id"]]).fetchall()
        return render_template("sell.html")
    elif request.method == "POST":
        now = time.strftime("%c")
        current_user = session["user_id"]
        stock_symbol = request.form.get("stock-symbol")
        current_cash = c.execute("SELECT cash FROM users WHERE id = :CURRENT_USER", [current_user]).fetchall()[0][0]
        stock_available = c.execute(
            "SELECT sum(quantity) FROM transactions WHERE user_id = :user_id AND symbol = :symbol",
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
            c.execute("UPDATE users SET cash = :cash WHERE id = :id", [current_cash, current_user])
            c.execute("INSERT INTO transactions(user_id, symbol, price, quantity, transaction_date)"
                      "VALUES(:user_id, :symbol, :price, :quantity, :transaction_date)",
                      [current_user, stock_info["symbol"], stock_info["price"], 0 - stock_quantity, now])
            db.commit()
            print("Transaction sent.")
        else:
            return apology("ERROR", "You don't own that much!")
        return redirect(url_for("index"))

@app.route("/options", methods=["GET", "POST"])
@login_required
def options():
    if request.method == "GET":
        return apology("Error", "Under Maintainence")
        #return render_template("options.html")
    elif request.method == "POST":
        return apology("Error", "Under Maintainence")


if __name__ == "__main__":
    app.run(debug=False)
import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



@app.route("/", methods = ["GET", "POST"])
@login_required
def index():
    if "useeerrr" not in session:
        return render_template("login.html")
    
    
    """Show portfolio of stocks"""

    id = session["useeerrr"]
    db = sqlite3.connect("finance.db")
    cur = db.cursor()

    #portfolio  = cur.execute("SELECT username_id, quotation, symbol, SUM(shares), SUM(total)  FROM transactions WHERE username_id = ? GROUP BY symbol", (id,))
    
    portfolio  = cur.execute("SELECT symbol, SUM(shares), SUM(total) FROM transactions WHERE username_id = ? GROUP BY symbol HAVING SUM(shares) > 0", (id,))
    #portfolio = list(portfolio) # put to a list to enable for within the html tempalte
 
    pershare_dict = {}
    
    shares_by_symbol = []
    portfolio_total = 0
    STOCK = []
    for row in portfolio:
            STOCK.append(row[0])  # acceptable stocks for validation
            pershare_dict = lookup(row[0])
            pershare = pershare_dict["price"]
            total_value = row[1]*pershare
            print(f"the total value per stock is : {total_value}")
            portfolio_total +=  total_value
            print(f"{row} running stock value total is {portfolio_total}")
            shares_by_symbol.append({"symbol" : row[0], "sum_shares" : row[1], "price_per_share" : pershare, "total_value": total_value})
            
    print(f"the total value of all stock is {portfolio_total}")

    
    users = cur.execute("SELECT *  FROM users WHERE id = ? ", (id,)).fetchone() #fetchone so can pass data to html without a for loop, and it is a tuple.
    
    if users is not None:
        grand_total = users[3] + portfolio_total

    else:
        grand_total = portfolio_total

    if request.method == "POST":

        stocks_buy = request.form.get("stock_buy") #this will get the value of that is inputted.
        stock_symbol= request.form.get("stock_symbol") #this will get the second value from the submitted form for the symbol
        print(stocks_buy)
        print(stock_symbol)

        if not stocks_buy or not stock_symbol: # the inputs need to be satisfied (for validation purpose)
            return apology("no stock bought")
        
        try:
            if stock_symbol not in STOCK:
                return apology("Visit 'buy' for purchasing other stock")
            
            if int(stocks_buy) <= 0:
                return apology("Please input valid value of stock")
            
            else:
                stock_symbol_dict = lookup(stock_symbol)  #this will get the second value from the submitted form for the symbol
                print(stock_symbol_dict) #this prints out a dictionary
                stock_buy_price = stock_symbol_dict["price"] 
                print(stock_buy_price)
                
                total_price = int(stocks_buy) * stock_buy_price

                print(f"The number of shares you are buying is: {stocks_buy}")
                print(f"the user id is: {session['useeerrr']}" )
                
                username = users[1]
                print(f"The username of the person buying the shares is : {username}")
                cash = users[3]
                print(users)
                print(f"the cash in the bank is {cash}")

                if cash >= total_price:
                    print("you have enough bank")
                    try:
                        cash = float(cash - total_price)
                        cur.execute("UPDATE users SET cash = ? WHERE id = ? ", (cash, id))
                        print(f"The remaining cash is {cash}")
                        cur.execute("INSERT INTO transactions (username_id, symbol, quotation, shares, total) VALUES (?,?,?,?,?)", (id, stock_symbol, stock_buy_price, stocks_buy,total_price))
                        db.commit()
                        db.close()
                        return redirect ("/")
                    except sqlite3.Error as e:
                        print("SQLite error:", e)      
                else:
                    return apology("YOU TOO POOR!")

        except (ValueError, TypeError):
            return apology("Please input valid value of stock")
   
    else:
        return render_template("index.html" , portfolio = shares_by_symbol, users = users, portfolio_total = portfolio_total, grand_total = grand_total)
    

@app.route("/password", methods=["GET", "POST"])
@login_required

def change_password():
    
    id = session["useeerrr"]
    password_check = request.form.get("old_password")
    new_password = request.form.get("new_password")
    new_password_validation = request.form.get("new_password_validation")

    if request.method == "POST":
        
        if not password_check or not new_password or not new_password_validation:
            return apology("All inputs need to be filled")
        
        db = sqlite3.connect("finance.db")
        cur = db.cursor()
        rows = cur.execute("SELECT * FROM users WHERE id = ? ", (id,))
    
        hash = None

        for row in rows:
            hash = row[2]
        
        print(hash)

        if check_password_hash(hash,password_check) == True:
            
            if new_password == new_password_validation:
                hash = generate_password_hash(new_password)
                cur.execute("UPDATE users SET hash = ? WHERE id = ?" , (hash , id)) #getting the relevant rows for the user who wants to change their password
                db.commit()
                return render_template("password_updated.html")
            else:
                return apology("passwords do not match")
        else:
            return apology("Error in old password")
    else:
        return render_template("password.html")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if symbol:
            
            try:
                quotation = lookup(symbol)
                quotation_price = quotation["price"]
                
                if shares:
                    try:
                        total_cost= quotation_price * int(shares)

                        if int(shares) > 0:

                            print(f"The number of shares you are buying is: {shares}")
                            #username= request.form.get("username") # error here as username has to be taken from the form.
                            print(f"the user id is: {session['useeerrr']}" )
                            id=session["useeerrr"]
                            db  = sqlite3.connect("finance.db")
                            cur = db.cursor()
                            rows = cur.execute("SELECT * FROM users where id = ?", (id,))
                            
                            for row in rows:
                                username = row[1]
                                print(f"The username of the person buying the shares is : {username}")
                                cash = row[3]
                                print(row)
                                print(f"the cash in the bank is {cash}")
                                if cash >= total_cost:
                                    print("you have enough bank")
                                    try:
                                        cash = float(cash - total_cost)
                                        cur.execute("UPDATE users SET cash = ? WHERE id = ? ", (cash, id))
                                        print(f"The remaining cash is {cash}")
                                        cur.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, username_id INTEGER NOT NULL, symbol TEXT NOT NULL, quotation NUMERIC NOT NULL, shares INTEGER NOT NULL, total NUMERIC NOT NULL)")
                                        cur.execute("INSERT INTO transactions (username_id, symbol, quotation, shares, total) VALUES (?,?,?,?,?)", (id, symbol, quotation_price, shares,total_cost))
                                        db.commit()
                                        db.close()
                                        return redirect ("/")
                                    except sqlite3.Error as e:
                                        print("SQLite error:", e)      
                                else:
                                    return apology("YOU TOO POOR!")
                        else:
                            print("negative>>>!>>!>>!>!>>!")
                            return apology("Please input valid number of shares")
                        
                    except ValueError:
                        print("Value Error")
                        return apology("Please input valid number of shares")
                
                else:
                    print("no shares")
                    return apology("Please input valid number of shares")
            except TypeError:
                print("Type Error")
                return apology("Symbol does not exist")
        else:
            return apology("Please input symbol")
    else:
        
        return render_template("buy.html")



@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    db = sqlite3.connect("finance.db")
    cur = db.cursor()
    useeerrr = session["useeerrr"]
    users = cur.execute("SELECT username FROM users WHERE id = ?", (useeerrr,)).fetchone()

    transactions = cur.execute("SELECT * FROM transactions WHERE username_id = ? ", (useeerrr,))
    
    return render_template("history.html", users = users, transactions = transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any useeerrr
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username

        # Configure to use SQLite3 database
        db = sqlite3.connect("finance.db")

        cur = db.cursor()  
        
        username= request.form.get("username")
        print(username)
        
        rows = cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        print(rows)
        # Ensure username exists and password is correct
        
        existing_username = [] # validation of the current usernames
        print(existing_username)
        print(len(existing_username))
        
        hash= None
        
        for row in rows:
            id = row[0]
            username = row[1]
            hash = row[2]
            existing_username.append({"id" : id, "username" : username, "hash": hash })
            for item in existing_username:
                hash = item["hash"]
                print(hash)
            break
        
        print(len(existing_username))
        print(existing_username)
        
        
        print(hash)

        if len(existing_username) != 1 or not check_password_hash(hash, request.form.get("password")): #(hashed_password, password_input)
            
            print(type(request.form.get("password")))
            print(request.form.get("password"))

            return apology("invalid username and/or password", 403)
        
            
        session["useeerrr"] = row[0] # Remember which user has logged in
        
        #if check_password_hash(rows[0]["hash"], (request.form.get("password"))):
        #    return apology("invalid username and/or password", 403)

        # Redirect user to home page
        
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any useeerrr
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        symbol = request.form.get("symbol")
        if symbol:
            try:
                quotation = lookup(symbol)
                quotation_price = usd(quotation["price"]) 
                print(quotation_price)
                return render_template("quoted.html", symbol = symbol, quotation = quotation_price)
            except ( ValueError, KeyError, IndexError, TypeError):
                return apology("Please check symbol")
        else:
            return redirect("/quote")
    
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # get the username from the user
        username = request.form.get("username")
        password= request.form.get("password")
        password_validation = request.form.get("password_validation")
        
        try:
            if username and password:
                if password == password_validation:
                    password = generate_password_hash(password)
                    db = sqlite3.connect("finance.db")
                    cur = db.cursor()
                    cur. execute("INSERT INTO users (username, hash) VALUES (? , ?) ", (username, password))
                    db.commit()
                    rows = cur.execute("SELECT * FROM users")
                    for row in rows:
                        print(row)
                    db.close()
                    return render_template("login.html")
                
                else:
                    return apology("Passwords must match", 403)
        
            else:
                return apology("Username and password fields must be filled", 403)

        except sqlite3.IntegrityError:
            return apology("User name has been used, please choose another", 403)

    else:
        return render_template("register.html") 
    
    

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
   
    #put into the options as part of the selections
    
    # database query within the "/" 

    id = session["useeerrr"]
    db = sqlite3.connect("finance.db")
    cur = db.cursor()

    portfolio  = cur.execute("SELECT symbol, SUM(shares), SUM(total) FROM transactions WHERE username_id = ? GROUP BY symbol HAVING SUM(shares) > 0", (id,))

    shares_by_symbol = []
    pershare_dict = {}
    STOCK = []
    portfolio_total = 0

    for row in portfolio: 
        STOCK.append(row[0])         # put the list of stocks into a list to validate against
        max_shares= row[1]
        pershare_dict = lookup(row[0])
        print(pershare_dict)
        pershare = pershare_dict["price"]
        print(f"value of the stock is {pershare}")
        total_value = max_shares*pershare
        print(f"the total value per stock is : {total_value}")
        portfolio_total +=  total_value
        print(f"{row} running stock value total is {portfolio_total}")
        shares_by_symbol.append({"symbol" : row[0], "sum_shares" : max_shares, "price_per_share" : pershare, "total_value": total_value})
        #shares_sell = range(1, max_shares+1)

        #print(shares_sell)
        #for stock in shares_sell:
        #   print(stock)
        
    print(shares_by_symbol)

    print(f"the total value of all stock is {portfolio_total}")

    users = cur.execute("SELECT *  FROM users WHERE id = ? ", (id,)).fetchone() #fetchone so can pass data to html without a for loop, and it is a tuple.

    grand_total = users[3] + portfolio_total

    #POST
    if request.method == "POST":
        
        selected_stock_sell = request.form.get("stock_sell_option")
        print(type(selected_stock_sell))



        # put the range numbers into a list to validate against
        # can we choose the max number per row and make it into a dictionary? How do i fetch that ?? 
        
        if selected_stock_sell:
            
            try: 
                values = selected_stock_sell.split("|") #this is a list indicating the stock and alo the number of shares
                symbol_sell = values[0]

                if symbol_sell not in STOCK:         # validation that the stock exists in the users portfolio
                    return apology("you do not own that stock!")
                else:
                    print(type(selected_stock_sell))
                    stock_sell = int(values[1])
                    
                    # validation regarding the number that can be sold

                    for item in shares_by_symbol:
                        if item["symbol"] == symbol_sell:
                            MAX_SHARES = item["sum_shares"]
                            break
                    
                    if stock_sell > MAX_SHARES:
                        return apology("you do not own that much stock!")
                     
                    elif stock_sell > 0:
                        print(type(stock_sell))
                        negative_stock_sell = -1 * stock_sell
                        print(f"symbol: {symbol_sell} stock: {negative_stock_sell}")
                        to_sell_dict= lookup(symbol_sell)
                        sell_price = to_sell_dict["price"]
                        print(sell_price)
                        value_sold_stock = float(stock_sell)*sell_price
                        print(f"the value of the sold stock is: {value_sold_stock}")
                        balance_cash = users[3] + value_sold_stock
                        portfolio_total_after_sold = portfolio_total - value_sold_stock
                        print(f"the balance of cash is now: {balance_cash}")
                        print(f"the total value of stocks is now: {portfolio_total_after_sold}")

                        cur.execute("INSERT INTO transactions (username_id, symbol, quotation, shares, total) VALUES (?,?,?,?,?)", (id, symbol_sell, sell_price, negative_stock_sell,value_sold_stock))
                        cur.execute("UPDATE users SET cash = ? WHERE id = ? ", (balance_cash, id))
                        
                        db.commit()

                        return redirect("/")
                    
                    else:
                        return apology("No stock selected")
                
            except (ValueError, TypeError):
                return apology("No stock selected")
        else:
            return apology("No stock selected")
        
    #GET
    else:

        return render_template("sell.html", portfolio = shares_by_symbol, users = users, portfolio_total = portfolio_total, grand_total = grand_total)    




    

if __name__ == '__main__':
    
    port = 8080
    app.run(port = port)
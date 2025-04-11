from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from fhict_cb_01.custom_telemetrix import CustomTelemetrix
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import Nullable
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from datetime import datetime, timedelta
import random, time, sys, threading, csv
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, UserMixin, login_required, login_user
from flask_bcrypt import Bcrypt




# ------------------------------------------------------------------------------------------------------------------------------------------
# Start Sequence & shared variables
# ------------------------------------------------------------------------------------------------------------------------------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SECRET_KEY'] = 'ENTER YOUR SECRET KEY'
db = SQLAlchemy()
login_manager = LoginManager(app)
bcrypt = Bcrypt()
arduinoIsAlive = False
cooldownLuigiButton = False
notificationOven = [0, 1, False]
uniqueCartItemNumber = 0 
uniqueOrderNumber = 0
temporaryMarioCart = []
temporaryCustomerCart = []
baking_orders = [] # Luigi
orderOven = []
indexCartItemOven = 0
indexOven = 0
ordersHistoric = []

Item_ID = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 300, 301, 302, 303, 304, 305, 306]
pizza_name = ["Margherita", "Pepperoni", "4 Cheeses", "Calzone", "Tuna", "Prosciutto", "4 Stagioni", "BBQ Chicken", "Caprese", "Funghi", "Meat Lovers", "New York", "Spinach", "Spicy"] # 14 pizzas
pizza_timer = [11, 14, 24, 23, 24, 27, 15, 27, 24, 20, 27, 23, 16, 23]
pizza_price = [11, 14, 12, 14, 16, 13, 16, 15, 15, 15, 13, 11, 16, 15]
drink_name = ["San Pellegrino", "Acqua Panna", "Prosecco", "House Red", "House White", "Birra Moretti", "Cola", "Fanta", "Sprite", "Limoncello"] # 10 drinks
drink_price = [3, 3, 10, 9, 9, 8, 3, 3, 3, 9]
dessert_name = ["Tiramisu", "The Colonel", "Chocolate Mousse", "Cannoli", "Panna Cotta", "Affogato", "Gelato"] # 7 desserts
dessert_price = [9, 7, 6, 7, 7, 5, 5]



# ------------------------------------------------------------------------------------------------------------------------------------------
# Database
# ------------------------------------------------------------------------------------------------------------------------------------------
@login_manager.user_loader 
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
   id = db.Column(db.Integer, primary_key=True)
   username = db.Column(db.String(20), unique=True, nullable=False)
   email = db.Column(db.String(120), unique=True, nullable=False)
   password = db.Column(db.String(60), nullable=False)
   pfp_file = db.Column(db.String(20), nullable=False, default='default.jpg')

   def __repr__(self):
      return f"User('{self.username}', '{self.email}', '{self.pfp_file}')"
   
   
class Pizza(db.Model):
    Item_ID = db.Column(db.Integer, primary_key = True)
    Price = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
      return f"User('{self.Item_ID}', '{self.Price}', '{self.date_posted}')"


    
    
db.init_app(app)
with app.app_context():
    db.create_all()





class RegistrationForm(FlaskForm):
   username = StringField('Username', 
                          validators=[DataRequired(), Length(min=2, max=20)])
   email = StringField('Email',
                       validators= [DataRequired(), Email()])
   password = PasswordField('Password',
                             validators=[DataRequired(), Length(min=5)])
   confirm_password = PasswordField('Confirm Password',
                                    validators= [DataRequired(), EqualTo(password)])
   submit = SubmitField('Sign up')

   def validate_username(self, username):
       user = User.query.filter_by(username=username.data).first()
       if user:
           raise ValidationError('That username already exists')
       
   def validate_email(self, email):
       user = User.query.filter_by(email=email.data).first()
       if user:
           raise ValidationError('That email is already taken.')

class LoginForm(FlaskForm):
   email = StringField('Email',
                       validators=[DataRequired(), Email()])
   password = PasswordField('Password', validators=[DataRequired()])
   remember = BooleanField('Remember Me')
   submit = SubmitField('Login')   



# ------------------------------------------------------------------------------------------------------------------------------------------
# Arduino
# ------------------------------------------------------------------------------------------------------------------------------------------
POTPIN = 0  # analog pin A0
potValue = 0
potPrevValue = 0
potTimer = 100 # if its 100 then potentiometer isn't being used

BUTTON1 = 8 # digital pin 8
BUTTON2 = 9 # digital pin 9
level1 = 0
prevLevel1 = 0
level2 = 0
prevLevel2 = 0

LED_PINS = [4, 5, 6, 7]

BUZZER = 3 # digital pin 3

display_i = 3
timerIsAlive = False
shutdownCheck = False

def potOn(potTimer):
    '''Makes the Display show the pot number for 15 seconds, unless interrupted by Left Button.\n
    Returns potTimer'''
    rightNow = datetime.now()
    x = int(rightNow.strftime("%S")) + 15 # How long display switches to Pot
    x%=60
    potTimer=x
    #print("x ="+str(x))
    #print("potTimer ="+str(potTimer))
    return potTimer

def potOnCheck(potTimer):
    '''Is the Potentiometer changing (aka in use) and has it been 15 seconds since it was last touched.\n
    Returns 100 if yes and potTimer if not'''
    rightNow = datetime.now()
    x = int(rightNow.strftime("%S"))
    #print("x ="+str(x))
    #print("potTimer ="+str(potTimer))
    if potTimer<16 and x>30:
        return potTimer
    if x>potTimer:
        return 100
    return potTimer

def map_range(x, in_min, in_max, out_min, out_max):
  '''Copied from the arduino map function definiton'''
  return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def timerStartArduino(cookingTime):
    '''Starts a timer sequence for the Arduino that takes slightly more than the time given.\n
    Displays time on display & when done blinks LEDS + buzzes'''
    x=0
    cycleLenght=1 # Cycle lenght
    board.digital_write(LED_PINS[1], 0) # Green LED off

    # Cooking Time Actions
    while x<cookingTime:
        if x%2==1:
            board.digital_write(LED_PINS[0], 1) # Red on
        else:
            board.digital_write(LED_PINS[0], 0) # Red off
        board.displayShow(x)
        x+=cycleLenght # Add how much time passed in this cycle
        time.sleep(cycleLenght) 

    # Actions when pizza done (LEDS Flash in sequence + Buzzer)
    board.digital_write(LED_PINS[0], 0) # Red off
    for _ in range(3):
        for pin in range(3):
            board.digital_write(LED_PINS[pin], 0)
            board.digital_write(LED_PINS[pin+1], 1)
            time.sleep(0.4)
        board.digital_write(LED_PINS[3], 0)
        board.analog_write(BUZZER,100)
        time.sleep(0.2)
        board.analog_write(BUZZER,0)
    board.analog_write(BUZZER,0)
    return

def PotChanged(data):#
    '''Callback function that reads Potentiometer\n
    Returns [pin_type, pin_number, pin_value, raw_time_stamp]'''
    global potValue
    potValue = data[2]

def ButtonChanged1(data):
    '''Callback function that reads Button1 Level\n
    Returns [pin_type, pin_number, pin_value, raw_time_stamp]'''
    global level1
    level1 = data[2] # get the level
    # Keep the callback function short and fast.
    # Let loop() do the 'expensive' tasks.

def ButtonChanged2(data):
    '''Callback function that reads Button2 Level\n
    Returns [pin_type, pin_number, pin_value, raw_time_stamp]'''
    global level2
    level2 = data[2] # get the level

def setup():
    global board
    board = CustomTelemetrix()
    board.displayOn()
    for pin in LED_PINS: # LEDs Setup
        board.set_pin_mode_digital_output(pin)
    board.set_pin_mode_analog_output(BUZZER) # Buzzer Analog Input
    board.set_pin_mode_analog_input(POTPIN, callback=PotChanged, differential=10) # Potentiometer
    board.set_pin_mode_digital_input_pullup(BUTTON1, callback = ButtonChanged1)
    board.set_pin_mode_digital_input_pullup(BUTTON2, callback = ButtonChanged2)
    # Note: Getting button level via callback ButtonChanged() is more 
    #       accurate for Firmata. When button is pressed or release,
    #       the ButtonChanged() function is called and this sets the 
    #       level variable.
    time.sleep(0.05)

def loop():
    '''Main Arduino function. Will attemp to run when app.py starts.\n
    If succefull then runs a while loop until Flask is shutdown'''
    while True:
        global t_timer, display_i, cooldownLuigiButton, pizza_name, pizza_timer, level1, prevLevel1, level2, prevLevel2, potTimer, potValue, potPrevValue, shutdownCheck, arduinoIsAlive, timerIsAlive, orderOven, indexCartItemInOven, uniqueOrderNumber

        arduinoIsAlive=True

        while timerIsAlive:
            time.sleep(1)
            continue

        # Shutdown check
        if shutdownCheck:
            break

        # Buttons
        if (prevLevel1 != level1 and prevLevel2 ==level2): # Changes when Right Button is pressed
            if prevLevel1 ==1:
                potTimer=100
                display_i+=1
                if display_i>=len(pizza_name):
                    display_i=0
            prevLevel1 = level1
        elif (prevLevel2 != level2 and prevLevel1 ==level1): # Changes when Left Button is pressed, starts the timer program
            if prevLevel2 ==1 and not timerIsAlive:
                indexCartItemInOven=0
                cooldownLuigiButton = True
                if potTimer==100:
                    t_timer= threading.Thread(target=timerStart)
                    pizzaDetails = find_item(Item_ID[display_i])
                    pizzaArduino = make_cart_item(pizzaDetails['ID'], pizzaDetails['name'], 1, pizzaDetails['price'], "Made through Arduino")
                    orderOven={"table": 0, "order number": uniqueOrderNumber, "cart": [pizzaArduino], "pizzas": [pizzaArduino], "others": []}
                    uniqueOrderNumber+=1
                    t_timer.start()
                elif potTimer <=60:
                    temp=map_range(potValue,0,1023,0,300)
                    t_timer= threading.Thread(target=timerStart)
                    pizzaArduino = {"ID": 99, "name": "Employees", "quantity": temp, "price": 0, "notes": "Made through Arduino"}
                    orderOven={"table": 0, "order number": uniqueOrderNumber, "cart": [pizzaArduino], "pizzas": [pizzaArduino], "others": []}
                    uniqueOrderNumber+=1
                    t_timer.start()
                else: # Redundant Safety Code (RSC)
                    print("Error: Timer is not starting")
                    time.sleep(1)
                ordersHistoric.append(orderOven)
            prevLevel2 = level2

        # Potentiometer Change Check
        if potPrevValue>potValue+1 or potPrevValue<potValue-1:
            potTimer=potOn(potTimer)
            potPrevValue=potValue
                                                                                                                
        # Display
        potTimer=potOnCheck(potTimer)  # Check if 15 seconds have passed
        if display_i<len(pizza_name) and potTimer == 100:
            temp = "-"+str(Item_ID[display_i])
            board.displayShow(temp)
        elif potTimer <=60:
            temp=map_range(potValue,0,1023,0,300)
            board.displayShow(temp)
        else: # Redundant Safety Code (RSC)
            print("Error: Display isn't updating")
            time.sleep(1)

        time.sleep(0.05)  # Give Firmata some time to handle protocol.
        # One cycle is 0.05 seconds

if not arduinoIsAlive:
    try:
        setup()
        # Reduntant code but why not?
        # Starts the loop function in another Thread so it runs parallel to Flask.
        t_loop= threading.Thread(target=loop)
        t_loop.start()
        print("\n\nArduino has started\n\n")
    except:
        print("\n\nArduino code not executed\n\n")


# ------------------------------------------------------------------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------------------------------------------------------------------

def timerStart():
    '''Timer starts. Can either run a timer on the Arduino if its online or a simple timer if its offline.'''
    global orderOven, indexCartItemInOven, arduinoIsAlive, pizza_timer, cooldownLuigiButton, notificationOven, arduinoIsAlive, timerIsAlive
    while True:
        timerIsAlive=True
        if orderOven["pizzas"][indexCartItemInOven]["ID"]==99: timer=orderOven["pizzas"][indexCartItemInOven]["quantity"]
        else: timer=pizza_timer[orderOven["pizzas"][indexCartItemInOven]["ID"]-100]*orderOven["pizzas"][indexCartItemInOven]["quantity"]
        if arduinoIsAlive:
            print("\nArduino is Alive\n")
            timerStartArduino(timer)
        else:
            print("\nArduino is not Alive\n")
            time.sleep(timer)
        #print(f'Cart item {orderOven["pizzas"][indexCartItemInOven]} is done')
        notificationOven = [1, orderOven["pizzas"][indexCartItemInOven], True] # How long the notification will stay up (refresh rate Luigi is 5sec so 1*5=5sec) & what is done
        indexCartItemInOven+=1
        try:
            timer=pizza_timer[orderOven["pizzas"][indexCartItemInOven]["ID"]-100]
        except:
            timerIsAlive=False
            cooldownLuigiButton=False
            break

def make_cart_item(itemID, itemName, quantity, price, notes):
    """Makes a cart_item{"ID": int, "name": str, "quantity": int, "price": int, "notes": str}"""
    name = {
        "ID": int(itemID),
        "name": itemName,
        "quantity" : int(quantity),
        "price": int(price),
        "notes" : notes
    }
    return name

def make_order(tableNumber, cart):
    """Creates an order{"table": int, "order number": int, "cart": list, "pizzas": list, "others": list}, appends order["pizzas"] to baking_orders\n
    or if order["pizzas"]==[] directly to historic and, finally, returns the order in case it is needed"""
    global uniqueOrderNumber, baking_orders, ordersHistoric, temporaryCustomerCart

    pizzas=[]
    others=[]
    for cartItem in cart:
        if cartItem["ID"]>=100 and cartItem["ID"]<200: pizzas.append(cartItem)
        elif cartItem["ID"]>=200 and cartItem["ID"]<400: others.append(cartItem)
    name = uniqueOrderNumber
    name = {"table": tableNumber, "order number": uniqueOrderNumber, "cart": pizzas+others, "pizzas": pizzas, "others": others}
    uniqueOrderNumber+=1
    print(temporaryCustomerCart, name)
    try:
        if temporaryCustomerCart['cart'] == name['cart'] and temporaryCustomerCart['table'] == name['table']: return name
    except: 1
    if name['pizzas']!=[]: baking_orders.append(name)
    else: ordersHistoric.append(name)
    return name # to reset cart without destroying list

def find_item(IDorName):
    """This function takes an ID or Name and returns a with all information on an item except timer\n
        itemDetails={"index":int, "ID":int, "name":str, "price":int}\n
        e.g. 101 ->  itemDetails{1, 101, Pepperoni, 14}\n
        e.g. Margherita ->  itemDetails{0, 100, Margherita, 11}\n"""
    itemDetails="error in find_item()"
    #ID is given
    if isinstance(IDorName, int):
        if IDorName>=100 and IDorName<200:itemDetails={"index":IDorName-100, "ID":IDorName, "name":pizza_name[IDorName-100], "price":pizza_price[IDorName-100]}
        elif IDorName>=200 and IDorName<300:itemDetails={"index":IDorName-200, "ID":IDorName, "name":drink_name[IDorName-200], "price":drink_price[IDorName-200]}
        elif IDorName>=300 and IDorName<400:itemDetails={"index":IDorName-300, "ID":IDorName, "name":dessert_name[IDorName-300], "price":dessert_price[IDorName-300]}

    #Name is given
    elif isinstance(IDorName, str):
        try: index=pizza_name.index(IDorName); itemDetails={"index":index, "ID":index+100, "name":pizza_name[index], "price":pizza_price[index]}
        except: 1
        try: index=drink_name.index(IDorName); itemDetails={"index":index, "ID":index+200, "name":drink_name[index], "price":drink_price[index]}
        except: 1
        try: index=dessert_name.index(IDorName); itemDetails={"index":index, "ID":index+300, "name":dessert_name[index], "price":dessert_price[index]}
        except: 1
    return itemDetails


# ------------------------------------------------------------------------------------------------------------------------------------------
# Flask
# ------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/')
def home():
    return redirect('/Customers/')
    #return render_template('index.html')

@app.route('/Yoshi/')
def Yoshi_page():
    return render_template('Yoshi.html')

@app.route('/Mario/')
@app.route('/Mario/<page>')
def Mario_page(page="Mario.html"):
    if page == "notes.html":
        return redirect('/notes/')
    elif page == "cart.html":
        return redirect('/cart/')
    else: return render_template(page) # All other pages

@app.route('/notes/')
@app.route('/notes/<itemName>', methods=["POST", "GET"])
def notes(itemName = None):
    global temporaryMarioCart
    # If we receive a POST request (with Quantity and Notes)
    notesCategory=find_item(itemName)
    if request.method == "POST":
        quantity = request.form["quantity"]
        notes = request.form["notes"]
        temporaryMarioCart.append(make_cart_item(notesCategory["ID"], notesCategory["name"], quantity,notesCategory["price"], notes))
        return redirect("../Mario")
    # Normal\GET request
    if itemName != None:
        return render_template('notes.html', itemName=notesCategory["name"], itemPrice=notesCategory["price"])
    else: return render_template('error.html')

@app.route('/cart/', methods=["POST", "GET"])
def cart():
    global temporaryMarioCart
    if request.method == "POST":
        tableNumber = request.form["tableNumber"]
        if temporaryMarioCart != []:
            _ = make_order(tableNumber, temporaryMarioCart)
            temporaryMarioCart=[]
        return redirect("../Mario")
    return render_template('cart.html', cart=temporaryMarioCart)

@app.route('/Luigi/')
def dashboard():
    global notificationOven, cooldownLuigiButton, baking_orders
    if notificationOven[0]>0: 
        notificationOven[2]=True
        notificationOven[0]-=1
    else: notificationOven[2]=False
    return render_template('Luigi.html', orders = baking_orders, cooldown = cooldownLuigiButton, notificationOven = notificationOven)

@app.route('/baking_orders/', methods=['GET'])
def baking():
    global t_timerFlask, t_timer, baking_orders, ordersHistoric, cooldownLuigiButton, pizza_timer, indexCartItemInOven, orderOven
    
    # Timer Start Button
    if cooldownLuigiButton == False and len(baking_orders)>0 and not timerIsAlive:
        cooldownLuigiButton = True
        orderOven = baking_orders[0]
        ordersHistoric.append(baking_orders[0])
        baking_orders.pop(0)

        indexCartItemInOven=0
        t_timerFlask= threading.Thread(target=timerStart)
        t_timerFlask.start()
        return redirect('/Luigi')
    if not timerIsAlive: cooldownLuigiButton = False
    return redirect('/Luigi')

@app.route('/Customers/')
@app.route('/Customers/<page>')
def Customers_page(page="Mario_Luigi_Index.html"):
    if page == "M_L_Check_Order.html":
        global pizza_timer, temporaryCustomerCart
        timer=0
        if temporaryCustomerCart==[]: return render_template("error.html")
        for pizzas in temporaryCustomerCart["pizzas"]:
            timer+=pizza_timer[pizzas["ID"]-100]*pizzas["quantity"]
            m, s = divmod(timer, 60)
        #print(f'\n\n{timer}\n{temporaryCustomerCart}\n\n')
        return render_template("M_L_Check_Order.html", order=temporaryCustomerCart, m=m, s=s)
    temporaryCustomerCart=[]
    return render_template(f"{page}")

@app.route('/checkout', methods=['POST'])
def javascript_cart_checkout():
    global temporaryCustomerCart

    tempList = []
    data = request.get_json()
    #print(f'\n\n{data}\n\n')
    for item in data['cart']:
        customerItem=find_item(item[0])
        quantity = item[1]
        tempList.append(make_cart_item(customerItem["ID"], customerItem["name"], quantity, customerItem["price"], ''))
        #print(f'\n\n{tempList}\n\n')
    if tempList != []: temporaryCustomerCart=make_order(data['table'], tempList)
    print(temporaryCustomerCart)
    return jsonify([])

@app.route('/Statistic')
def Statistic_page():
    global ordersHistoric
    
    listOfItems = []

    for order in ordersHistoric:
        for newItem in order['cart']:
            if len(listOfItems)==0 and len(ordersHistoric)>0:
                listOfItems.append(newItem)
                continue
            foundMatch=False
            for oldItem in listOfItems:
                if newItem['ID'] == oldItem['ID']:
                    oldItem['quantity']+=newItem['quantity']
                    foundMatch=True
                    break
            if not foundMatch:
                listOfItems.append(newItem)

    listSummary = {'total_quantity':0, 'total_price':0}
    for item in listOfItems:
        if item['ID']==99: continue
        listSummary['total_quantity']+=item['quantity']
        listSummary['total_price']+=item['price']*item['quantity']

    return render_template('Statistic.html', list = listOfItems, list_2 = listSummary) 

@app.route('/Register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if request.method == "POST":
        print(form.username.data), print("POST")
    #if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}, welcome to the family!')
        return redirect('/Login')
    return render_template('register.html', form=form)

@app.route('/Login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.email == 'mario@pizza.com':
                login_user(user, remember=form.remember.data)
                return redirect(url_for('Mario_page'))
            elif user.email == 'luigi@pizza.com':
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))
            elif user.email == 'admin@pizza.com':
                login_user(user, remember=form.remember.data)
                return redirect(url_for("Statistic_page"))
            else:
                login_user(user, remember=form.remember.data)
                return redirect(url_for('Customers_page'))
        else:
            # Handle the case when the user is not found or the password is incorrect
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', form=form)


  

if __name__=="__main__":
    app.run()#debug=True)

if arduinoIsAlive: # Arduino shutdown sequence, yes it might be unnecessary
    try: 
        shutdownCheck = True
        t_loop.join()
        print('shutdown')
        board.displayShow("----")
        board.shutdown()
        sys.exit(0)
    except:1

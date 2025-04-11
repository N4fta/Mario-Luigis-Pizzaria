uniqueOrderNumber = 0
baking_orders=[]

orderHistoric = [
    { # order 1
        'table': '15',
        'order number': 0,
        'cart': [
            {'ID': '101', "name": "Pepperoni", "quantity": 2, "price": 14, 'notes': 'One big and the other with pepperoni'},
            {'ID': '100', "name": "Margherita", "quantity": 1, "price": 11,'notes': 'One small'},
            {'ID': '201', "name": "Acqua Panna", "quantity": 3, "price": 6, 'notes': ''},
            {'ID': '204', "name": "House Red", "quantity": 1, "price": 9, 'notes': ''},
            {'ID': '300', "name": "Tiramisu", "quantity": 1, "price": 9, 'notes': ''}
            ],
        'pizzas': [
            {'ID': '101', "name": "Pepperoni", "quantity": 2, "price": 14, 'notes': 'One big and the other with pepperoni'},
            {'ID': '100', "name": "Margherita", "quantity": 1, "price": 11,'notes': 'One small'}
            ],
        'others':[
            {'ID': '201', "name": "Acqua Panna", "quantity": 3, "price": 6, 'notes': ''},
            {'ID': '204', "name": "House Red", "quantity": 1, "price": 9, 'notes': ''},
            {'ID': '300', "name": "Tiramisu", "quantity": 1, "price": 9, 'notes': ''}
            ]
    },
    { # order 2
        'table': '16',
        'order number': 1,
        'cart': [
            {'ID': '101', "name": "Pepperoni", "quantity": 2, "price": 14, 'notes': 'One big and the other with pepperoni'},
            {'ID': '100', "name": "Margherita", "quantity": 1, "price": 11,'notes': 'One small'},
            {'ID': '201', "name": "Acqua Panna", "quantity": 3, "price": 6, 'notes': ''},
            {'ID': '204', "name": "House Red", "quantity": 1, "price": 9, 'notes': ''},
            {'ID': '300', "name": "Tiramisu", "quantity": 1, "price": 9, 'notes': ''}
            ],
        'pizzas': [
            {'ID': '102', "name": "Pepperoni", "quantity": 2, "price": 14, 'notes': 'One small and the other with cheese'},
            {'ID': '102', "name": "Pepperoni", "quantity": 3, "price": 14, 'notes': 'One big, other small'}
            ],
        'others':[
            {'ID': '201', "name": "Acqua Panna", "quantity": 3, "price": 6, 'notes': ''},
            {'ID': '204', "name": "House Red", "quantity": 1, "price": 9, 'notes': ''},
            {'ID': '300', "name": "Tiramisu", "quantity": 1, "price": 9, 'notes': ''}
            ]
    }
]

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
    """Creates an order{"table": int, "order number": int, "pizzas": list, "others": list} and appends order["pizzas"] it to baking_orders\n
    and returns an empty list to clear cart in a non-destructive way"""
    global uniqueOrderNumber, baking_orders

    pizzas=[]
    others=[]
    for cartItem in cart:
        if cartItem["ID"]>=100 and cartItem["ID"]<200: pizzas.append(cartItem)
        elif cartItem["ID"]>=200 and cartItem["ID"]<400: others.append(cartItem)
    name = uniqueOrderNumber
    name = {"table": tableNumber, "order number": uniqueOrderNumber, "cart": pizzas+others, "pizzas": pizzas, "others": others}
    uniqueOrderNumber+=1
    baking_orders.append(name)
    return [] # to reset cart without destroying list

print("Items (dict): ")
print(f"\norderHistoric[0]['cart'][0] = {orderHistoric[0]['cart'][0]}")

print("\n\nAll Orders (list): ")
print(f"orderHistoric = {orderHistoric}")

print("\n\nOrder[0] (dict): ")
print(f"orderHistoric[0] = {orderHistoric[0]}")

print("\n\nOrder[0], [\"cart\"]:")
print(f"orderHistoric[0]['cart'] = {orderHistoric[0]['cart']}")

print("\n\nOrder[0], [\"cart\"], Cart[0]:")
print(f"orderHistoric[0]['cart'][0] = {orderHistoric[0]['cart'][0]}\n")

############################################################################################################################################################################################################################################################################

Item_ID = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 300, 301, 302, 303, 304, 305, 306]
pizza_name = ["Margherita", "Pepperoni", "4 Cheeses", "Calzone", "Tuna", "Prosciutto", "4 Stagioni", "BBQ Chicken", "Caprese Pizza", "Funghi", "Meat Lovers", "New York", "Spinach", "White Pepper"] # 14 pizzas
pizza_timer = [11, 14, 24, 23, 24, 27, 15, 27, 24, 20, 27, 23, 16, 23]
pizza_price = [11, 14, 12, 14, 16, 13, 16, 15, 15, 15, 13, 11, 16, 15]
drink_name = ["San Pellegrino", "Acqua Panna", "Prosecco", "House Red", "House White", "Birra Moretti", "Cola", "Fanta", "Sprite", "Limoncello"] # 10 drinks
drink_price = [7, 6, 10, 9, 9, 8, 3, 3, 3, 9]
dessert_name = ["Tiramisu", "The Colonel", "Chocolate Mousse", "Cannoli", "Panna Cotta", "Affogato", "Gelato"] # 7 desserts
dessert_price = [9, 7, 6, 7, 7, 5, 5]
# Example Pizza:
# Margherita has index 0 and ID 100. Its index is 0 because (ID-100=0)
# By inputing its index into any list we get its information:
# Item_ID[0] = 100
# pizza_name[0] = Margherita
# pizza_price[0] = 11
# pizza_timer[0] = 234
# 
# Example Drink:
# Drinks have IDs in the 200s. SanPellegrino has ID 200 and index 0 (ID-200=0)
# Item_ID[len(pizza_name)+0] = 200
# drink_name[0] = SanPellegrino
# drink_price[0] = 7
# 
# Example Dessert:
# Desserts have IDs in the 300s. Tiramisu has ID 300 and index 0 (ID-300=0)
# Item_ID[len(pizza_name)+len(drink_name)+0] = 300
# dessert_name[0] = Tiramisu
# dessert_price[0] = 9
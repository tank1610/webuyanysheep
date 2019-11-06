import argparse
import json
import copy
from flask import Flask, request
import xml.etree.ElementTree as ET
from decimal import *
from twilio.rest import Client


account_sid = ''
auth_token = ''
client = Client(account_sid, auth_token)
TXT_UPDATE = True


global_herd_dict = None
global_stock_dict = None
current_day = 0

def read_herd(filename):
    '''
    Read an .xml file into an ElementTree object
    '''
    root = ET.parse(filename).getroot()
    return root.findall('labsheep')

def get_herd_dict(herd):
    '''
    Take a herd ElementTree and returns a Dict
    '''
    herd_dict = {}
    sheep_list = []
    for sheep in herd:
        sheep_list.append({
            'name': sheep.get('name'),
            'age': sheep.get('age'),
            'age-last-shaved':sheep.get('age-last-shaved')
        })
    herd_dict['herd']=sheep_list
    return herd_dict

def get_stock(days, herd_dict=None, stock_dict=None, update_herd=0):
    '''
    Function to get stock and herd on a given day.

    args:
        days: time in days
        herd_dict=None: a dict of herd, default to None if using global herd
        stock_dict=None: a dict of the stock, default to None if using global stock
        update_herd=0: if set to 1, global herd and stock is used (mainly for placing orders)
    
    returns:
        copy_herd_dict: copy of herd_dict or global_herd_dict
        copy_stock_dict: copy of stock_dict or global_stock_dict
    '''
    global current_day
    global global_herd_dict
    global global_stock_dict
    if update_herd:
        #Use the global dict to update stock
        copy_herd_dict = global_herd_dict
        copy_stock_dict = global_stock_dict
    else:
        #Make deep copies to present a preview of stock
        copy_herd_dict = copy.deepcopy(global_herd_dict)
        copy_stock_dict = copy.deepcopy(global_stock_dict)

    if current_day == 0 or global_stock_dict is None:
        #Initialise the stock
        current_day = days
        copy_stock_dict = {}
        copy_stock_dict['milk'] = 0
        copy_stock_dict['skins'] = 0
        copy_stock_dict['skins'] = len(copy_herd_dict['herd']) #On day 0 all sheeps get shaved
        for sheep in copy_herd_dict['herd']:
            sheep_days = (int(Decimal(sheep['age'])*100))
            sheep['age-last-shaved'] = sheep_days
    else:
        temp_day = days
        days = days - current_day
        if update_herd:
            current_day = temp_day

    for index, sheep in enumerate(copy_herd_dict['herd']):
        sheep_days = (int(Decimal(sheep['age'])*100))
        for elapsed_days in range(0, days):
            if sheep_days >= 1000:
                copy_herd_dict['herd'].pop(index)
                break
            else:
                copy_stock_dict['milk'] = float(copy_stock_dict['milk']) + (50-sheep_days*0.03)
                if(sheep_days > 8+1.01*int(sheep['age-last-shaved'])):
                    copy_stock_dict['skins'] =  copy_stock_dict['skins'] + 1
                    sheep['age-last-shaved'] = sheep_days
                sheep_days =  sheep_days + 1
        copy_stock_dict['milk'] = str(round(copy_stock_dict['milk'],2))
        copy_stock_dict['milk'] = float(copy_stock_dict['milk'])
        sheep['age'] = str(Decimal(sheep_days)/100)

    if update_herd:
        global_stock_dict = copy_stock_dict
        global_herd_dict = copy_herd_dict
    return copy_herd_dict, copy_stock_dict

def process_order(time, milk, wool):
    '''
    Process an order of milk and wool.

    args:
        time: of the order, in days
        milk: amount of milk in the order
        wool: amount of wool in the order
    
    return:
        status: 0 if fulfilled
                1 if only milk sent
                2 if only wool sent
                -1 if unfulfilled
        order_dict: a dict of the stock that was sent
    '''
    global global_stock_dict
    current_herd, current_stock = get_stock(time, update_herd=1)
    
    current_milk = current_stock['milk']
    current_wool = current_stock['skins']
    order_dict ={}

    print('Current milk: ', current_milk)
    print(milk)

    if current_milk >= milk and current_wool >= wool:
        #Order fully fulfilled
        order_dict = {'milk': milk, 'skins':wool}
        global_stock_dict['milk'] = global_stock_dict['milk'] - milk
        global_stock_dict['skins'] = global_stock_dict['skins'] - wool
        if TXT_UPDATE:
            send_text(time, milk, wool, global_stock_dict, order_dict)
        return 0, order_dict
    elif current_milk>= milk:
        #Milk can be fulfilled
        order_dict = {'milk': milk}
        global_stock_dict['milk'] = global_stock_dict['milk'] - milk
        if TXT_UPDATE:
            send_text(time, milk, wool, global_stock_dict, order_dict)
        return 1, order_dict
    elif current_wool>=wool:
        #Wool can be fulfilled
        order_dict = {'skins': wool}
        global_stock_dict['skins'] = global_stock_dict['skins'] - wool
        if TXT_UPDATE:
            send_text(time, milk, wool, global_stock_dict, order_dict)
        return 2, order_dict
    else:
        #Nothing can be fulfilled
        if TXT_UPDATE:
            send_text(time, milk, wool, global_stock_dict, order_dict, unfulfilled=1)
        return -1, None

def send_text(time, milk, wool, stock_dict, order_dict, unfulfilled=0):
    '''
    Send a text message using Twilio about the last order.
    
    args:
        time: time of order in days
        milk: amount of milk ordered
        wool: amount of wool ordered
        stock_dict: dict of current stock
        order_dict: dict of the fulfilled order 
    '''
    if 'milk' not in order_dict:
        order_dict['milk'] = 0
    if 'skins' not in order_dict:
        order_dict['skins'] = 0

    if unfulfilled:
        msg_body = ("A customer ordered {order_milk} of milk and {order_wool} of wool "
            "on day {time} but stock is too low. Current stock:"
            "{milk} of milk, {wool} of wool".format(
                order_milk=milk, order_wool = wool, time=time,
                milk=stock_dict['milk'], wool=stock_dict['skins']
            ))
    else:
        msg_body = ("A customer ordered {order_milk} of milk and {order_wool} of wool "
            "on day {time}. Order fulfilled with: "
            "{sent_milk} of milk and {sent_wool} of wool."
            "Current stock: {milk} of milk, {wool} of wool".format(
                order_milk=milk, order_wool = wool, time=time,
                milk=stock_dict['milk'], wool=stock_dict['skins'], 
                sent_milk=order_dict['milk'], sent_wool=order_dict['skins']
            ))
    message = client.messages \
                .create(
                     body=msg_body,
                     from_='+3197014202048',
                     to='+31643679276'
                 )

def create_app():
    app = Flask(__name__)

    @app.route('/sheep-shop/load',methods=['POST'])
    def load_herd():
        '''
        Load a new herd
        '''
        global global_herd_dict
        global global_stock_dict
        global current_day
        root = ET.fromstring(request.data)
        #Set the global herd and stock to 0 day
        global_herd_dict = get_herd_dict(root.findall('labsheep'))
        global_stock_dict = None
        current_day = 0
        return '', 205

    @app.route('/sheep-shop/stock/<int:time>',methods=['GET'])
    def take_stock(time):
        '''
        Returns the stock on day
        '''
        current_herd, current_stock = get_stock(time, update_herd=0)
        return json.dumps(current_stock), 200

    @app.route('/sheep-shop/herd/<int:time>',methods=['GET'])
    def take_herd(time):
        '''
        Returns the herd on day
        '''
        current_herd, stock = get_stock(time, update_herd=0)
        return json.dumps(current_herd), 200

    @app.route('/sheep-shop/order/<int:time>',methods=['POST'])
    def order(time):
        '''
        Method for placing an order
        '''
        order_details = json.loads(request.data)
        print('Customer: %s ordering %s of milk and %s of wool' %(order_details['customer'],
        order_details['order']['milk'], order_details['order']['skins']))

        order_status, order_dict = process_order(time, int(order_details['order']['milk']),\
            int(order_details['order']['skins']))

        if order_status == -1:
            return '',404
        elif order_status == 0:
            return json.dumps(order_dict), 201
        else:
            return json.dumps(order_dict), 206
    
    return app

if __name__ == '__main__':
    #Get herd file and days elapsed as arguments
    parser = argparse.ArgumentParser(description='Process a herd of sheeps.')
    parser.add_argument('file', type=str, help='name of herd file.')
    parser.add_argument('days', type=int, help='elapsed time in days.')
    args = parser.parse_args()

    input_herd = read_herd(args.file)

    global_herd_dict = get_herd_dict(input_herd)

    init_herd, stock = get_stock(args.days,herd_dict=global_herd_dict, stock_dict=global_stock_dict)
    print('In stock:\n' \
        '    %s liters of milk\n' \
        '    %s skins of wool' %(stock['milk'], stock['skins']))
    print('Herd:\n')
    for sheep in init_herd['herd']:
        print('    %s %s years old' %(sheep['name'], sheep['age']))
    app = create_app()
    app.run()
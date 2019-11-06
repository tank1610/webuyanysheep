import pytest
import herd_flask
import copy

herd_dict = {'herd': [{'name': 'Betty-1', 'age': '4', 'age-last-shaved': None},
                    {'name': 'Betty-2', 'age': '8', 'age-last-shaved': None}, 
                    {'name': 'Betty-3', 'age': '9.5', 'age-last-shaved': None}]}
stock_dict = {'milk': 0, 'skins': 0}

day_13 = ({'herd': [{'name': 'Betty-1', 'age': '4.13', 'age-last-shaved': 400}, 
                    {'name': 'Betty-2', 'age': '8.13', 'age-last-shaved': 800}, 
                    {'name': 'Betty-3', 'age': '9.63', 'age-last-shaved': 950}]}, 
        {'milk': 1104.48, 'skins': 3})

day_14 = ({'herd': [{'name': 'Betty-1','age': '4.14', 'age-last-shaved': 413}, 
                    {'name': 'Betty-2', 'age': '8.14', 'age-last-shaved': 800}, 
                    {'name': 'Betty-3', 'age': '9.64', 'age-last-shaved': 950}]}, 
        {'milk': 1188.81, 'skins': 4})

def test_get_dict():
    '''
    Given an .xml file
    check that a dict of correct format is returned
    '''
    import xml.etree.ElementTree as ET
    root = ET.parse('herd.xml').getroot()
    assert herd_flask.get_herd_dict(root.findall('labsheep')) == herd_dict

def test_get_stock_check():
    '''
    Check that stock and herd on day 13 and 14 are according to user stories
    '''
    herd_flask.global_herd_dict = copy.deepcopy(herd_dict)
    assert herd_flask.get_stock(13, herd_dict, None) == day_13
    assert herd_flask.get_stock(14, herd_dict, None) == day_14

def test_place_order():
    '''
    Given an order of 100 milk and 3 skins on day 14
    check that order is fulfilled
    check that stock is updated
    '''
    herd_flask.global_herd_dict = copy.deepcopy(herd_dict)
    herd_flask.current_day = 0
    assert herd_flask.get_stock(14, herd_dict, None) == day_14

    order_dict = {'milk': 1000, 'skins':3}

    assert herd_flask.process_order(14,1000,3) == (0, order_dict)
    assert herd_flask.get_stock(14) == ({"herd": [{"age": "4.14", "age-last-shaved": 413, 
                                                    "name": "Betty-1"}, 
                                                {"age": "8.14", "age-last-shaved": 800, "name": "Betty-2"}, 
                                                {"age": "9.64", "age-last-shaved": 950, "name": "Betty-3"}]},
                                        {"milk": 188.81, "skins": 1})

def test_past_order():
    '''
    Given the current day is 14
    and an order is placed for day 13
    check that order cannot be fulfilled
    '''
    herd_flask.global_herd_dict = copy.deepcopy(herd_dict)
    herd_flask.current_day = 14
    assert herd_flask.process_order(13,1000,3) == (-1, None)

def test_milk_only_order():
    '''
    Given an order for 1000 milk and 5 wool on day 13
    check that order is partially fulfilled
    check that stock is updated
    '''
    herd_flask.global_herd_dict = copy.deepcopy(herd_dict)
    herd_flask.global_stock_dict = None
    herd_flask.current_day = 0

    assert herd_flask.get_stock(13, herd_dict, None) == day_13

    order_dict = {'milk': 1000}

    assert herd_flask.process_order(13,1000,5) == (1, order_dict)
    assert herd_flask.get_stock(13) == ({"herd": [{"age": "4.13", "age-last-shaved": 400, 
                                                    "name": "Betty-1"}, 
                                                {"age": "8.13", "age-last-shaved": 800, "name": "Betty-2"}, 
                                                {"age": "9.63", "age-last-shaved": 950, "name": "Betty-3"}]},
                                        {"milk": 104.48, "skins": 3})

def test_wool_only_order():
    '''
    Given an order for 1200 milk and 3 wool on day 13
    check that order is partially fulfilled
    check that stock is updated
    '''
    herd_flask.global_herd_dict = copy.deepcopy(herd_dict)
    herd_flask.global_stock_dict = None
    herd_flask.current_day = 0

    assert herd_flask.get_stock(13, herd_dict, None) == day_13

    order_dict = {'skins': 3}

    assert herd_flask.process_order(13,1200,3) == (2, order_dict)
    assert herd_flask.get_stock(13) == ({"herd": [{"age": "4.13", "age-last-shaved": 400, 
                                                    "name": "Betty-1"}, 
                                                {"age": "8.13", "age-last-shaved": 800, "name": "Betty-2"}, 
                                                {"age": "9.63", "age-last-shaved": 950, "name": "Betty-3"}]},
                                        {"milk": 1104.48, "skins": 0})

def test_dead_sheep():
    '''
    On day 51
    check that Betty 3 is no longer with us
    '''
    herd_flask.global_herd_dict = copy.deepcopy(herd_dict)
    herd_flask.global_stock_dict = None
    herd_flask.current_day = 0

    assert herd_flask.get_stock(51, herd_dict, None)[0] == {"herd": [{"age": "4.51", "age-last-shaved": 439, "name": "Betty-1"}, 
                                                {"age": "8.51", "age-last-shaved": 834, "name": "Betty-2"}]}


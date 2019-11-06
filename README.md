# sheep-shop
An online shop that sells sheep products. 

The online shop can be started from the terminal. It accepts `herd.xml` as an input file containing details of the herd.
The functions and APIs available allow the user to:
* Check the herd and stock on a given day.
* Upload a new herd.
* Query and fulfil an online order.
* Notify the farmer when an order is placed/fulfiled/partly fulfiled.

## Quickstart
The project was developed in Python 3.7.1 and is compatible with Python 2.7 or and higher.
Flask is needed for the application and tests were written using pytest.
`pip install flask pytest`

Per the user story, the webshop can be started with:
```
python herd_flask.py herd.xml 13
```
Which will print out:
```
In stock:
    1104.48 liters of milk
    3 skins of wool
Herd:

    Betty-1 4.13 years old
    Betty-2 8.13 years old
    Betty-3 9.63 years old
```
By default, the webshop will run on `http://127.0.0.1:5000/` 

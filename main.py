#
# programmed by Chris, 02/17/2023
#

from bs4 import BeautifulSoup
import requests
import json

import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.message import EmailMessage

import email_info

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# dictionary of the items at full price
full_prices = {
    'TOMS Carlo Sneaker'           : 54.95,
    'MoonGoat Pocket Shop T-Shirt' : 22.27
}


# get data for TOMS shoe
def get_toms_data():

    link = 'https://www.toms.com/us/men/shoes/sneakers/' \
           'black-on-black-heritage-canvas-mens-carlo-sneaker-topanga-collection/10012282.html'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    data_product = soup.find('div', {'data-product': True})['data-product']
    product_dict = json.loads(data_product)['product']

    shoe = product_dict['variants'][0]

    name = product_dict['brand_name'] + ' ' + product_dict['name']
    price = float(shoe['price'])
    size = 10
    in_stock = shoe['in_stock']
    image_link = shoe['image_url']

    return name, price, size, link


# get data for MoonGoat shirt
def get_moongoat_data():

    link = 'https://moongoat.com/products/pocket-shop-t-shirt'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    product_data = soup.find('script', id='wcp_json_7807686967547')
    product_dict = json.loads(product_data.string)

    shirt = product_dict['variants'][1]

    name = product_dict['vendor'] + ' ' + product_dict['title']
    price = str(shirt['price'])
    size = shirt['title']
    in_stock = shirt['available']
    image_link = product_dict['featured_image']

    # fix formatting of data
    name = ''.join(char.upper() if (index == 0 or index == 4) else char for index, char in enumerate(name))
    price = float(price[:2] + '.' + price[2:])

    return name, price, size, link


# scrape HTML from web pages, get basic data, send email if sale found
def get_website_data():

    items = [get_toms_data, get_moongoat_data]
    on_sale = []

    for item in items:

        name, price, size, link = item()
        full_price = full_prices[name]

        if(price < full_price):
            data = (name, price, size, link)
            on_sale.append(data)

    if on_sale:
        send_sale_email(on_sale)


# send an email to myself with the data of the item(s) on sale
def send_sale_email(sales):

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        email_body = 'sales bot found a sale\n'

        for sale in sales:

            name, price, size, link = sale

            sale_str = f'\n| {name} |\n  on sale ${price}, size {size}\n{link}\n'

            email_body = ''.join((email_body, sale_str))

        message.set_content(email_body)
  
        message['To'] = email_info.get_email()
        message['From'] = email_info.get_email()
        message['Subject'] = 'You\'ve got sale'
  
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
  
        create_message = {
            'raw': encoded_message
        }

        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(f'Message Id: {send_message["id"]}')

    except HttpError as error:
        send_message = None
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    get_website_data()

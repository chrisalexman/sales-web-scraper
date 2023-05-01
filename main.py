#
# programmed by Chris, 02/17/2023
#

import json
import base64
import logging
import os.path
import requests

from bs4 import BeautifulSoup
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
    'TOMS Carlo Sneaker'                         : 54.95,
    'MoonGoat Pocket Shop T-Shirt'               : 22.27,
    'Sony WH-1000XM4 Noise Canceling Headphones' : 349.99,
    'Hades No Escape Shirt'                      : 32.00
}


# configure the logging to output
def config_logging():

    logging.basicConfig(filename='output.log', filemode='a', level=logging.INFO, 
                        format='%(asctime)s %(levelname)s %(message)s')
    
    # to avoid - INFO file_cache is only supported with oauth2client<4.0.0
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


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


# get data for Sony WH-1000XM4 Noise Canceling Headphones
def get_headphone_data():

    link = 'https://electronics.sony.com/audio/headphones/headband/p/wh1000xm4-b'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    product_data = soup.find('script', id='pdp-jsonld-data')
    product_dict = json.loads(product_data.string)

    name = ' '.join([product_dict['brand']['name'], product_dict['description'][3:13], product_dict['description'][31:57]])
    price = product_dict['offers']['price']
    size = 'N/A'
    in_stock = 'Y'
    image_link = product_dict['image']

    return name, price, size, link


# get data for Hades Shirt
def get_hades_data():

    link = 'https://www.fangamer.com/collections/hades/products/hades-shirt-no-escape'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    product_data = soup.find('section', id='pricing_and_sizes')
    price_size_data = soup.find('option', value='40367665610809').text

    name = 'Hades No Escape Shirt'
    price = float(price_size_data[-5:])
    size = price_size_data[7:8]
    in_stock = 'Y'
    image_link = 'N/A'

    return name, price, size, link


# scrape HTML from web pages, get basic data, send email if sale found
def get_website_data():

    items = [get_toms_data, get_moongoat_data, get_headphone_data, get_hades_data]
    on_sale = []

    for item in items:

        name, price, size, link = item()
        full_price = full_prices[name]

        if(price < full_price):
            data = (name, price, size, link)
            on_sale.append(data)

    if on_sale:
        send_sale_email(on_sale)
    else:
        logging.info('no sales found, no email sent')


# send an email to myself with the data of the item(s) on sale
def send_sale_email(sales):

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # refresh the credentials
        creds.refresh(Request())

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

            logging.info(f'item on sale - {name} (${price})')

        message.set_content(email_body)
  
        message['To'] = email_info.get_email()
        message['From'] = email_info.get_email()
        message['Subject'] = 'you\'ve got sale'
  
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
  
        create_message = {
            'raw': encoded_message
        }

        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        logging.info(f'sent email, id {send_message["id"]}')

    except HttpError as error:
        send_message = None
        logging.error(f'An error occurred: {error}')


if __name__ == '__main__':
    config_logging()
    get_website_data()

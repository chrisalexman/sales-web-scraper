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
    'Hades No Escape Shirt'                      : 32.00,
    'Battlecry Acre Crusader Broadsword'         : 329.95,
    'CROM Dark Splendor T-shirt'                 : 31.00,
    'LG 34WQ75C-B Monitor'                       : 599.99
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

    product_data = soup.find('div', {'data-product': True})['data-product']
    product_dict = json.loads(product_data)['product']

    size_data = soup.find('button', {'aria-label' : 'Select Men Size 10'})['data-size']

    shoe_variant = product_dict['variants'][0]

    name = ' '.join([product_dict['brand_name'], product_dict['name']])
    price = float(shoe_variant['price'])
    size = size_data
    in_stock = shoe_variant['in_stock']
    image_link = shoe_variant['image_url']

    return name, price, size, link


# get data for MoonGoat shirt
def get_moongoat_data():

    link = 'https://moongoat.com/products/pocket-shop-t-shirt'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    product_data = soup.find('script', id='wcp_json_7807686967547')
    product_dict = json.loads(product_data.string)

    shirt_variant = product_dict['variants'][1]

    name = ' '.join([product_dict['vendor'], product_dict['title']])
    price = str(shirt_variant['price'])
    size = shirt_variant['title']
    in_stock = shirt_variant['available']
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

    stock_data = soup.find('button', {'class' : 'sony-btn sony-btn--primary sony-btn--primary w-100'}).text[1:12]

    name = ' '.join([product_dict['brand']['name'], product_dict['description'][3:13], product_dict['description'][31:57]])
    price = product_dict['offers']['price']
    size = 'N/A'
    in_stock = stock_data == 'Add to cart'
    image_link = product_dict['image']

    return name, price, size, link


# get data for Hades Shirt
def get_hades_data():

    link = 'https://www.fangamer.com/collections/hades/products/hades-shirt-no-escape'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    price_size_data = soup.find('option', value='40367665610809').text

    stock_data = soup.find('meta', content='InStock')

    image_data = ''.join(['https:', soup.find_all('a', {'class' : 'item'})[1]['href']])
    
    name = 'Hades No Escape Shirt'
    price = float(price_size_data[-5:])
    size = price_size_data[7:8]
    in_stock = stock_data['content']
    image_link = 'N/A'

    return name, price, size, link


# get data for the battlecry acre crusader broadsword
def get_broadsword_data():

    link = 'https://www.museumreplicas.com/acre-crusader-broadsword'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    name_data = soup.find('meta', property='og:title')['content']
    
    price_data = soup.select_one('span[class*=price]').text
    price_data = price_data[2:8]

    stock_data = soup.select_one('span[id=stock-availability-value-2878]').text

    image_data = soup.find_all('a', {'class' : 'cloud-zoom-gallery thumb-item'})[-1]['href']

    name = name_data
    price = float(price_data)
    size = '39-1/4"'
    in_stock = stock_data
    image_link = image_data

    return name, price, size, link


# get data for the crom dark splendor t-shirt
def get_crom_data():

    link = 'https://crom.ink/shop/dark-splendor-t-shirt'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    name_data = soup.find('title').text

    product_data = soup.find('div', {'class' : 'product-variants'})

    variant = json.loads(product_data['data-variants'])[0]

    name = ' '.join([name_data[24:28], name_data[0:21]])
    price = float(variant['salePriceMoney']['value'])
    size = variant['attributes']['Size']
    in_stock = int(variant['qtyInStock']) > 0
    image_link = variant['mainImage']['assetUrl']

    return name, price, size, link


# get data for the LG 34WQ75C-B Monitor
def get_monitor_data():

    link = 'https://www.lg.com/us/monitors/lg-34wq75c-b'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    name_data = soup.find('meta', {'property' : 'og:description'})

    price_data = soup.find('meta', {'itemprop' : 'price'})

    stock_data = soup.find('div', {'class' : 'in-stock-pdp-new'})\
    
    image_data = soup.find('img', {'class' : 'pc'})

    name = ' '.join([name_data['content'][5:17], 'Monitor'])
    price = float(price_data['content'])
    size = 'N/A'
    in_stock = stock_data.text[0:9]
    image_link = image_data['src']
    
    return name, price, size, link


# scrape HTML from web pages, get basic data, send email if sale found
def get_website_data():

    items = [get_toms_data, get_moongoat_data, get_headphone_data, get_hades_data, get_broadsword_data, 
             get_crom_data, get_monitor_data]
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

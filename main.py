#
# programmed by Chris, 02/17/2023
#

from bs4 import BeautifulSoup
import requests
import json


# dictionary of the items at full price
full_price = {
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
    price = shoe['price']
    size = 10
    in_stock = shoe['in_stock']
    image_link = shoe['image_url']

    return name, price, size


# get data for MoonGoat shirt
def get_moongoat_data():

    link = 'https://moongoat.com/products/pocket-shop-t-shirt'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    product_data = soup.find('script', id='wcp_json_7807686967547')
    product_dict = json.loads(product_data.text)

    shirt = product_dict['variants'][1]

    name = product_dict['vendor'] + ' ' + product_dict['title']
    price = str(shirt['price'])
    size = shirt['title']
    in_stock = shirt['available']
    image_link = product_dict['featured_image']

    # fix formatting of data
    name = ''.join(char.upper() if (index == 0 or index == 4) else char for index, char in enumerate(name))
    price = price[:2] + '.' + price[2:]

    return name, price, size


items = [get_toms_data, get_moongoat_data]

# scrape HTML from web pages, get price data and more
def get_website_info():

    for item in items:

        name, price, size = item()

        print(f'{name} : ${price} : size {size}')


if __name__ == '__main__':
    get_website_info()

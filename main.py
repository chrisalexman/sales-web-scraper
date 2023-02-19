#
# programmed by Chris, 02/17/2023
#

from bs4 import BeautifulSoup
import requests
import json


def get_toms_data():

    link = 'https://www.toms.com/us/men/shoes/sneakers/' \
           'black-on-black-heritage-canvas-mens-carlo-sneaker-topanga-collection/10012282.html'

    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    data_product = soup.find('div', {'data-product': True})['data-product']

    product_dict = json.loads(data_product)['product']

    name = product_dict['brand_name'] + ' ' + product_dict['name']

    shoe = product_dict['variants'][0]

    price = shoe['price']
    size = 10
    in_stock = shoe['in_stock']
    image_link = shoe['image_url']

    return name, price, size


def get_moongoat_data():

    link = 'https://moongoat.com/products/pocket-shop-t-shirt'

    name = 'name'
    price = 'price'
    size = 'size'

    return name, price, size


items = [get_toms_data, get_moongoat_data]

# scrape HTML from web pages, get price data and more
def get_website_info():

    for item in items:

        name, price, size = item()

        print(f'{name} : ${price} : size {size}')


if __name__ == '__main__':
    get_website_info()

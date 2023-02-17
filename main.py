#
# programmed by Chris, 02/16/2023
#

from bs4 import BeautifulSoup
import requests
import json


# scrape HTML from toms shoe web page, get price data
def get_website_info():
    toms_link = 'https://www.toms.com/us/men/shoes/sneakers/' \
                'black-on-black-heritage-canvas-mens-carlo-sneaker-topanga-collection/10012282.html'

    page = requests.get(toms_link)
    soup = BeautifulSoup(page.content, 'html.parser')

    product_data = soup.find(id='schemaData')
    product_dict = json.loads(product_data.text)

    price = product_dict['offers']['price']

    print(f'price: {price}, ({type(price)})')

    # print(soup.prettify())


if __name__ == '__main__':
    get_website_info()

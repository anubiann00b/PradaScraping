from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import time

chromedriver = "./chromedriver"
browser = webdriver.Chrome(executable_path = chromedriver)

def waitFor(condition_function):
    start_time = time.time()
    while time.time() < start_time + 3:
        if condition_function():
            return True
        else:
            time.sleep(0.1)
    raise Exception(
        'Timeout waiting for {}'.format(condition_function.__name__)
    )

def openPage(link):
    link.click()

    def isStale():
        try:
            # poll the link with an arbitrary call
            link.find_elements_by_id('doesnt-matter')
            return False
        except StaleElementReferenceException:
            return True

    waitFor(isStale)

def getDepartments():
    departments = []
    departments.append({'name':'Fashion Show',
                        'url':'http://www.prada.com/en/US/e-store/department/fashion-show.html',
                        'gender':'none'})
    departments.append({'name':'Travel',
                        'url':'http://www.prada.com/en/US/e-store/department/travel.html',
                        'gender':'none'})

    url = 'http://www.prada.com/en/US/e-store/collection/woman.html'
    gender = 'female'
    browser.get(url)
    departmentList = browser.find_element_by_id('enUSe-storecollectionwoman-top-menu')
    for departmentBullet in departmentList.find_elements_by_tag_name('li'):
        departmentElement = departmentBullet.find_element_by_tag_name('a')
        # "<span class="selector">_</span>" is in the innerHTML before the name
        departments.append({'name':departmentElement.get_attribute("innerHTML")[31:],
                            'url':departmentElement.get_attribute('href'),
                            'gender':gender})
    return departments

departments = getDepartments()


def getItems(department):
    items = []
    browser.get(department['url'])

    while True:  # sometimes the element doesn't load
        try:
            openPage(browser.find_element_by_class_name('nextItem')) # first item
        except NoSuchElementException:
            time.sleep(0.1)
            continue
        break
    while True:
        item = {}
        item['id'] = browser.find_element_by_class_name('product').find_element_by_class_name('title').find_element_by_tag_name('h1').text
        if len(items) != 0 and item['id'] == items[0]['id']:
            print department['name'] + ' done! ' + str(len(items)) + " items."
            break

        item['type'] = browser.find_element_by_class_name('nameProduct').text

        while 'price' not in item or item['price'] == '':
            item['price'] = browser.find_element_by_id('price_target').text  # TODO: format price ("$ 2,415")

        buyMessage = browser.find_element_by_class_name('addToCartButton').get_attribute('innerHTML')
        if buyMessage == '_add to shopping bag':
            item['available'] = 'Available'
        elif buyMessage == '_sold out':
            item['available'] = 'Sold Out'
        elif buyMessage == '_available soon':
            item['available'] = 'Coming Soon'
        else:
            item['available'] = 'Unknown'
            raise RuntimeError('Error: Unknown Availability: ' + buyMessage)

        images = []
        for imageHolder in browser.find_elements_by_class_name('als-item'):
            imageUrl = imageHolder.find_element_by_tag_name('img').get_attribute('src')
            images.append(imageUrl)
        item['images'] = images

        print item
        items.append(item)
        openPage(browser.find_element_by_id('nextButton'))

for department in departments:
    getItems(department)
print departments

browser.close()
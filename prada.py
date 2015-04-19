from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
import time

chromedriver = "./chromedriver"
browser = webdriver.Chrome(executable_path = chromedriver)
materials = ['silk', 'cotton', 'chiffon', 'satin', 'silt', 'wool', 'linen', 'cashmere', 'taffita', 'leather', 'mink', 'fur', 'suade', 'tweed', 'fleece', 'velvet', 'grogaine', 'corduroy', 'denim']

def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def waitFor(condition_function):
    start_time = time.time()
    while time.time() < start_time + 20:
        if condition_function():
            return True
        else:
            time.sleep(0.1)
    raise Exception(
        'Timeout waiting for ' + condition_function.__name__
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

def getDepartmentsFromCollection(url, gender, element):
    browser.get(url)
    departmentList = browser.find_element_by_id(element)
    collectionDepartments = []
    for departmentBullet in departmentList.find_elements_by_tag_name('li'):
        departmentElement = departmentBullet.find_element_by_tag_name('a')
        # "<span class="selector">_</span>" is in the innerHTML before the name
        collectionDepartments.append({'name':departmentElement.get_attribute("innerHTML")[31:].title(),
                                      'url':departmentElement.get_attribute('href'),
                                      'gender':gender})
    return collectionDepartments

def getDepartments():
    departments = []
    departments.append({'name':'Fashion Show',
                        'url':'http://www.prada.com/en/US/e-store/department/fashion-show.html',
                        'gender':'none'})
    departments.append({'name':'Travel',
                        'url':'http://www.prada.com/en/US/e-store/department/travel.html',
                        'gender':'none'})
    departments += getDepartmentsFromCollection('http://www.prada.com/en/US/e-store/collection/woman.html', 'female', 'enUSe-storecollectionwoman-top-menu')
    departments += getDepartmentsFromCollection('http://www.prada.com/en/US/e-store/collection/man.html', 'male', 'enUSe-storecollectionman-top-menu')
    departments.reverse()
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
        except WebDriverException:
            time.sleep(0.1)
            continue
        break
    while True:
        item = {}
        while item.get('id', '') == '':
            try:
                item['id'] = browser.find_element_by_class_name('product').find_element_by_class_name('title').find_element_by_tag_name('h1').text
            except NoSuchElementException:
                time.sleep(0.1)
                continue
        if len(items) != 0 and item['id'] == items[0]['id']:
            print department['name'] + ' done! ' + str(len(items)) + " items."
            break

        item['url'] = department['url']
        item['gender'] = department['gender']
        item['currency'] = 'USD'
        item['brand'] = 'Prada'

        availableSizes = []
        unavailableSizes = []
        if department['name'] == 'Footwear':
            sizeElements = []
            while len(sizeElements) == 0:
                sizeElements = browser.find_element_by_class_name('size_list').find_elements_by_tag_name('li')
            for sizeElement in sizeElements:
                size = sizeElement.find_element_by_tag_name('div').get_attribute('innerHTML')
                availability = sizeElement.get_attribute('class')
                if availability == 'available':
                    availableSizes.append(size)
                elif availability == 'unavailable':
                    unavailableSizes.append(size)
                else:
                    raise RuntimeError('Error: Unknown Size Availability: ' + availability + '\n' + department['url'])
            item['sizes'] = availableSizes
            item['unavailable'] = unavailableSizes


        item['category'] = browser.find_element_by_class_name('nameProduct').text

        while item.get('price', '') == '':
            item['price'] = browser.find_element_by_id('price_target').text
            for char in '$ ,': item['price'] = item['price'].replace(char, '');

        buyMessage = browser.find_element_by_class_name('addToCartButton').get_attribute('innerHTML')
        if buyMessage == '_add to shopping bag':
            item['available'] = 'Available'
        elif buyMessage == '_sold out':
            item['available'] = 'Sold Out'
        elif buyMessage == '_available soon':
            item['available'] = 'Coming Soon'
        else:
            item['available'] = 'Unknown'
            raise RuntimeError('Error: Unknown Availability: ' + buyMessage + '\n' + department['url'])

        images = []
        for imageHolder in browser.find_element_by_class_name('als-wrapper').find_elements_by_class_name('als-item'):
            imageUrl = imageHolder.find_element_by_tag_name('img').get_attribute('src')
            images.append(imageUrl)
        item['images'] = images

        # dimensions, department, sentences

        description = browser.find_element_by_class_name('description')
        dimensions = description.get_attribute('innerHTML')
        if '<br>' in dimensions:
            dimensions = dimensions[dimensions.index('<br>'):]
            position = dimensions.find('l. ')
            try:
                item['length'] = dimensions[position+3:dimensions.index('&nbsp;', position+3)]
            except ValueError:
                item['length'] = '-1'

            position = dimensions.find('w. ')
            try:
                item['width'] = dimensions[position+3:dimensions.index('&nbsp;', position+3)]
            except ValueError:
                item['width'] = '-1'
            position = dimensions.find('h. ')
            try:
                item['height'] = dimensions[position+3:dimensions.index('&nbsp;', position+3)]
            except ValueError:
                item['height'] = '-1'

            if not isNumber(item['length']):
                item['length'] = -1
            if not isNumber(item['width']):
                item['width'] = -1
            if not isNumber(item['height']):
                item['height'] = -1

        item['description'] = description.find_element_by_tag_name('p').get_attribute('innerHTML').split('<br><br>')

        try:
            item['colors'] = browser.find_element_by_class_name('color').find_element_by_tag_name('span').get_attribute('innerHTML').split('+')
        except NoSuchElementException:
            pass

        print item
        items.append(item)
        openPage(browser.find_element_by_id('nextButton'))

for department in departments:
    getItems(department)

browser.close()
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
import time

chromedriver = "./chromedriver"
browser = webdriver.Chrome(executable_path = chromedriver)
materials = ['silk', 'cotton', 'chiffon', 'satin', 'silt', 'wool', 'linen', 'cashmere', 'taffita', 'leather', 'mink', 'fur', 'suade', 'tweed', 'fleece', 'velvet', 'grogaine', 'corduroy', 'denim']

friendlyName = { 'backpack': 'backpack', 'trolley': 'suitcase', 'thong': 'flip flop', 'ballerina': 'flat',
                'driver': 'moccasin', 'top handle': 'handbag', 'shoulder bag': 'purse' }

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
    raise Exception('Timeout waiting for ' + condition_function.__name__)

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
        departmentName = departmentElement.get_attribute("innerHTML")[31:].title()
        if departmentName == "Fragrances":
            continue
        collectionDepartments.append({'name':departmentName,
                                      'url':departmentElement.get_attribute('href'),
                                      'gender':gender})
    return collectionDepartments

def getDepartments():
    departments = []
    departments.append({'name':'Fashion Show',
                        'url':'http://www.prada.com/en/US/e-store/department/fashion-show.html',
                        'gender':'women'})
    departments.append({'name':'Travel',
                        'url':'http://www.prada.com/en/US/e-store/department/travel.html',
                        'gender':'men'})
    departments += getDepartmentsFromCollection('http://www.prada.com/en/US/e-store/collection/woman.html', 'women', 'enUSe-storecollectionwoman-top-menu')
    departments += getDepartmentsFromCollection('http://www.prada.com/en/US/e-store/collection/man.html', 'men', 'enUSe-storecollectionman-top-menu')
    return departments

departments = getDepartments()


def getItems(department):
    items = {}
    browser.get(department['url'])

    while True:  # sometimes the element doesn't load
        try:
            openPage(browser.find_element_by_class_name('nextItem'))  # first item
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
            if len(items) == 0:
                firstItemId = item['id']
        if len(items) != 0 and item['id'] == firstItemId:
            print department['name'] + ' done! ' + str(len(items)) + " items."
            return items
        duplicate = False
        for alternateColorDiv in browser.find_element_by_class_name('container').find_element_by_class_name('colors').find_elements_by_tag_name('div'):
            try:
                alternateColorId = alternateColorDiv.get_attribute('id')[5:]  # colorBN2899_2E14_F0J4L
            except StaleElementReferenceException:  # Sometimes a false alternate loads and then disappears
                continue
            if alternateColorId in items:
                duplicate = True
                existingItem = items[alternateColorId]

                images = []
                for imageHolder in browser.find_element_by_class_name('als-wrapper').find_elements_by_class_name('als-item'):
                    imageUrl = imageHolder.find_element_by_tag_name('img').get_attribute('src')
                    images.append(imageUrl)
                try:
                    colorName = browser.find_element_by_class_name('color').find_element_by_tag_name('span').get_attribute('innerHTML')
                    existingItem['images'] += images  # HERE
                    existingItem['colors'].append({'name':colorName,
                                           'color_family':'',
                                           'images':images})
                    print 'Added color ' + colorName + ' to item ' + existingItem['id']
                    print existingItem
                except NoSuchElementException:
                    pass
        if duplicate:
            openPage(browser.find_element_by_id('nextButton'))
            continue

        item['url'] = browser.current_url
        item['gender'] = department['gender']
        item['currency'] = 'USD'
        item['brand'] = 'prada'

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

        item['category'] = friendlyName.get(browser.find_element_by_class_name('nameProduct').text,
                                            browser.find_element_by_class_name('nameProduct').text)

        itemPrice = ''
        while itemPrice == '':  # Price is loaded dynamically -_-
            # Default formatting: "$ 2,915"
            itemPrice = browser.find_element_by_id('price_target').text
            for char in '$ ,': itemPrice = itemPrice.replace(char, '')
            if itemPrice != '':
                item['price'] = float(itemPrice)
            else:
                time.sleep(0.05)

        buyMessage = browser.find_element_by_class_name('addToCartButton').get_attribute('innerHTML')
        if buyMessage == '_add to shopping bag':
            item['available'] = True
        elif buyMessage == '_sold out':
            item['available'] = True
        elif buyMessage == '_available soon':
            item['available'] = False
        else:
            item['available'] = 'Unknown'
            raise RuntimeError('Error: Unknown Availability: ' + buyMessage + '\n' + department['url'])

        images = []
        for imageHolder in browser.find_element_by_class_name('als-wrapper').find_elements_by_class_name('als-item'):
            imageUrl = imageHolder.find_element_by_tag_name('img').get_attribute('src')
            images.append(imageUrl)

        item['images'] = list(images)

        item['colors'] = []
        try:
            item['colors'].append({'name':browser.find_element_by_class_name('color').find_element_by_tag_name('span').get_attribute('innerHTML'),
                                   'color_family':'',
                                   'images':images})
        except NoSuchElementException:
            pass

        description = browser.find_element_by_class_name('description')
        dimensions = description.get_attribute('innerHTML')
        length = ''
        width = ''
        height = ''
        if '<br>' in dimensions:
            dimensions = dimensions[dimensions.index('<br>'):]
            position = dimensions.find('l. ')
            try:
                length = dimensions[position+3:dimensions.index('&nbsp;', position+3)]
            except: pass

            position = dimensions.find('w. ')
            try:
                width = dimensions[position+3:dimensions.index('&nbsp;', position+3)]
            except: pass
            position = dimensions.find('h. ')
            try:
                height = dimensions[position+3:dimensions.index('&nbsp;', position+3)]
            except: pass

            if not isNumber(length):
                length = ''
            if not isNumber(width):
                width = ''
            if not isNumber(height):
                height = ''
        item['size'] = length + 'x' + width + 'x' + height

        descriptionString = description.find_element_by_tag_name('p').get_attribute('innerHTML').replace('<br><br>', '\n')
        try:
            firstItemIndex = descriptionString.index('\n')
            item['name'] = descriptionString[:firstItemIndex]
            item['description'] = descriptionString[firstItemIndex+1:]
        except ValueError:
            item['name'] = descriptionString
            item['description'] = ''

        print item
        items[item['id']] = item
        openPage(browser.find_element_by_id('nextButton'))

allItems = {}
for department in departments:
    allItems.update(getItems(department))

print '\n\n'
print allItems
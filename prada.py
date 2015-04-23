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

# Waits for a function to return true. Used for dynamic loading.
def waitFor(condition_function):
    start_time = time.time()
    while time.time() < start_time + 5:
        if condition_function():
            return True
        else:
            time.sleep(0.1)
    raise Exception('Timeout waiting for ' + condition_function.__name__)

# Opens a page and waits for it to load
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

# Gets a list of departments within a collection (men, women)
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

# Gets a list of departments (footwear, handbags, etc)
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

# Gets a list of items within a department
def getShoeSizes():
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
        return {'sizes': availableSizes, 'unavailable': unavailableSizes }
    return {}


def getPrice():
    while True:  # Price is loaded dynamically -_-
        # Default formatting: "$ 2,915"
        try:
            itemPrice = browser.find_element_by_id('price_target').text
        except StaleElementReferenceException:
            time.sleep(0.05)
            continue
        for char in '$ ,': itemPrice = itemPrice.replace(char, '')
        if itemPrice == '':
            time.sleep(0.05)
        else:
            return float(itemPrice)


def getAvailability():
    buyMessage = browser.find_element_by_class_name('addToCartButton').get_attribute('innerHTML')
    if buyMessage == '_add to shopping bag':
        return True
    elif buyMessage == '_sold out':
        return False
    elif buyMessage == '_available soon':
        return False
    else:
        return False

def getImages():
    while True:
        try:
            images = []
            for imageHolder in browser.find_element_by_class_name('als-wrapper').find_elements_by_class_name('als-item'):
                imageUrl = imageHolder.find_element_by_tag_name('img').get_attribute('src')
                images.append(imageUrl)
            return images
        except StaleElementReferenceException or NoSuchElementException:
            time.sleep(0.05)

# Gets description, name, and size
def getDescription():
    item = {}
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
        item['name'] = descriptionString[:firstItemIndex].title()
        item['description'] = descriptionString[firstItemIndex+1:]
    except ValueError:
        item['name'] = descriptionString
        item['description'] = ''
    return item

def getItems(department):
    visitedIds = []
    items = {}
    browser.get(department['url'])

    # Open the page of the first item
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

    # Get all the items
    while True:
        currentItem = {}
        currentItemId = ''
        # Get the id
        while currentItemId == '':
            try:
                currentItemId = browser.find_element_by_class_name('product').find_element_by_class_name('title').find_element_by_tag_name('h1').text
            except NoSuchElementException as e:
                time.sleep(0.1)
                continue
            if len(items) == 0:
                firstItemId = currentItemId
        # Check if we're done with the department
        if len(items) != 0 and currentItemId == firstItemId:
            print department['name'] + ' done! ' + str(len(items)) + " items."
            for item in items:
                print items[item]
            return items

        # If this was a duplicate item, just go to the next one. We already added it as a duplicate color.
        if currentItemId in items or currentItemId in visitedIds:
            while True:
                try:
                    openPage(browser.find_element_by_id('nextButton'))
                except WebDriverException:
                    time.sleep(0.05)
                    continue
                break
            continue
        print 'Starting ' + currentItemId

        currentItem['url'] = browser.current_url
        currentItem['gender'] = department['gender']
        currentItem['currency'] = 'USD'
        currentItem['brand'] = 'prada'
        currentItem['store'] = 'prada'

        currentItem.update(getShoeSizes())

        currentItem['category'] = friendlyName.get(browser.find_element_by_class_name('nameProduct').text,
                                            browser.find_element_by_class_name('nameProduct').text)

        currentItem['price'] = getPrice()
        currentItem['available'] = getAvailability()

        images = getImages()
        currentItem['images'] = list(images)  # Copy the list so we're not referencing the same element in the color

        currentItem['colors'] = []
        try:
            currentItem['colors'].append({'name':browser.find_element_by_class_name('color').find_element_by_tag_name('span').get_attribute('innerHTML'),
                                   'color_family':'',
                                   'images':images})
        except NoSuchElementException:
            pass

        currentItem.update(getDescription())  # Name, description, size

        # If we already indexed an item which this item is a duplicate of, then this is the same product in a different color.
        counter = 0
        while True:
            time.sleep(0.1)
            try:
                alternateColorDiv = browser.find_element_by_class_name('container').find_element_by_class_name('colors').find_elements_by_tag_name('div')[counter]
            except IndexError:
                break
            except NoSuchElementException:
                time.sleep(0.05)
                continue
            except StaleElementReferenceException:
                continue
            try:
                openPage(alternateColorDiv.find_element_by_tag_name('a'))
            except WebDriverException:
                continue
            except Exception:
                continue

            images = getImages()

            alternateColorId = ''
            # Get the id
            while alternateColorId == '':
                try:
                    alternateColorId = browser.find_element_by_class_name('product').find_element_by_class_name('title').find_element_by_tag_name('h1').text
                except NoSuchElementException as e:
                    time.sleep(0.1)
                    continue
            if alternateColorId in visitedIds:
                counter += 1
                continue
            visitedIds.append(alternateColorId)

            try:
                colorName = browser.find_element_by_class_name('color').find_element_by_tag_name('span').get_attribute('innerHTML')
                currentItem['images'] += images
                currentItem['colors'].append({'name':colorName,
                                       'color_family':'',
                                       'images':images})
                print '  Added ' + alternateColorId + ' to ' + currentItemId
            except NoSuchElementException as e:
                pass
            browser.back()
            counter += 1

        print 'Finished with ' + currentItemId
        items[currentItemId] = currentItem
        openPage(browser.find_element_by_id('nextButton'))

allItems = {}
for department in departments:
    allItems.update(getItems(department))

print '\n\n'
print allItems
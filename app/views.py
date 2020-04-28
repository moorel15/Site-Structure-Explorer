import json
import robotparser
from app import app
from flask import render_template, redirect, request, send_file
from .web_forms import MapURLForm, getImageForm
from urllib2 import urlopen, URLError
from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urlparse import urlsplit
import time
from anytree import Node
from anytree.exporter import DotExporter, JsonExporter


# declare global variables used by all functions and passed back to the user.
notfoundCounter = 0
finalQueue = []
JsonTreeStructure = {}
minutes = 0
pagesPerMinute = 0
delay = 0
current = ""
treeStructure = {}


# app route for the generate pages - calls all functions needed to scrape site.
@app.route('/', methods=['GET', 'POST'])
def index():
    form = MapURLForm()
    if form.validate_on_submit():
        URL = form.URL.data
        data = getRobotTxt(URL)
        delay = data[0]
        disallowed = data[1]
        scrapeLimit = 0
        choice = request.form['options']
        if choice == "shallow":
            scrapeLimit = 50
        elif choice == "medium":
            scrapeLimit = 150
        elif choice == "deep":
            scrapeLimit = 300
        elif choice == "custom":
            scrapeLimit = int(request.form['iterations'])
        buildTree(("https://" + URL), delay, disallowed, scrapeLimit)
        return redirect('/result')
    return render_template('generate.html', form=form)


# return the JSON queue
@app.route('/getJSON', methods=['GET', 'POST'])
def getJSON():
    return JsonTreeStructure


# return the finalQueue on AJAX request.
@app.route('/getLinks', methods=['GET', 'POST'])
def getLinks():
    return json.dumps(finalQueue)


# return the stats on request from AJAX.
@app.route('/getStats', methods=['GET', 'POST'])
def getStats():
    data = {"minutes": str(round(minutes, 2)), "pagesPerMinute": str(round(pagesPerMinute)), "titleNotFound": str(notfoundCounter),
            "pagesFound": str(len(finalQueue)), "delay": str(delay / 1000)}
    return json.dumps(data)


# app route for the results page
@app.route('/result', methods=['GET', 'POST'])
def result():
    form = getImageForm()
    if form.validate_on_submit():
        # get the first occurance of the page to ensure fullest possible image
        try:
            # convert title to node name and generate the image.
            if "Title Not Found" in form.node.data:
                input = form.node.data.strip()
            else:
                input = form.node.data.strip() + "0"
            generateImage(input, treeStructure)
        except KeyError as e:
            print e
        try:
            # return image
            return send_file('root.png', as_attachment=True, attachment_filename=(input + '.png'))
        except Exception as e:
            return str(e)
    return render_template('result.html', form=form)


@app.route('/notAccessed', methods=['GET', 'POST'])
def notAccessed():
    return render_template('error.html')

def getRobotTxt(URL):
    # access the robots.text file and get the data requred to scrape
    lines = []
    disallowed = []
    allowed = []
    length = len(URL)
    global delay
    delay = 0
    robots = 'https://' + URL[4:length] + '/robots.txt'
    try:
        # parse file to find data.
        contents = urlopen(robots)
        for i in contents:
            lines.append(i)
        for i in lines:
            if "User-agent: *" in i:
                index = lines.index(i)
                for j in startLoop(lines, (index + 1)):
                    if "User-agent: " in j:
                        break
                    elif not isLineEmpty(j):
                        if "Allow: " in j:
                            allowed.append(j[7:len(j)])
                        elif "Crawl-delay: " in j:
                            delay = j[13:len(j)]
            break
    # if cant find file in url then set values to be default
    except Exception as e:
        print e
    if delay == 0:
        global delay
        delay = 2000
    returnTuple = (delay, allowed)
    return returnTuple


# function called to build the tree.
def buildTree(startUrl, delay, disallowed, scrapeLimit):
    # set default values.
    global notfoundCounter
    notfoundCounter = 0
    start = time.time()
    scrapingQueue = []
    scraped = []
    local = []
    otherSites = []
    titles = []
    pages = 0
    i = 0
    # Begin scraping on URL inputted by the user. Then loop for consequent links
    # discovered until page count = scrapelimit or full site.
    parent = "root"
    pages += 1
    print scrapeLimit
    # iterate over the queue and collect the nodes from the pages if the page is allowed and if it
    # hasnt already been scraped to maintain tree - structure.
    collectNodes(startUrl, scrapingQueue, local, otherSites, parent, titles)
    while i < len(scrapingQueue):
        urlAlreadyScraped = False
        if pages == scrapeLimit:
            break
        url = scrapingQueue[i][2]
        parent = scrapingQueue[i][1]
        for page in scraped:
            if str(url) == str(page):
                urlAlreadyScraped = True
                break
        if not urlAlreadyScraped:
            if not checkUrlBanned(url, disallowed):
                time.sleep(delay / 1000)
                collectNodes(url, scrapingQueue, local, otherSites, parent, titles)
                scraped.append(url)
                pages += 1
        i += 1
        print pages
    # once queue or list is created - build structure in any tree - clean up links queue.
    # get time taken and build output queues.
    global treeStructure
    treeStructure = createStructure(scrapingQueue)
    cleanUpQueue(scrapingQueue)
    end = time.time()
    global minutes
    minutes = (end - start) / 60
    global pagesPerMinute
    pagesPerMinute = len(scrapingQueue) / minutes
    global finalQueue
    finalQueue = buildJSONQueue(scrapingQueue)
    return finalQueue


# build a JSON transferable queue from scraping queue.
def buildJSONQueue(scrapingQueue):
    jsonQueue = []
    for i in scrapingQueue:
        json = {"name": i[1], "parent": i[0], "link": i[2]}
        jsonQueue.append(json)
    return jsonQueue


# function to collect nodes from page.
def collectNodes(url, scrapingQueue, local, otherSites, parent, titles):
    # get response from page
    # create soup object to get data from
    try:
        resp = requests.get(url)
    except(requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL,
           requests.exceptions.InvalidSchema):
        return

    linksplit = urlsplit(url)
    # split into different parts of url to check if parts are missing to form full url
    root = "{0.netloc}".format(linksplit)
    root = root.replace("www.", "")
    siteRoot = "{0.scheme}://{0.netloc}".format(linksplit)
    try:
        soupObj = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print e
        return
    # loop through links on the pages, get title, create link of pages with parents and links. add the local pages to
    # entire queue.
    for link in soupObj.findAll('a'):
        a = link.attrs["href"] if "href" in link.attrs else ""
        try:
            title = (link.string[:50] + '...') if len(link.string) > 50 else link.string
            title = ' '.join(title.split())
            found = 0
            for i in titles:
                if i == title:
                    found += 1
            titles.append(title)
            title = title + str(found)
        except TypeError:
            title = ""
        if a.startswith('/'):
            newLink = siteRoot + a
            if title == "":
                title = generateTitle()
            local.append(tuple((title, newLink)))
        elif root in a:
            if title == "":
                title = generateTitle()
            local.append(tuple((title, a)))
        elif not a.startswith('http'):
            if title == "":
                title = generateTitle()
            local.append(tuple((title, a)))
        else:
            otherSites.append(a)
    for i in local:
        scrapingQueue.append(tuple((parent, i[0], i[1])))
    del local[:]


# check if url appears in the disallowed pages.
def checkUrlBanned(url, disallowed):
    for i in disallowed:
        if "*" in i:
            path = i.replace('*', '')
            if path in url:
                return True
        elif i in url:
            return True
    return False


# clean up queue, if no link is present then remove from the queue.
def cleanUpQueue(scrapingQueue):
    for i in scrapingQueue:
        if i[2] == "":
            index = scrapingQueue.index(i)
            del scrapingQueue[index]


# create the tree structure based on the scraping queue
def createStructure(scrapingQueue):
    nodes = {}
    root = Node('root')
    nodes['root'] = root
    for page in scrapingQueue:
        parent = page[0].encode('ascii', 'ignore').decode('ascii')
        title = page[1].encode('ascii', 'ignore').decode('ascii')
        nodes[title] = Node(title, parent=nodes[parent])
    global JsonTreeStructure
    JsonTreeStructure = JsonExporter().export(root)
    return nodes


# generate an image from the nodes created.
def generateImage(request, nodes):
    node = nodes[request]
    DotExporter(node, maxlevel=2).to_picture("root.png")


# generate title of pages which could not be created
def generateTitle():
    global notfoundCounter
    notfoundCounter += 1
    title = "Title Not Found - " + str(notfoundCounter)
    return title


# begin a loop from a start point - own loop start function
def startLoop(list, index):
    for i in range(index, len(list)):
        yield list[i]
    for i in range(index):
        yield list[i]


# check if a line is empty
def isLineEmpty(line):
    return len(line.strip()) < 1

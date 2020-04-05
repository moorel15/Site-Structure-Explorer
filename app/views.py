import json

from app import app
from flask import render_template, redirect
from .web_forms import MapURLForm
from urllib2 import urlopen
from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urlparse import urlsplit
import time
from anytree import Node, RenderTree
from anytree.exporter import DotExporter, JsonExporter

notfoundCounter = 0
finalQueue = []
JsonTreeStructure = {}
minutes = 0
pagesPerMinute = 0
delay = 0


@app.route('/', methods=['GET', 'POST'])
def index():
    form = MapURLForm()
    if form.validate_on_submit():
        URL = form.URL.data
        info = getRobotTxt(URL)
        delay = info[0]
        disallowed = info[1]
        allowed = info[2]
        buildTree(("https://" + URL), delay, disallowed)
        return redirect('/result')
    return render_template('generate.html', form=form)


@app.route('/getJSON', methods=['GET', 'POST'])
def getJSON():
    return JsonTreeStructure


@app.route('/getLinks', methods=['GET', 'POST'])
def getLinks():
    return json.dumps(finalQueue)


@app.route('/getStats', methods=['GET', 'POST'])
def getStats():
    data = {"minutes": str(minutes), "pagesPerMinute": str(pagesPerMinute), "titleNotFound": str(notfoundCounter), "pagesFound": str(len(finalQueue)), "delay": str(delay/1000)}
    return json.dumps(data)


@app.route('/result', methods=['GET', 'POST'])
def result():
    return render_template('result.html')


def getRobotTxt(URL):
    lines = []
    disallowed = []
    allowed = []
    length = len(URL)
    global delay
    delay = 0
    robots = 'https://' + URL[4:length] + '/robots.txt'
    try:
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
                        if "Disallow: " in j:
                            disallowed.append(j[10:len(j)])
                        elif "Allow: " in j:
                            allowed.append(j[7:len(j)])
                        elif "Crawl-delay: " in j:
                            delay = j[13:len(j)]
    except Exception:
        print("Error encountered: Unable to establish link to robot.txt file resorting to default values")
    if delay == 0:
        global delay
        delay = 2000
    returnTuple = (delay, disallowed, allowed)
    return returnTuple


def buildJSONQueue(scrapingQueue):
    jsonQueue = []
    for i in scrapingQueue:
        json = {"name": i[1], "parent": i[0], "link": i[2]}
        jsonQueue.append(json)
    return jsonQueue


def buildTree(startUrl, delay, disallowed):
    start = time.time()
    scrapingQueue = []
    scraped = []
    local = []
    otherSites = []
    titles = []
    pages = 0
    i = 0
    scrapeLimit = 40
    # Begin scraping on URL inputted by the user. Then loop for consequent links
    # discovered until page count = scrapelimit.
    parent = "root"
    collectNodes(startUrl, scrapingQueue, local, otherSites, parent, pages, titles)
    pages += 1
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
                collectNodes(url, scrapingQueue, local, otherSites, parent, pages, titles)
                scraped.append(url)
                pages += 1
        i += 1
    createStructure(scrapingQueue)
    cleanUpQueue(scrapingQueue)
    end = time.time()
    global minutes
    minutes = (end - start) / 60
    global pagesPerMinute
    pagesPerMinute = len(scrapingQueue) / minutes
    global finalQueue
    finalQueue = buildJSONQueue(scrapingQueue)
    return finalQueue


def collectNodes(url, scrapingQueue, local, otherSites, parent, pages, titles):
    print pages
    try:
        resp = requests.get(url)
    except(requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL,
           requests.exceptions.InvalidSchema):
        return
    linksplit = urlsplit(url)
    root = "{0.netloc}".format(linksplit)
    root = root.replace("www.", "")
    siteRoot = "{0.scheme}://{0.netloc}".format(linksplit)
    path = url[:url.rfind('/') + 1] if '/' in linksplit.path else url
    soupObj = BeautifulSoup(resp.text, "html.parser")
    found = 0
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
                title = generateTitle(newLink, titles)
            local.append(tuple((title, newLink)))
        elif root in a:
            if title == "":
                title = generateTitle(a, titles)
            local.append(tuple((title, a)))
        elif not a.startswith('http'):
            if title == "":
                title = generateTitle(a, titles)
            local.append(tuple((title, a)))
        else:
            otherSites.append(a)
    for i in local:
        scrapingQueue.append(tuple((parent, i[0], i[1])))
    del local[:]


def checkUrlBanned(url, disallowed):
    for i in disallowed:
        if "*" in i:
            path = i.replace('*', '')
            if path in url:
                return True
        elif i in url:
            return True
    return False


def cleanUpQueue(scrapingQueue):
    for i in scrapingQueue:
        if i[2] == "":
            index = scrapingQueue.index(i)
            del scrapingQueue[index]
        for j in scrapingQueue:
            if i[2] == j[2]:
                index =scrapingQueue.index(j)
                del scrapingQueue[index]


def createStructure(scrapingQueue):
    nodes = {}
    root = Node('root')
    nodes['root'] = root
    for page in scrapingQueue:
        parent = page[0].encode('ascii', 'ignore').decode('ascii')
        title = page[1].encode('ascii', 'ignore').decode('ascii')
        nodes[title] = Node(title, parent=nodes[parent])
    # print the final structure
    print("\n\n\nPrinting tree...")
    for pre, fill, node in RenderTree(root):
        name = node.name
        print("%s%s" % (pre, name))
    # create image
    DotExporter(root,
                nodeattrfunc=lambda node: "fixedsize=true, height=2, width=2, shape=diamond",
                edgeattrfunc=lambda parent, child: "style=bold"
                ).to_picture("root.png")
    #create JSON
    global JsonTreeStructure
    JsonTreeStructure = JsonExporter().export(root)


def generateTitle(url, titles):
    global notfoundCounter
    notfoundCounter += 1
    title = "Title Not Found - " + str(notfoundCounter)
    return title


def startLoop(list, index):
    for i in range(index, len(list)):
        yield list[i]
    for i in range(index):
        yield list[i]


def isLineEmpty(line):
    return len(line.strip()) < 1

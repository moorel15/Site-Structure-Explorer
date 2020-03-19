from app import app
from flask import render_template, flash
from .web_forms import MapURLForm
from urllib2 import urlopen
from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urlparse import urlparse, urlsplit
import mechanize
import time
from anytree import Node, RenderTree
from anytree.exporter import DotExporter

notfoundCounter = 0


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
    return render_template('generate.html', form=form)


@app.route('/result', methods=['GET', 'POST'])
def result():
    return render_template('result.html')


def getRobotTxt(URL):
    lines = []
    disallowed = []
    allowed = []
    delay = 0
    length = len(URL)
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
        delay = 2000
    returnTuple = (delay, disallowed, allowed)
    return returnTuple


def buildTree(startUrl, delay, disallowed):
    start = time.time()
    scrapingQueue = []
    scraped = []
    local = []
    otherSites = []
    pages = 0
    i = 0
    scrapeLimit = 5
    # Begin scraping on URL inputted by the user. Then loop for consequent links discovered until page count = 100.
    parent = "root"
    collectNodes(startUrl, scrapingQueue, local, otherSites, parent)
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
                time.sleep(delay/1000)
                collectNodes(url, scrapingQueue, local, otherSites, parent)
                scraped.append(url)
                pages += 1
        i += 1
    print "Cleaning up the queue..."
    cleanUpQueue(scrapingQueue)
    createStructure(scrapingQueue)
    print "\nResults after " + str(pages) + " pages scraped:\n"
    print "Number of pages scraped on site: " + str(len(scrapingQueue))
    end = time.time()
    minutes = (end-start)/60
    print "Time elapsed: " + str(minutes) + "m"


def collectNodes(url, scrapingQueue, local, otherSites, parent):
    try:
        resp = requests.get(url)
    except(requests.exceptions.MissingSchema, requests.exceptions.ConnectionError, requests.exceptions.InvalidURL,
           requests.exceptions.InvalidSchema):
        print "Error scraping: " + str(url)
        return
    linksplit = urlsplit(url)
    root = "{0.netloc}".format(linksplit)
    root = root.replace("www.", "")
    siteRoot = "{0.scheme}://{0.netloc}".format(linksplit)
    path = url[:url.rfind('/')+1] if '/' in linksplit.path else url
    soupObj = BeautifulSoup(resp.text, "html.parser")
    parent = parent
    print("URL: " + url + ", Pages found: " + str(len(soupObj.findAll('a'))))

    for link in soupObj.findAll('a'):
        a = link.attrs["href"] if "href" in link.attrs else ""
        try:
            title = (link.string[:50] + '...') if len(link.string) > 50 else link.string
            title = ' '.join(title.split())
        except TypeError:
            title = ""
        if a.startswith('/'):
            newLink = siteRoot + a
            if title == "":
                title = generateTitle(newLink)
            local.append(tuple((title, newLink)))
        elif root in a:
            if title == "":
                title = generateTitle(a)
            local.append(tuple((title, a)))
        elif not a.startswith('http'):
            if title == "":
                title = generateTitle(a)
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
    #create image
    DotExporter(root,
                nodeattrfunc=lambda node: "shape=diamond",
                edgeattrfunc=lambda parent, child: "style=bold"
                ).to_picture("root.png")

def generateTitle(url):
    try:
        browser = mechanize.Browser()
        browser.open(url)
        title = browser.title()
    except Exception:
        global notfoundCounter
        notfoundCounter += 1
        title = "Link of non text type - " + str(notfoundCounter)
    return title


def startLoop(list, index):
    for i in range(index, len(list)):
        yield list[i]
    for i in range(index):
        yield list[i]


def isLineEmpty(line):
    return len(line.strip()) < 1

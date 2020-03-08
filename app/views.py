from app import app
from flask import render_template, flash
from .web_forms import MapURLForm
from urllib2 import urlopen
from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urlparse import urlparse, urlsplit
import time
from anytree import Node, RenderTree


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
    scrapingQueue = []
    scraped = []
    local = []
    otherSites = []
    pages = 0
    i = 0
    collectNodes(startUrl, scrapingQueue, local, otherSites)
    while len(scrapingQueue):
        urlAlreadyScraped = False
        if pages == 100:
            break
        url = scrapingQueue[i][1]
        for page in scraped:
            if url == page:
                print "here"
                urlAlreadyScraped = True
                break
        if not urlAlreadyScraped:
            if not checkUrlBanned(url, disallowed):
                time.sleep(delay/1000)
                collectNodes(url, scrapingQueue, local, otherSites)
                scraped.append(url)
                pages += 1
        i += 1
    print "Results after 100 pages scraped:\n\n"
    print str(len(scrapingQueue))


def collectNodes(url, scrapingQueue, local, otherSites):
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
    newLink = ""
    try:
        parent = soupObj.title.string
    except(AttributeError):
        parent = "No Parent Title Found"
    print("Pages found: " + str(len(soupObj.findAll('a'))))
    for link in soupObj.findAll('a'):
        a = link.attrs["href"] if "href" in link.attrs else ''
        if a.startswith('/'):
            newLink = siteRoot + a
            local.append(newLink)
        elif root in a:
            local.append(a)
        elif not a.startswith('http'):
            newLink = path + a
            local.append(newLink)
        else:
            otherSites.append(a)

    for i in local:
        scrapingQueue.append(tuple((parent, i)))


def checkUrlBanned(url, disallowed):
    for i in disallowed:
        if "*" in i:
            path = i.replace('*', '')
            if path in url:
                return True
        elif i in url:
            return True
    return False


def startLoop(list, index):
    for i in range(index, len(list)):
        yield list[i]
    for i in range(index):
        yield list[i]


def isLineEmpty(line):
    return len(line.strip()) < 1

from app import app
from flask import render_template, flash
from .web_forms import MapURLForm
from urllib2 import urlopen, URLError, HTTPError
from bs4 import BeautifulSoup
import re
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
    if delay == 0:
        delay = 2000
    returnTuple = (delay, disallowed, allowed)
    return returnTuple


def buildTree(startUrl, delay, disallowed):
    scrapingQueue = []
    collectNodes(startUrl, scrapingQueue, disallowed, startUrl)
    pagesScraped = 1
    for link in scrapingQueue:
        if pagesScraped == 100:
            print("Finished Scraping, size of tree will consist of " + str(len(scrapingQueue)) + " nodes.")
            break
        time.sleep(int(delay)/1000)
        collectNodes(str(link[1]), scrapingQueue, disallowed, startUrl)
        pagesScraped += 1
        print("Pages scraped: " + str(pagesScraped) + ", Size of scraping queue: " + str(len(scrapingQueue)))
        duplicates = []
        for elem in scrapingQueue:
            if scrapingQueue.count(elem[1]) > 1:
                duplicates.append(elem)
    for i in scrapingQueue:
        print i


def collectNodes(url, scrapingQueue, disallowed, startUrl):
    try:
        print("here")
        soupObj = BeautifulSoup(urlopen(url), features="html.parser")
        title = soupObj.title.string
    except (URLError, HTTPError, AttributeError) as e:
        if e == URLError:
            print("Error for link: " + url + "\n Error Reason: " + str(e.reason))
        if e == HTTPError:
            print("Error for link: " + url + "\n Error Reason: " + str(e.code))
        if e == AttributeError:
            print("No title for page")
            title = "No Valid Title"
        return
    errorFound = False
    for link in soupObj.findAll('a', attrs={'href': re.compile("^https://")}):
        linkString = link.get('href')
        i = 0
        for elem in scrapingQueue:
            if linkString in scrapingQueue[i][1]:
                errorFound = True
                break
            i += 1
        for na in disallowed:
            if na in linkString:
                errorFound = True
        if not errorFound:
            scrapingQueue.append(tuple((title, linkString)))
    print(errorFound)


def startLoop(list, index):
    for i in range(index, len(list)):
        yield list[i]
    for i in range(index):
        yield list[i]


def isLineEmpty(line):
    return len(line.strip()) < 1
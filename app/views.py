from app import app
from flask import render_template, flash
from .web_forms import MapURLForm
from urllib2 import urlopen
from bs4 import BeautifulSoup
import re
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
        print("Delay: " + str(delay))
        print("Disallowed size: " + str(len(disallowed)))
        print("Allowed size: " + str(len(allowed)))
        buildTree(("https://" + URL), delay, disallowed, allowed)
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
        delay = 3000
    returnTuple = (delay, disallowed, allowed)
    return returnTuple


def buildTree(URL, delay, disallowed, allowed):
    scrapingQueue = []
    htmlSoupObj = BeautifulSoup(urlopen(URL), 'html.parser')
    title = htmlSoupObj.find_all('title')
    for link in htmlSoupObj.find_all('a', attrs={'href': re.compile("^https://")}):
        print(link.get('href'))


def startLoop(list, index):
    for i in range(index, len(list)):
        yield list[i]
    for i in range(index):
        yield list[i]


def isLineEmpty(line):
    return len(line.strip()) < 1
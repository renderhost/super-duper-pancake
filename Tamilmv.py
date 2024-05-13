import requests
from bs4 import BeautifulSoup
import torrent_parser as tp
import xml.etree.ElementTree as ET
from datetime import datetime 
import itertools
from time import sleep
import concurrent.futures
import pickle
import schedule
from flask import Flask, send_file
import os




# Save a list to a file
def save_list_to_file(list_to_save):
    with open('rssList', 'wb') as f:
        pickle.dump(list_to_save, f)

# Load a list from a file
def load_list_from_file():
    with open('rssList', 'rb') as f:
        return pickle.load(f)

def get_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    # cPost_contentWrap = soup.find('div', class_='cPost_contentWrap')
    a_tags = soup.find_all('a', href=lambda href: href and 'attachment.php' in href)
    return a_tags

def get_torrent_size(torrent_file_path):
    data = tp.parse_torrent_file(torrent_file_path)
    if 'files' in data['info']:
        size = sum(file['length'] for file in data['info']['files'])
    else:
        size = data['info']['length']
    return size

def get_links_with_delay(link):
    result = get_links(link)
    sleep(3)  # Introduce a delay of 5 seconds between each request
    return result

def scrape(links):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map tasks for each link to get_links_with_delay function
        results = executor.map(get_links_with_delay, itertools.islice(links, 30))
        # Iterate over completed tasks
        for result in results:
            # Yield results from each completed task
            for a in result:
                yield a.text, a['href']
    del links


def build_xml(data,channel):
    now = datetime.now()
    for x in data:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = x[0]
        ET.SubElement(item, 'link').text = x[1]
        # ET.SubElement(item, 'description').text = 'wDbots'
        ET.SubElement(item, 'pubDate').text = now.isoformat('T')
    del data

all_links = []

def begin():
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = 'TamilMV RSS Feed by wDBots'
    ET.SubElement(channel, 'description').text = 'Duck a Sick'
    ET.SubElement(channel, 'link').text = 'https://t.me/whiteDevilBots'

    url = 'https://www.1tamilmv.eu/'

    # Lets use the requests get method to fetch the data from url
    response = requests.get(url)
    content = response.content
    soup = BeautifulSoup(content, 'html.parser')

    # Find all the paragraphs with 'font-size: 13.1px;'
    paragraphs = soup.find_all('p', style='font-size: 13.1px;')

    # Get all the links from the paragraphs
    links = [a['href'] for p in paragraphs for a in p.find_all('a', href=True)]
    # Filter the links to get only the ones that contain 'index.php?/forums/topic/'
    filtered_links = [link for link in links if 'index.php?/forums/topic/' in link]
    global all_links
    all_links=scraped=list(scrape(filtered_links))

    build_xml(scraped,channel)

    save_list_to_file(all_links)

    tree = ET.ElementTree(rss)
    tree.write('tamilmvRSS.xml', encoding='utf-8', xml_declaration=True)
    print('Begined finished')

def job():
    global all_links
    if not len(all_links):
        all_links=load_list_from_file()
        print(len(all_links))
    url = 'https://www.1tamilmv.eu/'

    # Lets use the requests get method to fetch the data from url
    response = requests.get(url)
    content = response.content
    soup = BeautifulSoup(content, 'html.parser')

    # Find all the paragraphs with 'font-size: 13.1px;'
    paragraphs = soup.find_all('p', style='font-size: 13.1px;')

    # Get all the links from the paragraphs
    links = [a['href'] for p in paragraphs for a in p.find_all('a', href=True)]
    # Filter the links to get only the ones that contain 'index.php?/forums/topic/'
    filtered_links = [link for link in links if 'index.php?/forums/topic/' in link]

    scraped=list(scrape(filtered_links))

    new_links = [link for link in scraped if link not in all_links]

    all_links= new_links + all_links
    save_list_to_file(all_links)

    if len(new_links):
        tree=ET.ElementTree()
        tree.parse('tamilmvRSS.xml')

        root=tree.getroot()
        channel=root.find('channel')
        npw=datetime.now().isoformat()
        for item_data in reversed(new_links):
            item = ET.Element('item')
            ET.SubElement(item, 'title').text = item_data[0]
            ET.SubElement(item, 'link').text = item_data[1]
            ET.SubElement(item, 'pubDate').text = npw
            channel.insert(3, item)
        tree.write('tamilmvRSS.xml', encoding='utf-8', xml_declaration=True)




    # tree = ET.ElementTree(rss)
    # tree.write('tamilmvRSS.xml', encoding='utf-8', xml_declaration=True)


# begin()
# job()

begin()
from threading import Thread
def run_schedule():
    while True:
        schedule.run_pending()
        sleep(1)

schedule.every(25).minutes.do(job)
Thread(target=run_schedule).start()

app = Flask(__name__)

@app.route('/')
def serve_rss():
    return send_file('tamilmvRSS.xml')
@app.route('/start')
def start():
    return 'Started'
@app.route('/reset')
def something():
    begin()
@app.route('/job')
def something2():
    job()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(port=port,host='0.0.0.0')




# torrent_file_path = "test1.torrent"
# size_in_bytes = get_torrent_size(torrent_file_path)
# print(f"Total size of files in torrent: {size_in_bytes} bytes")

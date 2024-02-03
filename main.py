import requests
import pandas as pd
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm

pd.set_option('max_colwidth', 100)

def get_sitemap_links(url, all_links = []):
    response = requests.get(url)
    if response.status_code == 200:
        try:

            soup = BeautifulSoup(response.text, 'xml')
            links = [loc.text for loc in soup.find_all('loc') if 'wp-content' not in loc.text]

        except:
            return
        
        else:

            for link in links:
                if link[-3:] != 'xml':
                    all_links.append(link)
            
            return all_links
    else:
        print(f'Request failed with status code {response.status_code}')
        return

def get_soup(url):
    response = requests.get(url)
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except:
        return
    
def get_title(soup):
    try:
        return soup.find('title').text
    except:
        return

def get_post_links(soup, class_):
    
    articles = soup.find_all(class_=class_)
    links = []
    for article in articles:
        links_elms = article.find_all('a')
        for link in links_elms:
            links.append(link['href'])

    links = list(set(links))
    return links

def is_internal(url, domain):
    if (not bool(urlparse(url).netloc)):
        return True
    else:
        if domain in url:
            return True
        return False
    
def fetch_links_dataframe(sitemap_url):
    
    domain = urlparse(sitemap_url).netloc

    df_links = pd.DataFrame(columns=[
        'url',
        'title',
        'post_link_href',
        'internal'
    ])

    sitemap_links = get_sitemap_links(sitemap_url)
    data = {}

    for link in tqdm(sitemap_links):
        soup = get_soup(link)
        link_srcs = get_post_links(soup, 'prose')
        for src in link_srcs:
            data['url'] = link
            data['title'] = get_title(soup)
            data['post_link_href'] = src
            data['internal'] = is_internal(src, domain)
            df_links = pd.concat([df_links, pd.DataFrame.from_dict([data])])
    
    df_links.reset_index(inplace=True)
    df_links.pop('index')

    return df_links
    
if __name__ == '__main__':
    url = 'https://ak-codes.com/post-sitemap.xml'
    
    df = fetch_links_dataframe(url)

    # find only internal links
    df_internal = df[df['internal'] == True]
    print(df_internal.head(20))
    print('Number of total internal links:', df_internal['url'].count())
    print('Number of unique internal links:', df_internal['url'].nunique())

    # find only external links
    df_external = df[df['internal'] == False]
    print(df_external.head(20))
    print('Number of total external links:', df_external['url'].count())
    print('Number of unique external links:', df_external['url'].nunique())

    # find pages without any links
    df_no_links = df[df['internal'].isnull()]
    print(df_no_links.head(20))
    print('Number of pages without any links:', df_no_links['url'].nunique())



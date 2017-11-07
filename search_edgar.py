import json
import random
import re
import requests
import sys
from lxml import html
from pprint import pprint
from requests.auth import HTTPProxyAuth
import boto3
from collections import defaultdict

sns = boto3.client('sns')
s3 = boto3.client('s3')


START_URL = 'https://searchwww.sec.gov/EDGARFSClient/jsp/EDGAR_MainAccess.jsp'
PARAM = '?search_text=*&sort=Date&formType={}&isAdv=true&stemming=true&numResults=5&queryCo={}&numResults=5'

def invoke(name, files, dest):
        req = {
                'Company': name,
                'Documents': files,
                'Destination': dest 
        }
        resp = sns.publish(TopicArn='arn:aws:sns:us-east-1:256782092976:GetDirectors',
                          Message=json.dumps(req))    
        return resp



def download_html(url, proxy_list=None):
    """
    Downloads html file using random proxy from list
    :param url: string
        Url that needs to be downloaded
    :param proxy_list: list
        Proxy list containing dict{ip, port, username, password}
    :return string or None:
        HTML content of url
    """
    html_content = None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/56.0.2924.87 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q = 0.9, image / webp, * / *;q = 0.8"}
    try:
        if proxy_list is not None:
            i = random.randint(0, len(proxy_list) - 1)
            http = 'http://{username}:{password}@{ip}:{port}'.format(**proxy_list[i])
            https = 'https://{username}:{password}@{ip}:{port}'.format(**proxy_list[i])
            proxies = {"http": http, "https": https}
            s = requests.Session()
            s.trust_env = False
            s.proxies.update(proxies)
            s.auth = HTTPProxyAuth(proxy_list[i]['username'], proxy_list[i]['password'])
            r = s.get(url, headers=headers, allow_redirects=True)
            r.raise_for_status()
        else:
            r = requests.get(url, headers=headers, allow_redirects=True)
            r.raise_for_status()
        if r.status_code != 200:
            print('[%s] Error Downloading %s' % r.status_code, url)
            print(r.headers)
            print(r.cookies)
        else:
            html_content = r.content
    except requests.exceptions.RequestException as err:
        print('Failed to open url %s' % url)
        html_content = None
    finally:
        if type(html_content) == bytes:
            return html_content.decode('utf-8')
        else:
            return html_content


def get_proxy_from_file(filechache):
    """
    Gets proxy list from JSON file
    :param filechache:
        Location of JSON file
    :return dict or None:
    """
    try:
        with open(filechache, 'r') as data_file:
            result = json.load(fp=data_file)
        if result is not None:
            return result['proxy_list']
    except:
        print('Cannot open cache file')
    return None

forms_with_parent = {
    'Form10K': True        
}

def search(query_co, form_type='Form10K', proxy_list=None):
    """
    Searches for Company Name in SEC EDGAR
    :param query_co: string
        Company Name
    :param form_type: string
        In Form Type : default 'Frorm10K'
    :param proxy_list: list
        List of proxies from function get_proxy_from_file : default None
    :return:
    """

    sdict = {'CompanyName': query_co, 'InFormType': form_type}
    params = PARAM.format(form_type, query_co)
    sdict['surl'] = START_URL + params
    results = download_html(sdict['surl'], proxy_list)
    if results is not None:
        tree = html.fromstring(results)

        if form_type in forms_with_parent: 
            a = tree.xpath('//div[@id="ifrm2"]/table[2]//a[contains(text(), "Parent Filing")]')
        else:
            a = tree.xpath('//a[@id="viewFiling"]')

        if a is not None and len(a) > 0:
            a_href = a[0].get('href').replace("'", ' ')
            sdict['content_url'] = re.search("(?P<url>https?://[^\s]+)", a_href).group("url")
            sdict['content'] = download_html(sdict['content_url'], proxy_list)
            if sdict['content'] is not None:
                sdict['status'] = 'OK'
            else:
                sdict['status'] = 'ERROR'
                sdict['err_info'] = 'Cannot open content'
        else:
            sdict['status'] = 'EMPTY'
            sdict['err_info'] = 'Empty Result Set'
    else:
        sdict['status'] = 'ERROR'
        sdict['err_info'] = 'Search results are empty'
    return sdict


def process(name, docs, dest):
    for doc in docs:
        resp = search(name, doc)
        err = resp.get('err_info', False)
        status = resp.get('status')
        if err:
            if status == 'EMPTY':
                parts = name.split(' ')
                if len(parts) > 2:
                    print('Recurse for shortened name: {}'.format(parts))
                    newname = " ".join(parts[:-1])
                    invoke(newname, [doc], dest)
                    return

                print("Failed to fetch: {}".format(resp))
                ct = 'application/json'
                key = "{}/{}.json".format(dest, doc)
                data = json.dumps(resp)
        else:
            data = resp['content']
            ct = 'plain/html'
            key = "{}/{}.html".format(dest, doc)

        s3.put_object(
            Bucket='directors.rdig.co', 
            Key=key, 
            ContentType=ct, 
            Body=data)


# Batch functions
CORE_DOCS = ['Form10K', 'FormDEF14A']
BUCKET = 'directors.rdig.co'

def get_records(prefix='companies'):
    """
    Returns a List of all files in bucket with a given prefix
    """
    paginator = s3.get_paginator('list_objects')
    page_iterator = paginator.paginate(Bucket=BUCKET, Prefix=prefix)
    names = []
    for page in page_iterator:
        keys = page['Contents']
#        for key in keys:
#            yield key['Key']
        names.extend([key['Key'] for key in keys])
    return names

def get_index():
    """
    Returns a dict of all files under the first level delimeter. In this case the company name.
    """
    records = get_records()
    index = defaultdict(list)
    for name in records:
        parts = name.split('/')
        path = "/".join(parts[:-1])
        file = parts[-1]
        index[path].append(file)
    return index

def needed_docs(index, target):
    """
       Given a list of desired docs. 
       Returns a list of tuples containing companies and the list of docs we don't yet have for them. 
    """
    ret = []
    needed = set(target)
    for i in index:
        gots = set([x.split('.')[0] for x in index[i]])
        needs = needed - gots
        ret.append((i, list(needs)))
    return [n for n in ret if n[1]]

def marshal(count):
    index = get_index()
    needs = needed_docs(index=index, target=CORE_DOCS)
    for need, files in needs[:count]:
        name = need.split('/')[-1]
        name = name.replace('_', ' ')
        print("Bulk Marshaling {}".format(name))
        invoke(name, files, need)

def check_works():
    return sns.list_topics()


if __name__ == '__main__':
    proxy_list = get_proxy_from_file('proxy_list.json')
    content = search('General Electric', proxy_list=proxy_list)
    pprint(content)

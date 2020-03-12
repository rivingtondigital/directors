from datetime import datetime
import requests
from lxml import etree
from io import StringIO, BytesIO
from bs4 import BeautifulSoup
import re
import pandas
import boto3
import json
import sys 

s3 = boto3.client('s3')
BUCKET = 'directors.rdig.co'

class TenKParser:
        
    def __init__(self, url):
        resp = requests.get(url)
        content = str(resp.content)
        content = content.replace('\xa0', ' ')
        self.soup = BeautifulSoup(content, 'lxml')
        self.signature_text = None

    def get_header_styles(self):
        header_style = style_parents[1].get('style')
        sub_style = style_parents[0].get('style')
        return header_style, sub_style

    def get_headers(self):
        sig_header = self.soup.find_all('', string=re.compile("signatures", re.IGNORECASE))[-1]
        self.signature_text = sig_header.parent.text
        style_parents = sig_header.find_parents(style=True)
        header = style_parents[1]
        sub = style_parents[0]
        headers = []
        for hd in self.soup.find_all(header.name, attrs=header.attrs):
            inner = hd.text.strip()
            if inner:
                if hd.find_all(sub.name, attrs=sub.attrs):
                    if hd.find(sig_header.parent.name):
                        headers.append(hd)
        return headers

    def get_sig_sec(self):
        # legal = "Pursuant to the requirements of the Securities Exchange Act of 1934"
        headers = self.get_headers()
        sig_index=None
        for i, header in enumerate(headers):
            if header.get_text() == self.signature_text:
                sig_index = i
        sigs = headers[sig_index]
        if len(headers) > sig_index+1:
            nxt = headers[sig_index+1]
        else:
            nxt = None
        target = []
        index = None
        for i, nxt_sib in enumerate(sigs.find_next_siblings()):
            if nxt_sib == nxt:
                break
#             if legal in nxt_sib.get_text():
#                 index = i+1
            target.append(nxt_sib)

        return index, target


def mung(obj):
    txt = obj[0]
    if isinstance(txt, str):
        txt = txt.replace('/s/', '')
        txt = txt.replace('nan', '')
        txt = txt.replace('(', '')
        txt = txt.replace(')', '')
        txt = txt.strip()
        txt = txt.title()
        obj.Name = txt
    return obj


def sub_asterix(obj):
    values = obj.values
    ret_values = {}
    for i, ele in enumerate(obj):
        if '*' == ele:
            ret_values[i] = values[i+1]
    obj = obj.replace(to_replace='*', value=ret_values, inplace=True)
    return obj


def extract(table):
    tables = pandas.read_html(str(table), header=0)[1:]

    def cleanup(table):
        table = table.dropna(axis=1, how='all')
        table.columns = ['Name', 'Position', 'Date']
        return table
    tables = [cleanup(x) for x in tables]
    one = pandas.concat(tables, ignore_index=True)
    
    one.apply(mung, axis=1)
    one.apply(sub_asterix, axis=0)

    # one = one.dropna(axis=0, how='all')
    one = one.dropna(axis=0, how='any')
    return one.to_json(orient='records')


def make_url(key):
    url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': 'directors.rdig.co',
            'Key': key
        }
    )
    return url


def process_10K(filename):
    url = "Unknown"
    try:
        company_folder = "/".join(filename.split('/')[:-1])
        url = make_url(filename)
        print(url)
        parser = TenKParser(url) 
        sig_table = parser.get_sig_sec()
        data = extract(sig_table)
        print(data)
        filename = "{}/directors.json".format(company_folder)
        filetype = 'application/json' 
    except Exception as e:
        import traceback
        exc_info = sys.exc_info()
        data = "{}:\n{}".format(e, traceback.format_exception(*exc_info)) 
        print(data)
        filename = "{}/directors_err.txt".format(company_folder)
        filetype = 'plain/text'
        
    s3.put_object(
        Bucket=BUCKET,
        Key=filename,
        ContentType=filetype,
        Body=data
    )



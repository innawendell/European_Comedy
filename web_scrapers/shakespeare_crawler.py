 #-*- coding: utf-8 -*-
import scrapy
import os
import pandas as pd
from scrapy import Request
from datetime import datetime, date

metadata_file = pd.read_csv('../Contrastive_Material/shakespeare.tsv', sep='\t')
start_urls = metadata_file['url'].tolist()

class TheaterSpider(scrapy.Spider):
    name = 'theater_crawler'
    allowed_domains = ['linkedin.com']

    start_urls = start_urls
    print("START URLS", start_urls)
    custom_settings = {
        'CONCURRENT_ITEMS': 1,
        'FEED_FORMAT': 'jsonlines',
        'DOWNLOAD_DELAY': 2,
        'FEED_URI': '../Contrastive_Material/shakespeare_xml_plays.jsl',
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"
       
    }

    def parse(self, response):
        item = {}
        item['date_crawled'] = datetime.now()
        item['url'] = response.url
        item['xml'] = response.text
        
        yield item
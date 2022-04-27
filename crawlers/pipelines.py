# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from database import DB

class CrawlersPipeline:
    
    def __init__(self):
        DB.init()

    def process_item(self, item, spider):
        DB.insert(item)
        return item

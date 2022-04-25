import os
import scrapy
import logging
from scrapy import Request
from scrapy.http import Response

from crawlers.items import BookItem
from crawlers.settings import DATA_PATH


class XbiqugeSoSpider(scrapy.Spider):
    name = 'xbiquge_so'
    allowed_domains = ['xbiquge.so']
    url_base = "https://www.xbiquge.so/top/allvisit/"
    spider_data_path = os.path.join(DATA_PATH,name)

    def start_requests(self):
        yield Request(url=self.url_base, callback=self.parse_first)

    def parse_first(self, r: Response):
        page_count = r.xpath(
            '//*[@id="pagelink"]/a[@class="last"]/text()').extract()
        if (not page_count):
            logging.warning("No page count get")
            return
        page_count = int(page_count[0])
        logging.info("Get total page count: {}".format(page_count))

        urls = [self.url_base+"{}.html".format(i)
                for i in range(1, page_count+1)]
        for url in urls:
            yield Request(url=url, callback=self.parse_page)
            # break

    def parse_page(self, r: Response):
        lis = r.xpath(
            '//*[@id="main"]/div[@class="novelslistss"]/li')
        for li in lis:
            btype, author, lastUpdate = li.xpath('./span/text()').extract()
            bname, _ = li.xpath('./span/a/text()').extract()
            url, _ = li.xpath('./span/a/@href').extract()

            item = BookItem()
            item['bname'] = bname.strip()
            item['author'] = author.strip()
            item['btype'] = btype.strip()
            item['url'] = url
            item['lastUpdate'] = lastUpdate

            logging.info(
                "Download book: {} - {} - {}".format(bname, author, lastUpdate))
            yield Request(url=url, callback=self.parse_book, meta={"item": item})
            # break

    def parse_book(self, r: Response):
        item = r.meta.get("item")
        chapter_urls = r.xpath('//*[@id="list"]/dl/dd/a/@href').extract()
        chapter_urls = set(chapter_urls)
        item['total_chapters'] = len(chapter_urls)
        # yield item

        save_dir = os.path.join(
            self.spider_data_path, item['btype'], "{}-{}".format(item['author'], item['bname']))
        download_chapters = set()
        if os.path.exists(save_dir):
            for _,_,files in os.walk(save_dir):
                ids = [f.replace(".txt",".html") for f in files]
                download_chapters.update(ids)
        
        target_chapters=chapter_urls-download_chapters
        item["download_chapters"] = 0
        for chapter_url in target_chapters:
            url = r.url+chapter_url
            chapter_id = chapter_url.replace(".html", "")
            yield Request(url=url, callback=self.parse_chapter, 
                meta={"item": item, "cid": chapter_id,"total":len(target_chapters)})

    def parse_chapter(self, r: Response):
        item = r.meta.get("item")
        chapter_id = r.meta.get("cid")
        total = r.meta.get("total")
        title = r.xpath(
            '//*[@id="box_con"]/div[@class="bookname"]/h1/text()').extract()
        if (not title):
            title = ""
        else:
            title = title[0]

        save_dir = os.path.join(
            self.spider_data_path, item['btype'], "{}-{}".format(item['author'], item['bname']))
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        save_path = os.path.join(save_dir, "{}.txt".format(chapter_id))

        lines = r.xpath('//*[@id="content"]/text()').extract()
        lines.pop(0)
        lines = [line.strip(" ")+"\n" for line in lines]

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(title+"\n")
            f.writelines(lines)
            f.write("\n\n")
            f.close()
            item["download_chapters"] = item["download_chapters"] + 1
            logging.info("Saved chapter[{}/{}]: {}".format(item["download_chapters"],total,save_path))

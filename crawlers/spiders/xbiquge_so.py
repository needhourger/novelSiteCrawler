import os
import scrapy
import logging
from scrapy import Request
from scrapy.http import Response

from crawlers.items import BookItem
from crawlers.settings import DATA_PATH
from crawlers.settings import OUTPUT_PATH
from progress import Progress
from database import DB


class XbiqugeSoSpider(scrapy.Spider):
    name = 'xbiquge_so'
    allowed_domains = ['xbiquge.so']
    url_base = "https://www.xbiquge.so/top/allvisit/"
    spider_data_path = os.path.join(DATA_PATH, name)

    def __init__(self, start=1, end=1, *args, **kwargs):
        super(XbiqugeSoSpider, self).__init__(*args, **kwargs)
        self.pstart = int(start)
        self.pend = int(end)

    def start_requests(self):
        yield Request(url=self.url_base, callback=self.parse_first)

    def parse_first(self, r: Response):
        page_count = r.xpath(
            '//*[@id="pagelink"]/a[@class="last"]/text()').extract()
        if (not page_count):
            logging.warning("No page count get")
            return
        page_count = int(page_count[0])
        logging.info("Get total page count: {} download from {} to {}".format(
            page_count, self.pstart, self.pend))

        urls = [self.url_base+"{}.html".format(i)
                for i in range(self.pstart, self.pend+1)]
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
            item['bid'] = int(url.split('/')[-2])
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

        save_dir = os.path.join(
            self.spider_data_path, item['btype'], "{}-{}".format(item['bname'], item['author']))
        download_chapters = set()
        if os.path.exists(save_dir):
            for _, _, files in os.walk(save_dir):
                ids = [f.replace("txt", "html") for f in files]
                download_chapters.update(ids)
        target_chapters = chapter_urls-download_chapters
        item["download_chapters"] = len(download_chapters)
        logging.info("total:{} downloaded:{} target:{}".format(
            len(chapter_urls), len(download_chapters), len(target_chapters)))
        # return

        if not DB.needUpdateBook(item):
            logging.info('{}.{} already complete ...'.format(
                item['bid'], item['bname']))
            return

        bar = Progress(item['total_chapters'], item['bname'], item['author'])
        bar.start()
        for chapter_url in target_chapters:
            url = r.url+chapter_url
            chapter_id = chapter_url.replace(".html", "")

            yield Request(url=url, callback=self.parse_chapter,
                          meta={"item": item, "cid": chapter_id, "bar": bar})

    def parse_chapter(self, r: Response):
        item = r.meta.get("item")
        chapter_id = r.meta.get("cid")
        bar = r.meta.get("bar")
        title = r.xpath(
            '//*[@id="box_con"]/div[@class="bookname"]/h1/text()').extract()
        if (not title):
            title = ""
        else:
            title = title[0]

        save_dir = os.path.join(
            self.spider_data_path, item['btype'], "{}-{}".format(item['bname'], item['author']))
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
            logging.info(
                "Saved chapter[{}/{}]: {}".format(item["download_chapters"], item["total_chapters"], save_path))
            bar.update(item["download_chapters"])

        if item["download_chapters"] == item["total_chapters"]:
            bar.finish()
            self.generateBook(save_dir)
            yield item

    def generateBook(self, target_dir):
        for root, dirnames, filenames in os.walk(target_dir):
            if not filenames:
                continue
            bname = root.split("/")[-1]+".txt"
            btype = root.split("/")[-2]
            spider = root.split("/")[-3]
            save_dir = os.path.join(OUTPUT_PATH, spider, btype)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            save_path = os.path.join(save_dir, bname)

            sorted_files = sorted(
                filenames, key=lambda x: int(x.replace(".txt", "")))
            with open(save_path, "wb") as f:
                for fname in sorted_files:
                    target = os.path.join(root, fname)
                    targetf = open(target, "rb")
                    data = targetf.read()
                    f.write(data)
                    targetf.close()
                    os.remove(target)
                    # logging.info("complete {}".format(target))
                f.close()
                logging.info("Generate Book: {}".format(save_path))
        os.rmdir(target_dir)

import os
import logging

from crawlers.settings import DATA_PATH

current_dir = os.path.split(os.path.abspath(__file__))[0]
output_path = os.path.join(current_dir,"output")

digit = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}

def _trans(s):
    num = 0
    if s:
        idx_q, idx_b, idx_s = s.find('千'), s.find('百'), s.find('十')
        if idx_q != -1:
            num += digit[s[idx_q - 1:idx_q]] * 1000
        if idx_b != -1:
            num += digit[s[idx_b - 1:idx_b]] * 100
        if idx_s != -1:
            # 十前忽略一的处理
            num += digit.get(s[idx_s - 1:idx_s], 1) * 10
        if s[-1] in digit:
            num += digit[s[-1]]
    return num

def trans(chn):
    chn = chn.replace('零', '')
    idx_y, idx_w = chn.rfind('亿'), chn.rfind('万')
    if idx_w < idx_y:
        idx_w = -1
    num_y, num_w = 100000000, 10000
    if idx_y != -1 and idx_w != -1:
        return trans(chn[:idx_y]) * num_y + _trans(chn[idx_y + 1:idx_w]) * num_w + _trans(chn[idx_w + 1:])
    elif idx_y != -1:
        return trans(chn[:idx_y]) * num_y + _trans(chn[idx_y + 1:])
    elif idx_w != -1:
        return _trans(chn[:idx_w]) * num_w + _trans(chn[idx_w + 1:])
    return _trans(chn)

for root,dirs,files in os.walk(output_path):
    if not files:
        continue

    for fname in files:
        count = 0
        flag = True
        path = os.path.join(root,fname)
        with open(path,"r",encoding="utf-8") as f:
            lines = f.readlines()
            f.close()
            titles = list(filter(lambda x:not x.startswith("    "), lines))
            for title in titles:
                t = title[title.find("第")+1:title.find("章")]
                t = t.strip()
                num = -1
                try:
                    num = int(t)
                except:
                    num = trans(t)
                if num - count == 1:
                    count = count + 1
                else:
                    flag = False
                    print(title)
                    break
        print("[{}] {}".format(flag,path))



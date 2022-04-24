import os
import logging

from crawlers.settings import DATA_PATH

current_dir = os.path.split(os.path.abspath(__file__))[0]
output_path = os.path.join(current_dir,"output")

for root,dirnames,filenames in os.walk(DATA_PATH):
    btype = root.split("/")[-2]
    bname = root.split("/")[-1]+".txt"
    save_dir = os.path.join(output_path,btype)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir,bname)

    sorted_files = sorted(filenames,key=lambda x:int(x.replace(".txt","")))
    with open(save_path,"wb") as f:
        for sorted_file in sorted_files:
            target = os.path.join(root,sorted_file)
            data = open(target,"rb").read()
            f.write(data)
            print("complete {}".format(target))
        f.close()
            

                


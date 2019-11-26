#!/usr/bin/env python3

import os
import argparse
import faster_than_requests as requests
import json
import ast
import copy 
import collections
from cursesmenu import *
from cursesmenu.items import *

main_menu = {}
images = {}
load = False
menus = []
menu_index = -1

def getImages(uri):
    request_url = uri+"/v2/_catalog"
    requests.setHeaders([])
    print("getImages: " + uri)
    r = requests.get2json(request_url)
    return json.loads(r)
    
def getTags(uri, image):
    request_url = uri+"/v2/"+image+"/tags/list"
    requests.setHeaders([])
    print("getTags: " + image)
    r = requests.get2json(request_url)
    return json.loads(r)

def getManifestSha(uri, image, tag):
    request_url = uri+"/v2/"+image+"/manifests/"+tag
    requests.setHeaders([("Accept", "application/vnd.docker.distribution.manifest.v2+json")])
    print("getManifestSha: " + image+ ": "+tag)
    r = json.loads(requests.gets(request_url)["headers"])
    h = r["docker-content-digest"]
    return h

def deleteSha(uri, images, image, sha):
    request_url = uri+"/v2/"+image+"/manifests/"+sha
    requests.setHeaders([("Accept", "application/vnd.docker.distribution.manifest.v2+json")])
    print("requests.deletes("+request_url+")")
    requests.deletes(request_url)
    for k, v in images[image].items():
        if v == sha:
            del(images[image]["v"])

def deleteTag(uri, images, image, tag):
    try:
        sha = images[image][tag][0]
        request_url = uri+"/v2/"+image+"/manifests/"+sha
        requests.setHeaders([("Accept", "application/vnd.docker.distribution.manifest.v2+json")])
        print("requests.deletes("+request_url+")")
        requests.deletes(request_url)
        for k, v in images[image].items():
            if v[0] == sha:
                del(images[image][k])    
                # pop_last_menu(uri, images)
                # get_last_menu().show()    
                break
        if len(images[image]) == 0:
            print("All tags removed, deleting image")
            del(images[image])
            pop_last_menu(uri, images)
            pop_last_menu(uri, images)
            get_last_menu().show()    
    except:
        print("Tag already deleted")   

def deleteImage(uri, images, image):
    requests.setHeaders([("Accept", "application/vnd.docker.distribution.manifest.v2+json")])
    for tag in copy.copy(images[image]):
        deleteTag(uri, images, image, tag)
    try:
        del(images[image])
    except:
        print("Image already deleted")
    pop_last_menu(uri, images)
    get_last_menu().show()

def tagsMenu(uri, images, image):
    menu = CursesMenu("Image: "+image, "Actions")
    tagdict = images[image]
    sorted_tagdict = collections.OrderedDict(sorted(tagdict.items()))
    for k,v in sorted_tagdict.items():
        v = v[0]
        function_del = FunctionItem("Delete Tag: "+k, deleteTag, [uri, images, image, k])
        menu.append_item(function_del)
    append_menu(menu)
    get_last_menu().show()
    pop_last_menu(uri, images)
    get_last_menu().show()

def imageMenu(uri, images, image):
    menu = CursesMenu("Image: "+image, "Actions")
    function_del_image = FunctionItem("Delete: "+image, deleteImage, [uri, images, image])
    function_tags = FunctionItem("Tags", tagsMenu, [uri, images, image])
    menu.append_item(function_del_image)
    menu.append_item(function_tags)
    append_menu(menu)
    get_last_menu().show()
    pop_last_menu(uri, images)
    get_last_menu().show()

def parse_images_file(filename):
    try:
        with open(filename) as f:
            content = f.read()
            content = ast.literal_eval(content)
            return content
    except FileNotFoundError:
        print("File not found")

def write_images_file(filename, images):
    with open(filename,'w') as f:
        f.write(repr(images))

def main_menu(uri, images):
    menu = CursesMenu(uri, "Catalog")

    for i in images:
        function_item = FunctionItem(i, imageMenu, [uri, images, i])
        menu.append_item(function_item)
    append_menu(menu)
    return menu

def get_images_from_registry(uri):
    catalog = getImages(uri=uri)
    for name in catalog["repositories"]:
        taglist = getTags(uri, name)
        sha = {}
        try: 
            for t in taglist["tags"]:
                s = getManifestSha(uri, name, t)
                sha[t] = s
            images[name] = sha
        except:
            print("Not tags for image"+name)
    return images

def append_menu(menu):
    global menus
    global menu_index
    menus.append(menu)
    menu_index += 1

def get_last_menu():
    return menus[menu_index]

def pop_last_menu(uri, images):
    global menus
    global menu_index
    menus[menu_index].exit()
    del(menus[menu_index])
    menu_index -= 1

    if len(menus) == 1:
        menus[0] = main_menu(uri, images)

def main():
    global menus
    parser = argparse.ArgumentParser(description='Interactive tool to clean up a docker registry')
    parser.add_argument('-r', '--registry', help="docker registry URI", nargs=1)
    parser.add_argument('-l', '--load', help="Load database from file (DEBUG)", nargs=1)
    parser.add_argument('-s', '--save', help="save database to file (DEBUG)", nargs=1)
    args = parser.parse_args() 
    if not args.registry:
        print("[ERROR] Must set a docker registry URI (-r). See -h for help.")
        exit(1)
    args = parser.parse_args() 
    registry = args.registry[0]
    if args.load:
        images = parse_images_file(args.load[0])
    else:
        images = get_images_from_registry(registry)

    print(images)    
    if args.save:
        write_images_file(args.save[0], images)
        exit(0)
        
    menu = main_menu(registry, images)
    menus[menu_index].show()
    
if __name__ == '__main__':
    main()
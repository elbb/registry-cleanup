#!/usr/bin/env python3

import os
import argparse
import faster_than_requests as requests
import json
import ast
import copy 
import collections
from enum import Enum

from tty_menu import tty_menu
images_index = {}
tags_index = {}
images = {}
load = False
debug = False

def getImages(uri):
    global images_index
    global tags_index
    request_url = uri+"/v2/_catalog"
    requests.setHeaders([])
    print("[INFO] Get images: \'" + uri+ "\'")
    r = requests.get2json(request_url)
    content = json.loads(r)
    make_index_dicts(content)
    return content
    
def getTags(uri, image):
    request_url = uri+"/v2/"+image+"/tags/list"
    requests.setHeaders([])
    print("[INFO] Get tags for \'" + image+ "\'")
    r = requests.get2json(request_url)
    return json.loads(r)

def getManifestSha(uri, image, tag):
    request_url = uri+"/v2/"+image+"/manifests/"+tag
    requests.setHeaders([("Accept", "application/vnd.docker.distribution.manifest.v2+json")])
    print("[INFO] Get manifest sha for image \'" + image+ "\' and tag \'"+tag+ "\'")
    r = json.loads(requests.gets(request_url)["headers"])
    h = r["docker-content-digest"]
    return h

def deleteSha(uri, images, image, sha):
    global debug
    if debug == False:
        request_url = uri+"/v2/"+image+"/manifests/"+sha
        requests.setHeaders([("Accept", "application/vnd.docker.distribution.manifest.v2+json")])
        requests.deletes(request_url)
    for k, v in images[image].items():
        if v == sha:
            del(images[image]["v"])

def deleteTag(uri, images, image, tag):
    global debug
    try:
        sha = images[image][tag][0]
        if debug == False:
            request_url = uri+"/v2/"+image+"/manifests/"+sha
            requests.setHeaders([("Accept", "application/vnd.docker.distribution.manifest.v2+json")])
            requests.deletes(request_url)
        for k, v in images[image].items():
            if v[0] == sha:
                del(images[image][k])    
                break
        if len(images[image]) == 0:
            print("All tags removed, deleting image")
            del(images[image])
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

def make_index_dicts(content):
    global images_index
    global tags_index
    index = 0
    for i in content:
        images_index[index] = i
        tags = []
        for tag in content[i]:
            tags.append(tag)
        tags_index[index] = tags
        index += 1

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
    make_index_dicts(images)            
    return images

def parse_images_file(filename):

    try:
        with open(filename) as f:
            content = f.read()
            content = ast.literal_eval(content)
            make_index_dicts(content)
            return content
    except FileNotFoundError:
        print("File not found")

def write_images_file(filename, images):
    with open(filename,'w') as f:
        f.write(repr(images))

class tag_actions(Enum):
    DELETE = 0
    EXIT = 1

def tag_menu(uri, index):
    i = []
    for it in tags_index[index]:
        i.append('Delete '+ it)
    i.append('Exit')
    return tty_menu(i, 'Tags for image: '+images_index[index])

class image_actions(Enum):
    DELETE = 0
    TAGS = 1
    EXIT = 2

def image_menu(uri, index):
    i = []
    i.append('Delete ')
    i.append('Tags')
    i.append('Exit')
    return tty_menu(i, 'Image: '+images_index[index])

class really_continue_actions(Enum):
    CONTINUE = 0
    ABORT = 1

def really_continue_menu(text):
    return tty_menu(['Continue', 'Abort'], 'Are you sure '+text+'?')

class continue_actions(Enum):
    OK = 0

def continue_menu(text):
    tty_menu(['OK'], 'Deleted' + text)

def main_menu(uri, images):
    i = []
    for it in images.keys():
        i.append(it)
    i.append('Refresh catalog')
    i.append('Exit')
    pos = tty_menu(i, uri)
    return pos

def refresh(debug, origin):
    print("Refreshing from " + origin)
    if debug:
        images = parse_images_file(origin)
    else:
        images = get_images_from_registry(origin)

def exit_message():
    print("Don't forget to cleanup your docker registry for the deleted tags.")
    print("$ bin/registry garbage-collect /etc/docker/registry/config.yml")
    print("\nDeleting a complete image does result in deleting all it's tags.")
    print("If you deleted complete images you need to manually delete the residues")
    print("in your docker registry filesystem.")

def main():
    global debug
    parser = argparse.ArgumentParser(description='Interactive tool to clean up a docker registry')
    parser.add_argument('-r', '--registry', help="docker registry URI", nargs=1)
    try:  
        os.environ['DOCKER_REGISTRY_CLEANUP_DEBUG']
        parser.add_argument('-l', '--load', help="Load catalog from file (DEBUG)", nargs=1)
        parser.add_argument('-s', '--save', help="save catalog to file (DEBUG)", nargs=1)
        debug = True
    except:
        pass

    args = parser.parse_args() 
    if not args.registry:
        print("[ERROR] Must set a docker registry URI (-r). See -h for help.")
        exit(1)
    args = parser.parse_args() 
    registry = args.registry[0]
    
    if debug:
        refresh(debug, args.load[0])
    else:
        refresh(debug, registry)

    if debug:    
        if args.save:
            write_images_file(args.save[0], images)
            exit(0)
    print("\n")
    while 1:
        pos = main_menu(registry, images)
        if pos == len(images_index):
            refresh(debug, registry)
            continue
        if pos == len(images_index)+1:
            exit_message()
            exit(1)
        print("Selected image: " + images_index[pos])
        image_action = image_actions(image_menu(registry, pos))
        if image_action == image_actions.DELETE:
            cont = really_continue_actions(really_continue_menu('deleting image \'' + images_index[pos]+'\''))
            if cont == really_continue_actions.CONTINUE:
                print("Deleting image: "+images_index[pos])
                deleteImage(registry, images, images_index[pos])
        elif image_action == image_actions.TAGS:
            while(1):
                tag = tag_menu(registry, pos)
                if tag == len(tags_index[pos]):
                    break
                cont = really_continue_actions(really_continue_menu('deleting tag \'' + tags_index[pos][tag]+'\''))
                if cont == really_continue_actions.CONTINUE:
                    print("Deleteing tag: \'" + tags_index[pos][tag]+"\' for image " + images_index[pos])
                    deleteTag(registry, images, images_index[pos], tags_index[pos][tag])
        elif image_action == image_actions.EXIT:
            pass
if __name__ == '__main__':
    main()
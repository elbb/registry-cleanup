# Docker registry cleanup tool
This interactive tool allows a user to delete images and/or single tags from a docker registry.

## Requirements
The tool was written in python3. Install the projects dependencies by
```
$ pip3 install -r requirements.txt
```

## Usage

```
./cleanup.py -h
usage: cleanup.py [-h] [-r REGISTRY]

Interactive tool to clean up a docker registry

optional arguments:
  -h, --help            show this help message and exit
  -r REGISTRY, --registry REGISTRY
                        docker registry URI
```

Connect to a docker registry and let the menu guide you through the catalog.
```
$ ./cleaup.py -r <docker-registry-uri>
```

Note: To see the changes after deleting tags or images you need to refresh.


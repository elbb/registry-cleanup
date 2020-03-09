# registry-cleanup
This interactive tool allows a user to delete images and/or single tags from a docker registry. It is written in golang.

## Requirements

* golang 1.13

### Building
Clone the repo wherever you like and build it using 
` $ make registry-cleanup`

You find the binary located in `$GOBIN`

## Usage

```
./registry-cleanup -h
Usage of registry-cleanup

Usage:
  -address string
    	docker registry URI (default "http://localhost:5000")
  -user string
    	User for auth to docker registry, empty for anymous
```

Connect to a docker registry and let the menu guide you through the catalog.
```
$ ./registry-cleanup -address <docker-registry-uri>
```

Note: Follow the instructions the program gives you on exit to entirely delete all residues of docker images.

## Using with docker
### Use the image from dockerhub
Start the application using
` $ docker run  --rm -it elbb/registry-cleanup <options>`

e.g. 
` $ docker run --rm -it elbb/registry-cleanup -address http://localhost:5000`

### Build your own image
Build the image using
` $ make docker`

Start the application using
` $ docker run --rm -it registry-cleanup <options>`

e.g. 
` $ docker run --rm -it registry-cleanup -address http://localhost:5000`

## License

Licensed under either of

 * Apache License, Version 2.0
   ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
 * MIT license
   ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.

## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be
dual licensed as above, without any additional terms or conditions.

all: registry-cleanup docker

registry-cleanup:
	cd cmd/registry-cleanup; go install

docker: 
	docker build --tag registry-cleanup . 
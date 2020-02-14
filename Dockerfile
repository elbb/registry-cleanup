FROM golang:1.13.8-alpine

RUN mkdir -p /build/src/registry-cleanup /build/bin
RUN addgroup -S user && adduser -S -G user user 
COPY . /build/src/registry-cleanup
ENV GOPATH=/build
ENV GOBIN=/build/bin
WORKDIR /build/src/registry-cleanup/cmd/registry-cleanup
RUN go install 
WORKDIR /build 
RUN rm -rf /build/src
RUN chown -R user:user /build/bin/
USER user
ENTRYPOINT [ "/build/bin/registry-cleanup"]
CMD ["-help"]

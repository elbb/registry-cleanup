FROM golang:1.13.8-alpine as builder
RUN mkdir -p /build/src/registry-cleanup /build/bin
COPY . /build/src/registry-cleanup
ENV GOPATH=/build
ENV GOBIN=/build/bin
WORKDIR /build/src/registry-cleanup/cmd/registry-cleanup
RUN go install 

FROM alpine:3.11.3
COPY --from=builder /build/bin/registry-cleanup /usr/local/bin/registry-cleanup
RUN addgroup -S user && adduser -S -G user user 
USER user
ENTRYPOINT [ "/usr/local/bin/registry-cleanup"]
CMD ["-help"]

# A Microservice that operates as a Redis/Mongo/S3 Cache

The redis key scheme to access an  object is `{source}:{object}:{id}`

*source* - data source

- mongodb
- s3

*object* - either the mongodb collection name or the s3 bucket name

- accounts
- messages

*id*

This is the unique identifier to retrieve that object with

## How to run locally

```console
docker-compose up
```

## Example

import os
import json
import re
from datetime import datetime
from bson import ObjectId, json_util
import boto3
from pymongo import MongoClient
from redis import StrictRedis, RedisError

from rediscache.config import logger, SourceType, DocType, default_expire_after
from rediscache.encryption import aes256


class RedisCache:
    def __init__(self, mongo_dsn, mongo_database, redis_dsn):

        self.mongo_client = MongoClient(mongo_dsn)
        self.__db = self.mongo_client[mongo_database]

        self.redis_client = StrictRedis.from_url(redis_dsn)

        self.s3_client = boto3.client('s3')

    def _get_expire_seconds(self, object_type, expire_after=None):
        if default_expire_after is '0':
            return None
        if object_type is DocType.ACCOUNTS.value:
            return None
        if expire_after and isinstance(expire_after, int):
            return expire_after
        return default_expire_after

    def _get_from_s3(self, bucket, key):
        logger.debug('get_from_s3 bucket:{0} key:{1}'.format(bucket, key))
        try:
            return self.s3_client.get_object(Bucket=bucket, Key=key)
        except Exception as err:
            logger.error('failed to get object from s3 -- {0}'.format(err))
            return None

    def _get_from_mongo(self, object_type, object_id):
        return self.__db[str(object_type)].find_one({'id': object_id})

    def _get_from_redis(self, key):
        try:
            doc_raw = self.redis_client.get(key)
        except RedisError as err:
            logger.error('failed redis get operation -- {0}'.format(err))

        if doc_raw:
            return json.loads(doc_raw.decode())

        return None

    def get_doc(
            self,
            source,
            doc_id_or_s3_key,
            object_type=None,
            bucket=None):
        """Gets document from mongo or s3 based on provided source.

        Document is written in redis using the format {source}:{object}:{id}.

        Parameters
        ----------
        source : str
            The source can be s3 or mongodb (see config.SourceType)
        doc_id_or_s3_key : str, optional
            Document id for mongodb, used as key for s3 objects
        object_type : str, optional
            Type of the object is based on mongodb models (see config.DocType)
        bucket : str, optional
            S3 bucket name (default is env AWS_S3_SECURE_MESSAGE_BUCKET_NAME)

        Returns
        -------
        doc
            a json encoded document or None
        """
        redis_key = RedisCache.fmt_redis_key(
            source,
            object_type,
            doc_id_or_s3_key)
        doc = self._get_from_redis(redis_key)

        src_mongodb = source is SourceType.MONGODB.value
        src_s3 = source is SourceType.S3.value

        if not doc and src_mongodb:
            doc = self._get_from_mongo(object_type, doc_id_or_s3_key)

        elif not doc and src_s3:
            redis_key = RedisCache.fmt_redis_key(
                source,
                bucket,
                doc_id_or_s3_key)
            doc = self._get_from_s3(bucket=bucket, key=doc_id_or_s3_key)

        else:
            logger.debug('doc:{0} found in redis'.format(doc_id_or_s3_key))
            return doc

        if doc:
            self.set_to_redis(
                document=doc,
                object_type=object_type,
                key=redis_key)

        return doc

    def set_to_redis(self, document, key, object_type=None, expire_after=None):
        exp_sec = self._get_expire_seconds(object_type, expire_after)

        response = False
        try:
            response = self.redis_client.set(
                key,
                json_util.dumps(document,
                                json_options=json_util.DEFAULT_JSON_OPTIONS),
                ex=exp_sec)
        except RedisError as err:
            logger.error('failed redis set operation -- {0}'.format(err))

        return response

    @staticmethod
    def decrypt_aes_256(text, passphrase):
        return aes256().decrypt(text, passphrase).decode('utf-8')

    @staticmethod
    def fmt_redis_key(source, object_type, object_id):
        return '{0}:{1}:{2}'.format(source, object_type, object_id)

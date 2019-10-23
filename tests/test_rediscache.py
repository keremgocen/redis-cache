import json
import os
import time
from unittest import TestCase, mock

from bson import ObjectId, json_util
from pymongo import MongoClient
from redis import RedisError, StrictRedis

from rediscache.config import DocType, SourceType, logger
from rediscache.rediscache import RedisCache


class TestBase(TestCase):

    @classmethod
    def setUpClass(cls):

        logger.info('Start RedisCache Test')
        os.environ['PYTESTING'] = 'True'

        cls.mongo_client = MongoClient('mongodb://mongodb:27017')
        cls.db = cls.mongo_client['test']

        cls.redis_client = StrictRedis.from_url('redis://redis:6379')

        cls.redisCache = RedisCache(
            mongo_dsn='mongodb://mongodb:27017',
            mongo_database='test',
            redis_dsn='redis://redis:6379')

    def setUp(self):

        self.mongo_client.drop_database('test')
        self.redis_client.flushall()

        self.msg_clt = self.db.messages
        self.act_clt = self.db.accounts

        with open('tests/mock_data/messages.json') as msg:
            meta = json.load(msg)
            self.msg_clt.insert_many(meta)

        with open('tests/mock_data/accounts.json') as act:
            meta = json.load(act)
            self.act_clt.insert_many(meta)

    def tearDown(self):

        self.mongo_client.drop_database('test')
        self.redis_client.flushall()


class TestRedisCache(TestBase):

    def test_account_not_in_redis_get_from_mongodb(self):
        src = SourceType.MONGODB.value
        obj_type = DocType.ACCOUNTS.value
        acc_id = 'fokan9ftxm4lpcokzox6asiq'
        key = RedisCache.fmt_redis_key(src, obj_type, acc_id)

        self.assertFalse(self.redis_client.exists(key))
        account = self.redisCache.get_doc(
            source=src,
            doc_id_or_s3_key=acc_id,
            object_type=obj_type)
        self.assertEqual(account['id'], acc_id)

    def test_account_found_in_redis_skips_mongodb(self):
        src = SourceType.MONGODB.value
        obj_type = DocType.ACCOUNTS.value

        with open('tests/mock_data/accounts.json') as accounts:
            acc_obj = json.load(accounts)[0]

        key = RedisCache.fmt_redis_key(src, obj_type, acc_obj['id'])
        self.redis_client.set(
            key,
            json_util.dumps(acc_obj,
                            json_options=json_util.DEFAULT_JSON_OPTIONS))

        with mock.patch.object(self.redisCache,
                               '_RedisCache__db',
                               return_value=None) as mock_rediscache_db:
            account = self.redisCache.get_doc(
                source=src,
                doc_id_or_s3_key=acc_obj['id'],
                object_type=obj_type)

            mock_rediscache_db.assert_not_called

        self.assertEqual(account, acc_obj)

    def test_message_not_in_redis_get_from_mongodb(self):
        src = SourceType.MONGODB.value
        obj_type = DocType.MESSAGES.value
        msg_id = '4c5d26zb08qwdcidrboo5zuq9'
        msg_subject = 'test request 2'
        key = RedisCache.fmt_redis_key(src, obj_type, msg_id)

        self.assertFalse(self.redis_client.exists(key))
        msg = self.redisCache.get_doc(
            source=src,
            doc_id_or_s3_key=msg_id,
            object_type=obj_type)
        self.assertEqual(msg['subject'], msg_subject)

    def test_message_found_in_redis_skips_mongodb(self):
        src = SourceType.MONGODB.value
        obj_type = DocType.MESSAGES.value

        with open('tests/mock_data/messages.json') as messages:
            msg_obj = json.load(messages)[0]

        key = RedisCache.fmt_redis_key(src, obj_type, msg_obj['id'])
        self.redis_client.set(
            key,
            json_util.dumps(msg_obj,
                            json_options=json_util.DEFAULT_JSON_OPTIONS))

        with mock.patch.object(self.redisCache,
                               '_RedisCache__db',
                               return_value=None) as mock_rediscache_db:
            msg = self.redisCache.get_doc(
                source=src,
                doc_id_or_s3_key=msg_obj['id'],
                object_type=obj_type)

            mock_rediscache_db.assert_not_called

        self.assertEqual(msg, msg_obj)

    def test_message_expires_after_x_seconds(self):
        src = SourceType.MONGODB.value
        obj_type = DocType.MESSAGES.value
        msg_id = '4c5d26zb08qwdcidrboo5zuq9'
        x = 1
        key = RedisCache.fmt_redis_key(src, obj_type, msg_id)

        if os.environ.get('EXPIRE_AFTER_SEC') is '0':
            self.skipTest('setting EXPIRE_AFTER_SEC cancels redis \
                key expiration')

        with open('tests/mock_data/messages.json') as messages:
            msg = json.load(messages)[0]

        _ = self.redisCache.set_to_redis(
            document=msg,
            object_type=obj_type,
            key=key,
            expire_after=x)

        time.sleep(x)

        self.assertIsNone(self.redis_client.get(key))

    def test_accounts_dont_expire_after_x_seconds(self):
        src = SourceType.MONGODB.value
        obj_type = DocType.ACCOUNTS.value
        acc_id = 'fokan9ftxm4lpcokzox6asiq'
        x = 1
        key = RedisCache.fmt_redis_key(src, obj_type, acc_id)

        if os.environ.get('EXPIRE_AFTER_SEC') is '0':
            self.skipTest('setting EXPIRE_AFTER_SEC cancels redis \
                key expiration')

        with open('tests/mock_data/accounts.json') as accounts:
            acc = json.load(accounts)[0]

        _ = self.redisCache.set_to_redis(
            document=acc,
            object_type=obj_type,
            key=key,
            expire_after=x)

        time.sleep(x)

        self.assertTrue(self.redis_client.exists(key))

    def test_set_to_redis_works_as_expected(self):
        src = SourceType.MONGODB.value
        obj_type = DocType.ACCOUNTS.value
        acc_id = 'fokan9ftxm4lpcokzox6asiq'
        key = RedisCache.fmt_redis_key(src, obj_type, acc_id)

        os.environ['EXPIRE_AFTER_SEC'] = '0'

        with open('tests/mock_data/accounts.json') as accounts:
            acc = json.load(accounts)[0]

        _ = self.redisCache.set_to_redis(
            document=acc,
            object_type=obj_type,
            key=key)

        self.assertTrue(self.redis_client.exists(key))

    def test_decryption_is_working_as_expected(self):
        with open('tests/mock_data/test_vectors.json') as test_vectors:
            test_vector = json.load(test_vectors)[0]

        account_encryption_key = test_vector['passphrase']

        message_content_body = test_vector['encrypted']
        decrypted_message = RedisCache.decrypt_aes_256(
            message_content_body, account_encryption_key)

        self.assertEqual(decrypted_message, test_vector['body'])

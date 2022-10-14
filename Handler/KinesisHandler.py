import json
import logging

import boto3
from botocore.exceptions import ClientError

from Entity.OperateInfo import ModelInfo


class KinesisHandler:
    def __init__(self, modelInfo:ModelInfo, logger:logging.Logger):
        self.__credentials = boto3.Session().get_credentials()
        self.__kinesis_client = boto3.client('kinesis', region_name=modelInfo.region,
                                      aws_access_key_id=self.__credentials.access_key,
                                      aws_secret_access_key=self.__credentials.secret_key)
        self.__logger = logger
        self.__name = None
        self.__details = None
        self.__stream_exists_waiter = self.__kinesis_client.get_waiter('stream_exists')
        self.__logger.debug(f"init Kinesis Handler -> Region: {modelInfo.region}, Stream Name: {modelInfo.streamName}")
    def clear(self):
        """
        Clears property data of the stream object.
        """
        self.__name = None
        self.__details = None

    def _arn(self):
        """
        Gets the Amazon Resource Name (ARN) of the stream.
        """
        return self.__details['StreamARN']

    def create(self, name, wait_until_exists=True):
        """
        Creates a stream.

        :param name: The name of the stream.
        :param wait_until_exists: When True, waits until the service reports that
                                  the stream exists, then queries for its metadata.
        """
        try:
            self.__kinesis_client.create_stream(StreamName=name, ShardCount=1)
            self.__name = name
            self.__logger.info("Created stream %s.", name)
            if wait_until_exists:
                self.__logger.info("Waiting until exists.")
                self.__stream_exists_waiter.wait(StreamName=name)
                self.describe(name)
        except ClientError:
            self.__logger.exception("Couldn't create stream %s.", name)
            raise

    def describe(self, name):
        """
        Gets metadata about a stream.

        :param name: The name of the stream.
        :return: Metadata about the stream.
        """
        try:
            response = self.__kinesis_client.describe_stream(StreamName=name)
            self.__name = name
            self.__details = response['StreamDescription']
            self.__logger.info("Got stream %s.", name)
        except ClientError:
            self.__logger.exception("Couldn't get %s.", name)
            raise
        else:
            return self.__details

    def delete(self):
        """
        Deletes a stream.
        """
        try:
            self.__kinesis_client.delete_stream(StreamName=self.__name)
            self.clear()
            self.__logger.info("Deleted stream %s.", self.__name)
        except ClientError:
            self.__logger.exception("Couldn't delete stream %s.", self.__name)
            raise

    def put_record(self, data, partition_key):
        """
        Puts data into the stream. The data is formatted as JSON before it is passed
        to the stream.

        :param data: The data to put in the stream.
        :param partition_key: The partition key to use for the data.
        :return: Metadata about the record, including its shard ID and sequence number.
        """
        try:
            response = self.__kinesis_client.put_record(
                StreamName=self.__name,
                Data=json.dumps(data),
                PartitionKey=partition_key)
            self.__logger.info("Put record in stream %s.", self.__name)
        except ClientError:
            self.__logger.exception("Couldn't put record in stream %s.", self.__name)
            raise
        else:
            return response

    def get_records(self, max_records):
        """
        Gets records from the stream. This function is a generator that first gets
        a shard iterator for the stream, then uses the shard iterator to get records
        in batches from the stream. Each batch of records is yielded back to the
        caller until the specified maximum number of records has been retrieved.

        :param max_records: The maximum number of records to retrieve.
        :return: Yields the current batch of retrieved records.
        """
        try:
            response = self.__kinesis_client.get_shard_iterator(
                StreamName=self.__name, ShardId=self.__details['Shards'][0]['ShardId'],
                ShardIteratorType='LATEST')
            shard_iter = response['ShardIterator']
            record_count = 0
            while record_count < max_records:
                response = self.__kinesis_client.get_records(
                    ShardIterator=shard_iter, Limit=10)
                shard_iter = response['NextShardIterator']
                records = response['Records']
                self.__logger.info("Got %s records.", len(records))
                record_count += len(records)
                yield records
        except ClientError:
            self.__logger.exception("Couldn't get records from stream %s.", self.__name)
            raise
      
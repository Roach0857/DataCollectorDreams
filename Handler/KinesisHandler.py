import json
import logging
import time
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
        self.kinesisDetails = None
        self.__DescribeStream(modelInfo.streamName)
        self.__logger.debug(f"init Kinesis Handler -> Details: {self.kinesisDetails}")

    def __DescribeStream(self, name):
        """
        Gets metadata about a stream.

        :param name: The name of the stream.
        :return: Metadata about the stream.
        """
        for i in range(3):
            try:
                response = self.__kinesis_client.describe_stream(StreamName=name)
                self.__name = name
                self.kinesisDetails = response['StreamDescription']
                self.__logger.info("Got stream %s.", name)
                return self.kinesisDetails
            except ClientError:
                self.__logger.exception("Couldn't get %s.", name)
            except Exception as ex:
                self.__logger.error(f"Describe stream faild {ex}.") 
            time.sleep(1)

    def PutRecord(self, data):
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
                PartitionKey=self.kinesisDetails['Shards'][0]['ShardId'])
            self.__logger.info("Put record in stream %s.", self.__name)
        except ClientError:
            self.__logger.exception("Couldn't put record in stream %s.", self.__name)
            raise
        else:
            return response

    def PutRecords(self, data):
        try:
            response = self.__kinesis_client.put_records(
                StreamName=self.__name,
                Records=[
                    {
                        'Data': json.dumps(d),
                        'PartitionKey': self.kinesisDetails['Shards'][0]['ShardId']
                    }
                    for d in data] 
                )
            self.__logger.info("Put record in stream %s.", self.__name)
        except ClientError:
            self.__logger.exception("Couldn't put record in stream %s.", self.__name)
            raise
        else:
            return response
    
    def GetShards(self):
        try:
            response = self.__kinesis_client.list_shards(StreamName=self.__name)
            self.__logger.info("Get shards in stream %s.", self.__name)
            self.kinesisDetails["Shards"] = response["Shards"]
        except ClientError:
            self.__logger.exception("Couldn't get shards in stream %s.", self.__name)
            raise
        else:
            return response
import datetime
import json
import sys
import time
from asyncio import Future
from logging import Logger

from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

import Entity
import Handler
from Entity.ObjectInfo import DeviceInfo


class AwsMqttHandler(Handler.DreamsHandler):
    def __init__(self, deadband: Handler.DeadbandHandler, thingName: str, awsInfo: Entity.AwsInfo, nodeInfo: Entity.NodeInfo,
                 deviceInfoList: list[DeviceInfo], deviceConfig: Entity.DeviceConfig, logger: Logger):
        super().__init__(deviceInfoList, deviceConfig, logger)
        self.__deadband = deadband
        self.__thingName = thingName
        self.__awsInfo = awsInfo
        self.__nodeInfo = nodeInfo
        self.__logger = logger
        self.__event_loop_group = io.EventLoopGroup(1)
        self.__host_resolver = io.DefaultHostResolver(self.__event_loop_group)
        self.__connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.__awsInfo.endpoint,
            port=443,
            cert_filepath=self.__awsInfo.certificatePath,
            pri_key_filepath=self.__awsInfo.privateKeyPath,
            client_bootstrap=io.ClientBootstrap(
                self.__event_loop_group, self.__host_resolver),
            on_connection_interrupted=self.__on_connection_interrupted,
            on_connection_resumed=self.__on_connection_resumed,
            client_id="awsiot-{}".format(thingName),
            clean_session=False,
            keep_alive_secs=30,
            http_proxy_options=None)

    def __on_connection_interrupted(self, connection, error, **kwargs):
        self.__logger.error(f"Connection interrupted. error: {error}")

    def __on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        self.__logger.info(f"Connection resumed. return_code: {return_code} session_present: {session_present}")
        if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
            self.__logger.error("Session did not persist. Resubscribing to existing topics...")
            resubscribe_future, packet_id = self.__connection.resubscribe_existing_topics()
            # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
            # evaluate result with a callback instead.
            resubscribe_future.add_done_callback(self.__on_resubscribe_complete)

    def __on_resubscribe_complete(self, resubscribe_future:Future):
        resubscribe_results = resubscribe_future.result()
        self.__logger.info(f"Resubscribe results: {resubscribe_results}")
        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))

    def __on_message_received(self, topic: str, payload, dup, qos, retain, **kwargs):
        self.__logger.info(f"Received message from topic '{topic}': {payload}")
        message = json.loads(payload)
        if 'invSet' in message:
            self.SetInv(message['invNumber'], message['invSet'])
        elif 'deadbandSet' in message:
            self.__deadband.Set(message['deadbandSet'])
        publishData = self.__GetAOData(message)
        self.Publish("ao", publishData)

    def GetAIData(self, invNumber: int):
        result = {
            "customerNumber": self.__thingName,
            "invNumber": invNumber,
            "ai":self.__deadband.aiData.__dict__,
            "timeStamp": int(time.mktime(datetime.datetime.now().timetuple()))
        }
        result["ai"]["invSet"] = self.invSet[invNumber].__dict__
        result["ai"]["invSet"]["control1"] = "".join(self.control1)
        result["ai"]["invSet"]["control2"] = "".join(self.control2)
        result["ai"]["deadbandSet"] = self.__deadband.deadbandSet.__dict__
        return json.dumps(result)

    def __GetAOData(self, message: dict) -> str:
        result = {
            "customerNumber": self.__thingName,
            "invNumber": message['invNumber'],
            "ao":{},
            "timeStamp": int(time.mktime(datetime.datetime.now().timetuple()))
        }
        return json.dumps(result)

    def Connect(self, thingName: str):
        reported = {"state": {
            "reported": {
                "nodeID": self.__nodeInfo.node.id,
                "state": False,
                "clientDevice": {},
                "thingName": thingName}}}
        lwt = mqtt.Will(topic=f"lwt/{thingName}/update", qos=0,payload=bytes(json.dumps(reported), 'utf-8'), retain=False)
        self.__connection.will = lwt
        connect_future = self.__connection.connect()
        connect_future.result()
        self.__logger.info(
            f"Connecting to {self.__awsInfo.endpoint} with client ID lwt-{thingName}...")

    def Subscribe(self):
        topic = f"rfdme/dreams/{self.__thingName}/ao"
        subscribeFuture, packet_id = self.__connection.subscribe(topic=topic, qos=mqtt.QoS.AT_MOST_ONCE, callback=self.__on_message_received)
        subscribeResult = subscribeFuture.result()
        self.__logger.info(f"Subscribed {topic} with {str(subscribeResult['qos'])}, packetID:{packet_id}")

    def Publish(self, payloadType: str, payload: str):
        topic = f"rfdme/dreams/{self.__thingName}/{payloadType}"
        publishFuture, packet_id = self.__connection.publish(topic=topic, qos=mqtt.QoS.AT_MOST_ONCE, payload=payload)
        publishResult = publishFuture.result()
        self.__logger.info(f"Published {topic} with {str(publishResult['qos'])}, packetID:{packet_id}, payload:{payload}")

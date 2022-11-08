import json
import sys
from asyncio import Future
from logging import Logger

from apscheduler.schedulers.background import BackgroundScheduler
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

from Entity import *
from Handler import *


class AwsMqttHandler(DreamsHandler):
    def __init__(self, 
                 thingName:str,
                 dreamsType: str, 
                 awsInfo: AwsInfo, 
                 nodeInfo: NodeInfo,
                 deviceInfoList: list[DeviceInfo], 
                 deviceConfig: DeviceConfig, 
                 deadband: DeadbandHandler,
                 logger: Logger):
        super().__init__(dreamsType, nodeInfo.powerNumber, deviceInfoList, deviceConfig, logger)
        self.__dreamsType = dreamsType
        self.__awsInfo = awsInfo
        self.__nodeInfo = nodeInfo
        self.__deadband = deadband
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
        self.__backgroundScheduler = BackgroundScheduler()
        self.__backgroundScheduler.add_job(self.__SendClass1Data, 'cron', minute='*/15', id='SelectData')
        self.__backgroundScheduler.start()

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
        if self.__dreamsType == "slave":
            if 'invSet' in message:
                self.SetInv(message)
                aiData = self.GetAIData("2", message)
                self.Publish(aiData, "2")
        elif self.__dreamsType == "master":
            if 'queryID' in message:
                aiData = self.GetAIData("0", message, self.__deadband.currentData.__dict__, self.__deadband.deadbandSet.__dict__)
                self.Publish(aiData, "0")
            else:
                if 'invSet' in message:
                    self.SetInv(message)
                if 'deadbandSet' in message:
                    self.__deadband.Set(message['deadbandSet'])
                aiData = self.GetAIData("2", message, self.__deadband.currentData.__dict__, self.__deadband.deadbandSet.__dict__)
                self.Publish(aiData, "2")
                    
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
        topic = f"rfdme/dreams/{self.__nodeInfo.powerNumber}/#"
        subscribeFuture, packet_id = self.__connection.subscribe(topic=topic, qos=mqtt.QoS.AT_MOST_ONCE, callback=self.__on_message_received)
        subscribeResult = subscribeFuture.result()
        self.__logger.info(f"Subscribed {topic} with {str(subscribeResult['qos'])}, packetID:{packet_id}")

    def Publish(self, payload: str, classType:str):
        topic = f"rfdme/dreams/{self.__nodeInfo.powerNumber}/ai/class{classType}"
        publishFuture, packet_id = self.__connection.publish(topic=topic, qos=mqtt.QoS.AT_MOST_ONCE, payload=payload)
        publishResult = publishFuture.result()
        self.__logger.info(f"Published {topic} with {str(publishResult['qos'])}, packetID:{packet_id}, payload:{payload}")

    def __SendClass1Data(self):
        if self.__dreamsType == "master":
            aiData = self.GetAIData("1", currentData = self.__deadband.currentData.__dict__,  deadbandSet = self.__deadband.deadbandSet.__dict__)
            self.Publish(aiData, "1")
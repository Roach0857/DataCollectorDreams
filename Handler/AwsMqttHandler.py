import json
import sys
from asyncio import Future
from logging import Logger
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
from Entity.AwsInfo import AwsInfo
from Entity.NodeInfo import NodeInfo

class AwsMqttHandler():
    def __init__(self, thingName:str, awsInfo: AwsInfo, nodeInfo: NodeInfo, logger: Logger):
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
            client_bootstrap=io.ClientBootstrap(self.__event_loop_group, self.__host_resolver),
            on_connection_interrupted=self.__on_connection_interrupted,
            on_connection_resumed=self.__on_connection_resumed,
            client_id=f"awsiot-{thingName}",
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

    def Connect(self):
        reported = {"state": {
            "reported": {
                "nodeID": self.__nodeInfo.node.id,
                "state": False,
                "clientDevice": {},
                "thingName": self.__thingName}}}
        lwt = mqtt.Will(topic=f"lwt/{self.__thingName}/update", qos=0, payload=bytes(json.dumps(reported), 'utf-8'), retain=False)
        self.__connection.will = lwt
        connect_future = self.__connection.connect()
        connect_future.result()
        self.__logger.info(
            f"Connecting to {self.__awsInfo.endpoint} with client ID lwt-{self.__thingName}...")
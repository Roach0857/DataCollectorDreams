from logging import Logger
import sys, json
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
import Entity

class AwsMqttHandler():
    def __init__(self, thingName:str, awsInfo:Entity.AwsInfo, nodeInfo:Entity.NodeInfo, logger:Logger):
        self.__awsInfo = awsInfo
        self.__nodeInfo = nodeInfo
        self.__logger = logger
        self.__event_loop_group = io.EventLoopGroup(1)
        self.__host_resolver = io.DefaultHostResolver(self.__event_loop_group)
        self.__connection = mqtt_connection_builder.mtls_from_path(
                    endpoint= self.__awsInfo.endpoint,
                    port= 443,
                    cert_filepath=self.__awsInfo.certificatePath,
                    pri_key_filepath=self.__awsInfo.privateKeyPath,
                    client_bootstrap=io.ClientBootstrap(self.__event_loop_group, self.__host_resolver),
                    on_connection_interrupted=self.__on_connection_interrupted,
                    on_connection_resumed=self.__on_connection_resumed,
                    client_id="awsiot-{}".format(thingName),
                    clean_session=False,
                    keep_alive_secs=30,
                    http_proxy_options=None)
        
    def __on_connection_interrupted(self, connection, error, **kwargs):
        self.__logger.error("Connection interrupted. error: {0}".format(error))
        
    def __on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        self.__logger.info("Connection resumed. return_code: {0} session_present: {1}".format(return_code, session_present))
        if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
            self.__logger.error("Session did not persist. Resubscribing to existing topics...")
            resubscribe_future, _ = self.__connection.resubscribe_existing_topics()
            resubscribe_future.add_done_callback(self.__on_resubscribe_complete)
            
    def __on_resubscribe_complete(self, resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        self.__logger.info("Resubscribe results: {0}".format(resubscribe_results))
        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))
    
    def __on_message_received(self, topic, payload, dup, qos, retain, **kwargs):
        self.__logger.info("Received message from topic '{}': {}".format(topic, payload))
        message = json.loads(payload)
        
    def Connect(self, thingName:str):
        reported = {"state": {
            "reported": {
                "nodeID": self.__nodeInfo.node.id,
                "state": False,
                "clientDevice":{},
                "thingName":thingName}}}
        lwt = mqtt.Will(topic=f"lwt/{thingName}/update", qos=0, payload=bytes(json.dumps(reported),'utf-8'), retain=False)
        self.__connection.will = lwt
        connect_future = self.__connection.connect()
        connect_future.result()
        self.__logger.info(f"Connecting to {self.__awsInfo.endpoint} with client ID lwt-{thingName}...")
        
    def Subscribe(self, locationObjectID:str):
        topic = f"{locationObjectID}"
        subscribe_future, packet_id = self.__connection.subscribe(topic=topic, qos=0, callback=self.__on_message_received)
        subscribe_result = subscribe_future.result()
        self.__logger.info(f"Subscribed {topic} with {str(subscribe_result['qos'])}")
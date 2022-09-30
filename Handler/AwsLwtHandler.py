from logging import Logger
import sys, json
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
import Entity

class AwsLwtHandler():
    def __init__(self, awsInfo:Entity.AwsInfo, nodeInfo:Entity.NodeInfo, logger:Logger):
        self.awsInfo = awsInfo
        self.nodeInfo = nodeInfo
        self.logger = logger
        
    def on_connection_interrupted(self, connection, error, **kwargs):
        self.logger.debug("Connection interrupted. error: {0}".format(error))
        
    def on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        self.logger.debug("Connection resumed. return_code: {0} session_present: {1}".format(return_code, session_present))
        if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
            self.logger.debug("Session did not persist. Resubscribing to existing topics...")
            resubscribe_future, _ = connection.resubscribe_existing_topics()
            resubscribe_future.add_done_callback(self.on_resubscribe_complete)
            
    def on_resubscribe_complete(self, resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        self.logger.debug("Resubscribe results: {0}".format(resubscribe_results))
        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))
                
    def Connect(self, thingName):
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        reported = {"state": {
            "reported": {
                "nodeID": self.nodeInfo.node.id,
                "state": False,
                "clientDevice":{},
                "thingName":thingName}}}
        lwt = mqtt.Will(topic=f"lwt/{thingName}/update", qos=0, payload=bytes(json.dumps(reported),'utf-8'), retain=False)
        mqttConnection = mqtt_connection_builder.mtls_from_path(
                    endpoint= self.awsInfo.endpoint,
                    port= 443,
                    cert_filepath=self.awsInfo.certificatePath,
                    pri_key_filepath=self.awsInfo.privateKeyPath,
                    client_bootstrap=client_bootstrap,
                    on_connection_interrupted=self.on_connection_interrupted,
                    on_connection_resumed=self.on_connection_resumed,
                    client_id="lwt-{}".format(thingName),
                    clean_session=False,
                    keep_alive_secs=30,
                    http_proxy_options=None)
        mqttConnection.will = lwt
        mqttConnection.connect()
        self.logger.info(f"Connecting to {self.awsInfo.endpoint} with client ID lwt-{thingName}...")
        
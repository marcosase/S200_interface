import json
import uuid
import time
import logging
import pika
import sys
#sys.path.insert(1, 'C:/Users/MarcosDaSilvaEleoter/OneDrive - Smart Photonics/Test & Measurement/Software/s200_wp1')
#from settings import settings

__logger__ = logging.getLogger("AMS.ezmes")


class RmqRpcClient:

    vhost = "/"

    def __init__(self, host, port, rpc_channel, reply_queue, username, password, vhost="/"):

        self.host = "mq-central.smartphotonics.loc"
        self.port = 5672
        self.rpc_channel = rpc_channel
        self.reply_queue = reply_queue
        self.vhost = "/pac"

        credentials = pika.PlainCredentials(username, password)
        __logger__.info("Setting up RabbitMQ client to %s on vhost %s:%s for channels %s and %s...",
                        host, port, vhost, rpc_channel, reply_queue)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                port=self.port,
                host=self.host,
                virtual_host=self.vhost,
                credentials=credentials,
            )
        )
        __logger__.info("RabbitMQ initialized succesfully")


        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.reply_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

        self.response = {}
        self.corr_id = None

    def on_response(self, ch, method, props, body) -> dict:
        if self.corr_id == props.correlation_id:
            self.response = json.loads(body.decode('utf-8'))
        else:
            body = {}

    def rpc_call(self, payload) -> dict:
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange="",
            routing_key=self.rpc_channel,
            properties=pika.BasicProperties(
                reply_to=self.reply_queue,
                correlation_id=self.corr_id,
            ),
            body=str(payload),
        )
        _start = time.time()
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
            if time.time() - _start > 15:
                __logger__.error("RPC call %s timed out.", self.reply_queue)
                return {}
            else:
                time.sleep(1)
        return self.response


class EzMesClient(RmqRpcClient):
    """Calls EzMes via rabbit mq to validate data"""
 
    correlation_id = str(uuid.uuid4())

    def __init__(self):
        super().__init__(
            rpc_channel="pac2ez_request", reply_queue="pac2ez_response",
            port=5672,
            host="mq-central.smartphotonics.loc",
            username="pac",
            password="pac",
            vhost="/pac",
        )

    def _request_authentication_token_(self) -> str:
        response = self.rpc_call(
            payload=self.__payload__auth(),
        )
        return response["Reply"]["Body"]["Passkey"] if response else None

    def mes_generic_transaction_request(self, wafer_id: str):
        # Get temporary access token
        access_token = self._request_authentication_token_()
        if not access_token:
            print('No Access!!!!')
            return {}

        response = self.rpc_call(
            payload=self.__payload_mes_generic_transaction__(wafer_id, access_token),
        )
        if response:
            print('Got response')
            __logger__.info("Generic mes transaction ")
        else:
            print('Got no response')
            __logger__.error("Generic mes transaction:failed")
        
        return response

    def mes_get_traveler_information(self, traveler_id: str) -> dict:
        # Get temporary access token
        access_token = self._request_authentication_token_()
        if not access_token:
            return {}
        response = self.rpc_call(
            payload=self.__payload_mes_get_traveler_information_request(
                traveler_id=traveler_id, pass_key=access_token
            ),
        )
        if not response.get("Reply"):
            __logger__.error("Invalid response received..")
        return response.get("Reply",{}).get("Body",{})

    def __payload_header__(self, service: str) -> dict:

        return {
            "CorrelationId": self.correlation_id,
            "Service": service,
            "Destination": "Ezmes-Sandbox",
            "SenderId": "EQ1",
            "SenderHost": "VM-3041-PAC",
            "SenderVersion": "PAC.1.2.0",
            "TimeToLive": 60000,
            "SenderEpoch": int(time.time()),
        }

    def __payload_mes_generic_transaction__(self, wafer_id: str, pass_key: str) -> str:
        return json.dumps(
            {
                "Request": {
                    "Header": self.__payload_header__("MesGenericTransaction.Request"),
                    "Body": {
                        "UserAuthentication": {
                            "User": "pac.user",
                            "Passkey": pass_key,
                        },
                        "Parameters": {
                            "GenericJson": {
                                "Mode": "mGenerateJSON",
                                "arJSColm": [
                                    {
                                        "sTyp": "string",
                                        "sTitle": "TravelerId",
                                        "sNm": "sFRID",
                                        "arJbConv": ["sPRFR"],
                                    }
                                ],
                                "bReturn_JObject_For_Data": False,
                                "o": {
                                    "sFlowName": "PR_Flow",
                                    "sMode_mSelectQuery_Return": "JObject",
                                },
                                "arCheckVals": [
                                    {
                                        "_EZQueryItem": True,
                                        "sNm": "sPRUniqueID",
                                        "sTyp": "string",
                                        "sOperation": "==",
                                        "sVal": wafer_id,
                                        "bAnd": True,
                                    }
                                ],
                            }
                        },
                    },
                }
            }
        )

    def __payload_mes_get_traveler_information_request(
        self, traveler_id: str, pass_key: str
    ) -> any:
        return {
            "Request": {
                "Header": self.__payload_header__("MesGetTravelerInformation.Request"),
                "Body": {
                    "UserAuthentication": {
                        "User": "pac.user",
                        "Passkey": pass_key,
                    },
                    "Parameters": {"TravelerID": traveler_id},
                },
            }
        }

    def __payload__auth(self):
        return json.dumps(
            {
                "Request": {
                    "Header": self.__payload_header__("MesGetUserAuthenticate.Request"),
                    "Body": {
                        "Parameters": {
                            "UserId": "pac.user",
                            "EncryptedPassword": "pac.user",
                        }
                    },
                }
            }
        )

if __name__ == "__main__":
    from pprint import pprint

    rpc = EzMesClient()

    wafer_id = input("Enter wafer id[34058 022 IP]:") or "34058 022 IP"

    # Check wafer id
    response = rpc.mes_generic_transaction_request(wafer_id=wafer_id)
    
    traveler_id = response["Reply"]["Body"]["GenericJson"]["arData"][0]["TravelerId"]

    assert traveler_id and traveler_id != 0, "Invalid traveler id"

    # Get data linked to wafer id
    traveler_info = rpc.mes_get_traveler_information(traveler_id=traveler_id)
    pprint(traveler_info)

__ezmes_instance__ = None

def get_ezmes_client():
    global __ezmes_instance__
    # Failed before
    if __ezmes_instance__ is False:
        return None
    if __ezmes_instance__:
        return __ezmes_instance__
    try:
        __ezmes_instance__ = EzMesClient()
        __logger__.info("Successfully initiated EzMesClient for validation of mes data")
    except:
        __ezmes_instance__ = False
        __logger__.error("Failed to initiate EzMesClient for validation of mes data")
    return __ezmes_instance__

if __name__ == "__main__":
    print("setup client...")
    client = EzMesClient()
    print("Client active")

    token = client._request_authentication_token_()
    print("Token: ", token)

    generic = client.mes_generic_transaction_request("1NS23036PFE 005 AC-02")
    print("Generic data", generic)

    print("Now validating traveler")
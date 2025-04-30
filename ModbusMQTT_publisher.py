from pymodbus.client import ModbusTcpClient
import paho.mqtt.client as mqtt
import time
import socket

# Modbus server details
IP_ADDRESS = '192.168.1.11'
PORT = 502
COIL_ADDRESS = 1          # Coil address to read
REGISTER_ADDRESS = 1      # Holding register (analog), base-1

# MQTT details
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "Win/MQTT_test/modbus_data"

def create_modbus_client():
    client = ModbusTcpClient(IP_ADDRESS, port=PORT)
    if client.connect():
        print("Connected to Modbus server.")
        return client
    else:
        print("Failed to connect to Modbus server.")
        return None

def read_coil(client, address):
    result = client.read_coils(address, count=1)
    return result.bits[0] if not result.isError() else None

def read_analog(client, address):
    result = client.read_holding_registers(address - 1, count=1)
    return result.registers[0] if not result.isError() else None

def main():
    modbus_client = create_modbus_client()
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()

    try:
        while True:
            # If modbus_client is not connected, try to reconnect
            if modbus_client is None or not modbus_client.connected:
                print("Reconnecting to Modbus server...")
                modbus_client = create_modbus_client()
                time.sleep(5)
                continue

            try:
                coil_value = read_coil(modbus_client, COIL_ADDRESS)
                analog_value = read_analog(modbus_client, REGISTER_ADDRESS)

                if coil_value is not None and analog_value is not None:
                    payload = {
                        "coil": coil_value,
                        "analog": analog_value
                    }
                    mqtt_client.publish(MQTT_TOPIC, str(payload))
                    print(f"Published to MQTT: {payload}")
                else:
                    print("Modbus read failed. Attempting reconnect...")
                    modbus_client.close()
                    modbus_client = None

            except (socket.error, Exception) as e:
                print(f"Modbus exception: {e}")
                if modbus_client:
                    modbus_client.close()
                    modbus_client = None

            time.sleep(5)

    except KeyboardInterrupt:
        print("Program stopped by user.")

    finally:
        if modbus_client:
            modbus_client.close()
        mqtt_client.disconnect()
        print("Connections closed.")

if __name__ == "__main__":
    main()

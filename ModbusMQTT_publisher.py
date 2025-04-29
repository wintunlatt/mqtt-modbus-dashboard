# modbus_mqtt_publisher.py
from pymodbus.client import ModbusTcpClient
import paho.mqtt.client as mqtt
import time

# Modbus server details
IP_ADDRESS = '192.168.1.11'
PORT = 502
COIL_ADDRESS = 1          # Coil address to read
REGISTER_ADDRESS = 1      # Holding register (analog), base-1

# MQTT details
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "Win/MQTT_test/modbus_data"

def read_coil(client, address):
    try:
        result = client.read_coils(address, count=1)
        if result.isError():
            print(f"Error reading coil {address}")
            return None
        return result.bits[0]
    except Exception as e:
        print(f"Exception reading coil: {e}")
        return None

def read_analog(client, address):
    try:
        result = client.read_holding_registers(address - 1, count=1)
        if result.isError():
            print(f"Error reading holding register {address}")
            return None
        return result.registers[0]
    except Exception as e:
        print(f"Exception reading analog value: {e}")
        return None

def main():
    # Connect to Modbus
    modbus_client = ModbusTcpClient(IP_ADDRESS, port=PORT)
    if not modbus_client.connect():
        print("Unable to connect to Modbus server.")
        return

    # Connect to MQTT
    mqtt_client = mqtt.Client()
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

    print("Connected to Modbus server and MQTT broker.")
    try:
        while True:
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
                print("Failed to read Modbus data. Skipping publish.")

            time.sleep(5)
    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        modbus_client.close()
        mqtt_client.disconnect()
        print("Connections closed.")

if __name__ == "__main__":
    main()

sudo apt install bluetooth bluez libbluetooth-dev python3-bleak

pip install bleak

pip install paho-mqtt structlog aiomqtt

sudo apt update
sudo apt upgrade
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl status mosquitto

mosquitto.conf :
listener 1883 0.0.0.0
allow_anonymous true

influxdb Mac Mini : pemesa:ISISpemesa
AP0FHvSCkps1IQqiRn5cPSsbdHGyJdtJB7iYXJ8e3ip_ABpW1n3sG6hC6UX5ygG0XrQqTF4kVwK0GXPDu-Q_Ow==

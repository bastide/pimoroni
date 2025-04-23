import logging
import json
import uuid
from datetime import datetime
import structlog
import paho.mqtt.client as mqtt
from threading import Lock

class MQTTLogger:
    def __init__(
        self,
        broker_host="localhost",
        broker_port=1883,
        topic="logs/app",
        service_name="my_service",
        client_id=None,
        username=None,
        password=None
    ):
        """
        Initialize an MQTT logger that publishes structured logs to an MQTT broker.

        Args:
            broker_host (str): MQTT broker hostname or IP.
            broker_port (int): MQTT broker port.
            topic (str): MQTT topic to publish logs to.
            service_name (str): Name of the service for log metadata.
            client_id (str, optional): Unique client ID for MQTT connection.
            username (str, optional): Username for broker authentication.
            password (str, optional): Password for broker authentication.
        """
        # Configure structlog for JSON output
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_log_level,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
        )
        self.logger = structlog.get_logger()
        self.service_name = service_name
        self.topic = topic
        self.lock = Lock()  # Thread-safe MQTT publishing

        # Initialize MQTT client
        self.client_id = client_id or f"mqtt-logger-{uuid.uuid4()}"
        self.client = mqtt.Client(client_id=self.client_id)
        if username and password:
            self.client.username_pw_set(username, password)
        
        # Set up MQTT callbacks
        self.client.on_connect = self._on_connect
        self.client.on_publish = self._on_publish

        # Connect to broker
        try:
            self.client.connect(broker_host, broker_port, keepalive=60)
            self.client.loop_start()  # Start network loop in a separate thread
        except Exception as e:
            self.logger.error("Failed to connect to MQTT broker", error=str(e))

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker."""
        if rc == 0:
            self.logger.info("Connected to MQTT broker", broker=client._host, port=client._port)
        else:
            self.logger.error("Connection to MQTT broker failed", code=rc)

    def _on_publish(self, client, userdata, mid):
        """Callback for when a message is published."""
        self.logger.debug("Published log message", message_id=mid)

    def log(self, level, event, **kwargs):
        """
        Log a message to the MQTT broker.

        Args:
            level (str): Log level ('debug', 'info', 'warning', 'error', 'critical').
            event (str): Log event description.
            **kwargs: Additional metadata to include in the log.
        """
        # Ensure level is valid
        level = level.lower()
        if level not in ("debug", "info", "warning", "error", "critical"):
            self.logger.warning("Invalid log level, defaulting to info", invalid_level=level)
            level = "info"

        # Prepare log message
        log_entry = {
            "service": self.service_name,
            "event": event,
            **kwargs
        }

        # Log locally and publish to MQTT
        try:
            with self.lock:
                # Log using structlog
                getattr(self.logger, level)(event, **kwargs)
                
                # Publish to MQTT
                payload = json.dumps(log_entry)
                result = self.client.publish(self.topic, payload, qos=1)
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    self.logger.error("Failed to publish log to MQTT", error_code=result.rc)
        except Exception as e:
            self.logger.error("Error logging to MQTT", error=str(e))

    def debug(self, event, **kwargs):
        """Log a debug message."""
        self.log("debug", event, **kwargs)

    def info(self, event, **kwargs):
        """Log an info message."""
        self.log("info", event, **kwargs)

    def warning(self, event, **kwargs):
        """Log a warning message."""
        self.log("warning", event, **kwargs)

    def error(self, event, **kwargs):
        """Log an error message."""
        self.log("error", event, **kwargs)

    def critical(self, event, **kwargs):
        """Log a critical message."""
        self.log("critical", event, **kwargs)

    def __del__(self):
        """Clean up MQTT client on destruction."""
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("Disconnected from MQTT broker")
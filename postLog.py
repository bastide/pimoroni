# Create an MQTT logger instance
mqtt_logger = MQTTLogger(
    broker_host="localhost",
    broker_port=1883,
    topic="logs/myapp",
    service_name="example_service",
    username="user",  # Optional
    password="pass"   # Optional
)

# Log messages with different levels
mqtt_logger.info("Application started", user_id=123)
mqtt_logger.error("Database connection failed", error_code=500, db="mysql")
mqtt_logger.debug("Processing request", request_id=str(uuid.uuid4()))

# Simulate some work
try:
    result = 1 / 0
except ZeroDivisionError as e:
    mqtt_logger.critical("Critical error in computation", error=str(e))
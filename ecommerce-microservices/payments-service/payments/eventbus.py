import json
import logging
import threading

import requests
from django.conf import settings

logger = logging.getLogger("eventbus")


def _publish_amqp(event_name, payload):
    import pika

    params = pika.URLParameters(settings.RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange="ecommerce.events", exchange_type="topic", durable=True)
    channel.basic_publish(
        exchange="ecommerce.events",
        routing_key=event_name,
        body=json.dumps(payload).encode(),
        properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
    )
    connection.close()


def _publish_http(event_name, payload):
    subscribers = settings.EVENT_SUBSCRIBERS.get(event_name, [])

    def _fanout():
        for url in subscribers:
            try:
                requests.post(
                    url,
                    json=payload,
                    headers={"X-Internal-Token": settings.INTERNAL_SERVICE_TOKEN},
                    timeout=5,
                )
                logger.info("delivered %s -> %s", event_name, url)
            except requests.RequestException as exc:
                logger.warning("failed to deliver %s -> %s: %s", event_name, url, exc)

    threading.Thread(target=_fanout, daemon=True).start()


def publish_event(event_name, payload):
    logger.info("event published: %s payload=%s", event_name, payload)
    if settings.EVENT_BUS_MODE == "amqp":
        try:
            _publish_amqp(event_name, payload)
            return
        except Exception as exc:
            logger.warning("amqp publish failed (%s), falling back to http", exc)
    _publish_http(event_name, payload)

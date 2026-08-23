import json

from django.core.management.base import BaseCommand
from django.conf import settings

from notifications.handlers import handle_event


class Command(BaseCommand):
    help = "Consume order.created / order.paid / order.payment_failed events from RabbitMQ."

    ROUTING_KEYS = ["order.created", "order.paid", "order.payment_failed"]

    def handle(self, *args, **options):
        import pika

        params = pika.URLParameters(settings.RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.exchange_declare(exchange="ecommerce.events", exchange_type="topic", durable=True)

        queue = channel.queue_declare(queue="notifications.all_order_events", durable=True)
        for key in self.ROUTING_KEYS:
            channel.queue_bind(exchange="ecommerce.events", queue=queue.method.queue, routing_key=key)

        self.stdout.write(self.style.SUCCESS("notifications-service: consuming order events from RabbitMQ..."))

        def callback(ch, method, properties, body):
            data = json.loads(body)
            event_type = method.routing_key
            self.stdout.write(f"received {event_type} for order #{data.get('order_id')}")
            try:
                handle_event(event_type, data)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"failed to process event: {exc}"))
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue.method.queue, on_message_callback=callback)
        channel.start_consuming()

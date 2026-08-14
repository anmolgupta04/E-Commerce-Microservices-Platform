import json

from django.core.management.base import BaseCommand
from django.conf import settings

from payments.handlers import handle_order_created


class Command(BaseCommand):
    help = "Consume order.created events from RabbitMQ (topic exchange 'ecommerce.events')."

    def handle(self, *args, **options):
        import pika

        params = pika.URLParameters(settings.RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.exchange_declare(exchange="ecommerce.events", exchange_type="topic", durable=True)

        queue = channel.queue_declare(queue="payments.order_created", durable=True)
        channel.queue_bind(exchange="ecommerce.events", queue=queue.method.queue, routing_key="order.created")

        self.stdout.write(self.style.SUCCESS("payments-service: consuming order.created from RabbitMQ..."))

        def callback(ch, method, properties, body):
            data = json.loads(body)
            self.stdout.write(f"received order.created for order #{data.get('order_id')}")
            try:
                handle_order_created(data)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"failed to process event: {exc}"))
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue.method.queue, on_message_callback=callback)
        channel.start_consuming()

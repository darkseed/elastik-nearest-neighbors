# Kafka consumer with following responsibilities:
# - Read feature vector from Kafka topic.
# - Compute vector hash via LSH.
# - Publish vector hash to topic.

from confluent_kafka import Consumer, KafkaError, Producer
from time import time
import numpy as np
import pdb


class SimpleLSH(object):

    def __init__(self, seed=865, bits=1024):
        self.bits = bits
        self.rng = np.random.RandomState(seed)
        self.planes = None

    def get_vector_hash(self, vector):
        return self.rng.binomial(1, 0.5, size=self.bits).astype(np.uint8)


if __name__ == "__main__":

    K_SERVER = "localhost:9092"
    K_SUB_TOPIC = "image-feature-vectors"
    K_PUB_TOPIC = "image-hash-vectors"

    settings = {
        'bootstrap.servers': K_SERVER,
        'group.id': 'TODO',
        'client.id': 'client-%d' % time(),
        'enable.auto.commit': True,
        'session.timeout.ms': 6000,
        'default.topic.config': {
            'auto.offset.reset': 'smallest'
        }
    }

    consumer = Consumer(settings)
    producer = Producer({"bootstrap.servers": K_SERVER})
    consumer.subscribe([K_SUB_TOPIC])

    simple_lsh = SimpleLSH()

    while True:

        # TODO: is it really best practice to poll like this?
        msg = consumer.poll(0.1)
        if msg is None:
            continue

        if msg.error():
            print('Error: %s' % msg.error().str())
            continue

        image_key = msg.key().decode()
        vec = np.fromstring(msg.value(), dtype=np.float32)
        hsh = simple_lsh.get_vector_hash(vec)

        print('%s %s %.3lf %s %d' % (
            image_key, str(vec.shape), vec.mean(), str(hsh.shape), hsh.sum()))

        producer.produce(K_PUB_TOPIC, key=image_key, value=hsh.tostring())

    # TODO: use atexit to make sure it flushes if the script fails.
    producer.flush()
#!/usr/bin/env node
/**
 * Peek at Kalmar Energi Team 1's Kafka data stream.
 *
 * Usage:
 *   npm install kafkajs   # first time only
 *   node peek_kalmar1_kafka.js [count]
 *
 * Arguments:
 *   count - Number of messages to read (default: 5)
 *
 * Examples:
 *   node peek_kalmar1_kafka.js       # Read 5 messages
 *   node peek_kalmar1_kafka.js 10    # Read 10 messages
 *   node peek_kalmar1_kafka.js 1     # Read 1 message (quick check)
 */

const { Kafka } = require("kafkajs");

const KAFKA_BROKER = "194.47.171.153:30092";
const TOPIC = "meter-readings";

async function peek(maxMessages = 5) {
  const kafka = new Kafka({
    clientId: "meterstream-peek",
    brokers: [KAFKA_BROKER],
    logLevel: 1, // ERROR only - suppress INFO logs
  });

  // Unique group ID so we don't interfere with other consumers
  const groupId = `peek-${Date.now()}`;
  const consumer = kafka.consumer({ groupId });

  let done = false;

  console.log(`Connecting to Kafka at ${KAFKA_BROKER}...`);

  await consumer.connect();
  console.log(`Subscribing to topic: ${TOPIC}`);
  await consumer.subscribe({ topic: TOPIC, fromBeginning: false });

  let count = 0;

  const shutdown = () => {
    if (done) return;
    done = true;
    // Force exit - Kafka consumer doesn't shut down cleanly
    process.exit(0);
  };

  const timeout = setTimeout(() => {
    console.log("\nTimeout - no messages received in 10 seconds");
    console.log("The stream might be idle or not producing data right now.");
    shutdown();
  }, 10000);

  console.log(`Waiting for up to ${maxMessages} messages...\n`);
  console.log("=".repeat(60));

  await consumer.run({
    eachMessage: async ({ partition, message }) => {
      if (done) return;

      count++;
      const value = message.value.toString();

      console.log(`\n[Message ${count}]`);
      console.log(`  Partition: ${partition}`);
      console.log(`  Offset: ${message.offset}`);
      console.log(`  Timestamp: ${new Date(parseInt(message.timestamp)).toISOString()}`);

      // Try to parse as JSON for pretty printing
      try {
        const json = JSON.parse(value);
        console.log(`  Value (JSON):`);
        console.log(
          JSON.stringify(json, null, 4)
            .split("\n")
            .map((l) => "    " + l)
            .join("\n")
        );
      } catch {
        console.log(`  Value (raw): ${value}`);
      }

      if (count >= maxMessages) {
        clearTimeout(timeout);
        console.log("\n" + "=".repeat(60));
        console.log(`\nReceived ${count} messages. Done.`);
        shutdown();
      }
    },
  });
}

const count = parseInt(process.argv[2]) || 5;
peek(count).catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});

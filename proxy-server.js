const WebSocket = require('websocket').server;
const http = require('http');
const mqtt = require('mqtt');

// Create an HTTP server
const server = http.createServer(function(request, response) {
    // This server is only for WebSocket upgrade requests
});
server.listen(8080, function() {
    console.log('Proxy server is listening on port 8080');
});

// Create a WebSocket server
const wsServer = new WebSocket({
    httpServer: server
});

// Create an MQTT client
const mqttClient = mqtt.connect('mqtt://192.168.98.10:1883'); // Replace with your MQTT broker address and port

// Handle WebSocket connections
wsServer.on('request', function(request) {
    const connection = request.accept(null, request.origin);
    console.log('WebSocket connection accepted');

    // Forward WebSocket messages to MQTT broker
    connection.on('message', function(message) {
        if (message.type === 'utf8') {
            console.log('Received message from WebSocket:', message.utf8Data);
            // Forward the message to MQTT broker
            mqttClient.publish('vanetza/out/cam', message.utf8Data);
        }
    });

    // Handle MQTT messages
    mqttClient.on('message', function(topic, message) {
        console.log('Received message from MQTT broker:', message.toString());
        // Forward the message to WebSocket
        connection.sendUTF(message.toString());
    });

    connection.on('close', function(reasonCode, description) {
        console.log('WebSocket connection closed');
    });
});

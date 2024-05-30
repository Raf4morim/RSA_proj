var map = L.map('map').setView([40.748817, -73.985428], 16);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

var obuIconFrontCar = L.icon({
    iconUrl: "static/front_car.png",
    iconSize: [24, 24],
    iconAnchor: [18, 39],
    popupAnchor: [10, -35]
});

var obuIconAmbulance = L.icon({
    iconUrl: "static/ambulance.png",
    iconSize: [24, 24],
    iconAnchor: [18, 39],
    popupAnchor: [10, -35]
});

var obuIconViolatingCar = L.icon({
    iconUrl: "static/car.png",
    iconSize: [24, 24],
    iconAnchor: [18, 39],
    popupAnchor: [10, -35]
});

// Array of markers
var markers = [];

let popUpFlag = 0;
let notificationClosed = false;

setInterval(obuCall, 500);
setInterval(obuViolation, 500);

// Modify the obuCall function to track the ambulance marker and adjust map view
function obuCall() {
    $.ajax({
        url: '/get_coordinates',
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            // Clear existing markers
            markers.forEach(delMarker);

            let i = 0;
            let obuIcon;
            let ambulanceBounds = []; // Array to store ambulance marker positions
            response.forEach(function(data) {
                if (data[0] !== null && data[1] !== null) {
                    if (data[2] == "192.168.98.30")
                        obuIcon = obuIconFrontCar;
                    else if (data[2] == "192.168.98.20") {
                        obuIcon = obuIconAmbulance;
                        // Store the position of the ambulance marker
                        ambulanceBounds.push([data[0], data[1]]);
                    }
                    else if (data[2] == "192.168.98.10")
                        obuIcon = obuIconViolatingCar;
                    markers[i] = L.marker([data[0], data[1]], {icon: obuIcon}).addTo(map)
                        .bindTooltip(data[2], {permanent: false});
                    i++;
                }
            });

            // If ambulance marker exists, adjust map view to fit all markers
            // if (ambulanceBounds.length > 0) {
            //     // Create a LatLngBounds object from ambulanceBounds
            //     var bounds = L.latLngBounds(ambulanceBounds);
            //     // Fit the map to the bounds of the ambulance marker
            //     map.fitBounds(bounds, { padding: [60, 60], minZoom: 20 }); // You can adjust padding as needed
            // }
        },
        error: function(xhr, status, error) {
            console.error('Error:', status, xhr.responseText);
        }
    });
}

function obuViolation() {
    $.ajax({
        url: '/violations',
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            // See if data is not empty
            // show popup with data[2] message
            console.log(response);

            if (!notificationClosed && response[0][0].includes("behind the ambulance") && popUpFlag == 0) {
                showNotification(response[0][0]);
            }
        }
    });
}

function showNotification(message) {
    var notification = document.getElementById('notification');
    var notificationMessage = document.getElementById('notification-message');
    notificationMessage.innerText = message;
    notification.style.display = 'block';
}

function closeNotification() {
    var notification = document.getElementById('notification');
    notification.style.display = 'none';
    notificationClosed = true;  // Set flag to prevent future notifications
}

// Function to add markers to the map
function addMarker(latitude, longitude, icon, tooltipText) {
    var marker = L.marker([latitude, longitude], { icon: icon }).addTo(map);
    marker.bindTooltip(tooltipText).openTooltip(); // Bind tooltip to marker
    marker.on('click', function(e) {
        alert('Marker clicked!'); // Replace with your popup logic
    });
    markers.push(marker);
}

// Function to remove all markers from the map
function clearMarkers() {
    markers.forEach(function(marker) {
        map.removeLayer(marker);
    });
    markers = [];
}

function delMarker(value, index, array){
    map.removeLayer(value);
}

var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

socket.on('car_reaction', function(data) {
    alert(data.message);
});

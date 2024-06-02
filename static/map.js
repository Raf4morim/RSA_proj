var map = L.map('map').setView([40.6255656, -8.7194227], 16);

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
let n = 0;

setInterval(obuCall, 500);
setInterval(obuViolation, 500);
setInterval(obuFrontCar, 500)

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
                    if (data[2] == 3 || data[2] == 4)
                        obuIcon = obuIconFrontCar;
                    else if (data[2] == 2) {
                        obuIcon = obuIconAmbulance;
                        // Store the position of the ambulance marker
                        ambulanceBounds.push([data[0], data[1]]);
                    }
                    else if (data[2] == 1)
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
            console.log("BEHINDDD: "+ response[0][0]);
            if (response[0][0].includes("behind the ambulance")) {
                showNotification(response[0][0]);
            }
        }
    });
}

function obuFrontCar() {
    $.ajax({
        url: '/frontCar',
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            // See if data is not empty
            // show popup with data[2] message
            // console.log(response);

            //console.log("AAAAAAAAAAAA" + response[0][0]);
            console.log("AAAAAAAAAAAA" + response);
            response.forEach(function(item) {
                console.log("CARROS Á FRENTE: "+item[0]);
                if (item[0].includes("in front of ambulance should swerve")) {
                    showNotificationSwerve(item[0],6);
                }
            });
        }
    });
}

function showNotificationSwerve(message,n) {
    var notification = document.getElementById('notificationSwerve');
    var notificationMessage = document.getElementById('notification-messageSwerve');
    
    // Check if the number of paragraphs exceeds the limit
    if (notificationMessage.children.length >= n) {
        // Reset the notification content
        notificationMessage.innerText = message + '\n';
    } else {
        // Append the new message to the existing content
        notificationMessage.innerText += message + '\n';
    }
 
    // Ensure the notification is displayed
    notification.style.display = 'block';
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

function closeNotificationSwerve() {
    var notification = document.getElementById('notificationSwerve');
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

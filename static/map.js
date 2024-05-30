var map = L.map('map').setView([40.748817, -73.985428], 16);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
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

//array de markers
var markers = [];

setInterval(obuCall, 1000);

function obuCall() {
    $(document).ready(function(){
        $.ajax({
            url: '/get_coordinates',  // Update the URL to match your Flask route
            type: 'GET',
            dataType: 'json',  // Specify that the response is JSON
            success: function(response){
                markers.forEach(delMarker);

                let i = 0;
                let obuIcon;
                response.forEach(function(data) {
                    if (data[0] !== null && data[1] !== null) {
                        if (data[2] == "192.168.98.30")
                            obuIcon = obuIconFrontCar
                        if (data[2] == "192.168.98.20")
                            obuIcon = obuIconAmbulance
                        if (data[2] == "192.168.98.10")
                            obuIcon = obuIconViolatingCar
                        markers[i] = L.marker([data[0], data[1]], {icon: obuIcon}).addTo(map)
                            .bindTooltip(data[2], {permanent: false});
                        i++;
                    }
                });
            },
            error: function(xhr, status, error) {
                console.error('Error:', status, xhr.responseText);
            }
        });
    });
}


function delMarker(value, index, array){
    map.removeLayer(value)
}
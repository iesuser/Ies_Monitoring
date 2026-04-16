var markers = [];
var map;

function initMap() {
    var latlng = new google.maps.LatLng(42.264, 43.322);
    var myOptions = {
        zoom: 7,
        center: latlng,
        panControl: false,
        streetViewControl: false,
        mapTypeControl: true,
        mapTypeControlOptions: {style: google.maps.MapTypeControlStyle.DROPDOWN_MENU},
        mapTypeId: google.maps.MapTypeId.HYBRID,
        zoomControl: true,
        zoomControlOptions: {style: google.maps.ZoomControlStyle.SMALL}
    };
    map = new google.maps.Map(document.getElementById("map"), myOptions);
}

function updateMapMarkers(events) {
    // Remove existing markers from the map
    markers.forEach(marker => marker.setMap(null));
    markers = []; // Clear the markers array

    events.forEach(event => {
        var latitude = parseFloat(event.latitude);
        var longitude = parseFloat(event.longitude);
        if (Number.isNaN(latitude) || Number.isNaN(longitude)) {
            return;
        }

        var marker = new google.maps.Marker({
            position: {lat: latitude, lng: longitude},
            map: map,
            title: String(event.event_id || ''),
            icon: {
                url: '/static/img/event_red.png',
                scaledSize: new google.maps.Size(20, 20)
            }
        });
        attachInfoWindow(marker, event);
        markers.push(marker); // Add marker to the array
    });
}

function attachInfoWindow(marker, event) {
    var infoWindow = new google.maps.InfoWindow({
        content: `
            <div class="text-center">
                <strong>Event ID: ${event.event_id ?? '-'}</strong><br>
                <strong>მიწისძვრის დრო: ${event.origin_time}</strong><br>
                <strong>მაგნიტუდა (ML): ${event.ml}</strong><br>
                <strong>სიღრმე (km): ${event.depth}</strong><br>
                <strong>ლათიტუდა: ${event.latitude}</strong><br>
                <strong>ლონგიტუდა: ${event.longitude}</strong><br>
                <strong>რეგიონი: ${event.region_ge || event.region_en || '-'}</strong><br>
            </div>`
    });
    marker.addListener('click', function() {
        infoWindow.open(map, marker);
    });
}

// Initialize the map when the page loads
document.addEventListener("DOMContentLoaded", function() {
    initMap();
    });
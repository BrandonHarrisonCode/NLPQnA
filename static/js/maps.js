var map;
var marker;
var circle;
const metersPerMile = 1609.344;
const radius = 150 * metersPerMile;

function initMap() {
    var latitude = 47.6918452
    var longitude = -122.2226413
    map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: latitude, lng: longitude},
        zoom: 6,
    });

    map.addListener('click', function(event) {
        placeMarker(event.latLng, map);
    });
}

function placeMarker(location, map) {
    if(marker != null) {
        removeFromMap(marker);
    }
    if(circle != null) {
        removeFromMap(circle);
    }

    marker = new google.maps.Marker({
        position: location,
        map: map,
    });
    circle = new google.maps.Circle({
        map: map,
        radius: radius,
        fillColor: '#228B22', // Forest green
        strokeColor: '#1B4D3E', // Brunswick green
        strokeOpacity: .8,
    });
    circle.bindTo('center', marker, 'position');
    map.panTo(location);

    circle.addListener('click', function(event) {
        placeMarker(event.latLng, circle.getMap());
    });

    var url = new URL(window.location.origin + '/parksNearby');
    var params = {latitude: location.lat(), longitude: location.lng(), radius: radius}
    url.search = new URLSearchParams(params)
    fetch(url)
        .then(data=>{return data.json()})
        .then(res=>{console.log(res)})
}

function removeFromMap(object) {
    object.setMap(null);
    object = null;
}

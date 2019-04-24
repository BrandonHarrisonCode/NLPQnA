var map;
var marker;
var circle;
const metersPerMile = 1609.344;
const defaultRadius = 150 * metersPerMile;
const maxRadius = 300 * metersPerMile;

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
    oldMarker = marker;
    oldCircle = circle;
    marker = new google.maps.Marker({
        position: location,
        map: map,
    });
    circle = new google.maps.Circle({
        map: map,
        radius: oldCircle == null ? defaultRadius : oldCircle.getRadius(),
        editable: true,
        fillColor: '#228B22', // Forest green
        strokeColor: '#1B4D3E', // Brunswick green
        strokeOpacity: .8,
    });
    circle.bindTo('center', marker, 'position');
    map.panTo(location);

    circle.addListener('click', function(event) {
        placeMarker(event.latLng, this.getMap());
    });
    circle.addListener('radius_changed',function(){
        if (this.getRadius() > maxRadius) {
            this.setRadius(maxRadius);
        }

        getParksNearby();
    });

    getParksNearby();

    if(oldMarker != null) {
        removeFromMap(oldMarker);
    }
    if(oldCircle != null) {
        removeFromMap(oldCircle);
    }
}

function getParksNearby() {
    var url = new URL(window.location.origin + '/parksNearby');
    const latitude = marker.getPosition().lat();
    const longitude = marker.getPosition().lng();
    const radius = circle.getRadius()
    var params = {latitude: latitude, longitude: longitude, radius: radius}
    url.search = new URLSearchParams(params)
    fetch(url)
        .then(data=>{return data.json()})
        .then(res=>{console.log(res)})
}

function removeFromMap(object) {
    object.setMap(null);
    object = null;
}

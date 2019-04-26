var map;
var marker;
var circle;
var parkMarkers;
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

    controlDiv = createControlDiv();
    map.controls[google.maps.ControlPosition.BOTTOM_CENTER].push(controlDiv);
}

function createControlDiv() {
    // Create a div to hold everything else
    var controlDiv = document.createElement('div');
    controlDiv.id = "controls";
    controlDiv.style.width = "60%";

    var row = document.createElement('div');
    row.classList.add("input-group");
    row.classList.add("mb-3");

    // Create an input field
    var controlInput = document.createElement('input');
    controlInput.type = "text";
    controlInput.classList.add("form-control");
    controlInput.id = "question";
    controlInput.name = "question";
    controlInput.placeholder = "What do you want to know?";

    var submitDiv = document.createElement('div');
    submitDiv.classList.add("input-group-btn");

    // Create a button to send the information
    var controlButton = document.createElement('button');
    controlButton.classList.add("btn");
    controlButton.classList.add("btn-primary");
    controlButton.type = "button";
    controlButton.innerHTML = 'Ask!';

    submitDiv.appendChild(controlButton);
    row.appendChild(controlInput);
    row.appendChild(submitDiv);
    controlDiv.appendChild(row);

    controlButton.addEventListener('click', function(event) {
        askQuestion(controlInput.value);
    }, false);

    return controlDiv;
}

function askQuestion(question) {
    var url = new URL(window.location.origin + '/ask');
    var names = parkMarkers.map(x => x.getTitle())
    var payload = {parks: names, question: question}
    fetch(url, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
    })
        .then(data=>{return data.json()})
        .then(res=>{console.log(res)})
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
        .then(res=>{markParks(res)})
}

function removeFromMap(object) {
    if(object == null) {
        return;
    }
    object.setMap(null);
    object = null;
}

function markParks(parks) {
    if(parkMarkers != null) {
        parkMarkers.map(removeFromMap);
    }

    parkMarkers = parks.map(createParksMarker);
}

function createParksMarker(park) {
    if(park == null) {
        return null;
    }

    var icon = {
        url: 'https://image.flaticon.com/icons/png/512/8/8181.png',
        scaledSize: new google.maps.Size(50, 50), // scaled size
    };

    var parkMarker = new google.maps.Marker({
        position: {lat: park.latitude, lng: park.longitude},
        map: map,
        icon: icon,
        title: park.name,
    });

    return parkMarker;
}

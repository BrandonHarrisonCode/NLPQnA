var map;
var center;
var circle;
var parkMarkers;
const metersPerMile = 1609.344;
const defaultRadius = 150 * metersPerMile;
const maxRadius = 300 * metersPerMile;
const confidenceThreshold = 1000;

function initMap() {
    var latitude = 47.6918452
    var longitude = -122.2226413
    map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: latitude, lng: longitude},
        zoom: 6,
    });

    map.addListener('click', function(event) {
        placeCenter(event.latLng, map);
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
        .then(res=>{addInfoWindows(res)})
}

function placeCenter(location, map) {
    oldCenter = center;
    oldCircle = circle;

    center = new google.maps.Marker({
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
    circle.bindTo('center', center, 'position');
    map.panTo(location);

    circle.addListener('click', function(event) {
        placeCenter(event.latLng, this.getMap());
    });
    circle.addListener('radius_changed',function(){
        if (this.getRadius() > maxRadius) {
            this.setRadius(maxRadius);
        }

        getParksNearby();
    });

    getParksNearby();

    if(oldCenter != null) {
        removeFromMap(oldCenter);
    }
    if(oldCircle != null) {
        removeFromMap(oldCircle);
    }
}

function getParksNearby() {
    var url = new URL(window.location.origin + '/parksNearby');
    const latitude = center.getPosition().lat();
    const longitude = center.getPosition().lng();
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
    if(typeof(object.setMap) !== "undefined") {
        object.setMap(null);
    }
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
        position: {lat: park.lat, lng: park.lng},
        map: map,
        icon: icon,
        title: park.name,
    });

    return parkMarker;
}

function addInfoWindows(parks) {
    parks.map(createInfoWindow);
}

function createInfoWindow(park) {
    var answer = park.answer;
    var answerText = "<b>No answer found.</b>";
    var confidence = 0;
    if(answer != null) {
        confidence = answer[2];
        console.log(park.name + ": " + confidence);
        if(confidence >= confidenceThreshold) {
            answerText = String(answer[0]);
        }
    }

    var content = "<b>" + park.name + ":</b> " + answerText
    var infoWindow = new google.maps.InfoWindow({
        content: content
    });

    var marker = parkMarkers.find(x => x.getTitle() === park.name);
    if(marker.infoWindow != null) {
        marker.infoWindow.close();
    }
    marker.infoWindow = infoWindow;
    marker.addListener('click', function() {
        this.setAnimation(null);
        this.infoWindow.open(map, marker);
    });

    if(confidence >= confidenceThreshold) {
        marker.setAnimation(google.maps.Animation.BOUNCE);
    }

    return infoWindow;
}

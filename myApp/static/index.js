/** function initalizes page by selecting the correct box for the dropdown 
    ensures the dispay is correct for the users data
*/
function initalize(id, dur){
    var dropdown = document.getElementById("testerIds");
    for(let i = 0; i < dropdown.childElementCount; i++){
        if (id == dropdown.children[i].value){
            dropdown.children[i].selected = true; 
        }
    } 
    if (dur != ''){
        var dur_dropdown = document.getElementById("duration");
        for(let i = 0; i < dur_dropdown.childElementCount; i++){
            if (dur == dur_dropdown.children[i].value){
                dur_dropdown.children[i].selected = true; 
            }
        } 
    }
}

function sendData(){
    var id = document.getElementById("testerIds").value;
    var frequency = document.getElementById("freq").value;
    var data = {"id": id, "frequency": frequency};
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            document.getElementById("freq-resp").innerHTML = this.response;
       }
    };
    xhttp.open("POST", "/update_freq", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.send(JSON.stringify(data));
}

function upload(){
    var xhttp = new XMLHttpRequest();
    var time = new Date();
    var data = {"time": time.getTime(), "pH": 6.8, "TDS": 100, "coliform": true};
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            document.getElementById("upload-resp").innerHTML = this.response;
       }
    };
    xhttp.open("POST", "/upload", true);
    xhttp.setRequestHeader("Content-type", "application/json");
    xhttp.send(JSON.stringify(data));
}
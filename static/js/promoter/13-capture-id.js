async function startCamera() {
    let video = document.querySelector("#video");
    let camera_button = document.querySelector("#start-camera");
    let click_button = document.querySelector("#click-photo");
    let canvas = document.querySelector("#canvas");

   	let stream = null;

    try {
    	stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    }
    catch(error) {
    	alert(error.message);
    	return;
    }

    video.srcObject = stream;

    video.style.display = 'block';
    camera_button.style.display = 'none';
    click_button.style.display = 'block';
}

function capturePhoto() {
    let video = document.querySelector("#video");
    let canvas = document.querySelector("#canvas");
    let approve_button = document.querySelector("#approve-photo");

    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    approve_button.style.display = 'block';
}

function savePhoto() {
    let canvas = document.querySelector("#canvas");

    canvas.toBlob((blob) => {
      var data = new FormData()
      data.append('file', blob, 'cam_image.jpg');


      fetch('/promoter/captureid', {
          method: 'POST',
          body: data
      });
      //.then(response => response.json()
      //).then(json => {
      //    console.log(json)
      //});

    }, 'image/jpeg', 0.95);
}

document.addEventListener('DOMContentLoaded', function() {
  setTimeout(startCamera(), 3000);
}, false);
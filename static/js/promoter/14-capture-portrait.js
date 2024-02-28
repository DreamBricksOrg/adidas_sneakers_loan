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

async function savePhoto() {
    let canvas = document.querySelector("#canvas");

    try {
        const blob = await new Promise((resolve, reject) => {
            canvas.toBlob(resolve, 'image/jpeg', 0.95);
        });

        const publicKey = getRsaPublicKey();
        const blobArray = await blob.arrayBuffer();
        const encryptedBlob = await dbEncryptByte(blobArray, publicKey);
        var data = new FormData();
        data.append('file', new Blob([encryptedBlob], {type:"application/octet-stream"}), "image.bin");

        const response = await fetch('/promoter/captureportrait', {
            method: 'POST',
            body: data
        });

        if (response.ok) {
            // Se a solicitação foi bem-sucedida, redirecione para outra página
            window.location.href = '/promoter/aproverental';
        } else {
            // Se a solicitação falhou, exiba uma mensagem de erro ou tome outra ação apropriada
            console.error('Erro ao enviar foto');
        }
    } catch (error) {
        console.error('Erro ao enviar foto:', error);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(startCamera(), 3000);
}, false);

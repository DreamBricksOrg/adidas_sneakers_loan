var html5QrCode = null;

function onScanSuccess(decodedText, decodedResult) {
  // handle the scanned code as you like, for example:
  console.log("Code matched = ${decodedText}", decodedResult);
  try {
    const url = new URL(decodedText);
    const estandeId = url.searchParams.get('estande');

    if (estandeId != null) {
        document.getElementById("demo").innerHTML = "<h2>" + estandeId + "</h2>";
        //document.getElementById("qrcode_out").value = decodedText;
        html5QrCode.stop();
        post('/promoter/start', {estande: estandeId});
    }
  }
  catch(e) {
    alert(e);
  }
}

function onScanFailure(error) {
  // handle scan failure, usually better to ignore and keep scanning.
  // for example:
  console.warn("Code scan error = ${error}");
}

async function startScan() {
    html5QrCode = new Html5Qrcode("reader");
    const config = { fps: 10, qrbox: { width: 200, height: 300 } };

    // If you want to prefer back camera
    html5QrCode.start({ facingMode: "environment" }, config, onScanSuccess, onScanFailure);
}

document.addEventListener('DOMContentLoaded', function() {
  setTimeout(startScan(), 3000);
}, false);

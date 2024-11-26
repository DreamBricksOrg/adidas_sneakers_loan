var html5QrCode = null;

function onScanSuccess(decodedText, decodedResult) {
  // handle the scanned code as you like, for example:
  console.log("Code matched = ${decodedText}", decodedResult);
  try {
    // replace single quotes by double quotes for correct JSON parsing
    const decodedText2 = decodedText.replaceAll("'", '"');
    const obj = JSON.parse(decodedText2);
    const user_id = obj.user_id;
    const tenis_id = obj.tenis_id;

    if (user_id != null && tenis_id != null) {
        document.getElementById("demo").innerHTML = "<h2>" + user_id + " / " + tenis_id + "</h2>";
        html5QrCode.stop();
        post('/promoter/scanreturn', {user_id: user_id, tenis_id: tenis_id});
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

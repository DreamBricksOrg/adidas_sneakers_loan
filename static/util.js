const uint8ArrayfromHexString = (hexString) => Uint8Array.from(hexString.match(/.{1,2}/g).map((byte) => parseInt(byte, 16)));

function _base64StringToArrayBuffer(b64str) {
    const byteStr = atob(b64str);
    const bytes = new Uint8Array(byteStr.length);
    for (let i = 0; i < byteStr.length; i++) {
        bytes[i] = byteStr.charCodeAt(i);
    }
    return bytes.buffer;
}

function _arrayBufferToBase64(arrayBuffer) {
    const byteArray = new Uint8Array(arrayBuffer);
    let byteString = '';
    for (let i = 0; i < byteArray.byteLength; i++) {
        byteString += String.fromCharCode(byteArray[i]);
    }
    const b64 = window.btoa(byteString);
    return b64;
}

const _arrayBufferFromHexString = (hexString) => {
    const bytes = Uint8Array.from(hexString.match(/.{1,2}/g).map((byte) => parseInt(byte, 16)));
    return bytes.buffer;
};

const _stringToArrayBuffer = (str) => {
    const encoder = new TextEncoder();
    return encoder.encode(str).buffer;
};

const _stringFromArrayBuffer = (buffer) => {
    const decoder = new TextDecoder();
    return decoder.decode(buffer);
};

const _arrayBufferToHexString = (buffer) => {
    const byteArray = new Uint8Array(buffer);
    const hexCodes = [...byteArray].map(value => {
        const hexCode = value.toString(16);
        const paddedHexCode = hexCode.padStart(2, '0');
        return paddedHexCode;
    });
    return hexCodes.join('');
};

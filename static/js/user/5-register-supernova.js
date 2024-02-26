
async function submitFormJs() {

    nome = sanitize(document.getElementById("nome").value);
    email = sanitize(document.getElementById("email").value);
    data_nascimento = sanitize(document.getElementById("data_nascimento").value);
    documento = sanitize(document.getElementById("documento").value);
    telefone = sanitize(document.getElementById("telefone").value);
    genero = sanitize(document.getElementById("genero").value);

    nome_iniciais = getNameInitials(nome);
    documento_masq = maskDocument(documento);

    dataToEncrypt = nome + "," + email + "," + data_nascimento + "," + documento + "," + telefone + "," + genero;

    rsa_public_key = getRsaPublicKey();
    dataEncrypted = await dbEncryptString(dataToEncrypt, rsa_public_key);

    console.log(nome_iniciais)
    console.log(documento_masq)
    console.log(dataEncrypted);

    post('/user_register', {nome_iniciais: nome_iniciais, documento: documento_masq, telefone: telefone, dados_criptografados: dataEncrypted});
}
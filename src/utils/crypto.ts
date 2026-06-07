// Client-side JWT generator using SubtleCrypto (Web Crypto API)
// Compatible with the FastAPI backend JWT authentication system

function base64url(source: ArrayBuffer | string): string {
  let binary = "";
  if (typeof source === "string") {
    // string input (JSON)
    binary = btoa(unescape(encodeURIComponent(source)));
  } else {
    // ArrayBuffer signature input
    const bytes = new Uint8Array(source);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    binary = btoa(binary);
  }
  return binary.replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}

async function signHMAC(message: string, secret: string): Promise<string> {
  const enc = new TextEncoder();
  const keyData = enc.encode(secret);
  const messageData = enc.encode(message);

  const key = await window.crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "HMAC", hash: { name: "SHA-256" } },
    false,
    ["sign"]
  );

  const signature = await window.crypto.subtle.sign(
    "HMAC",
    key,
    messageData
  );

  return base64url(signature);
}

export async function generateToken(user: { id: number; email: string; role: string }): Promise<string> {
  const header = { alg: "HS256", typ: "JWT" };
  const exp = Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 7; // 7 days expiration

  const payload = {
    exp,
    id: user.id,
    email: user.email,
    role: user.role
  };

  const headerStr = base64url(JSON.stringify(header));
  const payloadStr = base64url(JSON.stringify(payload));
  const message = `${headerStr}.${payloadStr}`;
  
  // Use the static JWT_SECRET matching settings.JWT_SECRET in config.py
  const secret = "hrms_super_secret_key_12345";
  const signatureStr = await signHMAC(message, secret);

  return `${message}.${signatureStr}`;
}

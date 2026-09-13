# PicCall mobile shell (Expo / React Native)

Hits the same PicCall API as the web app.

```bash
# terminal 1
python3 backend/server.py

# terminal 2
cd mobile
npm install
# phone on the same Wi-Fi: point at your laptop
EXPO_PUBLIC_API_URL=http://YOUR_LAN_IP:8787 npx expo start
```

- Search name / street / `#Hashtag`
- Lookup a raw phone number
- Open storefront, interior, parking, night shots
- Rate safety
- `Call #Hashtag` uses the native dialer (`tel:`)

`src/api.js` resolves the API host from `EXPO_PUBLIC_API_URL`, then the Expo packager host, then `127.0.0.1:8787` (simulator only).

# PicCall (`piccall.app`)

See the destination before you call it. Businesses publish interior, parking, and night photos plus a short **#hashtag**. The listing number is proven with SMS. Customers rate how safe arriving felt. New users can paste a phone number and read that rating before they drive.

Safety index, stores nearby, a 3-stop one-trip shop, and a low-level FAQ brain (PicCall Grok) live on the same app.

## Run the web + API

```bash
python3 backend/server.py
```

- Landing — http://127.0.0.1:8787/
- Customer web app — http://127.0.0.1:8787/app.html
- Business dashboard — http://127.0.0.1:8787/business.html

Port: `PICCALL_PORT=9000`.

## Photo upload

`POST /api/photos` as `multipart/form-data`:

| field | notes |
|---|---|
| `file` | jpeg / png / webp / gif, max 8 MB |
| `slot` | `storefront` · `interior` · `parking` · `night` |
| `verifyToken` | after SMS verify, before the profile exists |
| `businessId` | attach to an existing listing |

Files land in `backend/data/uploads/` and are served at `/uploads/<file>`.

## SMS verification of the business line

1. `POST /api/verify/start` `{ "phone": "+15595550140" }`
2. Owner receives a 6-digit code
3. `POST /api/verify/confirm` `{ "phone", "code" }` → `{ verifyToken }`
4. `POST /api/businesses` must include that `verifyToken` and the same number

If `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_FROM` are set, the code is sent through Twilio. Otherwise the API is in demo mode and returns `demoCode` in the start response (shown on the business dashboard).

## API

| Method | Path | Notes |
|---|---|---|
| GET | `/api/health` | `{ sms: "twilio" \| "demo" }` |
| GET | `/api/businesses` | Public profiles |
| GET | `/api/businesses/:id` | One profile |
| GET | `/api/search?q=` | Name, tag, street, phone |
| GET | `/api/lookup?phone=` | Safety check by number |
| GET | `/api/hashtag/:tag` | Resolve `#HarborOak` |
| GET | `/api/nearby?lat=&lng=&radius=` | Stores nearby + miles + safety index |
| GET | `/api/recommend?lat=&lng=` | Ranked by index, distance, specials |
| POST | `/api/verify/start` | Text a code to the business line |
| POST | `/api/verify/confirm` | Exchange code for `verifyToken` |
| POST | `/api/photos` | Multipart photo for a slot |
| POST | `/api/businesses` | Create listing (`verifyToken` required) |
| POST | `/api/ratings` | `{ businessId, stars, comment }` |
| POST | `/api/specials` | `{ businessId, title, body, until }` |
| POST | `/api/trip` | `{ lat, lng, needs: ["pharmacy","restaurant","auto"] }` → 3-stop loop |
| POST | `/api/faq` | Low-level PicCall Grok FAQ `{ question }` |

## React Native shell

`mobile/` is an Expo app against this API. See `mobile/README.md`.

```bash
cd mobile
npm install
EXPO_PUBLIC_API_URL=http://YOUR_LAN_IP:8787 npx expo start
```

## What this is not

Not a carrier, App Store build, or payment processor. Hashtag calls use the device `tel:` link. Sample listings are Central Valley fiction for walkthroughs.

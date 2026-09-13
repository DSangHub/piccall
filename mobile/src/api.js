import { NativeModules, Platform } from "react-native";

const fromEnv = process.env.EXPO_PUBLIC_API_URL;
const scriptURL = NativeModules.SourceCode?.scriptURL || "";
const packagerHost = (scriptURL.match(/https?:\/\/([^:/]+)/) || [])[1];

export const API_URL = (
  fromEnv ||
  (packagerHost && packagerHost !== "127.0.0.1" && packagerHost !== "localhost"
    ? `http://${packagerHost}:8787`
    : "http://127.0.0.1:8787")
).replace(/\/$/, "");

function mediaUrl(path) {
  if (!path) return path;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return API_URL + path;
}

async function api(path, opts = {}) {
  const res = await fetch(API_URL + path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.error || "request_failed");
    err.data = data;
    err.status = res.status;
    throw err;
  }
  return data;
}

function hydrate(b) {
  if (!b) return b;
  const photos = {};
  Object.entries(b.photos || {}).forEach(([k, v]) => {
    photos[k] = mediaUrl(v);
  });
  return { ...b, photos };
}

export const PicCall = {
  apiUrl: API_URL,
  platform: Platform.OS,
  list: async () => {
    const data = await api("/api/businesses");
    return { businesses: (data.businesses || []).map(hydrate) };
  },
  search: async (q) => {
    const data = await api("/api/search?q=" + encodeURIComponent(q || ""));
    return { ...data, businesses: (data.businesses || []).map(hydrate) };
  },
  lookup: async (phone) => {
    const data = await api("/api/lookup?phone=" + encodeURIComponent(phone));
    return { ...data, business: hydrate(data.business) };
  },
  byHash: async (tag) => hydrate(await api("/api/hashtag/" + encodeURIComponent(String(tag).replace(/^#/, "")))),
  get: async (id) => hydrate(await api("/api/businesses/" + encodeURIComponent(id))),
  rate: async (payload) =>
    hydrate(
      await api("/api/ratings", {
        method: "POST",
        body: JSON.stringify(payload),
      })
    ),
};

export function scoreLabel(n) {
  if (n >= 4.6) return "Very safe";
  if (n >= 4.0) return "Mostly safe";
  if (n >= 3.2) return "Use care";
  if (n > 0) return "Go with someone";
  return "Unrated";
}

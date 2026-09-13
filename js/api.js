const API = "";

async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(data.error || "request_failed"), { data, status: res.status });
  return data;
}

const PicCall = {
  list: () => api("/api/businesses"),
  search: (q) => api("/api/search?q=" + encodeURIComponent(q || "")),
  lookup: (phone) => api("/api/lookup?phone=" + encodeURIComponent(phone)),
  byHash: (tag) => api("/api/hashtag/" + encodeURIComponent(String(tag).replace(/^#/, ""))),
  get: (id) => api("/api/businesses/" + encodeURIComponent(id)),
  rate: (payload) => api("/api/ratings", { method: "POST", body: JSON.stringify(payload) }),
  special: (payload) => api("/api/specials", { method: "POST", body: JSON.stringify(payload) }),
  create: (payload) => api("/api/businesses", { method: "POST", body: JSON.stringify(payload) }),
  verifyStart: (phone) => api("/api/verify/start", { method: "POST", body: JSON.stringify({ phone }) }),
  verifyConfirm: (phone, code) => api("/api/verify/confirm", { method: "POST", body: JSON.stringify({ phone, code }) }),
  nearby: (lat, lng, radius = 8) =>
    api(`/api/nearby?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}&radius=${radius}`),
  recommend: (lat, lng) =>
    api(`/api/recommend?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}`),
  trip: (payload) => api("/api/trip", { method: "POST", body: JSON.stringify(payload) }),
  faq: (question, extra = {}) =>
    api("/api/faq", { method: "POST", body: JSON.stringify({ question, ...extra }) }),
  uploadPhoto: async (fields) => {
    const fd = new FormData();
    Object.entries(fields).forEach(([k, v]) => {
      if (v != null) fd.append(k, v);
    });
    const res = await fetch(API + "/api/photos", { method: "POST", body: fd });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error || "upload_failed"), { data, status: res.status });
    return data;
  },
};

function toast(msg) {
  let el = document.querySelector(".toast");
  if (!el) {
    el = document.createElement("div");
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.style.display = "block";
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (el.style.display = "none"), 2400);
}

function scoreLabel(n) {
  if (n >= 4.6) return "Very safe";
  if (n >= 4.0) return "Mostly safe";
  if (n >= 3.2) return "Use care";
  if (n > 0) return "Go with someone";
  return "Unrated";
}

function telHref(phone) {
  return "tel:" + String(phone).replace(/[^\d+]/g, "");
}

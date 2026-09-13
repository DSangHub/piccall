const $ = (s) => document.querySelector(s);
let tier = "standard";
let verifyToken = "";
let verifiedPhone = "";

document.querySelectorAll("[data-tier]").forEach((el) => {
  el.onclick = () => {
    tier = el.dataset.tier;
    document.querySelectorAll("[data-tier]").forEach((c) => c.classList.toggle("picked", c === el));
  };
});

function setStatus(html, ok = false) {
  const el = $("#verify-status");
  el.innerHTML = html;
  el.className = ok ? "badge-ok" : "muted";
}

$("#send-code").onclick = async () => {
  const phone = $("#phone").value;
  try {
    const res = await PicCall.verifyStart(phone);
    $("#code-row").hidden = false;
    if (res.demo && res.demoCode) {
      setStatus(`Demo SMS · code <strong>${res.demoCode}</strong> for ${res.phone}`);
      $("#sms-code").value = res.demoCode;
    } else {
      setStatus(`Code sent to ${res.phone} via ${res.provider}.`);
    }
    toast("Code sent");
  } catch (err) {
    toast(err.data?.error || "Could not send code");
  }
};

$("#confirm-code").onclick = async () => {
  try {
    const res = await PicCall.verifyConfirm($("#phone").value, $("#sms-code").value);
    verifyToken = res.verifyToken;
    verifiedPhone = res.phone;
    setStatus(`Verified ${res.phone}`, true);
    $("#publish").disabled = false;
    toast("Phone verified");
  } catch (err) {
    const map = {
      bad_code: "Wrong code",
      code_expired: "Code expired — send a new one",
      no_pending_code: "Send a code first",
      too_many_attempts: "Too many tries",
    };
    toast(map[err.data?.error] || "Verify failed");
  }
};

document.querySelectorAll("#photo-slots input").forEach((input) => {
  input.addEventListener("change", async () => {
    const file = input.files && input.files[0];
    if (!file) return;
    const img = input.parentElement.querySelector("img");
    img.src = URL.createObjectURL(file);
    if (!verifyToken) {
      toast("Verify the phone, then the photo will upload");
      return;
    }
    try {
      const res = await PicCall.uploadPhoto({
        slot: input.dataset.slot,
        file,
        verifyToken,
      });
      img.src = res.url;
      toast(input.dataset.slot + " uploaded");
    } catch (err) {
      toast(err.data?.error || "Upload failed");
    }
  });
});

$("#biz-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!verifyToken) return toast("Verify the business number first");
  const fd = new FormData(e.target);
  const payload = {
    name: fd.get("name"),
    phone: verifiedPhone || fd.get("phone"),
    hashtag: fd.get("hashtag"),
    category: fd.get("category"),
    address: fd.get("address"),
    hours: fd.get("hours"),
    safetyNotes: fd.get("safetyNotes"),
    cameras: fd.get("cameras") === "on",
    wellLit: fd.get("wellLit") === "on",
    nightSafe: fd.get("nightSafe") === "on",
    staffedNight: fd.get("staffedNight") === "on",
    feeTier: tier,
    verifyToken,
  };
  try {
    const biz = await PicCall.create(payload);
    $("#result").hidden = false;
    $("#result").innerHTML = `
      <h3>You're live as #${biz.hashtag}</h3>
      <p>${biz.phoneVerified ? "Number verified by SMS." : ""} Customers call without hunting a number.</p>
      <p class="hash">#${biz.hashtag} → ${biz.phoneDisplay}</p>
      <a class="btn btn-amber" href="app.html#${biz.hashtag}">Preview public profile</a>
    `;
    toast("Profile created");
    verifyToken = "";
    $("#publish").disabled = true;
    e.target.reset();
  } catch (err) {
    const map = {
      hashtag_taken: "That hashtag is taken",
      phone_not_verified: "Verify the business number first",
    };
    toast(map[err.data?.error] || "Could not create profile");
  }
});

$("#special-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const list = await PicCall.search(fd.get("who"));
    const biz = list.businesses[0];
    if (!biz) return toast("Business not found");
    await PicCall.special({
      businessId: biz.id,
      title: fd.get("title"),
      body: fd.get("body"),
      until: fd.get("until"),
    });
    toast("Special posted to #" + biz.hashtag);
  } catch {
    toast("Could not post special");
  }
});

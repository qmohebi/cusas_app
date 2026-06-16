// global CSRF header to manage the HTMX

function getCookie(name) {
  const m = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]+)"));
  return m ? decodeURIComponent(m[2]) : null;
}
document.body.addEventListener("htmx:configRequest", (e) => {
  const token = getCookie("csrftoken");
  if (token) e.detail.headers["X-CSRFToken"] = token;
});

function showSuccessModal(payload, modalId = "successModal") {
  const modalEl = document.getElementById(modalId);
  if (!modalEl) return;

  // title
  const titleEl = modalEl.querySelector(".modal-success-msg");
  if (titleEl && payload?.title) titleEl.textContent = payload.title;

  // items
  const listEl = modalEl.querySelector(".success-modal-items");
  if (listEl) {
    listEl.innerHTML = "";
    (payload?.items || []).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      listEl.appendChild(li);
    });
  }

  const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
  modal.show();
}

document.addEventListener("DOMContentLoaded", () => {
  const payloadEl = document.getElementById("success-modal-payload");
  if (!payloadEl) return;

  let payload;
  try {
    payload = JSON.parse(payloadEl.textContent);
  } catch (e) {
    console.error("Invalid success modal payload JSON", e);
    return;
  }

  // payload: { title, items, modalId?, redirectUrl? }
  showSuccessModal(
    { title: payload.title, items: payload.items },
    payload.modalId || "successModal"
  );

  // Optional redirect on close
  if (payload.redirectUrl) {
    const modalEl = document.getElementById(payload.modalId || "successModal");
    if (modalEl) {
      modalEl.addEventListener(
        "hidden.bs.modal",
        () => (window.location.href = payload.redirectUrl),
        { once: true }
      );
    }
  }
});

// Footer date
const currentYear = new Date().getFullYear();
$("#current-year").text(currentYear);

const itemsBody = document.querySelector("#items");
const emptyState = document.querySelector("#empty-state");
const errorMessage = document.querySelector("#error-message");
const formError = document.querySelector("#form-error");
let activeStatus = "";
let searchTimer;
let editingId = null;

function showError(element, message) {
  element.textContent = message;
  element.hidden = false;
}

function dateLabel(value) {
  if (!value) return { text: "No date set", kind: "" };
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const expiry = new Date(`${value}T00:00:00`);
  const days = Math.round((expiry - today) / 86400000);
  if (days < 0) return { text: `${Math.abs(days)}d ago`, kind: "expired" };
  if (days === 0) return { text: "Today", kind: "soon" };
  if (days <= 7) return { text: `${days}d left`, kind: "soon" };
  return { text: expiry.toLocaleDateString(undefined, { month: "short", day: "numeric" }), kind: "" };
}

function renderItems(items) {
  itemsBody.replaceChildren();
  for (const item of items) {
    const row = document.createElement("tr");
    const itemCell = document.createElement("td");
    const itemWrap = document.createElement("div");
    itemWrap.className = "item-cell";
    const dot = document.createElement("span");
    dot.className = "item-dot";
    dot.textContent = item.name.slice(0, 1).toUpperCase();
    const nameWrap = document.createElement("div");
    const name = document.createElement("div");
    name.className = "item-name";
    name.textContent = item.name;
    const category = document.createElement("div");
    category.className = "item-category";
    category.textContent = item.category;
    nameWrap.append(name, category);
    itemWrap.append(dot, nameWrap);
    itemCell.append(itemWrap);

    const quantity = document.createElement("td");
    quantity.textContent = `${item.quantity} ${item.unit}`;
    const dateCell = document.createElement("td");
    const date = dateLabel(item.expires_on);
    const pill = document.createElement("span");
    pill.className = `date-pill ${date.kind}`;
    pill.textContent = date.text;
    dateCell.append(pill);
    const action = document.createElement("td");
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "edit-button";
    edit.textContent = "Edit";
    edit.addEventListener("click", () => editItem(item));
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "delete-button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Remove ${item.name}`);
    remove.addEventListener("click", () => deleteItem(item.id));
    action.append(edit, remove);
    row.append(itemCell, quantity, dateCell, action);
    itemsBody.append(row);
  }
  emptyState.hidden = items.length > 0;
  document.querySelector("#item-total").textContent = items.length;
}

async function loadItems() {
  errorMessage.hidden = true;
  const params = new URLSearchParams();
  const search = document.querySelector("#search").value.trim();
  if (search) params.set("q", search);
  if (activeStatus) params.set("status", activeStatus);
  try {
    const [itemsResponse, summaryResponse] = await Promise.all([
      fetch(`/api/items?${params}`),
      fetch("/api/summary"),
    ]);
    if (!itemsResponse.ok || !summaryResponse.ok) throw new Error("The pantry could not be loaded.");
    const [items, summary] = await Promise.all([itemsResponse.json(), summaryResponse.json()]);
    renderItems(items);
    document.querySelector("#total-count").textContent = summary.total_items;
    document.querySelector("#expiring-count").textContent = summary.expiring_soon;
    document.querySelector("#expired-count").textContent = summary.expired;
  } catch (error) {
    showError(errorMessage, error.message || "The pantry could not be loaded.");
  }
}

async function deleteItem(id) {
  try {
    const response = await fetch(`/api/items/${id}`, { method: "DELETE" });
    if (!response.ok) throw new Error("That item could not be removed.");
    if (editingId === id) resetForm();
    await loadItems();
  } catch (error) {
    showError(errorMessage, error.message || "That item could not be removed.");
  }
}

function editItem(item) {
  editingId = item.id;
  const form = document.querySelector("#item-form");
  for (const [key, value] of Object.entries(item)) {
    const field = form.elements.namedItem(key);
    if (field) field.value = value ?? "";
  }
  document.querySelector("#form-title").innerHTML = 'Update pantry<br>item<span class="period">.</span>';
  document.querySelector("#cancel-edit").hidden = false;
  document.querySelector("#name").focus();
}

function resetForm() {
  editingId = null;
  document.querySelector("#item-form").reset();
  document.querySelector("#quantity").value = "1";
  document.querySelector("#unit").value = "item";
  document.querySelector("#category").value = "Other";
  document.querySelector("#form-title").innerHTML = 'Add to your<br>pantry<span class="period">.</span>';
  document.querySelector("#cancel-edit").hidden = true;
  formError.hidden = true;
}

document.querySelector("#item-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.hidden = true;
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  const payload = {
    ...values,
    quantity: Number(values.quantity),
    expires_on: values.expires_on || null,
  };
  try {
    const response = await fetch(editingId ? `/api/items/${editingId}` : "/api/items", {
      method: editingId ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.[0]?.msg || error.detail || "The item could not be saved.");
    }
    resetForm();
    await loadItems();
  } catch (error) {
    showError(formError, error.message || "The item could not be saved.");
  }
});

document.querySelector("#cancel-edit").addEventListener("click", resetForm);

document.querySelector("#search").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadItems, 180);
});

document.querySelectorAll(".filter").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelector(".filter.active").classList.remove("active");
    button.classList.add("active");
    activeStatus = button.dataset.status;
    loadItems();
  });
});

loadItems();

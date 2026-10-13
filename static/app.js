const $ = (id) => document.getElementById(id);
const COLORS = ["#7c3a1d", "#2f6f8f", "#4b7f52", "#8a4f7d", "#b5651d", "#3d4f7c"];
const EMOJI = { Programming: "💻", "Computer Science": "🧠", DevOps: "🔧", Biography: "👤",
                History: "🏛️", Fiction: "📖", "Self Help": "🌱" };

let books = [], cart = [], category = "All";

function toast(msg, isError = false) {
  const t = $("toast");
  t.textContent = msg; t.className = isError ? "error" : ""; t.style.display = "block";
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.style.display = "none"), 3000);
}

async function loadCategories() {
  const cats = await (await fetch("/api/categories")).json();
  $("chips").innerHTML = "";
  cats.forEach((c) => {
    const b = document.createElement("button");
    b.className = "chip" + (c === category ? " active" : "");
    b.textContent = c;
    b.onclick = () => { category = c; loadCategories(); loadBooks(); };
    $("chips").appendChild(b);
  });
}

async function loadBooks() {
  const q = new URLSearchParams({ search: $("search").value, category });
  books = await (await fetch("/api/books?" + q)).json();
  const grid = $("grid");
  grid.innerHTML = "";
  if (!books.length) { grid.innerHTML = '<div class="empty">No books found.</div>'; return; }
  books.forEach((b, i) => {
    const inCart = cart.some((c) => c.id === b.id);
    const el = document.createElement("div");
    el.className = "book";
    el.innerHTML = `
      <div class="cover" style="background:${COLORS[i % COLORS.length]}">${EMOJI[b.category] || "📕"}</div>
      <h3></h3><div class="meta"></div>
      <span class="tag">${b.category}</span>
      <div class="row">
        <div><strong>₹${b.price_per_day.toFixed(2)}</strong><span class="meta"> /day</span><br>
          <span class="${b.available_copies ? "stock-ok" : "stock-out"}">
            ${b.available_copies ? b.available_copies + " available" : "Out of stock"}</span></div>
        <button ${b.available_copies && !inCart ? "" : "disabled"}>${inCart ? "Added" : "Rent"}</button>
      </div>`;
    el.querySelector("h3").textContent = b.title;
    el.querySelector(".meta").textContent = b.author;
    el.querySelector("button").onclick = () => addToCart(b);
    grid.appendChild(el);
  });
}

function addToCart(b) {
  if (!cart.some((c) => c.id === b.id)) cart.push(b);
  renderCart(); loadBooks();
}
function removeFromCart(id) { cart = cart.filter((c) => c.id !== id); renderCart(); loadBooks(); }

function renderCart() {
  $("count").textContent = cart.length;
  const box = $("cartItems");
  box.innerHTML = cart.length ? "" : '<div class="empty">No books selected yet.</div>';
  const days = Number($("days").value);
  let total = 0;
  cart.forEach((b) => {
    total += b.price_per_day * days;
    const row = document.createElement("div");
    row.className = "cart-item";
    row.innerHTML = `<span></span><span>₹${(b.price_per_day * days).toFixed(2)} <button class="ghost">✕</button></span>`;
    row.firstChild.textContent = b.title;
    row.querySelector("button").onclick = () => removeFromCart(b.id);
    box.appendChild(row);
  });
  $("total").textContent = total.toFixed(2);
  $("rentBtn").disabled = !cart.length;
}

async function confirmRental() {
  const body = {
    member_name: $("name").value, member_id: $("mid").value,
    days: Number($("days").value), book_ids: cart.map((c) => c.id),
  };
  const res = await fetch("/api/rent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) { toast(data.error || "Rental failed", true); return; }
  $("mId").textContent = data.rental_id;
  $("mInfo").textContent = `${data.books.length} book(s) • Due on ${data.due_on} • Total ₹${data.total_amount.toFixed(2)}`;
  $("modalBg").style.display = "flex";
  cart = []; renderCart(); loadBooks();
}

$("search").addEventListener("input", loadBooks);
$("days").addEventListener("change", renderCart);
$("rentBtn").addEventListener("click", confirmRental);
$("mClose").addEventListener("click", () => ($("modalBg").style.display = "none"));
loadCategories(); loadBooks(); renderCart();

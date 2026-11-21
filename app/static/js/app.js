async function load() {
  try {
    drawCameras(await API.list());
  } catch (e) {
    document.getElementById("grid").textContent = e.message;
  }
}

document.getElementById("vendor").onchange = (e) => {
  const urlInput = document.getElementById("url");
  const nameInput = document.getElementById("name");
  if (e.target.value === "laptop") {
    urlInput.value = "local://0";
    if (!nameInput.value) nameInput.value = "Камера ноутбука";
  } else if (urlInput.value === "local://0") {
    urlInput.value = "";
  }
};

document.getElementById("add-laptop").onclick = async () => {
  const btn = document.getElementById("add-laptop");
  btn.disabled = true;
  btn.textContent = "⏳ Поиск камеры ноутбука...";
  try {
    const res = await API.detectLocal();
    const list = document.getElementById("local-list");
    if (!res.cameras || res.cameras.length === 0) {
      // Если автопоиск не дал кадра (например, камера занята), всё равно предложим добавить local://0
      await API.add({ name: "Камера ноутбука", rtsp_url: "local://0", vendor: "laptop" });
      await load();
    } else if (res.cameras.length === 1) {
      const cam = res.cameras[0];
      await API.add({ name: "Камера ноутбука", rtsp_url: cam.url, vendor: "laptop" });
      await load();
    } else {
      list.innerHTML = res.cameras.map(c => `
        <div class="local-item">
          <span>${safe(c.label)}</span>
          <button data-local-url="${c.url}" data-local-name="${safe(c.label)}">Подкл.</button>
        </div>
      `).join("");
      list.querySelectorAll("button").forEach(b => {
        b.onclick = async () => {
          await API.add({ name: b.dataset.localName, rtsp_url: b.dataset.localUrl, vendor: "laptop" });
          list.innerHTML = "";
          await load();
        };
      });
    }
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "📷 Подключить камеру ноутбука";
  }
};

document.getElementById("add").onclick = async () => {
  let name = document.getElementById("name").value.trim(),
      rtsp_url = document.getElementById("url").value.trim(),
      vendor = document.getElementById("vendor").value;
  if (!name || !rtsp_url) return alert("Заполни название и адрес потока (например, local://0)");
  try {
    await API.add({ name, rtsp_url, vendor });
    document.getElementById("name").value = "";
    document.getElementById("url").value = "";
    await load();
  } catch (e) {
    alert(e.message);
  }
};

document.getElementById("refresh").onclick = load;
load();
setInterval(load, 4000);

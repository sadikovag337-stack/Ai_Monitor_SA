const API = {
  async list() {
    let r = await fetch("/api/cameras");
    if (!r.ok) throw Error("Ошибка сервера");
    return r.json();
  },
  async detectLocal() {
    let r = await fetch("/api/local-cameras");
    if (!r.ok) throw Error("Не удалось просканировать камеры");
    return r.json();
  },
  async add(data) {
    let r = await fetch("/api/cameras", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    let j = await r.json();
    if (!r.ok) throw Error(j.detail || "Ошибка");
    return j;
  },
  async remove(id) {
    let r = await fetch("/api/cameras/" + id, { method: "DELETE" });
    if (!r.ok) throw Error("Не удалось удалить");
  }
};

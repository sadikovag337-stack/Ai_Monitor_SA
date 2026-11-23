function safe(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function drawCameras(items){
  let on=items.filter(x=>x.online).length;
  document.getElementById("stats").textContent=`Всего: ${items.length} · В сети: ${on} · Нет сигнала: ${items.length-on}`;
  let grid=document.getElementById("grid");
  if(!items.length){grid.textContent="Добавь первую камеру.";return}
  grid.innerHTML=items.map(c=>{
    const pending=c.vendor==="onvif"&&!c.enabled;
    const status=pending?"ОЖИДАЕТ НАСТРОЙКИ RTSP":c.online?"В СЕТИ":"НЕТ СИГНАЛА";
    const feed=c.online
      ? `<img src="/api/video/${safe(c.id)}" alt="Видео">`
      : safe(pending?"Укажи RTSP-адрес, чтобы подключить камеру.":c.error||"Нет сигнала");
    const configure=c.vendor==="onvif"
      ? `<button class="secondary configure" data-config-id="${safe(c.id)}">Настроить RTSP</button>`
      : "";
    return `<article class="cam"><div class="feed">${feed}</div><div class="info"><div><b>${safe(c.name)}</b><br><small>${status}</small></div><div>${configure}<button class="remove" data-id="${safe(c.id)}">Удалить</button></div></div></article>`;
  }).join("");
  grid.querySelectorAll("[data-id]").forEach(b=>b.onclick=async()=>{
    if(confirm("Удалить камеру?")){await API.remove(b.dataset.id);await load()}
  });
  grid.querySelectorAll("[data-config-id]").forEach(b=>{
    const camera=items.find(c=>c.id===b.dataset.configId);
    b.onclick=()=>window.beginCameraEdit(camera);
  });
}
document.getElementById('analyzeBtn').addEventListener('click', () => {
  const fileInput = document.getElementById('fileInput');
  const errorElem = document.getElementById('error');
  errorElem.textContent = '';
  if (!fileInput.files.length) {
    errorElem.textContent = 'Vui lòng chọn file ZIP PCB.';
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  fetch('/api/analyze', {
    method: 'POST',
    body: formData
  })
  .then(res => {
    if (!res.ok) throw new Error('Lỗi server khi phân tích.');
    return res.json();
  })
  .then(data => {
    displayResults(data);
  })
  .catch(err => {
    errorElem.textContent = err.message;
  });
});

function displayResults(data) {
  // Hiển thị điểm metric
  const metricsDiv = document.getElementById('metrics');
  metricsDiv.innerHTML = `
    <h3>Điểm phân tích</h3>
    <p>F1: ${data.score?.f1 || 'N/A'}</p>
    <p>Precision: ${data.score?.precision || 'N/A'}</p>
    <p>Recall: ${data.score?.recall || 'N/A'}</p>
    <p>Component Assignment Accuracy: ${data.score?.component_acc || 'N/A'}</p>
  `;

  // Hiển thị bảng linh kiện
  const compsBody = document.getElementById('componentsBody');
  compsBody.innerHTML = '';
  if (data.components && data.components.length) {
    data.components.forEach(c => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${c.ref}</td><td>${c.value}</td><td>${c.footprint}</td>`;
      compsBody.appendChild(tr);
    });
  }

  // Hiển thị bảng nets
  const netsBody = document.getElementById('netsBody');
  netsBody.innerHTML = '';
  if (data.nets && data.nets.length) {
    data.nets.forEach(net => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${net.name}</td><td>${net.pins ? net.pins.join(', ') : ''}</td>`;
      netsBody.appendChild(tr);
    });
  }

  // PCB hình mặt top và bottom
  const pcbContainer = document.getElementById('pcbSVGContainer');
  let topSVG = data.layers_svg?.top || '';
  let bottomSVG = data.layers_svg?.bottom || '';
  pcbContainer.innerHTML = topSVG;

  document.getElementById('btnTop').onclick = () => pcbContainer.innerHTML = topSVG;
  document.getElementById('btnBottom').onclick = () => pcbContainer.innerHTML = bottomSVG;

  // Schematic
  const schematicContainer = document.getElementById('schematicSVGContainer');
  schematicContainer.innerHTML = data.schematic_svg || '';
}

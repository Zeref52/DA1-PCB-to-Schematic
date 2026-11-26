// ===== Trạng thái dùng chung =====
let result = null;        // JSON trả về từ /api/analyze
let currentSide = 'top';  // mặt PCB đang xem
let selectedNet = null;   // tên net đang tô sáng

const $ = (id) => document.getElementById(id);

// ===== 1. Gửi file lên API =====
$('analyzeBtn').addEventListener('click', async () => {
  $('error').textContent = '';
  const fileInput = $('fileInput');
  if (!fileInput.files.length) {
    $('error').textContent = 'Vui lòng chọn file ZIP PCB.';
    return;
  }
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  $('analyzeBtn').disabled = true;
  $('status').textContent = 'Đang phân tích...';
  try {
    const res = await fetch('/api/analyze', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok || data.error) {
      throw new Error(data.error || 'Lỗi server khi phân tích.');
    }
    result = data;
    selectedNet = null;
    currentSide = 'top';
    displayResults();
    $('status').textContent = 'Xong.';
  } catch (err) {
    $('error').textContent = 'Lỗi: ' + err.message;
    $('status').textContent = '';
  } finally {
    $('analyzeBtn').disabled = false;
  }
});

// ===== 2. Hiển thị kết quả =====
function fmt(v) {
  return (typeof v === 'number') ? v.toFixed(3) : 'N/A';
}

function displayResults() {
  if (!result) {
    // Khi chưa có kết quả, co khung lại
    $('pcbSVGContainer').classList.add('empty');
    $('nets').classList.add('empty');
    $('pcbSVGContainer').innerHTML = '<p style="color:#666; text-align:center; margin-top:40px;"></p>';
    $('netsBody').innerHTML = '';
    $('selectedNet').textContent = '';
    $('metrics').innerHTML = '';
    $('componentsBody').innerHTML = '';
    $('schematicSVGContainer').innerHTML = '';
    return;
  }

  // Khi có kết quả, bỏ class empty để hiện bình thường
  $('pcbSVGContainer').classList.remove('empty');
  $('nets').classList.remove('empty');

  // Điểm
  const s = result.score;
  $('metrics').innerHTML = s ? `
    <h3>Điểm phân tích</h3>
    <p>F1: <b>${fmt(s.f1)}</b> &nbsp;|&nbsp; Precision: ${fmt(s.precision)}
       &nbsp;|&nbsp; Recall: ${fmt(s.recall)}
       &nbsp;|&nbsp; Net khớp hoàn toàn: ${fmt(s.net_exact_match)}</p>
    <p>Tỷ lệ gán linh kiện đúng: <b>${(s.component_accuracy * 100).toFixed(1)} %</b></p>`
    : '<h3>Điểm phân tích</h3><p>File không có đáp án (netlist attributes) nên không chấm điểm.</p>';

  // Bảng linh kiện
  $('componentsBody').innerHTML = result.components.map(c =>
    `<tr><td>${c.ref}</td><td>${c.value}</td><td>${c.footprint}</td><td>${c.side}</td></tr>`
  ).join('');

  // Bảng net (trường là "pads", không phải "pins")
  $('netsBody').innerHTML = result.nets.map(n =>
    `<tr data-net="${n.name}"><td>${n.name}</td><td>${n.pads.length}</td><td>${n.pads.join(', ')}</td></tr>`
  ).join('');
  document.querySelectorAll('#netsBody tr').forEach(tr => {
    tr.addEventListener('click', () => {
      selectedNet = tr.dataset.net;
      drawPCB();
    });
  });
  // Schematic
  $('schematicSVGContainer').innerHTML = result.schematic_svg || '';

  drawPCB();
}

// ===== 3. Vẽ ảnh PCB + tô sáng net =====
function drawPCB() {
  if (!result) return;
  const box = $('pcbSVGContainer');
  box.innerHTML = result.layers_svg[currentSide] || '';

  // Đánh dấu dòng net đang chọn trong bảng
  document.querySelectorAll('#netsBody tr').forEach(tr =>
    tr.classList.toggle('selected', tr.dataset.net === selectedNet));
  $('selectedNet').textContent = selectedNet ? `(đang tô sáng ${selectedNet})` : '';
  $('btnTop').classList.toggle('active', currentSide === 'top');
  $('btnBottom').classList.toggle('active', currentSide === 'bottom');
  if (!selectedNet) return;

  const g = box.querySelector('svg g');
  if (!g) return;
  const NS = 'http://www.w3.org/2000/svg';
  result.pads
    .filter(p => p.net === selectedNet)
    .filter(p => p.side === currentSide || p.function === 'ComponentPad')
    .forEach(p => {
      const c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', p.x);
      c.setAttribute('cy', p.y);
      c.setAttribute('r', 1.2);
      c.setAttribute('class', 'hl');
      g.appendChild(c);
    });
}

$('btnTop').onclick = () => { currentSide = 'top'; drawPCB(); };
$('btnBottom').onclick = () => { currentSide = 'bottom'; drawPCB(); };
$('btnClear').onclick = () => { selectedNet = null; drawPCB(); };

// ===== 4. Tải netlist =====
function download(filename, text, type) {
  const blob = new Blob([text], { type });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

$('btnJson').onclick = () => {
  if (!result) return;
  const out = { components: result.components, nets: result.nets };
  download('netlist.json', JSON.stringify(out, null, 2), 'application/json');
};

$('btnCsv').onclick = () => {
  if (!result) return;
  const lines = ['net,pad'];
  result.nets.forEach(n => n.pads.forEach(p => lines.push(`${n.name},${p}`)));
  download('netlist.csv', '' + lines.join('\n'), 'text/csv');
};

// Khởi tạo trạng thái ban đầu khi mở trang
displayResults();

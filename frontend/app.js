const API = '/api';

const pageTitles = {
    'dashboard': '控制中心',
    'assets': '音檔與 TTS 管理',
    'schedules': '時間排程與設定'
};

async function fetchAPI(endpoint, options = {}) {
    try {
        const res = await fetch(`${API}${endpoint}`, options);
        if (!res.ok) throw new Error(await res.text());
        return await res.json();
    } catch (e) {
        alert("API 錯誤: " + e.message);
        throw e;
    }
}

let hardwarePollInterval = null;

// ================= Navigation =================
function navigate(view) {
    if (hardwarePollInterval) {
        clearInterval(hardwarePollInterval);
        hardwarePollInterval = null;
    }

    // Update sidebar active state
    document.querySelectorAll('.sidebar nav button').forEach(btn => {
        btn.classList.remove('active');
        // Find button by its onclick function's parameter
        if (btn.getAttribute('onclick')?.includes(`'${view}'`)) {
            btn.classList.add('active');
        }
    });

    document.getElementById('page-title').innerText = pageTitles[view] || 'NPCron';

    const content = document.getElementById('content');
    const tpl = document.getElementById(`tpl-${view}`);
    if (tpl) {
        content.innerHTML = '';
        content.appendChild(tpl.content.cloneNode(true));
        initView(view);
    }
}

function initView(view) {
    if (view === 'dashboard') loadDashboard();
    if (view === 'assets') loadAssets();
    if (view === 'schedules') loadSchedules();
}

// ================= Dashboard =================
async function loadDashboard() {
    const assets = await fetchAPI('/assets/');
    const list = document.getElementById('instant-play-list');
    list.innerHTML = '';
    if (assets.length === 0) {
        list.innerHTML = '<div class="row"><span class="title" style="color:var(--text-muted);">尚無音檔</span></div>';
        return;
    }
    assets.forEach(a => {
        const row = document.createElement('div');
        row.className = 'row';
        row.innerHTML = `
            <span class="title row-label">${a.label}</span>
            <button class="btn btn-primary" onclick="playSound(${a.id})">執行播放</button>
        `;
        list.appendChild(row);
    });

}

async function playSound(id) {
    await fetchAPI(`/system/play/${id}`, { method: 'POST' });
}

async function stopAllAudio() {
    await fetchAPI('/system/stop', { method: 'POST' });
    alert("已送出強制中止指令");
}

// ================= Schedules =================
async function loadSchedules() {
    const assets = await fetchAPI('/assets/');
    const select = document.getElementById('sched-sound');
    if (select) {
        select.innerHTML = '<option value="">請選擇要廣播的音檔...</option>';
        assets.forEach(a => {
            select.innerHTML += `<option value="${a.id}">${a.label}</option>`;
        });
    }

    const schedules = await fetchAPI('/schedules');
    const tbody = document.getElementById('schedules-list');
    if (tbody) {
        tbody.innerHTML = '';
        schedules.forEach(s => {
            const sound = assets.find(a => a.id === s.sound_id) || { label: '未知音檔' };
            const div = document.createElement('div');
            div.className = 'row';
            div.innerHTML = `
                <span class="title" style="font-size:1.05rem; min-width:4rem;">${s.time}</span>
                <div class="row-label">
                    <span class="title">${sound.label}</span>
                    <span class="subtitle">每週執行日: ${s.days_of_week}</span>
                </div>
                <button class="btn btn-danger" onclick="deleteSchedule(${s.id})">移除</button>
            `;
            tbody.appendChild(div);
        });
    }

    const exclusions = await fetchAPI('/exclusions');
    const exBody = document.getElementById('exclusions-list');
    if (exBody) {
        exBody.innerHTML = '';
        exclusions.forEach(ex => {
            const div = document.createElement('div');
            div.className = 'row';
            div.innerHTML = `
                <div class="row-label">
                    <span class="title" style="color:var(--destructive-bg)">${ex.date}</span>
                    <span class="subtitle">${ex.reason}</span>
                </div>
                <button class="btn btn-danger" onclick="deleteExclusion(${ex.id})">移除</button>
            `;
            exBody.appendChild(div);
        });
    }
}

async function createSchedule() {
    const sound_id = document.getElementById('sched-sound').value;
    const time = document.getElementById('sched-time').value;
    // Collect checked days
    const checkedBoxes = document.querySelectorAll('#sched-days-group input[type="checkbox"]:checked');
    const days_of_week = Array.from(checkedBoxes).map(cb => cb.value).sort().join(',');

    if (!sound_id || !time || !days_of_week) return alert("請填寫完整資訊並至少選擇一個執行日");

    await fetchAPI('/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sound_id: parseInt(sound_id), time, days_of_week })
    });

    document.getElementById('sched-time').value = '';
    document.querySelectorAll('#sched-days-group input[type="checkbox"]').forEach(cb => cb.checked = true);
    loadSchedules();
}

async function deleteSchedule(id) {
    if (!confirm("確定要刪除排程？")) return;
    await fetchAPI(`/schedules/${id}`, { method: 'DELETE' });
    loadSchedules();
}

async function addExclusion() {
    const date = document.getElementById('ex-date').value;
    const reason = document.getElementById('ex-reason').value;

    await fetchAPI('/exclusions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, reason })
    });
    document.getElementById('ex-date').value = '';
    document.getElementById('ex-reason').value = '';
    loadSchedules();
}

async function deleteExclusion(id) {
    if (!confirm("確定要刪除排除日？")) return;
    await fetchAPI(`/exclusions/${id}`, { method: 'DELETE' });
    loadSchedules();
}

// ================= Assets & TTS =================
async function loadAssets() {
    const assets = await fetchAPI('/assets/');
    const tbody = document.getElementById('assets-list');
    tbody.innerHTML = '';
    assets.forEach(a => {
        const div = document.createElement('div');
        div.className = 'row';
        div.innerHTML = `
            <div class="row-label">
                <span class="title">${a.label}</span>
                <span class="subtitle">${a.filename}</span>
            </div>
            <span class="badge ${a.is_tts ? 'badge-secondary' : 'badge-primary'}">${a.is_tts ? 'TTS' : 'UPLOAD'}</span>
            <div style="display:flex; gap:0.5rem;">
                <button class="btn" onclick="playSound(${a.id})">播放</button>
                <button class="btn btn-danger" onclick="deleteAsset(${a.id})">移除</button>
            </div>
        `;
        tbody.appendChild(div);
    });
}

async function uploadAsset() {
    const fileInput = document.getElementById('upload-file');
    if (!fileInput.files.length) return alert("請先選擇檔案");
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    await fetch(`${API}/assets/upload`, { method: 'POST', body: formData });
    fileInput.value = '';
    const label = document.getElementById('upload-filename');
    if (label) label.textContent = '未選擇檔案';
    loadAssets();
}

async function generateTTS() {
    const text = document.getElementById('tts-text').value;
    if (!text) return alert("請輸入文字");

    document.getElementById('tts-text').value = '正在生成中...請稍候';
    await fetchAPI('/assets/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });

    document.getElementById('tts-text').value = '';
    loadAssets();
}

async function deleteAsset(id) {
    if (!confirm("⚠️ 警告：刪除此音檔將會同步刪除所有使用它的「播放排程」！\n確定要永久移除嗎？")) return;
    await fetchAPI(`/assets/${id}`, { method: 'DELETE' });
    loadAssets();
}


async function clearDatabase() {
    if (!confirm("⚠️ 警告：此操作將永久刪除所有音檔、排程與休假設定！確定要繼續嗎？")) return;
    if (!confirm("請再次確認，刪除後將無法復原。")) return;

    try {
        const res = await fetchAPI('/system/clear', { method: 'POST' });
        alert(res.message || "資料庫已重設！");
        // Reload all views by simulating a click on the current active tab
        const activeNav = document.querySelector('.sidebar nav button.active');
        if (activeNav) activeNav.click();
    } catch (e) {
        alert("重設失敗：" + e.message);
    }
}

// ================= Init =================
document.addEventListener('DOMContentLoaded', () => {
    navigate('schedules');
});

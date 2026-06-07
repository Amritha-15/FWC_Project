async function runBulkScreen() {
  const jobId = document.getElementById('jobId').value.trim();
  const token = document.getElementById('token').value.trim();
  const status = document.getElementById('status');
  const results = document.getElementById('results');
  results.innerHTML = '';
  if (!jobId) { status.textContent = 'Please enter a job ID.'; return; }
  status.textContent = 'Running bulk screening...';

  const res = await fetch(`/api/hr/agents/bulk-screen/job/${jobId}`, {
    method: 'POST',
    headers: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': token } : {})
  });

  if (!res.ok) {
    const txt = await res.text();
    status.textContent = 'Screening failed: ' + txt;
    return;
  }

  const payload = await res.json();
  status.textContent = 'Bulk screening completed — showing results';

  const responseData = payload.data || payload;
  const job = responseData.job || null;
  const rows = responseData.results || responseData.data || responseData || [];

  if (job) {
    const title = document.createElement('h2');
    title.textContent = `Job: ${job.title} (ID: ${job.id})`;
    results.insertAdjacentElement('afterbegin', title);
  }

  renderTable(rows);

  function renderTable(list) {
    if (!list || list.length === 0) { results.innerHTML = '<p>No applicants found.</p>'; return; }

    const table = document.createElement('table');
    table.innerHTML = `
      <thead>
        <tr><th>Rank</th><th>Candidate</th><th>Email</th><th>Score</th><th>Actions</th></tr>
      </thead>
      <tbody></tbody>
    `;

    const tbody = table.querySelector('tbody');
    list.forEach((c, idx) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${idx+1}</td>
        <td>${escapeHtml(c.candidate_name || c.name || '')}</td>
        <td>${escapeHtml(c.candidate_email || c.email || '')}</td>
        <td>${(c.resume_quality_score||c.match_score||0)}</td>
        <td class="actions">
          <button data-app="${c.application_id}" data-action="Shortlisted">Shortlist</button>
          <button data-app="${c.application_id}" data-action="Rejected">Reject</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    results.innerHTML = '';
    results.appendChild(table);

    // wire actions
    results.querySelectorAll('button[data-app]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const appId = e.target.getAttribute('data-app');
        const action = e.target.getAttribute('data-action');
        e.target.disabled = true;
        try {
          const r = await fetch(`/api/hr/applications/${appId}/status`, {
            method: 'PUT',
            headers: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': token } : {}),
            body: JSON.stringify({ status: action })
          });
          if (!r.ok) {
            const t = await r.text();
            alert('Failed: ' + t);
            e.target.disabled = false;
            return;
          }
          e.target.textContent = action + ' ✓';
        } catch (err) {
          alert('Error: ' + err.message);
          e.target.disabled = false;
        }
      });
    });
  }
}

function escapeHtml(str){
  if(!str) return '';
  return String(str).replace(/[&<>\"]/g, s=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"})[s]);
}

document.getElementById('runBtn').addEventListener('click', runBulkScreen);

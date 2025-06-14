document.addEventListener("DOMContentLoaded", async () => {
  if (!localStorage.getItem('access_token')) {
    alert('Você precisa estar logado para ver suas reservas.');
    window.location.href = '/login/';
    return;
  }

  const logoutButton = document.getElementById('logoutButton');
  if (logoutButton) {
    logoutButton.addEventListener('click', () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login/';
    });
  }

  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/reservations/', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const reservations = await response.json();
  const list = document.getElementById('reservationsList');

  reservations.forEach(r => {
    const li = document.createElement('li');

    let statusText = `Status: ${r.status}`;
    if (r.local_cancelado) {
      statusText += ' (cancelado pelo proprietário)';
    }

    li.innerHTML = `
      <strong>${r.location_name}</strong><br>
      Data: ${r.date}<br>
      Horário: ${r.start_time} - ${r.end_time}<br>
      ${statusText}
      ${r.status === 'confirmed' ? `<br><button onclick="cancelReservation(${r.id})">Cancelar</button>` : ''}
    `;

    list.appendChild(li);
  });
});

async function cancelReservation(id) {
  const token = localStorage.getItem('access_token');

  const res = await fetch(`/api/reservations/${id}/cancel/`, {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (res.ok) {
    alert('Reserva cancelada com sucesso!');
    location.reload();
  } else {
    const err = await res.json();
    alert('Erro ao cancelar: ' + (err.detail || JSON.stringify(err)));
  }
}
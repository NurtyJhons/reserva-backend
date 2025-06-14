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

    const images = r.location_images && r.location_images.length > 0
      ? r.location_images
      : ['https://via.placeholder.com/400x200?text=Sem+Imagem'];

    let currentImageIndex = 0;

    const statusMap = {
      'pending': { text: 'Pendente', color: '#ffc107', emoji: '⏳' },
      'confirmed': { text: 'Confirmada', color: '#28a745', emoji: '✅' },
      'cancelled': { text: 'Cancelada', color: '#dc3545', emoji: '❌' }
    };

    const statusData = statusMap[r.status] || { text: r.status, color: '#6c757d', emoji: '' };
    if (r.local_cancelado) {
      statusData.text += ' (cancelado pelo proprietário)';
      statusData.color = '#6c757d';
      statusData.emoji = '⚠️';
    }

    li.innerHTML = `
      <div class="image-container">
        <button class="prev-btn">&#10094;</button>
        <img class="reservation-image" src="${images[0]}" alt="Imagem do local">
        <button class="next-btn">&#10095;</button>
      </div>

      <strong>${r.location_name}</strong><br>
      <small style="color: #555">${r.location_address || r.location_description || ''}</small><br><br>

      <span><strong>Data:</strong> ${r.date}</span><br>
      <span><strong>Horário:</strong> ${r.start_time} - ${r.end_time}</span><br>
      <span><strong>Status:</strong> <span style="color: ${statusData.color}; font-weight: bold;">${statusData.emoji} ${statusData.text}</span></span><br>

      ${r.status === 'confirmed' ? `<br><button onclick="cancelReservation(${r.id})">Cancelar</button>` : ''}
    `;

    const img = li.querySelector('.reservation-image');
    const prevBtn = li.querySelector('.prev-btn');
    const nextBtn = li.querySelector('.next-btn');

    prevBtn.onclick = () => {
      currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
      img.src = images[currentImageIndex];
    };

    nextBtn.onclick = () => {
      currentImageIndex = (currentImageIndex + 1) % images.length;
      img.src = images[currentImageIndex];
    };

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
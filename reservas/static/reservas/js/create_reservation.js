// Executa isoladamente no carregamento
document.addEventListener('DOMContentLoaded', () => {
  const logoutButton = document.getElementById('logoutButton');
  if (logoutButton) {
    logoutButton.addEventListener('click', () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login/';
    });
  }
});

document.addEventListener('DOMContentLoaded', async () => {
  const token = localStorage.getItem('access_token');

  if (!token) {
    alert('Você precisa estar logado para fazer uma reserva.');
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

  const cardsContainer = document.getElementById('locationCards');
  const locationInput = document.getElementById('location');
  const msg = document.getElementById('message');
  let locationsMap = {};

  // Modal handlers
  const modal = document.getElementById('locationModal');
  const closeBtn = document.querySelector('.close');
  closeBtn.onclick = () => { modal.style.display = 'none'; };
  window.onclick = (event) => {
    if (event.target === modal) modal.style.display = 'none';
  };

  try {
    const response = await fetch('/api/locations/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const locations = await response.json();

    locations.forEach(loc => {
      locationsMap[loc.id] = loc;

      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <img src="${(loc.images && loc.images.length > 0) ? loc.images[0] : 'https://via.placeholder.com/250x150?text=Sem+Imagem'}" alt="${loc.name}" />
        <h4>${loc.name}</h4>
        <p>Preço por hora: R$ ${loc.price_per_hour !== null && loc.price_per_hour !== undefined ? Number(loc.price_per_hour).toFixed(2) : 'N/D'}</p>
      `;

      card.addEventListener('click', () => {
        document.querySelectorAll('.card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        locationInput.value = loc.id;

        document.getElementById('modalName').textContent = loc.name;
        document.getElementById('modalDescription').textContent = loc.description || 'Sem descrição disponível';
        document.getElementById('modalPrice').textContent =
          loc.price_per_hour !== null && loc.price_per_hour !== undefined
            ? Number(loc.price_per_hour).toFixed(2) : 'N/D';
        document.getElementById('modalAddress').textContent = loc.address || 'Endereço não informado';

        let currentImageIndex = 0;
        let modalImages = loc.images && loc.images.length > 0 ? loc.images : ['https://via.placeholder.com/400x200?text=Sem+Imagem'];

        const modalImage = document.getElementById('modalImage');
        const prevBtn = document.getElementById('prevImage');
        const nextBtn = document.getElementById('nextImage');

        function updateModalImage() {
          modalImage.src = modalImages[currentImageIndex];
        }

        if (modalImages.length <= 1) {
          prevBtn.style.display = 'none';
          nextBtn.style.display = 'none';
        } else {
          prevBtn.style.display = 'block';
          nextBtn.style.display = 'block';
        }

        prevBtn.onclick = (e) => {
          e.stopPropagation();
          currentImageIndex = (currentImageIndex - 1 + modalImages.length) % modalImages.length;
          updateModalImage();
        };

        nextBtn.onclick = (e) => {
          e.stopPropagation();
          currentImageIndex = (currentImageIndex + 1) % modalImages.length;
          updateModalImage();
        };

        currentImageIndex = 0;
        updateModalImage();

        // Buscar horários disponíveis
        const today = new Date().toISOString().split('T')[0];
        fetch(`/api/locations/${loc.id}/available-slots/?date=${today}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
          .then(response => response.json())
          .then(data => {
            const slotsList = document.getElementById('modalSlots');
            slotsList.innerHTML = '';

            const availableSlots = data.available_slots || [];

            if (availableSlots.length > 0) {
              availableSlots.forEach(slot => {
                const li = document.createElement('li');
                li.textContent = slot;
                slotsList.appendChild(li);
              });
            } else {
              slotsList.innerHTML = '<li>Nenhum horário disponível hoje.</li>';
            }
          })
          .catch(err => {
            console.error('Erro ao buscar horários:', err);
            const slotsList = document.getElementById('modalSlots');
            slotsList.innerHTML = '<li>Erro ao carregar horários.</li>';
          });

        modal.style.display = 'block';
      });

      cardsContainer.appendChild(card);
    });
  } catch (err) {
    console.error('Erro ao carregar locais:', err);
    msg.style.color = 'red';
    msg.textContent = 'Erro ao carregar locais.';
  }

  // Envio da reserva
  document.getElementById('reservationForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!locationInput.value) {
      msg.style.color = 'red';
      msg.textContent = 'Selecione um local antes de continuar.';
      return;
    }

    const data = {
      location: parseInt(locationInput.value),
      date: document.getElementById('date').value,
      start_time: document.getElementById('start_time').value,
      end_time: document.getElementById('end_time').value,
      payment_method: document.getElementById('payment_method').value
    };

    try {
      const res = await fetch('/api/reservations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });

      if (res.ok) {
        msg.style.color = 'green';
        msg.textContent = 'Reserva realizada com sucesso!';
        document.getElementById('reservationForm').reset();
        document.querySelectorAll('.card').forEach(c => c.classList.remove('selected'));
        locationInput.value = '';
      } else {
        const err = await res.json();
        msg.style.color = 'red';
        msg.textContent = 'Erro: ' + (err.detail || JSON.stringify(err));
      }
    } catch (err) {
      console.error('Erro ao enviar reserva:', err);
      msg.style.color = 'red';
      msg.textContent = 'Erro ao enviar reserva.';
    }
  });
});
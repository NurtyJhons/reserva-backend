document.addEventListener("DOMContentLoaded", async () => {
  const token = localStorage.getItem("access_token");

  if (!token) {
    alert("Você precisa estar logado.");
    window.location.href = "/login/";
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

  try {
    const response = await fetch("/api/owner/dashboard/", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (response.ok) {
      const data = await response.json();

      // Atualizar estatísticas
      document.getElementById("totalLocations").textContent = data.total_locations;
      document.getElementById("totalReservations").textContent = data.total_reservations;
      document.getElementById("upcomingReservations").textContent = data.upcoming_reservations;

      // Mostrar reservas por local
      const list = document.getElementById("reservationsPerLocation");
      data.reservations_per_location.forEach(item => {
        const li = document.createElement("li");
        li.textContent = `${item.location__name}: ${item.count} reservas`;
        list.appendChild(li);
      });

      // Carregar locais ativos (para cancelar)
      const locationsRes = await fetch('/api/locations/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const locations = await locationsRes.json();
      const select = document.getElementById('locationSelect');

      locations.forEach(loc => {
        if (loc.is_active) {
          const opt = document.createElement('option');
          opt.value = loc.id;
          opt.textContent = loc.name;
          select.appendChild(opt);
        }
      });

      // Botão cancelar local
      const cancelButton = document.getElementById('cancelButton');
      const cancelMessage = document.getElementById('cancelMessage');

      cancelButton.addEventListener('click', async () => {
        const locationId = select.value;
        cancelMessage.textContent = '';
        if (!locationId) {
          cancelMessage.style.color = 'red';
          cancelMessage.textContent = 'Selecione um local primeiro.';
          return;
        }

        const confirmCancel = confirm("Tem certeza que deseja cancelar este local?");
        if (!confirmCancel) return;

        const res = await fetch(`/api/locations/${locationId}/cancel/`, {
          method: 'PATCH',
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (res.ok) {
          cancelMessage.style.color = 'green';
          cancelMessage.textContent = 'Local cancelado com sucesso!';
          // Remove do select
          select.querySelector(`option[value="${locationId}"]`).remove();
        } else {
          const err = await res.json();
          cancelMessage.style.color = 'red';
          cancelMessage.textContent = 'Erro: ' + (err.detail || 'Falha ao cancelar local.');
        }
      });

    } else {
      alert("Erro ao carregar dados do dashboard");
    }
  } catch (err) {
    alert("Erro de conexão com o servidor.");
  }
});
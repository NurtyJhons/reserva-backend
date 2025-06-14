document.addEventListener("DOMContentLoaded", () => {
  // Botão de logout
  const logoutButton = document.getElementById('logoutButton');
  if (logoutButton) {
    logoutButton.addEventListener('click', () => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login/';
    });
  }

  // Proteção de acesso
  const token = localStorage.getItem('access_token');
  if (!token) {
    alert("Você precisa estar logado.");
    window.location.href = "/login/";
    return;
  }

  // Formulário
  const form = document.getElementById('location-form');
  const message = document.getElementById('message');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.textContent = '';
    message.style.color = '';

    const formData = new FormData(form);

    try {
      const res = await fetch('/api/locations/', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + token,
        },
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json();
        message.style.color = 'red';
        message.textContent = 'Erro ao cadastrar local: ' + JSON.stringify(errorData);
        return;
      }

      message.style.color = 'green';
      message.textContent = 'Local cadastrado com sucesso!';
      form.reset();

    } catch (err) {
      message.style.color = 'red';
      message.textContent = 'Erro ao conectar ao servidor.';
    }
  });
});
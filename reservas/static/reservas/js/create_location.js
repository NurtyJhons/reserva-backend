document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById('location-form');
  const message = document.getElementById('message');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.textContent = '';
    message.style.color = '';

    const token = localStorage.getItem('access_token');
    if (!token) {
      message.style.color = 'red';
      message.textContent = 'Você precisa estar logado.';
      window.location.href = "/login/";  // redireciona para login se necessário
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

    const formData = new FormData(form);

    try {
      const res = await fetch('/api/locations/', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + token,
          // NÃO defina Content-Type! O browser define automaticamente para multipart/form-data
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
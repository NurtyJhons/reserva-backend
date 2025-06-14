document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById('register-form');
    const messageEl = document.getElementById('message');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      messageEl.textContent = '';

      const formData = new FormData(form);
      const data = Object.fromEntries(formData.entries());

      try {
        const response = await fetch('/api/auth/register/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });

        if (response.ok) {
          messageEl.style.color = 'green';
          messageEl.textContent = 'Usuário registrado com sucesso! Você pode agora fazer login.';
          form.reset();
        } else {
          const errorData = await response.json();
          messageEl.style.color = 'red';
          messageEl.textContent = 'Erro: ' + JSON.stringify(errorData);
        }
      } catch (error) {
        messageEl.style.color = 'red';
        messageEl.textContent = 'Erro na conexão com o servidor.';
      }
    });
});
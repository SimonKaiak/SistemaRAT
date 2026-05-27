/*
 * validator_login.js
 * ------------------
 * Validación del formulario de login en el lado del cliente,
 * ejecutada antes de enviar las credenciales al servidor.
 *
 * Se activa al hacer submit del formulario de login y valida:
 *   - Email: formato válido (algo@dominio.ext) mediante regex.
 *   - Contraseña: largo entre 6 y 20 caracteres.
 *   - Contraseña: al menos una letra mayúscula.
 *   - Contraseña: al menos un número.
 *
 * Si hay errores, cancela el submit con preventDefault() y
 * muestra un alert con la lista de requisitos no cumplidos.
 *
 * Nota: esta validación es solo una primera capa de UX — la
 * validación real y segura ocurre en el servidor (vistas_auth.py).
 */
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('form');

    loginForm.addEventListener('submit', function(event) {
        // Seleccionamos los campos por su atributo 'name' (según tu validador_login.py)
        const emailField = document.querySelector('input[name="username"]');
        const passwordField = document.querySelector('input[name="password"]');
        
        const email = emailField.value.trim();
        const pass = passwordField.value;

        // Expresiones Regulares
        const regexEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const regexMayuscula = /[A-Z]/;
        const regexNumero = /[0-9]/;

        let errores = [];

        // Validación Correo
        if (!regexEmail.test(email)) {
            errores.push("Ingrese un correo electrónico válido (ejemplo@correo.com).");
        }

        // Validación Largo (6-20)
        if (pass.length < 6 || pass.length > 20) {
            errores.push("La contraseña debe tener entre 6 y 20 caracteres.");
        }

        // Validación Mayúscula
        if (!regexMayuscula.test(pass)) {
            errores.push("La contraseña debe contener al menos una letra mayúscula.");
        }

        // Validación Número
        if (!regexNumero.test(pass)) {
            errores.push("La contraseña debe contener al menos un número.");
        }

        // Manejo de Errores
        if (errores.length > 0) {
            event.preventDefault(); // Detiene el envío a Python
            alert("⚠️ Requisitos de validación:\n\n" + errores.map(e => "• " + e).join("\n"));
        }
    });
});
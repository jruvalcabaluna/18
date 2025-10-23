# Notas para el CI en runner self-hosted


1. **Runner**: Instala y registra un runner self-hosted en GitHub. Asegúrate de que el runner tenga:
- Docker (daemon) instalado y que el usuario del runner pueda ejecutar `docker build`.
- Python 3.10 (o un interprete compatible) y `pip`.
- Acceso al repositorio privado/submódulo de Enterprise si lo usas (SSH key o token configurado).


2. **Etiquetas**: Si tu runner tiene una etiqueta personalizada, cámbiala en `runs-on` del workflow.


3. **Enterprise**: Odoo Enterprise no es código público; el Dockerfile asume que colocas los módulos en `enterprise/` dentro del repo o como submódulo. Alternativamente, monta los addons desde un volumen en producción.


4. **Secretos (opcional)**: Si quieres subir la imagen a un registry, añade pasos `docker login` y `docker push` usando secretos `DOCKERHUB_USERNAME` y `DOCKERHUB_TOKEN`.


5. **Pre-commit**: El workflow ejecuta `pre-commit run --all-files`. Si quieres ejecutar sólo archivos cambiados en commits, usa `pre-commit run --from-ref origin/main --to-ref HEAD` o la configuración que prefieras.

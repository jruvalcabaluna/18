# Dockerfile para construir Odoo 17 Enterprise
# Nota: necesitas el código fuente de Odoo Enterprise (no público) como submódulo
# o en una carpeta /enterprise dentro del repo. Si tienes licencia, coloca los
# módulos en /enterprise/addons y configúralo como se indica aquí.


FROM odoo:17


# Crea directorios
USER root
RUN mkdir -p /mnt/extra-addons /enterprise/addons


# Copia los addons (asume que el repo contiene la carpeta enterprise/ con código licenciado)
# Si mantienes enterprise en un submódulo privado, asegúrate de que el runner tenga acceso.
COPY ./addons /enterprise
#COPY ./addons /mnt/extra-addons


# Instala dependencias extra si es necesario
COPY ./requirements.txt /tmp/requirements.txt
RUN if [ -f /tmp/requirements.txt ]; then pip install -r /tmp/requirements.txt; fi


# Ajusta permisos
RUN chown -R odoo:odoo /enterprise /mnt/extra-addons


# Ajusta variables de entorno para que Odoo cargue los addons Enterprise
ENV ODOO_ADDONS_PATH=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/enterprise


USER odoo


# Exponer puerto estándar
EXPOSE 8068


# Entrypoint por defecto ya viene en la imagen oficial de odoo

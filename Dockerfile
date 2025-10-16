FROM python:3.11



ENV LANG C.UTF-8



# System deps

RUN apt-get update && apt-get install -y \
    git build-essential libpq-dev libxml2-dev libxslt1-dev \
    libldap2-dev libsasl2-dev libjpeg-dev zlib1g-dev \
    libjpeg-dev libpng-dev liblcms2-dev libblas-dev \
    libffi-dev libssl-dev libevent-dev \
    && apt-get clean



# Create odoo user

RUN useradd -ms /bin/bash odoo



# Clone Odoo

RUN git clone --depth 1 --branch 17.0 https://github.com/odoo/odoo.git /opt/odoo



WORKDIR /opt/odoo



# Install Python dependencies

COPY requirements.txt /opt/odoo/

RUN pip install -r requirements.txt



# Set permissions

RUN chown -R odoo:odoo /opt/odoo

USER odoo



CMD ["python3", "odoo-bin", "-c", "/etc/odoo/odoo.conf"]

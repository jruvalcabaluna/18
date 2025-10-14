# Use official Python image as a base
FROM python:3.9-slim
# Set environment variables
ENV ODOO_HOME=/opt/odoo
ENV ODOO_USER=odoo

# Update apt-get and install dependencies
RUN apt-get update && apt-get install -y \
build-essential \
python3 \
python3-pip \ 
python3-dev \
libldap2-dev \
libsasl2-dev \
python3-setuptools \
libjpeg-dev \
nodejs \
npm \
git \
&& apt-get clean

# Clone Odoo from GitHub (version 15 in this case)
RUN git clone --branch 17.0 https://github.com/odoo/odoo.git $ODOO_HOME

# Install Python dependencies
RUN pip3 install -r /opt/odoo/requirements.txt

# Add the Odoo configuration file
COPY ./odoo.conf /etc/odoo.conf

# Set file permissions
RUN useradd -m -d /opt/odoo -s /bin/bash odoo
RUN chown -R odoo:odoo /opt/odoo
RUN chown -R odoo:odoo /etc/odoo.conf
#RUN chown $ODOO_USER:$ODOO_USER /etc/odoo.conf

# Expose Odoo port
EXPOSE 8069

# Set the working directory
WORKDIR $ODOO_HOME

# Define the entrypoint to run Odoo
CMD ["python3", "odoo-bin", "--config", "/etc/odoo.conf"]

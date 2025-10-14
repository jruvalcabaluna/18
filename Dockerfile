

# Base image for Odoo (e.g., official Odoo image or a custom one)
FROM odoo:17.0

# Install necessary dependencies for the runner
RUN apt-get update && apt-get install -y \
    curl \
    git \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create a user for the runner (optional but recommended for security)
RUN useradd -m github-runner && usermod -aG sudo github-runner

# Download and extract the GitHub Actions runner application
ARG RUNNER_VERSION="2.316.0" # Check for the latest version on GitHub Actions docs
RUN curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz && \
    tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -C /home/github-runner && \
    rm actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Set permissions
RUN chown -R github-runner:github-runner /home/github-runner

# Switch to the runner user for security
USER github-runner

# Set the working directory for the runner
WORKDIR /home/github-runner

# Entrypoint script to configure and run the runner
COPY entrypoint.sh /home/github-runner/entrypoint.sh
RUN chmod +x /home/github-runner/entrypoint.sh

# Expose Odoo port (if needed)
EXPOSE 8069

ENTRYPOINT ["/home/github-runner/entrypoint.sh"]

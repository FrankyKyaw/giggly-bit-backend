FROM debian:12

RUN \
  # set up dependencies for adding apt repos
  apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install --yes curl ca-certificates gnupg && \
  # set up nodesource apt repo
  mkdir -p /etc/apt/keyrings && \
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
  NODE_MAJOR=20 && \
  echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
  # set up github apt repo
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
  && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
  # install packages
  apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install --yes nodejs wget build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev dumb-init git vim less iputils-ping postgresql-15 redis python3 python3-pip apache2-utils python3-certbot-nginx python3-certbot-dns-digitalocean sudo libsecret-1-0 command-not-found rsync man-db php php-pgsql gh netcat-openbsd python3-deepmerge python3-requests python3-ipython python3-dotenv dnsutils cron procps lsof ffmpeg \
  # Add audio-related dependencies
  portaudio19-dev python3-pyaudio && \
  # needed for postgres
  locale-gen en_US.UTF-8 && \
  # set up adminer
  curl -L -o /opt/adminer.php https://github.com/vrana/adminer/releases/download/v4.8.1/adminer-4.8.1.php && \
  # clean up apt cache
  apt-get clean && \
  rm -rf /tmp/* /var/tmp/* /var/lib/apt/archive/* /var/lib/apt/lists/* && \
  # complete!
  echo "Dockerfile RUN complete!"

# Copy requirements first to leverage Docker cache
COPY requirements.txt /
RUN pip3 install --break-system-packages -r /requirements.txt

# Set working directory
WORKDIR /app

# Copy the application code
COPY . /app/

# Expose the Flask port
EXPOSE 5000

# Add environment variables if needed
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Use dumb-init to handle signals properly
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Start both the Flask app and any other processes you need
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
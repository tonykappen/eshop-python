FROM postgres:17

# Copy our initialization script
COPY init-db.sql /docker-entrypoint-initdb.d/01-init-db.sql

# Create a script that runs on every container start
COPY ensure-schemas.sh /usr/local/bin/ensure-schemas.sh
RUN chmod +x /usr/local/bin/ensure-schemas.sh

# Create a wrapper entrypoint that ensures schemas exist
COPY docker-entrypoint-wrapper.sh /usr/local/bin/docker-entrypoint-wrapper.sh
RUN chmod +x /usr/local/bin/docker-entrypoint-wrapper.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint-wrapper.sh"]
CMD ["postgres"]

FROM prom/alertmanager:latest

WORKDIR /etc/alertmanager

COPY alertmanager.template.yml .
COPY generate-config.sh .
COPY .env.secrets .

RUN sh ./generate-config.sh && rm -f .env.secrets generate-config.sh
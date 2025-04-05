# opicluster_monitoring

opicluster_monitoring/  
├── alertmanager/  
│   ├── alertmanager.template.yml  
│   └── alertmanager.yml       # ← généré automatiquement  
├── grafana-data/              # ← data persistante (gitignore)  
├── prometheus/  
│   ├── prometheus.yml  
│   └── alert.rules.yml  
├── traefik/  
│   ├── acme/  
│   │   └── acme.json          # ← certificats TLS (gitignore)  
├── web_app/  
│   ├── app.py  
│   ├── auth.py  
│   ├── sms_alert.py  
│   ├── templates/  
│   └── static/  
├── docker-compose.yml  
├── .env.secrets               # ← non versionné  
├── generate-config.sh  
└── README.md  

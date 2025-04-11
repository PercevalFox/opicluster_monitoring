# Configuration de Vault - mode UI activé et stockage en fichier

ui = true

listener "tcp" {
  address     = "0.0.0.0:8201"   # Vault écoutera sur le port 8201
  tls_disable = true             # Désactive TLS pour simplifier, sinon configure TLS
}

storage "file" {
  path = "/vault/data"           # Chemin pour le stockage persistant
}

disable_mlock = true             # Nécessaire dans des environnements containerisés
default_lease_ttl = "1h"
max_lease_ttl     = "4h"

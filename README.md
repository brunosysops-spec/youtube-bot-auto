# YouTube Bot Automático

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Kubernetes](https://img.shields.io/badge/kubernetes-ready-green)

Bot automatizado que varre canais do YouTube através de Feed RSS, identifica vídeos novos e utiliza Inteligência Artificial (Ollama - Phi-3) para inferir o contexto daquele vídeo e postar o primeiro comentário de forma orgânica. 

## 🚀 Funcionalidades
* **Identificação Inédita**: Só comenta em vídeos que ainda não foram processados (guardados em um histórico local).
* **12-Factor App Ready**: Todas as configurações vitais (`OLLAMA_URL`, tokens do Google, etc) podem ser passadas por variáveis de ambiente ou montadas em Volumes (K8s ConfigMaps).
* **Gerador de IA (Ollama)**: Integração robusta com uma instalação local ou exposta do Ollama rodando LLMs não-censurados em 4-bits ou mais.
* **Fallback Seguro**: Caso o Ollama esteja offline, possui geradores estáticos randômicos de emergência.

---

## 🏗 Arquitetura Sugerida (K8s + LXC)
Para maximizar a eficiência em Hosts modestos (ex: 4GB de RAM) recomendamos:
1. **Ollama no LXC (Proxmox)**: Roda "fora" do Kubernetes para não competir por RAM/CPU com outros Pods e Core components.
2. **Bot no Kubernetes (CronJob)**: Acorda a cada `X` minutos, processa a lista de canais, anota no arquivo de banco persistente e morre limpo liberando recursos.

### 🐧 Instalação do Ollama In-House (LXC)
No seu container LXC do Proxmox:
1. Instale o Ollama normalmente: `curl -fsSL https://ollama.com/install.sh | sh`
2. Baixe o modelo leve Phi-3: `ollama run phi3` (Logo depois digite `/bye` para sair).
3. **Exponha o Ollama para a rede local**:
   - Edite o serviço systemd: `sudo systemctl edit ollama`
   - Cole as linhas abaixo e salve:
   ```ini
   [Service]
   Environment="OLLAMA_HOST=0.0.0.0"
   ```
   - Reinicie o serviço: `sudo systemctl restart ollama`

O Ollama estará pronto no IP da sua máquina (ex: `http://192.168.1.50:11434`).

---

## ☸️ Deploy no Kubernetes
O repositório inclui a pasta `/k8s/` com todos os manifestos prontos para um cluster:

1. Modifique os arquivos em `/k8s` com seus IPs internos reais:
   - Em `03-configmap.yaml`, atualize a variável `url` do bloco do Ollama.
   - Opcional: Modifique em `04-cronjob.yaml` a periodicidade de `*/1 * * * *` para o valor de sua preferência.

2. Crie uma **Secret** primária no seu cluster para armazenar o arquivo das credenciais do Google API Auth (substitua o path abaixo pelo path válido do seu `tokens.json` ou `client_secret...json`):
   ```bash
   kubectl create secret generic youtube-bot-creds --from-file=tokens.json=./tokens.json -n youtube-bot
   ```

3. Aplique todos os manifestos:
   ```bash
   kubectl apply -f k8s/
   ```

## 🛠 Desenvolvimento / Rodando Local
Para testar a lógica do Bot local antes de conteinerizar:

```bash
# 1. Crie o VENV e instale requerimentos
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt

# 2. Configure seus canais
# Edite o `config.json` na raiz declarando o ID do canal desejado.

# 3. Rode
python scripts/main_polling.py
```

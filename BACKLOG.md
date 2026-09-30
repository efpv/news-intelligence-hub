# Backlog de Melhorias — News Intelligence Hub

Documento para rastrear melhorias identificadas mas ainda não implementadas.

---

## 🔐 Autenticação e Persistência por Usuário

**Status:** ✅ Implementado (29/09) — identificação por e-mail + cookie, sem senha.

**Problema original:** `user_preferences.json` era um arquivo único compartilhado no servidor — todos os usuários que acessavam o app viam/sobrescreviam a mesma carteira e os mesmos filtros.

**Tentativa 1 (abandonada):** UUID automático gerado e mantido só no query param `uid` da URL. Problema: se o usuário fechava/reabria o navegador sem a URL exata salva, perdia o vínculo.

**Tentativa 2 (abandonada):** UUID automático persistido em cookie via `extra-streamlit-components`, gerado silenciosamente sem ação do usuário. Problema real encontrado em teste ao vivo: na primeira renderização após reabrir o navegador, o componente de cookie ainda não tinha entregue o valor existente ao Python, e o código gerava um UUID novo antes de dar tempo do cookie real chegar — sobrescrevendo o vínculo do usuário de forma silenciosa (falha de UX grave, mesmo com uma tentativa de retry via `st.rerun()`).

**Solução final (implementada):** o usuário informa seu e-mail explicitamente (accordion "💾 Salvar minhas preferências por e-mail" no topo da página). O e-mail é salvo em cookie (`nih_email`, 1 ano de validade) via `extra-streamlit-components`, e um hash SHA-256 do e-mail vira o nome do arquivo em `data/user_prefs/{hash}.json`. Como a ação é explícita (o usuário clica em "Salvar/Carregar"), não há race condition: na pior hipótese, se o cookie não for lido a tempo em uma visita futura, o app apenas volta a mostrar o formulário de e-mail (usuário digita de novo) — nunca perde ou sobrescreve dados silenciosamente.

**⚠️ Não é autenticação segura:** não há senha nem verificação de posse do e-mail. Quem souber/adivinhar o e-mail de outra pessoa pode carregar as mesmas preferências. Aceitável para uso pessoal/baixo risco; **não deve ser usado se dados sensíveis forem adicionados no futuro**.

**Limitações conhecidas:**
- Filesystem do Streamlit Community Cloud é efêmero — redeploys/reinícios apagam `data/user_prefs/`. Mitigado pelo export/import CSV já existente.
- Cookie pode ser limpo pelo usuário/navegador (modo anônimo, "limpar dados de navegação"), exigindo novo login por e-mail.

**Evolução futura (não feita ainda):** Login real com conta Google (`st.login()`, nativo do Streamlit ≥1.42) + Google Drive API, salvando o JSON na pasta oculta *App Data* de cada usuário. Resolveria a perda de dados em redeploys e adicionaria verificação real de identidade.

**Pré-requisitos (fora do código, feitos manualmente no Google Cloud Console):**
- Criar projeto no Google Cloud Console
- Configurar tela de consentimento OAuth (modo *Testing* dispensa verificação até 100 usuários)
- Ativar a Google Drive API
- Criar credencial OAuth 2.0 Client ID (Web application) com redirect URI do app
- Fornecer Client ID/Secret via `.streamlit/secrets.toml` (não versionar)

**Escopo de implementação (quando for feito):**
- `st.login()` / `st.user` para autenticação
- Módulo de integração com Google Drive API (`google-api-python-client`) para ler/gravar o JSON
- Fallback para o modo atual (UID na URL) quando usuário não estiver logado
- Indicador de usuário logado + botão de logout na sidebar

---

## 📊 Integrações de Mercado (Roadmap Original)

- **Integração B3**: importação automática de carteira diretamente da corretora/B3
- **Status Invest**: importação de ativos e dados fundamentalistas
- **Fundamentus**: enriquecimento dos ativos monitorados com indicadores fundamentalistas
- **BRAPI**: substituir/complementar o catálogo local estático (`B3_COMPANIES`) por consulta em tempo real a uma API de ativos da B3

---

## 🤖 Inteligência e Análise Avançada

- **Ranking de Impacto**: pontuar o quanto cada notícia pode impactar a carteira (ex: "Impacto: 92/100")
- **Resumo IA da Carteira**: gerar resumo executivo diário/periódico específico para os ativos monitorados (ex: "Nas últimas 24h foram identificadas 15 notícias relevantes para sua carteira...")
- Expandir catálogo `B3_COMPANIES` conforme usuários reportarem tickers ausentes (ex.: CURY3 adicionado após feedback)

---

## 🎨 UX / Interface

- Avaliar necessidade de paginação ou "carregar mais" na lista de notícias (hoje usa slider de quantidade exibida)
- Revisar acessibilidade de contraste dos badges de sentimento/relevância
- Considerar modo claro (light theme) como alternativa ao dark theme atual

---

## 🧪 Qualidade / Robustez

- Cobrir `classify_relevance`, `search_assets` e `normalize_portfolio` com testes automatizados (pytest)
- Monitorar feeds RSS com falha recorrente (ex.: CNN Economia, Exame Economia, Valor Investe retornando 404/400) e atualizar/substituir URLs em `src/config.py`

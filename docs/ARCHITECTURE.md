# Arquitetura inicial

- Frontend React + TypeScript + Vite consome API REST.
- Backend FastAPI com futura separação em rotas, serviços e modelos SQLAlchemy.
- SQLite apenas em desenvolvimento; PostgreSQL em produção.
- Módulos: autenticação/RBAC, clientes, contatos, oportunidades, chamados, OS, ativos, estoque, agenda, financeiro e relatórios.
- Segredos somente em variáveis de ambiente. Nunca versionar `.env`.

## Fluxo de branches

`feature/*` → pull request → `develop` (testes) → pull request → `main` (produção).

Nenhum deploy automático configurado. Antes de produção: testes, migrações, autenticação, auditoria e backups.

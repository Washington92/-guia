# Águia Gestão CRM — evolução

## Implementado na branch develop
- Clientes: cadastro, consulta e listagem
- Chamados: abertura, consulta e mudança de status
- Ordens de serviço: criação e mudança de status
- Ativos de infraestrutura: inventário por cliente, categoria, local e situação
- Dashboard: indicadores básicos
- Frontend responsivo com identidade visual Águia Design System

## Próximas etapas antes de qualquer uso real
1. Autenticação e controle de acesso por perfil (RBAC)
2. Migrações de banco com Alembic e PostgreSQL em homologação
3. Testes de integração e CI verde
4. Auditoria de alterações, backups e tratamento de dados pessoais
5. Hospedagem privada de homologação, separada de produção

**Aviso:** API atual não possui autenticação. Não expor publicamente nem cadastrar dados reais.

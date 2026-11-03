import React from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <main><h1>Águia Gestão CRM</h1><p>Ambiente de desenvolvimento inicializado.</p><p>Módulos: Clientes · Chamados · Ordens de serviço · Ativos · Estoque</p></main>
  </React.StrictMode>
);

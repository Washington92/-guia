import { FormEvent, useEffect, useState } from 'react';

type Client = { id: number; name: string; email: string | null; phone: string | null };
type Ticket = { id: number; client_id: number; title: string; description: string; status: string; priority: string };
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API + path, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } });
  if (!response.ok) throw new Error((await response.text()).slice(0, 250));
  return response.json();
}

export default function App() {
  const [clients, setClients] = useState<Client[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [clientId, setClientId] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('media');

  async function refresh() {
    const [c, t] = await Promise.all([request<Client[]>('/api/clients'), request<Ticket[]>('/api/tickets')]);
    setClients(c); setTickets(t);
  }
  useEffect(() => { refresh().catch(e => setError('API indisponível: ' + e.message)); }, []);

  async function addClient(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await request('/api/clients', { method: 'POST', body: JSON.stringify({ name, email: email || null, phone: phone || null }) });
      setName(''); setEmail(''); setPhone(''); await refresh();
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }
  async function addTicket(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await request('/api/tickets', { method: 'POST', body: JSON.stringify({ client_id: Number(clientId), title, description, priority }) });
      setTitle(''); setDescription(''); await refresh();
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }
  async function setStatus(id: number, status: string) {
    setError('');
    try { await request('/api/tickets/' + id, { method: 'PATCH', body: JSON.stringify({ status }) }); await refresh(); }
    catch (e) { setError(String(e)); }
  }
  return <main>
    <header><div className="brand">ÁGUIA <span>GESTÃO CRM</span></div><p>Suporte técnico • Infraestrutura • Relacionamento</p></header>
    <section className="stats"><article><small>Clientes</small><strong>{clients.length}</strong></article><article><small>Chamados</small><strong>{tickets.length}</strong></article><article><small>Em aberto</small><strong>{tickets.filter(t => t.status === 'aberto').length}</strong></article></section>
    {error && <div role="alert" className="error">{error}</div>}
    <section className="columns"><article><h2>Novo cliente</h2><form onSubmit={addClient}><input required minLength={2} placeholder="Nome / Empresa" value={name} onChange={e => setName(e.target.value)}/><input type="email" placeholder="E-mail" value={email} onChange={e => setEmail(e.target.value)}/><input placeholder="Telefone" value={phone} onChange={e => setPhone(e.target.value)}/><button disabled={busy}>Cadastrar cliente</button></form></article>
    <article><h2>Novo chamado</h2><form onSubmit={addTicket}><select required value={clientId} onChange={e => setClientId(e.target.value)}><option value="">Selecione o cliente</option>{clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select><input required minLength={3} placeholder="Título do chamado" value={title} onChange={e => setTitle(e.target.value)}/><textarea placeholder="Descrição" value={description} onChange={e => setDescription(e.target.value)}/><select value={priority} onChange={e => setPriority(e.target.value)}><option value="baixa">Baixa</option><option value="media">Média</option><option value="alta">Alta</option><option value="critica">Crítica</option></select><button disabled={busy || !clients.length}>Abrir chamado</button></form></article></section>
    <section className="columns"><article><h2>Clientes cadastrados</h2>{clients.length ? clients.map(c => <div className="item" key={c.id}><b>{c.name}</b><small>{c.email || c.phone || 'Sem contato informado'}</small></div>) : <p>Nenhum cliente cadastrado.</p>}</article>
    <article><h2>Chamados recentes</h2>{tickets.length ? tickets.map(t => <div className="item" key={t.id}><b>#{t.id} · {t.title}</b><small>{clients.find(c => c.id === t.client_id)?.name || 'Cliente'} · {t.priority}</small><select aria-label={'Status chamado ' + t.id} value={t.status} onChange={e => setStatus(t.id, e.target.value)}><option value="aberto">Aberto</option><option value="em_andamento">Em andamento</option><option value="resolvido">Resolvido</option><option value="fechado">Fechado</option></select></div>) : <p>Nenhum chamado registrado.</p>}</article></section>
    <footer>MVP de desenvolvimento · Não utilizar dados reais antes da autenticação e segurança.</footer>
  </main>;
}

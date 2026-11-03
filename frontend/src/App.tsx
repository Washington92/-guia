import { FormEvent, useEffect, useState } from 'react';
type Client = { id: number; name: string; email: string | null; phone: string | null };
type Asset = { id: number; client_id: number; name: string; category: string; serial_number: string | null; ip_address: string | null; location: string | null; status: string };
type WorkOrder = { id: number; client_id: number; ticket_id: number | null; title: string; description: string; status: string };
type Ticket = { id: number; client_id: number; title: string; description: string; status: string; priority: string };
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API + path, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } });
  if (!response.ok) throw new Error((await response.text()).slice(0, 250));
  return response.json();
}
const navigation = [{icon:'◫',label:'Visão geral'},{icon:'♙',label:'Clientes'},{icon:'▤',label:'Chamados'},{icon:'◇',label:'Ordens de serviço'},{icon:'▦',label:'Ativos'}] as const;
export default function App() {
  const [clients, setClients] = useState<Client[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [orders, setOrders] = useState<WorkOrder[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [assetClient, setAssetClient] = useState('');
  const [assetName, setAssetName] = useState('');
  const [assetCategory, setAssetCategory] = useState('switch');
  const [assetLocation, setAssetLocation] = useState('');
  const [assetIp, setAssetIp] = useState('');
  const [assetSerial, setAssetSerial] = useState('');
  const [orderTitle, setOrderTitle] = useState('');
  const [orderDescription, setOrderDescription] = useState('');
  const [orderClientId, setOrderClientId] = useState('');
  const [orderTicketId, setOrderTicketId] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [section, setSection] = useState<'Visão geral'|'Clientes'|'Chamados'|'Ordens de serviço'|'Ativos'>('Visão geral');
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [phone, setPhone] = useState('');
  const [clientId, setClientId] = useState(''); const [title, setTitle] = useState('');
  const [description, setDescription] = useState(''); const [priority, setPriority] = useState('media');
  async function refresh() {
    const [c, t, o, a] = await Promise.all([request<Client[]>('/api/clients'), request<Ticket[]>('/api/tickets'), request<WorkOrder[]>('/api/work-orders'), request<Asset[]>('/api/assets')]);
    setClients(c); setTickets(t); setOrders(o); setAssets(a);
  }
  useEffect(() => { refresh().catch(e => setError('Não foi possível conectar à API: ' + e.message)); }, []);
  async function addClient(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try { await request('/api/clients', { method:'POST', body:JSON.stringify({name,email:email||null,phone:phone||null}) }); setName('');setEmail('');setPhone('');await refresh(); }
    catch(e){setError(String(e));}finally{setBusy(false);}
  }
  async function addTicket(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try { await request('/api/tickets', {method:'POST',body:JSON.stringify({client_id:Number(clientId),title,description,priority})});setTitle('');setDescription('');await refresh();}
    catch(e){setError(String(e));}finally{setBusy(false);}
  }
  async function setStatus(id:number,status:string){setError('');try{await request('/api/tickets/'+id,{method:'PATCH',body:JSON.stringify({status})});await refresh();}catch(e){setError(String(e));}}
  async function addOrder(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await request('/api/work-orders', { method: 'POST', body: JSON.stringify({ client_id: Number(orderClientId), ticket_id: orderTicketId ? Number(orderTicketId) : null, title: orderTitle, description: orderDescription }) });
      setOrderTitle(''); setOrderDescription(''); setOrderTicketId(''); await refresh();
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }
  async function setOrderStatus(id: number, status: string) {
    setError('');
    try { await request('/api/work-orders/' + id, { method: 'PATCH', body: JSON.stringify({ status }) }); await refresh(); }
    catch (e) { setError(String(e)); }
  }
  async function addAsset(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await request('/api/assets', {method:'POST',body:JSON.stringify({client_id:Number(assetClient),name:assetName,category:assetCategory,location:assetLocation||null,ip_address:assetIp||null,serial_number:assetSerial||null})});
      setAssetName(''); setAssetLocation(''); setAssetIp(''); setAssetSerial(''); await refresh();
    } catch(e){setError(String(e));}finally{setBusy(false);}
  }
  async function setAssetStatus(id:number,status:string){
    setError('');
    try{await request('/api/assets/'+id,{method:'PATCH',body:JSON.stringify({status})});await refresh();}
    catch(e){setError(String(e));}
  }
  return <div className="shell">
    <aside className="sidebar">
      <div className="logo"><div className="logo-mark">A</div><div><strong>Águia Gestão</strong><small>CRM Workspace</small></div></div>
      <div className="nav-heading">WORKSPACE</div>
      <nav aria-label="Navegação principal">{navigation.map(item=><button key={item.label} className={'nav-item '+(section===item.label?'active':'')} onClick={()=>setSection(item.label)}><span className="nav-icon">{item.icon}</span>{item.label}</button>)}</nav>
      <div className="sidebar-bottom"><span className="status-dot"/> Ambiente de desenvolvimento</div>
    </aside>
    <div className="workspace">
      <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> {section}</div><div className="avatar" aria-label="Águia Gestão">AG</div></header>
      <main className="content">
        <div className="heading"><div><p className="eyebrow">ÁGUIA GESTÃO CRM</p><h1>{section==='Visão geral'?'Bom trabalho começa com clareza.':section}</h1><p className="subtitle">{section==='Visão geral'?'Sua operação de suporte e infraestrutura em um só lugar.':'Gerencie sua operação com simplicidade e precisão.'}</p></div><span className="env-pill"><span className="status-dot"/> Desenvolvimento</span></div>
        {error&&<div role="alert" className="error">{error}</div>}
        {section==='Visão geral'&&<><div className="stats"><article className="stat-card"><span>Clientes ativos</span><strong>{clients.length}</strong><small>Base cadastrada</small></article><article className="stat-card"><span>Chamados totais</span><strong>{tickets.length}</strong><small>Histórico operacional</small></article><article className="stat-card"><span>Em aberto</span><strong>{tickets.filter(t=>t.status==='aberto').length}</strong><small>Aguardando atendimento</small></article><article className="stat-card"><span>Em andamento</span><strong>{tickets.filter(t=>t.status==='em_andamento').length}</strong><small>Atendimentos ativos</small></article></div><section className="panel"><div className="panel-head"><div><h2>Chamados recentes</h2><p>Acompanhe o que está acontecendo.</p></div><button className="text-button" onClick={()=>setSection('Chamados')}>Ver todos →</button></div><TicketList tickets={tickets.slice(0,5)} clients={clients} setStatus={setStatus}/></section></>}
        {section==='Clientes'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Novo cliente</h2></div><form onSubmit={addClient}><label>Nome ou empresa<input required minLength={2} placeholder="Ex.: Unidade Centro" value={name} onChange={e=>setName(e.target.value)}/></label><label>E-mail<input type="email" placeholder="contato@empresa.com" value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Telefone<input placeholder="(11) 99999-9999" value={phone} onChange={e=>setPhone(e.target.value)}/></label><button className="primary" disabled={busy}>Cadastrar cliente</button></form></section><section className="panel"><div className="panel-head"><h2>Clientes cadastrados</h2><span className="count">{clients.length}</span></div>{clients.length?clients.map(c=><div className="list-row" key={c.id}><div className="person-icon">{c.name.slice(0,1).toUpperCase()}</div><div><b>{c.name}</b><small>{c.email||c.phone||'Sem contato informado'}</small></div></div>):<p className="empty">Nenhum cliente cadastrado.</p>}</section></div>}
        {section==='Chamados'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Abrir chamado</h2></div><form onSubmit={addTicket}><label>Cliente<select required value={clientId} onChange={e=>setClientId(e.target.value)}><option value="">Selecione um cliente</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Assunto<input required minLength={3} placeholder="Ex.: Falha de conectividade" value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Descrição<textarea placeholder="Descreva o problema" value={description} onChange={e=>setDescription(e.target.value)}/></label><label>Prioridade<select value={priority} onChange={e=>setPriority(e.target.value)}><option value="baixa">Baixa</option><option value="media">Média</option><option value="alta">Alta</option><option value="critica">Crítica</option></select></label><button className="primary" disabled={busy||!clients.length}>Abrir chamado</button></form></section><section className="panel"><div className="panel-head"><h2>Chamados</h2><span className="count">{tickets.length}</span></div><TicketList tickets={tickets} clients={clients} setStatus={setStatus}/></section></div>}
        {section==='Ordens de serviço'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Nova ordem de serviço</h2></div><form onSubmit={addOrder}><label>Cliente<select required value={orderClientId} onChange={e=>{setOrderClientId(e.target.value);setOrderTicketId('');}}><option value="">Selecione um cliente</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Chamado relacionado (opcional)<select value={orderTicketId} onChange={e=>setOrderTicketId(e.target.value)}><option value="">Sem chamado relacionado</option>{tickets.filter(t=>t.client_id===Number(orderClientId)).map(t=><option key={t.id} value={t.id}>#{t.id} · {t.title}</option>)}</select></label><label>Serviço<input required minLength={3} placeholder="Ex.: Instalação de Access Point" value={orderTitle} onChange={e=>setOrderTitle(e.target.value)}/></label><label>Descrição<textarea placeholder="Descreva as atividades previstas" value={orderDescription} onChange={e=>setOrderDescription(e.target.value)}/></label><button className="primary" disabled={busy||!clients.length}>Criar ordem de serviço</button></form></section><section className="panel"><div className="panel-head"><h2>Ordens de serviço</h2><span className="count">{orders.length}</span></div>{orders.length?orders.map(o=><div className="ticket-row" key={o.id}><div className="ticket-icon">◇</div><div className="ticket-info"><b>OS #{o.id} · {o.title}</b><small>{clients.find(c=>c.id===o.client_id)?.name||'Cliente'}{o.ticket_id?' · Chamado #'+o.ticket_id:''}</small></div><select aria-label={'Status da OS '+o.id} value={o.status} onChange={e=>setOrderStatus(o.id,e.target.value)}><option value="pendente">Pendente</option><option value="em_execucao">Em execução</option><option value="concluida">Concluída</option><option value="cancelada">Cancelada</option></select></div>):<p className="empty">Nenhuma ordem de serviço cadastrada.</p>}</section></div>}
        {section==='Ativos'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Cadastrar equipamento</h2></div><form onSubmit={addAsset}><label>Cliente<select required value={assetClient} onChange={e=>setAssetClient(e.target.value)}><option value="">Selecione um cliente</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Nome do equipamento<input required minLength={2} placeholder="Ex.: Switch 24 portas" value={assetName} onChange={e=>setAssetName(e.target.value)}/></label><label>Categoria<select value={assetCategory} onChange={e=>setAssetCategory(e.target.value)}>{[['switch','Switch'],['roteador','Roteador'],['access_point','Access Point'],['camera','Câmera'],['dvr_nvr','DVR / NVR'],['servidor','Servidor'],['outro','Outro']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label>Localização<input placeholder="Ex.: Rack principal" value={assetLocation} onChange={e=>setAssetLocation(e.target.value)}/></label><label>Endereço IP<input placeholder="Ex.: 192.168.1.10" value={assetIp} onChange={e=>setAssetIp(e.target.value)}/></label><label>Número de série<input placeholder="Opcional" value={assetSerial} onChange={e=>setAssetSerial(e.target.value)}/></label><button className="primary" disabled={busy||!clients.length}>Cadastrar equipamento</button></form></section><section className="panel"><div className="panel-head"><h2>Inventário de ativos</h2><span className="count">{assets.length}</span></div>{assets.length?assets.map(a=><div className="ticket-row" key={a.id}><div className="ticket-icon">▦</div><div className="ticket-info"><b>{a.name}</b><small>{clients.find(c=>c.id===a.client_id)?.name||'Cliente'} · {a.category.replace('_',' / ')} · {a.location||'Sem local'}{a.ip_address?' · '+a.ip_address:''}</small></div><select aria-label={'Status do ativo '+a.id} value={a.status} onChange={e=>setAssetStatus(a.id,e.target.value)}><option value="ativo">Ativo</option><option value="manutencao">Manutenção</option><option value="inativo">Inativo</option></select></div>):<p className="empty">Nenhum equipamento cadastrado.</p>}</section></div>}
        <footer>Águia Gestão CRM · MVP de homologação · Não inserir dados reais sem autenticação.</footer>
      </main>
    </div>
  </div>;
}
function TicketList({tickets,clients,setStatus}:{tickets:Ticket[];clients:Client[];setStatus:(id:number,status:string)=>void}){
  return tickets.length?<div className="ticket-list">{tickets.map(t=><div className="ticket-row" key={t.id}><div className="ticket-icon">▤</div><div className="ticket-info"><b>{t.title}</b><small>#{t.id} · {clients.find(c=>c.id===t.client_id)?.name||'Cliente'} · {t.priority}</small></div><select aria-label={'Status do chamado '+t.id} value={t.status} onChange={e=>setStatus(t.id,e.target.value)}><option value="aberto">Aberto</option><option value="em_andamento">Em andamento</option><option value="resolvido">Resolvido</option><option value="fechado">Fechado</option></select></div>)}</div>:<p className="empty">Tudo em ordem. Nenhum chamado por aqui.</p>;
}

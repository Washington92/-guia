import { FormEvent, useEffect, useState } from 'react';
type Client = { id: number; name: string; email: string | null; phone: string | null };
type StockItem = { id:number; name:string; sku:string|null; unit:string; quantity:number; min_quantity:number };
type StockMovement = { id:number; item_id:number; work_order_id:number|null; type:string; quantity:number; note:string };
type Asset = { id: number; client_id: number; name: string; category: string; serial_number: string | null; ip_address: string | null; location: string | null; status: string };
type WorkOrder = { id: number; client_id: number; ticket_id: number | null; title: string; description: string; status: string };
type Ticket = { id: number; client_id: number; title: string; description: string; status: string; priority: string };
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API + path, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } });
  if (!response.ok) throw new Error((await response.text()).slice(0, 250));
  return response.json();
}
const navigation = [{icon:'◫',label:'Visão geral'},{icon:'♙',label:'Clientes'},{icon:'▤',label:'Chamados'},{icon:'◇',label:'Ordens de serviço'},{icon:'▦',label:'Ativos'},{icon:'▥',label:'Estoque'}] as const;
export default function App() {
  const [search, setSearch] = useState('');
  const [darkMode, setDarkMode] = useState(() => typeof window !== 'undefined' && window.localStorage.getItem('aguia-theme') === 'dark');
  const [clients, setClients] = useState<Client[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [orders, setOrders] = useState<WorkOrder[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [stockItems,setStockItems] = useState<StockItem[]>([]);
  const [stockMovements,setStockMovements] = useState<StockMovement[]>([]);
  const [stockName,setStockName] = useState('');
  const [stockUnit,setStockUnit] = useState('un');
  const [stockMinimum,setStockMinimum] = useState('0');
  const [movementItem,setMovementItem] = useState('');
  const [movementType,setMovementType] = useState('entrada');
  const [movementQuantity,setMovementQuantity] = useState('1');
  const [movementOrder,setMovementOrder] = useState('');
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
  const [section, setSection] = useState<'Visão geral'|'Clientes'|'Chamados'|'Ordens de serviço'|'Ativos'|'Estoque'>('Visão geral');
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [phone, setPhone] = useState('');
  const [clientId, setClientId] = useState(''); const [title, setTitle] = useState('');
  const [description, setDescription] = useState(''); const [priority, setPriority] = useState('media');
  const matches = (value: string) => value.toLocaleLowerCase('pt-BR').includes(search.trim().toLocaleLowerCase('pt-BR'));
  const filteredClients = clients.filter(c => matches([c.name,c.email,c.phone].filter(Boolean).join(' ')));
  const filteredTickets = tickets.filter(t => matches([t.title,t.description,t.priority,clients.find(c=>c.id===t.client_id)?.name].filter(Boolean).join(' ')));
  const filteredOrders = orders.filter(o => matches([o.title,o.description,o.status,clients.find(c=>c.id===o.client_id)?.name].filter(Boolean).join(' ')));
  const filteredAssets = assets.filter(a => matches([a.name,a.category,a.location,a.ip_address,a.serial_number,clients.find(c=>c.id===a.client_id)?.name].filter(Boolean).join(' ')));
  const filteredStock = stockItems.filter(i => matches([i.name,i.sku].filter(Boolean).join(' ')));
  const openTickets = tickets.filter(t => t.status === 'aberto' || t.status === 'em_andamento');
  const criticalTickets = openTickets.filter(t => t.priority === 'critica' || t.priority === 'alta');
  const pendingOrders = orders.filter(o => o.status === 'pendente' || o.status === 'em_execucao');
  const lowStock = stockItems.filter(i => i.quantity <= i.min_quantity);
  const dashboardAlerts = [
    ...criticalTickets.map(t => ({ id:'ticket-'+t.id, title:t.title, detail:'Chamado #'+t.id+' · '+t.priority, target:'Chamados' as const, severity:'critical' })),
    ...lowStock.map(i => ({ id:'stock-'+i.id, title:i.name, detail:'Saldo '+i.quantity+' '+i.unit+' · mínimo '+i.min_quantity, target:'Estoque' as const, severity:'warning' })),
  ];
  async function refresh() {
    const [c, t, o, a, items, movements] = await Promise.all([request<Client[]>('/api/clients'), request<Ticket[]>('/api/tickets'), request<WorkOrder[]>('/api/work-orders'), request<Asset[]>('/api/assets'), request<StockItem[]>('/api/stock/items'), request<StockMovement[]>('/api/stock/movements')]);
    setClients(c); setTickets(t); setOrders(o); setAssets(a); setStockItems(items); setStockMovements(movements);
  }
  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? 'dark' : 'light';
    window.localStorage.setItem('aguia-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);
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
  async function addStockItem(e:FormEvent){
    e.preventDefault();setBusy(true);setError('');
    try{await request('/api/stock/items',{method:'POST',body:JSON.stringify({name:stockName,unit:stockUnit,min_quantity:Number(stockMinimum)})});setStockName('');await refresh();}
    catch(e){setError(String(e));}finally{setBusy(false);}
  }
  async function addStockMovement(e:FormEvent){
    e.preventDefault();setBusy(true);setError('');
    try{await request('/api/stock/movements',{method:'POST',body:JSON.stringify({item_id:Number(movementItem),type:movementType,quantity:Number(movementQuantity),work_order_id:movementOrder?Number(movementOrder):null})});await refresh();}
    catch(e){setError(String(e));}finally{setBusy(false);}
  }
  return <div className="shell">
    <aside className="sidebar">
      <div className="logo"><div className="logo-mark">A</div><div><strong>Águia Gestão</strong><small>CRM Workspace</small></div></div>
      <div className="nav-heading">WORKSPACE</div>
      <nav aria-label="Navegação principal">{navigation.map(item=><button key={item.label} className={'nav-item '+(section===item.label?'active':'')} onClick={()=>{setSection(item.label);setSearch('');}}><span className="nav-icon">{item.icon}</span>{item.label}</button>)}</nav>
      <div className="sidebar-bottom"><span className="status-dot"/> Ambiente de desenvolvimento</div>
    </aside>
    <div className="workspace">
      <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> {section}</div><div className="topbar-actions"><button type="button" className="theme-toggle" aria-label={darkMode?'Ativar modo claro':'Ativar modo escuro'} aria-pressed={darkMode} onClick={()=>setDarkMode(v=>!v)} title={darkMode?'Modo claro':'Modo escuro'}>{darkMode?'☀':'☾'} <span>{darkMode?'Claro':'Escuro'}</span></button><div className="avatar" aria-label="Águia Gestão">AG</div></div></header>
      <main className="content">
        <div className="heading"><div><p className="eyebrow">ÁGUIA GESTÃO CRM</p><h1>{section==='Visão geral'?'Bom trabalho começa com clareza.':section}</h1><p className="subtitle">{section==='Visão geral'?'Sua operação de suporte e infraestrutura em um só lugar.':'Gerencie sua operação com simplicidade e precisão.'}</p></div><span className="env-pill"><span className="status-dot"/> Desenvolvimento</span></div>
        {section!=='Visão geral'&&<div className="searchbar"><span aria-hidden="true">⌕</span><input type="search" aria-label="Buscar registros" placeholder={'Buscar em '+section.toLocaleLowerCase('pt-BR')+'...'} value={search} onChange={e=>setSearch(e.target.value)}/>{search&&<button type="button" onClick={()=>setSearch('')} aria-label="Limpar busca">✕</button>}</div>}
        {error&&<div role="alert" className="error">{error}</div>}
        {section==='Visão geral'&&<>
          <div className="stats">
            <article className="stat-card"><span>Clientes cadastrados</span><strong>{clients.length}</strong><small>Base de atendimento</small></article>
            <article className="stat-card"><span>Chamados ativos</span><strong>{openTickets.length}</strong><small>{criticalTickets.length} com prioridade alta/crítica</small></article>
            <article className="stat-card"><span>OS pendentes / execução</span><strong>{pendingOrders.length}</strong><small>{orders.length} ordens cadastradas</small></article>
            <article className="stat-card"><span>Estoque em alerta</span><strong>{lowStock.length}</strong><small>Itens no mínimo ou abaixo</small></article>
          </div>
          <div className="dashboard-quick-actions" aria-label="Acesso rápido aos módulos">
            {(['Clientes','Chamados','Ordens de serviço','Ativos','Estoque'] as const).map((label)=><button type="button" key={label} onClick={()=>{setSection(label);setSearch('')}}>{label}<span aria-hidden="true">↗</span></button>)}
          </div>
          <div className="dashboard-grid">
            <section className="panel"><div className="panel-head"><div><h2>Prioridades da operação</h2><p>Chamados urgentes e materiais para reposição.</p></div><span className="count">{dashboardAlerts.length}</span></div>
              {dashboardAlerts.length?dashboardAlerts.slice(0,6).map(a=><button type="button" className="alert-row" key={a.id} onClick={()=>{setSection(a.target);setSearch('')}}><span className={'alert-indicator '+a.severity} aria-hidden="true">!</span><span className="ticket-info"><b>{a.title}</b><small>{a.detail}</small></span><span className="alert-arrow" aria-hidden="true">→</span></button>):<p className="empty">Nenhum alerta operacional no momento.</p>}
            </section>
            <section className="panel"><div className="panel-head"><div><h2>Resumo de chamados</h2><p>Distribuição por status atual.</p></div><button className="text-button" onClick={()=>setSection('Chamados')}>Ver chamados →</button></div>
              <div className="status-breakdown">{[['Abertos',tickets.filter(t=>t.status==='aberto').length,'open'],['Em andamento',tickets.filter(t=>t.status==='em_andamento').length,'progress'],['Resolvidos',tickets.filter(t=>t.status==='resolvido').length,'done'],['Fechados',tickets.filter(t=>t.status==='fechado').length,'closed']].map(([label,count,kind])=><div className="breakdown-row" key={label}><span className={'breakdown-dot '+kind}/><span>{label}</span><strong>{count}</strong></div>)}</div>
            </section>
          </div>
          <section className="panel dashboard-recent"><div className="panel-head"><div><h2>Chamados recentes</h2><p>Acompanhe os últimos registros da operação.</p></div><button className="text-button" onClick={()=>setSection('Chamados')}>Ver todos →</button></div><TicketList tickets={tickets.slice(0,5)} clients={clients} setStatus={setStatus}/></section>
        </>}
        {section==='Clientes'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Novo cliente</h2></div><form onSubmit={addClient}><label>Nome ou empresa<input required minLength={2} placeholder="Ex.: Unidade Centro" value={name} onChange={e=>setName(e.target.value)}/></label><label>E-mail<input type="email" placeholder="contato@empresa.com" value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Telefone<input placeholder="(11) 99999-9999" value={phone} onChange={e=>setPhone(e.target.value)}/></label><button className="primary" disabled={busy}>Cadastrar cliente</button></form></section><section className="panel"><div className="panel-head"><h2>Clientes cadastrados</h2><span className="count">{clients.length}</span></div>{filteredClients.length?filteredClients.map(c=><div className="list-row" key={c.id}><div className="person-icon">{c.name.slice(0,1).toUpperCase()}</div><div><b>{c.name}</b><small>{c.email||c.phone||'Sem contato informado'}</small></div></div>):<p className="empty">Nenhum cliente cadastrado.</p>}</section></div>}
        {section==='Chamados'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Abrir chamado</h2></div><form onSubmit={addTicket}><label>Cliente<select required value={clientId} onChange={e=>setClientId(e.target.value)}><option value="">Selecione um cliente</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Assunto<input required minLength={3} placeholder="Ex.: Falha de conectividade" value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Descrição<textarea placeholder="Descreva o problema" value={description} onChange={e=>setDescription(e.target.value)}/></label><label>Prioridade<select value={priority} onChange={e=>setPriority(e.target.value)}><option value="baixa">Baixa</option><option value="media">Média</option><option value="alta">Alta</option><option value="critica">Crítica</option></select></label><button className="primary" disabled={busy||!clients.length}>Abrir chamado</button></form></section><section className="panel"><div className="panel-head"><h2>Chamados</h2><span className="count">{tickets.length}</span></div><TicketList tickets={filteredTickets} clients={clients} setStatus={setStatus}/></section></div>}
        {section==='Ordens de serviço'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Nova ordem de serviço</h2></div><form onSubmit={addOrder}><label>Cliente<select required value={orderClientId} onChange={e=>{setOrderClientId(e.target.value);setOrderTicketId('');}}><option value="">Selecione um cliente</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Chamado relacionado (opcional)<select value={orderTicketId} onChange={e=>setOrderTicketId(e.target.value)}><option value="">Sem chamado relacionado</option>{tickets.filter(t=>t.client_id===Number(orderClientId)).map(t=><option key={t.id} value={t.id}>#{t.id} · {t.title}</option>)}</select></label><label>Serviço<input required minLength={3} placeholder="Ex.: Instalação de Access Point" value={orderTitle} onChange={e=>setOrderTitle(e.target.value)}/></label><label>Descrição<textarea placeholder="Descreva as atividades previstas" value={orderDescription} onChange={e=>setOrderDescription(e.target.value)}/></label><button className="primary" disabled={busy||!clients.length}>Criar ordem de serviço</button></form></section><section className="panel"><div className="panel-head"><h2>Ordens de serviço</h2><span className="count">{orders.length}</span></div>{filteredOrders.length?filteredOrders.map(o=><div className="ticket-row" key={o.id}><div className="ticket-icon">◇</div><div className="ticket-info"><b>OS #{o.id} · {o.title}</b><small>{clients.find(c=>c.id===o.client_id)?.name||'Cliente'}{o.ticket_id?' · Chamado #'+o.ticket_id:''}</small></div><select aria-label={'Status da OS '+o.id} value={o.status} onChange={e=>setOrderStatus(o.id,e.target.value)}><option value="pendente">Pendente</option><option value="em_execucao">Em execução</option><option value="concluida">Concluída</option><option value="cancelada">Cancelada</option></select></div>):<p className="empty">Nenhuma ordem de serviço cadastrada.</p>}</section></div>}
        {section==='Ativos'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Cadastrar equipamento</h2></div><form onSubmit={addAsset}><label>Cliente<select required value={assetClient} onChange={e=>setAssetClient(e.target.value)}><option value="">Selecione um cliente</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Nome do equipamento<input required minLength={2} placeholder="Ex.: Switch 24 portas" value={assetName} onChange={e=>setAssetName(e.target.value)}/></label><label>Categoria<select value={assetCategory} onChange={e=>setAssetCategory(e.target.value)}>{[['switch','Switch'],['roteador','Roteador'],['access_point','Access Point'],['camera','Câmera'],['dvr_nvr','DVR / NVR'],['servidor','Servidor'],['outro','Outro']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label>Localização<input placeholder="Ex.: Rack principal" value={assetLocation} onChange={e=>setAssetLocation(e.target.value)}/></label><label>Endereço IP<input placeholder="Ex.: 192.168.1.10" value={assetIp} onChange={e=>setAssetIp(e.target.value)}/></label><label>Número de série<input placeholder="Opcional" value={assetSerial} onChange={e=>setAssetSerial(e.target.value)}/></label><button className="primary" disabled={busy||!clients.length}>Cadastrar equipamento</button></form></section><section className="panel"><div className="panel-head"><h2>Inventário de ativos</h2><span className="count">{assets.length}</span></div>{filteredAssets.length?filteredAssets.map(a=><div className="ticket-row" key={a.id}><div className="ticket-icon">▦</div><div className="ticket-info"><b>{a.name}</b><small>{clients.find(c=>c.id===a.client_id)?.name||'Cliente'} · {a.category.replace('_',' / ')} · {a.location||'Sem local'}{a.ip_address?' · '+a.ip_address:''}</small></div><select aria-label={'Status do ativo '+a.id} value={a.status} onChange={e=>setAssetStatus(a.id,e.target.value)}><option value="ativo">Ativo</option><option value="manutencao">Manutenção</option><option value="inativo">Inativo</option></select></div>):<p className="empty">Nenhum equipamento cadastrado.</p>}</section></div>}
        {section==='Estoque'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Novo material</h2></div><form onSubmit={addStockItem}><label>Material<input required minLength={2} placeholder="Ex.: Cabo de rede CAT6" value={stockName} onChange={e=>setStockName(e.target.value)}/></label><label>Unidade<select value={stockUnit} onChange={e=>setStockUnit(e.target.value)}><option value="un">Unidade</option><option value="m">Metro</option><option value="cx">Caixa</option><option value="pct">Pacote</option></select></label><label>Estoque mínimo<input type="number" min="0" required value={stockMinimum} onChange={e=>setStockMinimum(e.target.value)}/></label><button className="primary" disabled={busy}>Cadastrar material</button></form><div className="panel-head" style={{marginTop:30}}><h2>Movimentar estoque</h2></div><form onSubmit={addStockMovement}><label>Material<select required value={movementItem} onChange={e=>setMovementItem(e.target.value)}><option value="">Selecione o material</option>{stockItems.map(i=><option key={i.id} value={i.id}>{i.name}</option>)}</select></label><label>Movimento<select value={movementType} onChange={e=>setMovementType(e.target.value)}><option value="entrada">Entrada</option><option value="saida">Saída</option></select></label><label>Quantidade<input type="number" min="1" step="1" required value={movementQuantity} onChange={e=>setMovementQuantity(e.target.value)}/></label><label>Ordem de serviço (opcional)<select value={movementOrder} onChange={e=>setMovementOrder(e.target.value)}><option value="">Sem OS vinculada</option>{orders.map(o=><option key={o.id} value={o.id}>OS #{o.id} · {o.title}</option>)}</select></label><button className="primary" disabled={busy||!stockItems.length}>Registrar movimento</button></form></section><section className="panel"><div className="panel-head"><h2>Materiais em estoque</h2><span className="count">{stockItems.length}</span></div>{filteredStock.length?filteredStock.map(i=><div className="ticket-row" key={i.id}><div className="ticket-icon">▥</div><div className="ticket-info"><b>{i.name}</b><small>Saldo: {i.quantity} {i.unit} · Mínimo: {i.min_quantity} {i.unit}{i.quantity<=i.min_quantity?' · Repor estoque':''}</small></div></div>):<p className="empty">Nenhum material cadastrado.</p>}<div className="panel-head" style={{marginTop:28}}><h2>Últimas movimentações</h2></div>{stockMovements.slice(0,10).map(m=><div className="ticket-row" key={m.id}><div className="ticket-info"><b>{m.type==='entrada'?'+':'−'}{m.quantity} · {stockItems.find(i=>i.id===m.item_id)?.name||'Material'}</b><small>{m.work_order_id?'OS #'+m.work_order_id:'Movimento avulso'}</small></div></div>)}</section></div>}
        <footer>Águia Gestão CRM · MVP de homologação · Não inserir dados reais sem autenticação.</footer>
      </main>
    </div>
  </div>;
}
function TicketList({tickets,clients,setStatus}:{tickets:Ticket[];clients:Client[];setStatus:(id:number,status:string)=>void}){
  return tickets.length?<div className="ticket-list">{tickets.map(t=><div className="ticket-row" key={t.id}><div className="ticket-icon">▤</div><div className="ticket-info"><b>{t.title}</b><small>#{t.id} · {clients.find(c=>c.id===t.client_id)?.name||'Cliente'} · {t.priority}</small></div><select aria-label={'Status do chamado '+t.id} value={t.status} onChange={e=>setStatus(t.id,e.target.value)}><option value="aberto">Aberto</option><option value="em_andamento">Em andamento</option><option value="resolvido">Resolvido</option><option value="fechado">Fechado</option></select></div>)}</div>:<p className="empty">Tudo em ordem. Nenhum chamado por aqui.</p>;
}

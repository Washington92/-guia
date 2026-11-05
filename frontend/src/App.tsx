import { FormEvent, useEffect, useState } from 'react';
type Analytics = {filters:{client_id:number|null;start_date:string|null;end_date:string|null};tickets:{total:number;active:number;urgent_active:number;by_priority:Record<string,number>;by_status:Record<string,number>};work_orders:{pending_or_running:number};assets:{total:number};top_technician:{leaders:{id:number;name:string;completed_tickets:number}[];ranking:{id:number;name:string;completed_tickets:number}[];completed_total:number;completed_without_assignment:number};technician_workload:{id:number;name:string;active_tickets:number}[]};
type CRMUser = {id:number;username:string;role:string;active:boolean};
type Client = { id: number; name: string; email: string | null; phone: string | null };
type StockItem = { id:number; name:string; sku:string|null; unit:string; quantity:number; min_quantity:number };
type StockMovement = { id:number; item_id:number; work_order_id:number|null; type:string; quantity:number; note:string };
type Asset = { id: number; client_id: number; name: string; category: string; serial_number: string | null; ip_address: string | null; location: string | null; status: string };
type WorkOrder = { id: number; client_id: number; ticket_id: number | null; title: string; description: string; status: string; technician_id: number | null; scheduled_at: string | null; estimated_duration_hours: number };
type Technician = {id:number;name:string;email:string|null;specialty:string|null;active:number};
type Assignment = {ticket_id:number;technician_id:number;assigned_at:string};
type TicketEvent = { id:number; ticket_id:number; event_type:string; previous_value:string|null; new_value:string; created_at:string };
type TicketNote = { id:number; ticket_id:number; author:string; content:string; created_at:string };
type Ticket = { id: number; client_id: number; title: string; description: string; status: string; priority: string };
type InspectionIssue = { sector: string; item: string; observation: string; priority: string; photo_url: string };
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
let accessToken: string | null = null;
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API + path, { ...init, headers: { 'Content-Type': 'application/json', ...(accessToken ? { Authorization: 'Bearer ' + accessToken } : {}), ...init?.headers } });
  if (!response.ok) throw new Error((await response.text()).slice(0, 250));
  return response.json();
}
const navigation = [{icon:'◫',label:'Visão geral'},{icon:'♙',label:'Clientes'},{icon:'▤',label:'Chamados'},{icon:'◇',label:'Ordens de serviço'},{icon:'▦',label:'Agenda'},{icon:'✓',label:'Vistorias'},{icon:'▦',label:'Ativos'},{icon:'▥',label:'Estoque'},{icon:'♧',label:'Equipe técnica'},{icon:'⚙',label:'Usuários'}] as const;
export default function App() {
  const [currentRole,setCurrentRole] = useState('');
  const [users,setUsers] = useState<CRMUser[]>([]);
  const [newUsername,setNewUsername] = useState('');
  const [newPassword,setNewPassword] = useState('');
  const [newRole,setNewRole] = useState('technician');
  const [userMessage,setUserMessage] = useState('');
  const [authReady,setAuthReady] = useState(false);
  const [authenticated,setAuthenticated] = useState(false);
  const [authUser,setAuthUser] = useState('');
  const [authPassword,setAuthPassword] = useState('');
  const [authError,setAuthError] = useState('');
  const [authBusy,setAuthBusy] = useState(false);
  const [setupMode,setSetupMode] = useState(false);
  const [search, setSearch] = useState('');
  const [ticketFilter, setTicketFilter] = useState('todos');
  const [technicianFilter,setTechnicianFilter] = useState('todos');
  const [queueFilter,setQueueFilter] = useState('todas');
  const [selectedTicketId, setSelectedTicketId] = useState<number | null>(null);
  const [ticketNotes,setTicketNotes] = useState<TicketNote[]>([]);
  const [ticketEvents,setTicketEvents] = useState<TicketEvent[]>([]);
  const [noteAuthor,setNoteAuthor] = useState('Técnico');
  const [noteContent,setNoteContent] = useState('');
  const [noteBusy,setNoteBusy] = useState(false);
  const [noteError,setNoteError] = useState('');
  const [darkMode, setDarkMode] = useState(() => typeof window !== 'undefined' && window.localStorage.getItem('aguia-theme') === 'dark');
  const [analytics,setAnalytics] = useState<Analytics|null>(null);
  const [analyticsError,setAnalyticsError] = useState('');
  const [analyticsClient,setAnalyticsClient] = useState('');
  const [analyticsStart,setAnalyticsStart] = useState('');
  const [analyticsEnd,setAnalyticsEnd] = useState('');
  const [clients, setClients] = useState<Client[]>([]);
  const [technicians,setTechnicians] = useState<Technician[]>([]);
  const [assignments,setAssignments] = useState<Assignment[]>([]);
  const [technicianName,setTechnicianName] = useState('');
  const [technicianEmail,setTechnicianEmail] = useState('');
  const [technicianSpecialty,setTechnicianSpecialty] = useState('');
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
  const [orderTechnicianId, setOrderTechnicianId] = useState('');
  const [orderScheduledAt, setOrderScheduledAt] = useState('');
  const [orderDuration, setOrderDuration] = useState('2');
  const [inspectionClient,setInspectionClient]=useState('');
  const [inspectionName,setInspectionName]=useState('Vistoria de unidade');
  const [inspectionUnit,setInspectionUnit]=useState('');
  const [inspectorName,setInspectorName]=useState('');
  const [inspectionSector,setInspectionSector]=useState('Catracas');
  const [inspectionItem,setInspectionItem]=useState('');
  const [inspectionObservation,setInspectionObservation]=useState('');
  const [inspectionPriority,setInspectionPriority]=useState('media');
  const [inspectionPhoto,setInspectionPhoto]=useState('');
  const [inspectionTechnician,setInspectionTechnician]=useState('');
  const [inspectionCreateOrder,setInspectionCreateOrder]=useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [section, setSection] = useState<'Visão geral'|'Clientes'|'Chamados'|'Ordens de serviço'|'Agenda'|'Ativos'|'Estoque'|'Equipe técnica'|'Usuários'|'Vistorias'>('Visão geral');
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [phone, setPhone] = useState('');
  const [clientId, setClientId] = useState(''); const [title, setTitle] = useState('');
  const [description, setDescription] = useState(''); const [priority, setPriority] = useState('media');
  const matches = (value: string) => value.toLocaleLowerCase('pt-BR').includes(search.trim().toLocaleLowerCase('pt-BR'));
  const filteredTechnicians = technicians.filter(t=>matches([t.name,t.email,t.specialty].filter(Boolean).join(' ')));
  const filteredClients = clients.filter(c => matches([c.name,c.email,c.phone].filter(Boolean).join(' ')));
  const filteredTickets = tickets.filter(t => matches([t.title,t.description,t.priority,clients.find(c=>c.id===t.client_id)?.name].filter(Boolean).join(' ')) && (ticketFilter==='todos'||t.status===ticketFilter||t.priority===ticketFilter) && (technicianFilter==='todos'||(technicianFilter==='sem_responsavel'?!assignments.some(a=>a.ticket_id===t.id):assignments.some(a=>a.ticket_id===t.id&&a.technician_id===Number(technicianFilter)))) && (queueFilter==='todas'||(queueFilter==='nao_atribuidos'?!assignments.some(a=>a.ticket_id===t.id):queueFilter==='urgentes'?['alta','critica'].includes(t.priority)&&['aberto','em_andamento'].includes(t.status):queueFilter==='ativos'?['aberto','em_andamento'].includes(t.status):t.status===queueFilter)));
  const filteredOrders = orders.filter(o => matches([o.title,o.description,o.status,clients.find(c=>c.id===o.client_id)?.name].filter(Boolean).join(' ')));
  const filteredAssets = assets.filter(a => matches([a.name,a.category,a.location,a.ip_address,a.serial_number,clients.find(c=>c.id===a.client_id)?.name].filter(Boolean).join(' ')));
  const filteredStock = stockItems.filter(i => matches([i.name,i.sku].filter(Boolean).join(' ')));
  const assignedTechnician = (ticketId:number) => assignments.find(a=>a.ticket_id===ticketId)?.technician_id;
  const workload = technicians.map(tech=>{const assigned=tickets.filter(t=>assignedTechnician(t.id)===tech.id);return {technician:tech,assigned:assigned.length,active:assigned.filter(t=>['aberto','em_andamento'].includes(t.status)).length,resolved:assigned.filter(t=>['resolvido','fechado'].includes(t.status)).length,critical:assigned.filter(t=>['alta','critica'].includes(t.priority)&&['aberto','em_andamento'].includes(t.status)).length};});
  const unassignedTickets = tickets.filter(t=>!assignedTechnician(t.id)&&['aberto','em_andamento'].includes(t.status));
  const selectedTicket = tickets.find(t => t.id === selectedTicketId);
  const openTickets = tickets.filter(t => t.status === 'aberto' || t.status === 'em_andamento');
  const criticalTickets = openTickets.filter(t => t.priority === 'critica' || t.priority === 'alta');
  const pendingOrders = orders.filter(o => o.status === 'pendente' || o.status === 'em_execucao');
  const lowStock = stockItems.filter(i => i.quantity <= i.min_quantity);
  const dashboardAlerts = [
    ...criticalTickets.map(t => ({ id:'ticket-'+t.id, title:t.title, detail:'Chamado #'+t.id+' · '+t.priority, target:'Chamados' as const, severity:'critical' })),
    ...lowStock.map(i => ({ id:'stock-'+i.id, title:i.name, detail:'Saldo '+i.quantity+' '+i.unit+' · mínimo '+i.min_quantity, target:'Estoque' as const, severity:'warning' })),
  ];
  useEffect(() => {
    if(selectedTicketId===null){setTicketNotes([]);setNoteError('');return;}
    let active=true;
    setTicketNotes([]);
    setTicketEvents([]);
    setNoteError('');
    request<TicketNote[]>('/api/tickets/'+selectedTicketId+'/notes').then(notes=>{if(active)setTicketNotes(notes)}).catch(()=>{if(active)setNoteError('Não foi possível carregar o histórico técnico.')});
    request<TicketEvent[]>('/api/tickets/'+selectedTicketId+'/events').then(events=>{if(active)setTicketEvents(events)}).catch(()=>{if(active)setNoteError('Não foi possível carregar as alterações de status.')});
    return ()=>{active=false};
  },[selectedTicketId]);
  async function addTicketNote(e:FormEvent){
    e.preventDefault();
    if(selectedTicketId===null)return;
    setNoteBusy(true);setNoteError('');
    try{
      await request('/api/tickets/'+selectedTicketId+'/notes',{method:'POST',body:JSON.stringify({author:noteAuthor,content:noteContent})});
      setNoteContent('');
      setTicketNotes(await request<TicketNote[]>('/api/tickets/'+selectedTicketId+'/notes'));
    }catch(e){setNoteError('Erro ao registrar anotação: '+String(e))}
    finally{setNoteBusy(false)}
  }
  async function addTechnician(e:FormEvent){
    e.preventDefault();setBusy(true);setError('');
    try{await request('/api/technicians',{method:'POST',body:JSON.stringify({name:technicianName,email:technicianEmail||null,specialty:technicianSpecialty||null})});setTechnicianName('');setTechnicianEmail('');setTechnicianSpecialty('');await refresh();}
    catch(e){setError(String(e))}finally{setBusy(false)}
  }
  async function assignTechnician(ticketId:number,technicianId:string){
    if(!technicianId)return;
    setError('');
    try{await request('/api/tickets/'+ticketId+'/assignment',{method:'PUT',body:JSON.stringify({technician_id:Number(technicianId)})});setAssignments(await request<Assignment[]>('/api/tickets/assignments'));if(selectedTicketId===ticketId)setTicketEvents(await request<TicketEvent[]>('/api/tickets/'+ticketId+'/events'));}
    catch(e){setError(String(e))}
  }
  async function refreshUsers(){
    if(currentRole!=='admin')return;
    setUsers(await request<CRMUser[]>('/api/users'));
  }
  async function addUser(e:FormEvent){
    e.preventDefault();setUserMessage('');
    try{
      await request('/api/users',{method:'POST',body:JSON.stringify({username:newUsername,password:newPassword,role:newRole})});
      setNewUsername('');setNewPassword('');await refreshUsers();setUserMessage('Usuário cadastrado.');
    }catch(err){setUserMessage('Não foi possível cadastrar: '+String(err))}
  }
  async function changeUser(id:number,changes:{role?:string;active?:boolean}){
    setUserMessage('');
    try{await request('/api/users/'+id,{method:'PATCH',body:JSON.stringify(changes)});await refreshUsers();setUserMessage('Conta atualizada.');}
    catch(err){setUserMessage('Não foi possível atualizar: '+String(err))}
  }
  async function loadAnalytics(){
    if(analyticsStart&&analyticsEnd&&analyticsStart>analyticsEnd){setAnalyticsError('Data inicial maior que a final.');return}
    try{
      const params=new URLSearchParams();
      if(analyticsClient)params.set('client_id',analyticsClient);
      if(analyticsStart)params.set('start_date',analyticsStart);
      if(analyticsEnd)params.set('end_date',analyticsEnd);
      const result=await request<Analytics>('/api/dashboard/analytics'+(params.size?'?'+params.toString():''));
      setAnalytics(result);setAnalyticsError('');
    }catch(e){setAnalyticsError('Indicadores indisponíveis: '+String(e));setAnalytics(null)}
  }
  useEffect(()=>{if(authenticated)loadAnalytics()},[authenticated,analyticsClient,analyticsStart,analyticsEnd]);
  async function refresh() {
    const [c, t, o, a, items, movements] = await Promise.all([request<Client[]>('/api/clients'), request<Ticket[]>('/api/tickets'), request<WorkOrder[]>('/api/work-orders'), request<Asset[]>('/api/assets'), request<StockItem[]>('/api/stock/items'), request<StockMovement[]>('/api/stock/movements')]);
    setClients(c); setTickets(t); setOrders(o); setAssets(a); setStockItems(items); setStockMovements(movements);
    const [techs,assigned] = await Promise.all([request<Technician[]>('/api/technicians'),request<Assignment[]>('/api/tickets/assignments')]);
    setTechnicians(techs);setAssignments(assigned);await loadAnalytics();
  }
  useEffect(() => {
    document.documentElement.dataset.theme = darkMode ? 'dark' : 'light';
    window.localStorage.setItem('aguia-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);
  useEffect(() => {
    // O token fica somente em memória: recarregar exige novo login.
    setAuthReady(true);
  }, []);
  async function submitAuth(e:FormEvent){
    e.preventDefault();setAuthBusy(true);setAuthError('');
    try {
      if(setupMode){
        await request('/api/auth/bootstrap',{method:'POST',body:JSON.stringify({username:authUser,password:authPassword})});
        setSetupMode(false);
      }
      const response = await request<{access_token:string}>('/api/auth/login',{method:'POST',body:JSON.stringify({username:authUser,password:authPassword})});
      accessToken=response.access_token;
      const identity=await request<{role:string}>('/api/auth/me');
      setCurrentRole(identity.role);
      await refresh();
      setAuthenticated(true);setAuthPassword('');
    }catch(err){accessToken=null;setAuthError('Não foi possível autenticar. Verifique as credenciais e a conexão com a API.');}
    finally{setAuthBusy(false);}
  }
  async function signOut(){
    try{await request('/api/auth/logout',{method:'POST'});}catch{/* Sessão local será encerrada mesmo se a API estiver indisponível. */}
    accessToken=null;setAuthenticated(false);setCurrentRole('');setUsers([]);setClients([]);setTickets([]);setOrders([]);setAssets([]);setStockItems([]);setStockMovements([]);setTechnicians([]);setAssignments([]);setSelectedTicketId(null);setSection('Visão geral');
  }
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
  async function setStatus(id:number,status:string){setError('');try{await request('/api/tickets/'+id,{method:'PATCH',body:JSON.stringify({status})});await refresh();if(selectedTicketId===id)setTicketEvents(await request<TicketEvent[]>('/api/tickets/'+id+'/events'));}catch(e){setError(String(e));}}
  async function addOrder(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await request('/api/work-orders', { method: 'POST', body: JSON.stringify({ client_id: Number(orderClientId), ticket_id: orderTicketId ? Number(orderTicketId) : null, title: orderTitle, description: orderDescription, technician_id: orderTechnicianId ? Number(orderTechnicianId) : null, scheduled_at: orderScheduledAt ? new Date(orderScheduledAt).toISOString() : null, estimated_duration_hours: Number(orderDuration) }) });
      setOrderTitle(''); setOrderDescription(''); setOrderTicketId(''); setOrderTechnicianId(''); setOrderScheduledAt(''); setOrderDuration('2'); await refresh();
    } catch (e) { setError(String(e)); } finally { setBusy(false); }
  }
  async function downloadOrderPdf(id: number) {
    try {
      const response = await fetch(API + '/api/work-orders/' + id + '/pdf', { headers: accessToken ? { Authorization: 'Bearer ' + accessToken } : {} });
      if (!response.ok) throw new Error((await response.text()).slice(0, 250));
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a'); link.href = url; link.download = `ordem_servico_${String(id).padStart(5, '0')}.pdf`; link.click(); URL.revokeObjectURL(url);
    } catch (e) { setError(String(e)); }
  }
  async function downloadSlaPdf() {
    try {
      const response = await fetch(API + '/api/dashboard/report/pdf', { headers: accessToken ? { Authorization: 'Bearer ' + accessToken } : {} });
      if (!response.ok) throw new Error((await response.text()).slice(0, 250));
      const url = URL.createObjectURL(await response.blob()); const link = document.createElement('a'); link.href = url; link.download = 'relatorio_operacional_sla.pdf'; link.click(); URL.revokeObjectURL(url);
    } catch (e) { setError(String(e)); }
  }

  async function submitInspection(e: FormEvent) {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await request('/api/integrations/checklist-import', {method:'POST', body:JSON.stringify({client_id:Number(inspectionClient), checklist_name:inspectionName, unit_name:inspectionUnit, inspector_name:inspectorName, auto_create_work_orders:inspectionCreateOrder, technician_id:inspectionTechnician?Number(inspectionTechnician):null, issues:[{sector:inspectionSector,item:inspectionItem,observation:inspectionObservation,priority:inspectionPriority,photo_url:inspectionPhoto||null}]})});
      setInspectionItem(''); setInspectionObservation(''); setInspectionPhoto(''); await refresh(); setError('Vistoria importada: chamado criado com sucesso.');
    } catch(e) { setError(String(e)); } finally { setBusy(false); }
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
  if(!authReady)return null;
  if(!authenticated)return <main className="auth-screen"><section className="auth-card"><div className="auth-brand"><div className="logo-mark">A</div><div><strong>Águia Gestão</strong><small>CRM · Ambiente de desenvolvimento</small></div></div><h1>{setupMode?'Configuração inicial':'Acesso ao sistema'}</h1><p>{setupMode?'Crie a primeira conta administradora. Esta operação só é permitida uma vez.':'Entre com suas credenciais para acessar os módulos de suporte e infraestrutura.'}</p><form onSubmit={submitAuth}><label>Usuário<input autoComplete="username" required minLength={3} value={authUser} onChange={e=>setAuthUser(e.target.value)}/></label><label>Senha<input type="password" autoComplete={setupMode?'new-password':'current-password'} required minLength={setupMode?12:1} value={authPassword} onChange={e=>setAuthPassword(e.target.value)}/></label>{authError&&<p role="alert" className="error">{authError}</p>}<button className="primary" disabled={authBusy}>{authBusy?'Aguarde...':setupMode?'Criar administrador e entrar':'Entrar'}</button></form><button type="button" className="text-button" onClick={()=>{setSetupMode(v=>!v);setAuthError('')}}>{setupMode?'Voltar ao login':'Primeira instalação? Criar administrador'}</button><small>Não use dados reais antes da homologação de segurança.</small></section></main>;
  return <div className="shell">
    <aside className="sidebar">
      <div className="logo"><div className="logo-mark">A</div><div><strong>Águia Gestão</strong><small>CRM Workspace</small></div></div>
      <div className="nav-heading">WORKSPACE</div>
      <nav aria-label="Navegação principal">{navigation.filter(item=>item.label!=='Usuários'||currentRole==='admin').map(item=><button key={item.label} className={'nav-item '+(section===item.label?'active':'')} onClick={()=>{setSection(item.label);setSearch('');if(item.label==='Usuários')refreshUsers().catch(e=>setUserMessage(String(e)));}}><span className="nav-icon">{item.icon}</span>{item.label}</button>)}</nav>
      <div className="sidebar-bottom"><span className="status-dot"/> Ambiente de desenvolvimento</div>
    </aside>
    <div className="workspace">
      <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> {section}</div><div className="topbar-actions"><button type="button" className="theme-toggle" aria-label={darkMode?'Ativar modo claro':'Ativar modo escuro'} aria-pressed={darkMode} onClick={()=>setDarkMode(v=>!v)} title={darkMode?'Modo claro':'Modo escuro'}>{darkMode?'☀':'☾'} <span>{darkMode?'Claro':'Escuro'}</span></button><button type="button" className="text-button" onClick={signOut}>Sair</button><div className="avatar" aria-label="Águia Gestão">AG</div></div></header>
      <main className="content">
        <div className="heading"><div><p className="eyebrow">ÁGUIA GESTÃO CRM</p><h1>{section==='Visão geral'?'Bom trabalho começa com clareza.':section}</h1><p className="subtitle">{section==='Visão geral'?'Sua operação de suporte e infraestrutura em um só lugar.':'Gerencie sua operação com simplicidade e precisão.'}</p></div><span className="env-pill"><span className="status-dot"/> Desenvolvimento</span></div>
        {section!=='Visão geral'&&section!=='Usuários'&&<div className="searchbar"><span aria-hidden="true">⌕</span><input type="search" aria-label="Buscar registros" placeholder={'Buscar em '+section.toLocaleLowerCase('pt-BR')+'...'} value={search} onChange={e=>setSearch(e.target.value)}/>{search&&<button type="button" onClick={()=>setSearch('')} aria-label="Limpar busca">✕</button>}</div>}
        {error&&<div role="alert" className="error">{error}</div>}
        {section==='Visão geral'&&<>
          <div className="stats">
            <article className="stat-card"><span>Clientes cadastrados</span><strong>{clients.length}</strong><small>Base de atendimento</small></article>
            <article className="stat-card"><span>Chamados ativos</span><strong>{openTickets.length}</strong><small>{criticalTickets.length} com prioridade alta/crítica</small></article>
            <article className="stat-card"><span>OS pendentes / execução</span><strong>{pendingOrders.length}</strong><small>{orders.length} ordens cadastradas</small></article>
            <article className="stat-card"><span>Estoque em alerta</span><strong>{lowStock.length}</strong><small>Itens no mínimo ou abaixo</small></article>
          </div>
          <section className="panel" style={{marginBottom:20,padding:20}}>
            <div className="panel-head"><div><h2>Indicadores conectados à API</h2><p>Dados persistidos no servidor · período pela data de criação (UTC)</p></div><button type="button" className="text-button" onClick={loadAnalytics}>Atualizar</button></div>
            <div style={{display:'flex',gap:12,flexWrap:'wrap',marginBottom:16}}>
              <label>Cliente <select aria-label="Filtrar cliente" value={analyticsClient} onChange={e=>setAnalyticsClient(e.target.value)}><option value="">Todos</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
              <label>De <input aria-label="Data inicial" type="date" value={analyticsStart} onChange={e=>setAnalyticsStart(e.target.value)}/></label>
              <label>Até <input aria-label="Data final" type="date" value={analyticsEnd} onChange={e=>setAnalyticsEnd(e.target.value)}/></label>
              <button type="button" className="text-button" onClick={()=>{setAnalyticsClient('');setAnalyticsStart('');setAnalyticsEnd('')}}>Limpar filtros</button>
            </div>
            {analyticsError&&<p role="alert">{analyticsError}</p>}
            {analytics&&<>
              <div className="stats">
                <article className="stat-card"><span>Chamados no período</span><strong>{analytics.tickets.total}</strong><small>{analytics.tickets.active} ativos</small></article>
                <article className="stat-card"><span>Urgentes ativos</span><strong>{analytics.tickets.urgent_active}</strong><small>Crítica ou alta</small></article>
                <article className="stat-card"><span>OS em andamento / pendentes</span><strong>{analytics.work_orders.pending_or_running}</strong><small>Na seleção</small></article>
                <article className="stat-card"><span>Ativos cadastrados</span><strong>{analytics.assets.total}</strong><small>Na seleção</small></article>
              </div>
              <h3>Ranking dos 5 técnicos com mais chamados concluídos</h3>
              <p>Considera o técnico atualmente atribuído, não o autor auditado da conclusão.</p>
              {analytics.top_technician.ranking.length?
                analytics.top_technician.ranking.slice(0,5).map((tech,i)=><div key={tech.id} style={{display:'flex',justifyContent:'space-between',padding:'10px 0',borderBottom:'1px solid var(--line, #dce5e3)'}}><strong>{i+1}º · {tech.name}</strong><span>{tech.completed_tickets} concluídos</span></div>):
                <p>Nenhum técnico com conclusão atribuída nos filtros selecionados.</p>}
              <p>{analytics.top_technician.completed_without_assignment} conclusão(ões) sem técnico vinculado.</p>
            </>}
          </section>
          <div className="dashboard-quick-actions" aria-label="Acesso rápido aos módulos">
            <button type="button" onClick={downloadSlaPdf}>Relatório operacional PDF <span aria-hidden="true">↓</span></button>
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
          <section className="panel dashboard-recent"><div className="panel-head"><div><h2>Chamados recentes</h2><p>Acompanhe os últimos registros da operação.</p></div><button className="text-button" onClick={()=>setSection('Chamados')}>Ver todos →</button></div><TicketList tickets={tickets.slice(0,5)} clients={clients} setStatus={setStatus} onSelect={setSelectedTicketId}/></section>
        </>}
        {selectedTicket&&<div className="detail-overlay" role="presentation" onMouseDown={e=>{if(e.target===e.currentTarget)setSelectedTicketId(null)}}><section className="detail-dialog" role="dialog" aria-modal="true" aria-labelledby="ticket-detail-title"><div className="detail-header"><div><p className="eyebrow">CHAMADO # {selectedTicket.id}</p><h2 id="ticket-detail-title">{selectedTicket.title}</h2></div><button type="button" className="detail-close" aria-label="Fechar detalhes" onClick={()=>setSelectedTicketId(null)}>✕</button></div><div className="ticket-badges"><span className={'priority-badge priority-'+selectedTicket.priority}>{priorityNames[selectedTicket.priority]||selectedTicket.priority}</span><span className={'status-badge status-'+selectedTicket.status}>{statusNames[selectedTicket.status]||selectedTicket.status}</span></div><div className="detail-section"><span>Cliente</span><strong>{clients.find(c=>c.id===selectedTicket.client_id)?.name||'Cliente não localizado'}</strong></div><div className="detail-section"><label htmlFor="ticket-technician">Técnico responsável</label><select id="ticket-technician" value={assignedTechnician(selectedTicket.id)||''} onChange={e=>assignTechnician(selectedTicket.id,e.target.value)}><option value="">Não atribuído</option>{technicians.filter(t=>t.active).map(t=><option value={t.id} key={t.id}>{t.name}{t.specialty?' · '+t.specialty:''}</option>)}</select></div><div className="detail-section"><span>Descrição do atendimento</span><p>{selectedTicket.description||'Nenhuma descrição registrada.'}</p></div><div className="detail-section"><label htmlFor="detail-ticket-status">Atualizar status</label><select id="detail-ticket-status" value={selectedTicket.status} onChange={e=>setStatus(selectedTicket.id,e.target.value)}><option value="aberto">Aberto</option><option value="em_andamento">Em andamento</option><option value="resolvido">Resolvido</option><option value="fechado">Fechado</option></select></div><div className="detail-section"><span>Alterações de status</span><div className="event-list">{ticketEvents.length?ticketEvents.map(ev=><article className="event-entry" key={ev.id}><span className="event-dot" aria-hidden="true"/><div><strong>{ev.event_type==='assignment'?'Responsável: '+(technicians.find(t=>t.id===Number(ev.previous_value))?.name||'Não atribuído')+' → '+(technicians.find(t=>t.id===Number(ev.new_value))?.name||'Técnico #'+ev.new_value):(statusNames[ev.previous_value||'']||'Status inicial')+' → '+(statusNames[ev.new_value]||ev.new_value)}</strong><time dateTime={ev.created_at}>{new Date(ev.created_at).toLocaleString('pt-BR')}</time></div></article>):<p className="empty">Nenhuma alteração de status registrada.</p>}</div></div><div className="detail-section"><span>Histórico técnico</span>{noteError&&<p role="alert" className="note-error">{noteError}</p>}<form className="note-form" onSubmit={addTicketNote}><label>Responsável<input required minLength={2} maxLength={100} value={noteAuthor} onChange={e=>setNoteAuthor(e.target.value)}/></label><label>Registro do atendimento<textarea required minLength={3} maxLength={4000} rows={3} placeholder="Descreva os testes, ações realizadas e próximos passos..." value={noteContent} onChange={e=>setNoteContent(e.target.value)}/></label><button className="primary" disabled={noteBusy}>{noteBusy?'Salvando...':'Adicionar anotação'}</button></form><div className="note-timeline">{ticketNotes.length?ticketNotes.map(note=><article className="note-entry" key={note.id}><div><strong>{note.author}</strong><time dateTime={note.created_at}>{new Date(note.created_at).toLocaleString('pt-BR')}</time></div><p>{note.content}</p></article>):<p className="empty">Nenhuma anotação registrada.</p>}</div></div><button type="button" className="primary" onClick={()=>setSelectedTicketId(null)}>Concluir visualização</button></section></div>}
        {section==='Usuários'&&currentRole==='admin'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Novo usuário</h2></div><form onSubmit={addUser}><label>Usuário<input required minLength={3} maxLength={80} pattern="[a-zA-Z0-9._-]+" value={newUsername} onChange={e=>setNewUsername(e.target.value)} autoComplete="off"/></label><label>Senha temporária<input type="password" required minLength={12} maxLength={256} value={newPassword} onChange={e=>setNewPassword(e.target.value)} autoComplete="new-password"/></label><label>Perfil<select value={newRole} onChange={e=>setNewRole(e.target.value)}><option value="technician">Técnico</option><option value="supervisor">Supervisor</option><option value="admin">Administrador</option></select></label><button className="primary" type="submit">Cadastrar usuário</button></form>{userMessage&&<p role="status">{userMessage}</p>}</section><section className="panel"><div className="panel-head"><h2>Contas cadastradas</h2><button type="button" className="text-button" onClick={()=>refreshUsers().catch(e=>setUserMessage(String(e)))}>Atualizar</button></div>{users.map(u=><div className="ticket-row" key={u.id}><div className="ticket-info"><b>{u.username}</b><small>{u.active?'Ativo':'Inativo'} · #{u.id}</small></div><select aria-label={'Perfil de '+u.username} value={u.role} onChange={e=>changeUser(u.id,{role:e.target.value})}><option value="technician">Técnico</option><option value="supervisor">Supervisor</option><option value="admin">Administrador</option></select><button type="button" className="text-button" onClick={()=>changeUser(u.id,{active:!u.active})}>{u.active?'Desativar':'Ativar'}</button></div>)}{users.length===0&&<p className="empty">Clique em Atualizar para consultar as contas.</p>}</section></div>}
        {section==='Equipe técnica'&&<div className="queue-summary"><article><span>Sem responsável</span><strong>{unassignedTickets.length}</strong><button type="button" onClick={()=>{setSection('Chamados');setTechnicianFilter('sem_responsavel');setQueueFilter('ativos')}}>Ver fila →</button></article><article><span>Em atendimento</span><strong>{openTickets.filter(t=>assignedTechnician(t.id)).length}</strong><button type="button" onClick={()=>{setSection('Chamados');setTechnicianFilter('todos');setQueueFilter('ativos')}}>Ver chamados →</button></article><article><span>Técnicos cadastrados</span><strong>{technicians.length}</strong><small>Equipe operacional</small></article></div>}
        {section==='Equipe técnica'&&<section className="panel workload-panel"><div className="panel-head"><div><h2>Carga de trabalho por técnico</h2><p>Indicadores calculados a partir dos chamados atribuídos.</p></div></div><div className="workload-table"><div className="workload-head"><span>Profissional</span><span>Ativos</span><span>Urgentes</span><span>Resolvidos</span></div>{workload.length?workload.map(w=><button type="button" className="workload-row" key={w.technician.id} onClick={()=>{setSection('Chamados');setTechnicianFilter(String(w.technician.id));setQueueFilter('todas');setSearch('')}}><strong>{w.technician.name}</strong><span>{w.active}</span><span>{w.critical}</span><span>{w.resolved}</span></button>):<p className="empty">Cadastre um técnico para acompanhar os indicadores.</p>}</div></section>}
        {section==='Equipe técnica'&&<section className="panel technician-panel"><div className="panel-head"><div><h2>Equipe técnica</h2><p>Cadastre profissionais para atribuir os chamados.</p></div><span className="count">{technicians.length}</span></div><form className="technician-form" onSubmit={addTechnician}><label>Nome<input required minLength={2} maxLength={160} value={technicianName} onChange={e=>setTechnicianName(e.target.value)} placeholder="Nome do técnico"/></label><label>E-mail<input type="email" value={technicianEmail} onChange={e=>setTechnicianEmail(e.target.value)} placeholder="Opcional"/></label><label>Especialidade<input maxLength={100} value={technicianSpecialty} onChange={e=>setTechnicianSpecialty(e.target.value)} placeholder="Ex.: Redes / N2"/></label><button className="primary" disabled={busy}>Cadastrar técnico</button></form><div className="technician-list">{filteredTechnicians.map(t=><div className="technician-row" key={t.id}><span className="technician-avatar">{t.name.slice(0,1).toUpperCase()}</span><div><strong>{t.name}</strong><small>{t.specialty||'Sem especialidade definida'}</small></div><span className="count">{assignments.filter(a=>a.technician_id===t.id).length} chamados</span></div>)}</div></section>}
        {section==='Clientes'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Novo cliente</h2></div><form onSubmit={addClient}><label>Nome ou empresa<input required minLength={2} placeholder="Ex.: Unidade Centro" value={name} onChange={e=>setName(e.target.value)}/></label><label>E-mail<input type="email" placeholder="contato@empresa.com" value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Telefone<input placeholder="(11) 99999-9999" value={phone} onChange={e=>setPhone(e.target.value)}/></label><button className="primary" disabled={busy}>Cadastrar cliente</button></form></section><section className="panel"><div className="panel-head"><h2>Clientes cadastrados</h2><span className="count">{clients.length}</span></div>{filteredClients.length?filteredClients.map(c=><div className="list-row" key={c.id}><div className="person-icon">{c.name.slice(0,1).toUpperCase()}</div><div><b>{c.name}</b><small>{c.email||c.phone||'Sem contato informado'}</small></div></div>):<p className="empty">Nenhum cliente cadastrado.</p>}</section></div>}
        {section==='Vistorias'&&<div className="two-col"><section className="panel"><div className="panel-head"><div><h2>Registrar não conformidade</h2><p>Transforme o levantamento da unidade em chamado e, se necessário, ordem de serviço.</p></div></div><form onSubmit={submitInspection}><label>Unidade / cliente<select required value={inspectionClient} onChange={e=>setInspectionClient(e.target.value)}><option value="">Selecione a unidade</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Nome da vistoria<input required minLength={2} maxLength={160} value={inspectionName} onChange={e=>setInspectionName(e.target.value)}/></label><label>Unidade visitada<input required minLength={2} maxLength={160} value={inspectionUnit} onChange={e=>setInspectionUnit(e.target.value)} placeholder="Ex.: Paulista"/></label><label>Responsável pela vistoria<input required minLength={2} maxLength={120} value={inspectorName} onChange={e=>setInspectorName(e.target.value)} placeholder="Nome do inspetor"/></label><label>Setor<select value={inspectionSector} onChange={e=>setInspectionSector(e.target.value)}>{['Facial SPA','Catracas','Balcão','Rack','Câmeras','Som','Sala de ginástica','Sala de bike','TVs','Antenas e Wi-Fi','Ar-condicionado','Iluminação'].map(v=><option key={v}>{v}</option>)}</select></label><label>Item / demanda<input required minLength={1} maxLength={180} value={inspectionItem} onChange={e=>setInspectionItem(e.target.value)} placeholder="Ex.: leitor sem resposta"/></label><label>Observação<textarea maxLength={4000} value={inspectionObservation} onChange={e=>setInspectionObservation(e.target.value)} placeholder="Descreva o que precisa ser executado"/></label><label>Link da foto/evidência<input type="url" value={inspectionPhoto} onChange={e=>setInspectionPhoto(e.target.value)} placeholder="https://..."/></label><label>Prioridade<select value={inspectionPriority} onChange={e=>setInspectionPriority(e.target.value)}><option value="baixa">Baixa</option><option value="media">Média</option><option value="alta">Alta</option><option value="critica">Crítica</option></select></label><label>Técnico responsável (opcional)<select value={inspectionTechnician} onChange={e=>setInspectionTechnician(e.target.value)}><option value="">A definir</option>{technicians.filter(t=>t.active).map(t=><option key={t.id} value={t.id}>{t.name}</option>)}</select></label><label className="checkbox-label"><input type="checkbox" checked={inspectionCreateOrder} onChange={e=>setInspectionCreateOrder(e.target.checked)}/> Criar ordem de serviço automaticamente</label><button className="primary" disabled={busy||!clients.length}>Criar chamado da vistoria</button></form></section><section className="panel"><div className="panel-head"><div><h2>Chamados originados de vistorias</h2><p>Os itens importados aparecem na fila de chamados e podem receber OS.</p></div></div>{tickets.filter(t=>t.description.includes('Vistoria:')).slice(0,30).map(t=><div className="ticket-row" key={t.id}><div className="ticket-icon">✓</div><div className="ticket-info"><b>#{t.id} · {t.title}</b><small>{clients.find(c=>c.id===t.client_id)?.name||'Unidade'} · {t.priority} · {t.status}</small></div><button type="button" className="text-button" onClick={()=>{setSection('Chamados');setSelectedTicketId(t.id)}}>Abrir →</button></div>)}{tickets.filter(t=>t.description.includes('Vistoria:')).length===0&&<p className="empty">Ainda não há chamados criados por vistorias.</p>}</section></div>}
        {section==='Chamados'&&<div className="ticket-filterbar"><label>Responsável<select aria-label="Filtrar chamados por responsável" value={technicianFilter} onChange={e=>setTechnicianFilter(e.target.value)}><option value="todos">Todos os técnicos</option><option value="sem_responsavel">Sem responsável</option>{technicians.map(t=><option key={t.id} value={t.id}>{t.name}</option>)}</select></label><label>Fila<select aria-label="Filtrar fila de atendimento" value={queueFilter} onChange={e=>setQueueFilter(e.target.value)}><option value="todas">Todas as filas</option><option value="nao_atribuidos">Não atribuídos</option><option value="ativos">Ativos</option><option value="urgentes">Urgentes</option><option value="resolvido">Resolvidos</option><option value="fechado">Fechados</option></select></label><label>Filtrar chamados<select aria-label="Filtrar chamados" value={ticketFilter} onChange={e=>setTicketFilter(e.target.value)}><option value="todos">Todos</option><option value="aberto">Abertos</option><option value="em_andamento">Em andamento</option><option value="resolvido">Resolvidos</option><option value="fechado">Fechados</option><option value="alta">Prioridade alta</option><option value="critica">Prioridade crítica</option></select></label><span className="count">{filteredTickets.length} de {tickets.length}</span></div>}
        {section==='Chamados'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Abrir chamado</h2></div><form onSubmit={addTicket}><label>Cliente<select required value={clientId} onChange={e=>setClientId(e.target.value)}><option value="">Selecione um cliente</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Assunto<input required minLength={3} placeholder="Ex.: Falha de conectividade" value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Descrição<textarea placeholder="Descreva o problema" value={description} onChange={e=>setDescription(e.target.value)}/></label><label>Prioridade<select value={priority} onChange={e=>setPriority(e.target.value)}><option value="baixa">Baixa</option><option value="media">Média</option><option value="alta">Alta</option><option value="critica">Crítica</option></select></label><button className="primary" disabled={busy||!clients.length}>Abrir chamado</button></form></section><section className="panel"><div className="panel-head"><h2>Chamados</h2><span className="count">{tickets.length}</span></div><TicketList tickets={filteredTickets} clients={clients} setStatus={setStatus} onSelect={setSelectedTicketId}/></section></div>}
        {section==='Ordens de serviço'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Nova ordem de serviço</h2></div><form onSubmit={addOrder}><label>Cliente<select required value={orderClientId} onChange={e=>{setOrderClientId(e.target.value);setOrderTicketId('');}}><option value="">Selecione um cliente</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Chamado relacionado (opcional)<select value={orderTicketId} onChange={e=>setOrderTicketId(e.target.value)}><option value="">Sem chamado relacionado</option>{tickets.filter(t=>t.client_id===Number(orderClientId)).map(t=><option key={t.id} value={t.id}>#{t.id} · {t.title}</option>)}</select></label><label>Serviço<input required minLength={3} placeholder="Ex.: Instalação de Access Point" value={orderTitle} onChange={e=>setOrderTitle(e.target.value)}/></label><label>Descrição<textarea placeholder="Descreva as atividades previstas" value={orderDescription} onChange={e=>setOrderDescription(e.target.value)}/></label><label>Técnico responsável<select value={orderTechnicianId} onChange={e=>setOrderTechnicianId(e.target.value)}><option value="">A definir</option>{technicians.filter(t=>t.active).map(t=><option key={t.id} value={t.id}>{t.name}</option>)}</select></label><label>Data e horário previsto<input type="datetime-local" value={orderScheduledAt} onChange={e=>setOrderScheduledAt(e.target.value)}/></label><label>Duração estimada (horas)<input type="number" min="0.25" max="24" step="0.25" value={orderDuration} onChange={e=>setOrderDuration(e.target.value)}/></label><button className="primary" disabled={busy||!clients.length}>Criar ordem de serviço</button></form></section><section className="panel"><div className="panel-head"><h2>Ordens de serviço</h2><span className="count">{orders.length}</span></div>{filteredOrders.length?filteredOrders.map(o=><div className="ticket-row" key={o.id}><div className="ticket-icon">◇</div><div className="ticket-info"><b>OS #{o.id} · {o.title}</b><small>{clients.find(c=>c.id===o.client_id)?.name||'Cliente'}{o.ticket_id?' · Chamado #'+o.ticket_id:''}</small></div><div style={{display:'flex',gap:8,alignItems:'center'}}><button type="button" className="text-button" title="Baixar Ordem de Serviço em PDF para assinatura" onClick={()=>downloadOrderPdf(o.id)}>📄 Imprimir OS (PDF)</button><select aria-label={'Status da OS '+o.id} value={o.status} onChange={e=>setOrderStatus(o.id,e.target.value)}><option value="pendente">Pendente</option><option value="em_execucao">Em execução</option><option value="concluida">Concluída</option><option value="cancelada">Cancelada</option></select></div></div>):<p className="empty">Nenhuma ordem de serviço cadastrada.</p>}</section></div>}
        {section==='Agenda'&&<section className="panel"><div className="panel-head"><div><h2>Agenda da equipe técnica</h2><p>Visitas agendadas e carga prevista por profissional.</p></div><span className="count">{orders.filter(o=>o.scheduled_at&&o.status!=='cancelada'&&o.status!=='concluida').length} agendadas</span></div>{orders.filter(o=>o.scheduled_at).sort((a,b)=>new Date(a.scheduled_at!).getTime()-new Date(b.scheduled_at!).getTime()).length?orders.filter(o=>o.scheduled_at).sort((a,b)=>new Date(a.scheduled_at!).getTime()-new Date(b.scheduled_at!).getTime()).map(o=><div className="ticket-row" key={o.id}><div className="ticket-icon">◷</div><div className="ticket-info"><b>{new Date(o.scheduled_at!).toLocaleString('pt-BR')} · {o.title}</b><small>{clients.find(c=>c.id===o.client_id)?.name||'Cliente'} · {technicians.find(t=>t.id===o.technician_id)?.name||'Técnico a definir'} · {o.estimated_duration_hours}h · {o.status.replace('_',' ')}</small></div><button type="button" className="text-button" onClick={()=>setSection('Ordens de serviço')}>Ver OS →</button></div>):<p className="empty">Nenhuma visita agendada. Defina técnico, data e duração ao criar uma ordem de serviço.</p>}</section>}
        {section==='Ativos'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Cadastrar equipamento</h2></div><form onSubmit={addAsset}><label>Cliente<select required value={assetClient} onChange={e=>setAssetClient(e.target.value)}><option value="">Selecione um cliente</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Nome do equipamento<input required minLength={2} placeholder="Ex.: Switch 24 portas" value={assetName} onChange={e=>setAssetName(e.target.value)}/></label><label>Categoria<select value={assetCategory} onChange={e=>setAssetCategory(e.target.value)}>{[['switch','Switch'],['roteador','Roteador'],['access_point','Access Point'],['camera','Câmera'],['dvr_nvr','DVR / NVR'],['servidor','Servidor'],['outro','Outro']].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><label>Localização<input placeholder="Ex.: Rack principal" value={assetLocation} onChange={e=>setAssetLocation(e.target.value)}/></label><label>Endereço IP<input placeholder="Ex.: 192.168.1.10" value={assetIp} onChange={e=>setAssetIp(e.target.value)}/></label><label>Número de série<input placeholder="Opcional" value={assetSerial} onChange={e=>setAssetSerial(e.target.value)}/></label><button className="primary" disabled={busy||!clients.length}>Cadastrar equipamento</button></form></section><section className="panel"><div className="panel-head"><h2>Inventário de ativos</h2><span className="count">{assets.length}</span></div>{filteredAssets.length?filteredAssets.map(a=><div className="ticket-row" key={a.id}><div className="ticket-icon">▦</div><div className="ticket-info"><b>{a.name}</b><small>{clients.find(c=>c.id===a.client_id)?.name||'Cliente'} · {a.category.replace('_',' / ')} · {a.location||'Sem local'}{a.ip_address?' · '+a.ip_address:''}</small></div><select aria-label={'Status do ativo '+a.id} value={a.status} onChange={e=>setAssetStatus(a.id,e.target.value)}><option value="ativo">Ativo</option><option value="manutencao">Manutenção</option><option value="inativo">Inativo</option></select></div>):<p className="empty">Nenhum equipamento cadastrado.</p>}</section></div>}
        {section==='Estoque'&&<div className="two-col"><section className="panel"><div className="panel-head"><h2>Novo material</h2></div><form onSubmit={addStockItem}><label>Material<input required minLength={2} placeholder="Ex.: Cabo de rede CAT6" value={stockName} onChange={e=>setStockName(e.target.value)}/></label><label>Unidade<select value={stockUnit} onChange={e=>setStockUnit(e.target.value)}><option value="un">Unidade</option><option value="m">Metro</option><option value="cx">Caixa</option><option value="pct">Pacote</option></select></label><label>Estoque mínimo<input type="number" min="0" required value={stockMinimum} onChange={e=>setStockMinimum(e.target.value)}/></label><button className="primary" disabled={busy}>Cadastrar material</button></form><div className="panel-head" style={{marginTop:30}}><h2>Movimentar estoque</h2></div><form onSubmit={addStockMovement}><label>Material<select required value={movementItem} onChange={e=>setMovementItem(e.target.value)}><option value="">Selecione o material</option>{stockItems.map(i=><option key={i.id} value={i.id}>{i.name}</option>)}</select></label><label>Movimento<select value={movementType} onChange={e=>setMovementType(e.target.value)}><option value="entrada">Entrada</option><option value="saida">Saída</option></select></label><label>Quantidade<input type="number" min="1" step="1" required value={movementQuantity} onChange={e=>setMovementQuantity(e.target.value)}/></label><label>Ordem de serviço (opcional)<select value={movementOrder} onChange={e=>setMovementOrder(e.target.value)}><option value="">Sem OS vinculada</option>{orders.map(o=><option key={o.id} value={o.id}>OS #{o.id} · {o.title}</option>)}</select></label><button className="primary" disabled={busy||!stockItems.length}>Registrar movimento</button></form></section><section className="panel"><div className="panel-head"><h2>Materiais em estoque</h2><span className="count">{stockItems.length}</span></div>{filteredStock.length?filteredStock.map(i=><div className="ticket-row" key={i.id}><div className="ticket-icon">▥</div><div className="ticket-info"><b>{i.name}</b><small>Saldo: {i.quantity} {i.unit} · Mínimo: {i.min_quantity} {i.unit}{i.quantity<=i.min_quantity?' · Repor estoque':''}</small></div></div>):<p className="empty">Nenhum material cadastrado.</p>}<div className="panel-head" style={{marginTop:28}}><h2>Últimas movimentações</h2></div>{stockMovements.slice(0,10).map(m=><div className="ticket-row" key={m.id}><div className="ticket-info"><b>{m.type==='entrada'?'+':'−'}{m.quantity} · {stockItems.find(i=>i.id===m.item_id)?.name||'Material'}</b><small>{m.work_order_id?'OS #'+m.work_order_id:'Movimento avulso'}</small></div></div>)}</section></div>}
        <footer>Águia Gestão CRM · MVP de homologação · Não inserir dados reais sem autenticação.</footer>
      </main>
    </div>
  </div>;
}
const priorityNames: Record<string,string> = {baixa:'Baixa',media:'Média',alta:'Alta',critica:'Crítica'};
const statusNames: Record<string,string> = {aberto:'Aberto',em_andamento:'Em andamento',resolvido:'Resolvido',fechado:'Fechado'};
function TicketList({tickets,clients,setStatus,onSelect}:{tickets:Ticket[];clients:Client[];setStatus:(id:number,status:string)=>void;onSelect:(id:number)=>void}){
  return tickets.length?<div className="ticket-list">{tickets.map(t=><div className="ticket-row ticket-record" key={t.id}>
    <div className="ticket-icon" aria-hidden="true">▤</div>
    <div className="ticket-info">
      <button type="button" className="ticket-title-button" onClick={()=>onSelect(t.id)} aria-label={'Ver detalhes do chamado '+t.id}>{t.title}</button>
      <small>#{t.id} · {clients.find(c=>c.id===t.client_id)?.name||'Cliente'}</small>
      <div className="ticket-badges">
        <span className={'priority-badge priority-'+t.priority}>{priorityNames[t.priority]||t.priority}</span>
        <span className={'status-badge status-'+t.status}>{statusNames[t.status]||t.status}</span>
      </div>
    </div>
    <label className="ticket-status-field"><span>Atualizar status</span><select aria-label={'Status do chamado '+t.id} value={t.status} onChange={e=>setStatus(t.id,e.target.value)}><option value="aberto">Aberto</option><option value="em_andamento">Em andamento</option><option value="resolvido">Resolvido</option><option value="fechado">Fechado</option></select></label>
  </div>)}</div>:<p className="empty">Nenhum chamado encontrado para os filtros selecionados.</p>;
}

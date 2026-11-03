import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

clients = [{"id":1,"name":"Unidade Centro (Demo)","email":"contato@example.test","phone":"(11) 90000-0000"},{"id":2,"name":"Unidade Sul (Demo)","email":None,"phone":None}]
tickets = [{"id":1,"client_id":1,"title":"Wi-Fi instável no salão","description":"Exemplo","status":"em_andamento","priority":"alta"},{"id":2,"client_id":2,"title":"Câmera sem imagem","description":"Exemplo","status":"aberto","priority":"critica"}]
orders = [{"id":1,"client_id":1,"ticket_id":1,"title":"Instalação de access points","description":"Exemplo","status":"em_execucao"},{"id":2,"client_id":2,"ticket_id":None,"title":"Organização de rack","description":"Exemplo","status":"pendente"}]
assets = [{"id":1,"client_id":1,"name":"Switch 24 portas","category":"switch","serial_number":"DEMO001","ip_address":"192.0.2.10","location":"Rack principal","status":"ativo"},{"id":2,"client_id":2,"name":"Access Point Wi-Fi 6","category":"access_point","serial_number":None,"ip_address":"192.0.2.11","location":"Salão","status":"manutencao"}]
items = [{"id":1,"name":"Cabo CAT6","sku":None,"unit":"m","quantity":85,"min_quantity":30},{"id":2,"name":"Keystone RJ45","sku":None,"unit":"un","quantity":12,"min_quantity":20}]
technicians = [{"id":1,"name":"Técnico N1 (Demo)","email":"n1@example.test","specialty":"Service Desk","active":1},{"id":2,"name":"Técnico N2 (Demo)","email":"n2@example.test","specialty":"Redes e infraestrutura","active":1}]
assignments = [{"ticket_id":1,"technician_id":2,"assigned_at":"2026-11-03T10:00:00"}]
notes = [{"id":1,"ticket_id":1,"author":"Técnico N2","content":"Verificado cabeamento e conectividade.","created_at":"2026-11-03T10:30:00"}]
events = [{"id":1,"ticket_id":1,"event_type":"status","previous_value":"aberto","new_value":"em_andamento","created_at":"2026-11-03T10:15:00"}]
movements = [{"id":1,"item_id":1,"work_order_id":1,"type":"saida","quantity":15,"note":""}]
payload = {"/api/clients":clients,"/api/tickets":tickets,"/api/work-orders":orders,"/api/assets":assets,"/api/stock/items":items,"/api/stock/movements":movements,"/api/technicians":technicians,"/api/tickets/assignments":assignments,"/api/tickets/1/notes":notes,"/api/tickets/1/events":events}
pages = [("Visão geral","01-dashboard"),("Clientes","02-clientes"),("Chamados","03-chamados"),("Ordens de serviço","04-ordens-servico"),("Ativos","05-ativos"),("Estoque","06-estoque"),("Equipe técnica","07-equipe-tecnica")]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for device, viewport in [("desktop",{"width":1440,"height":1000}),("mobile",{"width":390,"height":844})]:
        page = browser.new_page(viewport=viewport, device_scale_factor=1, is_mobile=(device=="mobile"), has_touch=(device=="mobile"))
        def route_handler(route):
            path = route.request.url.split("/api/",1)[-1].split("?",1)[0]
            route.fulfill(status=200, content_type="application/json", body=json.dumps(payload.get("/api/"+path, [])))
        page.route("**/api/**", route_handler)
        page.goto(os.environ.get("FRONTEND_URL","http://127.0.0.1:5173"),wait_until="networkidle")
        page.evaluate("localStorage.setItem('aguia-theme','light')")
        page.reload(wait_until="networkidle")
        for label, filename in pages:
            page.get_by_role("navigation",name="Navegação principal").get_by_role("button",name=label).click()
            page.wait_for_timeout(250)
            page.screenshot(path=str(OUT / f"{filename}-{device}.png"),full_page=True,animations="disabled")
        page.get_by_role("navigation",name="Navegação principal").get_by_role("button",name="Chamados").click()
        page.get_by_role("button",name="Ver detalhes do chamado 1").click()
        page.screenshot(path=str(OUT / f"08-detalhes-chamado-{device}.png"),full_page=True,animations="disabled")
        page.get_by_role("button",name="Fechar detalhes").click()
        if device=="mobile":
            page.get_by_role("button",name="Ativar modo escuro").click()
            page.get_by_role("navigation",name="Navegação principal").get_by_role("button",name="Visão geral").click()
            page.screenshot(path=str(OUT / "09-dashboard-dark-mobile.png"),full_page=True,animations="disabled")
        page.close()
    browser.close()
print("Capturas geradas:",len(list(OUT.glob("*.png"))))

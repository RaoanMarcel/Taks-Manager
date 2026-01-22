import customtkinter as ctk
from tkinter import messagebox, filedialog
import time
import pandas as pd
import os
import json
from datetime import datetime, timedelta

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ProTaskApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Configurações Visuais ---
        self.title("PROTASK | Gestão Avançada")
        self.largura_normal = 1000
        self.altura_normal = 750
        self.largura_mini = 230 
        self.altura_mini = 100 # Aumentado levemente para acomodar info multi-task
        
        self.cor_fundo = "#1a1a1a"
        self.cor_card = "#2b2b2b"
        self.cor_card_ativo = "#1f2933"
        self.cor_borda_ativa = "#3B8ED0"
        self.cor_texto_secundario = "#a0a0a0"
        
        self.geometry(f"{self.largura_normal}x{self.altura_normal}")
        self.configure(fg_color=self.cor_fundo)
        
        # Estado
        self.modo_mini = False
        self.categorias = ["Organização", "Teste Automação", "Suporte Interno", "RMA", "Atendimento Cliente"]
        self.db_file = "database_tasks.json"
        self.tarefas = self.carregar_dados()
        
        # Variáveis de arraste
        self.x_mouse = 0
        self.y_mouse = 0

        # --- Containers ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.mini_container = ctk.CTkFrame(self, fg_color="#1c1c1c", border_width=2, border_color=self.cor_borda_ativa, corner_radius=15)

        self.setup_ui_completa()
        self.setup_ui_mini()
        
        self.main_container.pack(fill="both", expand=True)
        self.recarregar_lista_completa()
        self.atualizar_cronometro_visual()

    def carregar_dados(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f: 
                    dados = json.load(f)
                    for d in dados:
                        d['rodando'] = False # Sempre começa parado ao abrir o app
                        d['inicio_timer'] = None
                        if 'historico_acumulado' not in d: d['historico_acumulado'] = 0
                    return dados
            except: return []
        return []

    def salvar_dados(self):
        # Remove chaves temporárias de runtime antes de salvar
        dados_para_salvar = []
        for t in self.tarefas:
            copia = t.copy()
            if copia.get('rodando'):
                # Se fechar o app rodando, salva o tempo decorrido até agora
                decorrido = time.time() - copia['inicio_timer']
                copia['tempo_atual'] += decorrido
            
            copia.pop('rodando', None)
            copia.pop('inicio_timer', None)
            copia.pop('ui_widgets', None)
            dados_para_salvar.append(copia)
            
        with open(self.db_file, 'w', encoding='utf-8') as f: 
            json.dump(dados_para_salvar, f, indent=4)

    def setup_ui_completa(self):
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent", height=60)
        self.header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(self.header_frame, text="Minhas Demandas", font=("Segoe UI", 24, "bold"), text_color="white").pack(side="left")
        
        self.btn_mini = ctk.CTkButton(self.header_frame, text="↗ Modo Widget", width=120, height=35, corner_radius=18,
                                      fg_color="#222222", hover_color="#333333", border_width=1, border_color="#444444",
                                      command=self.alternar_modo_mini)
        self.btn_mini.pack(side="right")

        self.input_container = ctk.CTkFrame(self.main_container, fg_color=self.cor_card, corner_radius=15)
        self.input_container.pack(pady=10, padx=30, fill="x")

        self.input_tarefa = ctk.CTkEntry(self.input_container, placeholder_text="O que vamos fazer agora?", 
                                         height=50, border_width=0, fg_color="transparent", font=("Segoe UI", 16))
        self.input_tarefa.pack(side="left", padx=20, pady=10, expand=True, fill="x")
        self.input_tarefa.bind("<Return>", lambda e: self.adicionar_tarefa())

        self.menu_categoria = ctk.CTkOptionMenu(self.input_container, values=self.categorias, width=150, height=35, 
                                                fg_color="#333333", button_color="#444444")
        self.menu_categoria.pack(side="left", padx=10)
        self.menu_categoria.set("Organização")

        self.btn_add = ctk.CTkButton(self.input_container, text="+ NOVA TASK", command=self.adicionar_tarefa, 
                                     font=("Segoe UI", 13, "bold"), width=120, height=40, corner_radius=10)
        self.btn_add.pack(side="right", padx=20, pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.footer = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.footer.pack(pady=20, padx=30, fill="x")

        self.btn_export = ctk.CTkButton(self.footer, text="📊 Exportar Relatório Excel", fg_color="#2e7d32", 
                                        hover_color="#1b5e20", command=self.exportar_excel, height=45, corner_radius=10)
        self.btn_export.pack(fill="x")

    def setup_ui_mini(self):
        self.lbl_mini_nome = ctk.CTkLabel(self.mini_container, text="Multi-tarefas Ativas", 
                                          font=("Segoe UI", 10, "bold"), text_color=self.cor_borda_ativa)
        self.lbl_mini_nome.pack(pady=(5, 0), padx=10) 

        self.lbl_mini_tempo = ctk.CTkLabel(self.mini_container, text="00:00:00", font=("Consolas", 22, "bold"))
        self.lbl_mini_tempo.pack(pady=0)

        self.lbl_mini_count = ctk.CTkLabel(self.mini_container, text="0 tasks rodando", font=("Arial", 9), text_color="gray")
        self.lbl_mini_count.pack()

        for widget in [self.mini_container, self.lbl_mini_nome, self.lbl_mini_tempo, self.lbl_mini_count]:
            widget.bind("<Button-1>", self.iniciar_arrasto)
            widget.bind("<B1-Motion>", self.executar_arrasto)
            widget.bind("<Double-Button-1>", lambda e: self.alternar_modo_mini())

    def renderizar_uma_tarefa(self, index):
        t = self.tarefas[index]
        is_active = t.get('rodando', False)
        
        bg_color = self.cor_card_ativo if is_active else self.cor_card
        border_color = self.cor_borda_ativa if is_active else "gray20"
        
        card = ctk.CTkFrame(self.scroll_frame, fg_color=bg_color, corner_radius=12, border_width=2, border_color=border_color)
        card.pack(pady=8, padx=10, fill="x")

        info_cont = ctk.CTkFrame(card, fg_color="transparent")
        info_cont.pack(side="left", padx=20, pady=15, fill="x", expand=True)

        ctk.CTkLabel(info_cont, text=t['nome'], font=("Segoe UI", 16, "bold"), anchor="w").pack(fill="x")
        
        cat_text = f"🏷️ {t.get('categoria', 'Geral')}"
        if t.get('historico_acumulado', 0) > 0:
            cat_text += f" • 📚 Histórico: {self.formatar_tempo(t['historico_acumulado'])}"
            
        ctk.CTkLabel(info_cont, text=cat_text, font=("Segoe UI", 11), text_color=self.cor_texto_secundario, anchor="w").pack(fill="x")

        ctrl_cont = ctk.CTkFrame(card, fg_color="transparent")
        ctrl_cont.pack(side="right", padx=20)

        lbl_tempo = ctk.CTkLabel(ctrl_cont, text=self.formatar_tempo(t['tempo_atual']), 
                                 font=("Consolas", 24, "bold"), text_color=self.cor_borda_ativa if is_active else "white")
        lbl_tempo.pack(side="left", padx=(0, 20))

        # --- Lógica de Ícones Alterada ---
        btn_icon = "⏸" if is_active else "▶"
        
        btn_toggle = ctk.CTkButton(ctrl_cont, text=btn_icon, width=50, height=40, corner_radius=10,
                                   fg_color="#2c3e50", hover_color=self.cor_borda_ativa, font=("Arial", 18),
                                   command=lambda i=index: self.toggle_timer(i))
        btn_toggle.pack(side="left", padx=5)

        ctk.CTkButton(ctrl_cont, text="✅", width=50, height=40, corner_radius=10,
                      fg_color="#2c3e50", hover_color="#27ae60", font=("Arial", 16),
                      command=lambda i=index: self.finalizar_ciclo(i)).pack(side="left", padx=5)

        ctk.CTkButton(ctrl_cont, text="🗑️", width=50, height=40, corner_radius=10,
                      fg_color="transparent", hover_color="#c0392b", text_color="#7f8c8d",
                      command=lambda i=index: self.excluir_tarefa(i)).pack(side="left", padx=5)

        self.tarefas[index]['ui_widgets'] = {'lbl_tempo': lbl_tempo, 'btn_toggle': btn_toggle, 'card': card}

    def toggle_timer(self, index):
        t = self.tarefas[index]
        if t.get('rodando'):
            # Pausar
            decorrido = time.time() - t['inicio_timer']
            t['tempo_atual'] += decorrido
            t['rodando'] = False
            t['inicio_timer'] = None
            t['data_fim'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        else:
            # Iniciar
            t['rodando'] = True
            t['inicio_timer'] = time.time()
        
        self.recarregar_lista_completa()
        self.salvar_dados()

    def atualizar_cronometro_visual(self):
        tempo_total_ativo = 0
        tasks_ativas = 0

        for t in self.tarefas:
            tempo_exibicao = t['tempo_atual']
            
            if t.get('rodando'):
                decorrido = time.time() - t['inicio_timer']
                tempo_exibicao += decorrido
                tasks_ativas += 1
                tempo_total_ativo += tempo_exibicao
                
                # Atualiza label na lista principal se existir
                if 'ui_widgets' in t:
                    try:
                        t['ui_widgets']['lbl_tempo'].configure(text=self.formatar_tempo(tempo_exibicao))
                    except: pass
        
        # Atualiza Widget Mini
        if tasks_ativas > 0:
            self.lbl_mini_tempo.configure(text=self.formatar_tempo(tempo_total_ativo))
            self.lbl_mini_count.configure(text=f"{tasks_ativas} tasks rodando", text_color=self.cor_borda_ativa)
        else:
            self.lbl_mini_tempo.configure(text="00:00:00")
            self.lbl_mini_count.configure(text="0 tasks rodando", text_color="gray")

        self.after(1000, self.atualizar_cronometro_visual)

    def finalizar_ciclo(self, index):
        t = self.tarefas[index]
        if messagebox.askyesno("Finalizar Ciclo", f"Deseja finalizar o ciclo de '{t['nome']}'?"):
            if t.get('rodando'):
                decorrido = time.time() - t['inicio_timer']
                t['tempo_atual'] += decorrido
                t['rodando'] = False
                t['inicio_timer'] = None

            t['historico_acumulado'] += t['tempo_atual']
            t['tempo_atual'] = 0
            t['data_fim'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            self.salvar_dados()
            self.recarregar_lista_completa()

    def adicionar_tarefa(self):
        nome = self.input_tarefa.get().strip()
        if not nome: return
        
        nova_tarefa = {
            'nome': nome, 
            'categoria': self.menu_categoria.get(), 
            'tempo_atual': 0,
            'historico_acumulado': 0,
            'data_inicio': datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
            'data_fim': None,
            'rodando': False,
            'inicio_timer': None
        }
        
        self.tarefas.append(nova_tarefa)
        self.input_tarefa.delete(0, 'end')
        self.recarregar_lista_completa()
        self.salvar_dados()

    def excluir_tarefa(self, index):
        if messagebox.askyesno("Excluir", f"Remover tarefa '{self.tarefas[index]['nome']}'?"):
            self.tarefas.pop(index)
            self.salvar_dados()
            self.recarregar_lista_completa()

    def recarregar_lista_completa(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        for i in range(len(self.tarefas)): self.renderizar_uma_tarefa(i)

    def formatar_tempo(self, segundos):
        return str(timedelta(seconds=int(segundos)))

    def exportar_excel(self):
        # Salva estados atuais antes de exportar
        self.salvar_dados()
        
        lista_para_excel = []
        for t in self.tarefas:
            total_geral = t['tempo_atual'] + t.get('historico_acumulado', 0)
            lista_para_excel.append({
                "Demanda": t['nome'],
                "Categoria": t['categoria'],
                "Última Atividade": t.get('data_fim', '-'),
                "Tempo Sessão Atual": self.formatar_tempo(t['tempo_atual']),
                "Tempo Histórico": self.formatar_tempo(t.get('historico_acumulado', 0)),
                "TEMPO TOTAL GERAL": self.formatar_tempo(total_geral)
            })

        df = pd.DataFrame(lista_para_excel)
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if path:
            try:
                df.to_excel(path, index=False)
                messagebox.showinfo("Sucesso", "Planilha exportada!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar: {e}")

    def iniciar_arrasto(self, event): self.x_mouse, self.y_mouse = event.x, event.y
    def executar_arrasto(self, event):
        deltax, deltay = event.x - self.x_mouse, event.y - self.y_mouse
        self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")
    
    def alternar_modo_mini(self):
        if not self.modo_mini:
            self.main_container.pack_forget()
            self.overrideredirect(True)
            w, h = self.largura_mini, self.altura_mini
            x = self.winfo_screenwidth() - w - 20
            self.geometry(f"{w}x{h}+{x}+50")
            self.attributes("-topmost", True)
            self.mini_container.pack(fill="both", expand=True)
            self.modo_mini = True
        else:
            self.mini_container.pack_forget()
            self.overrideredirect(False)
            self.attributes("-topmost", False)
            self.geometry(f"{self.largura_normal}x{self.altura_normal}")
            self.main_container.pack(fill="both", expand=True)
            self.modo_mini = False

if __name__ == "__main__":
    app = ProTaskApp()
    app.mainloop()
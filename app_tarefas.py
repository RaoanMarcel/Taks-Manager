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
        
        # --- ALTERAÇÃO AQUI: Tamanho do Widget reduzido ---
        self.largura_mini = 230  # Antes era 320
        self.altura_mini = 85    # Antes era 130
        
        # Cores e Estilos
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
        
        self.tarefa_em_andamento_index = None
        self.inicio_sessao_timer = None
        self.loop_ativo = False
        self.x_mouse = 0
        self.y_mouse = 0

        # --- Containers ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        
        # Container Mini (Widget)
        self.mini_container = ctk.CTkFrame(self, fg_color="#1c1c1c", border_width=2, border_color=self.cor_borda_ativa, corner_radius=15)

        self.setup_ui_completa()
        self.setup_ui_mini()
        
        self.main_container.pack(fill="both", expand=True)

        self.recarregar_lista_completa()
        self.atualizar_cronometro_visual()

    def setup_ui_completa(self):
        # --- Header (Barra Superior) ---
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent", height=60)
        self.header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(self.header_frame, text="Minhas Demandas", font=("Segoe UI", 24, "bold"), text_color="white").pack(side="left")
        
        self.btn_mini = ctk.CTkButton(self.header_frame, text="↗ Modo Widget", width=120, height=35, corner_radius=18,
                                      fg_color="#222222", hover_color="#333333", border_width=1, border_color="#444444",
                                      command=self.alternar_modo_mini)
        self.btn_mini.pack(side="right")

        # --- Área de Input (Caixa Flutuante) ---
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

        # --- Lista de Tarefas (Scroll) ---
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # --- Footer ---
        self.footer = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.footer.pack(pady=20, padx=30, fill="x")

        self.btn_export = ctk.CTkButton(self.footer, text="📊 Exportar Relatório Excel", fg_color="#2e7d32", 
                                        hover_color="#1b5e20", command=self.exportar_excel, height=45, corner_radius=10)
        self.btn_export.pack(fill="x")

    def renderizar_uma_tarefa(self, index):
        t = self.tarefas[index]
        is_active = (self.tarefa_em_andamento_index == index)
        
        bg_color = self.cor_card_ativo if is_active else self.cor_card
        border_color = self.cor_borda_ativa if is_active else "gray20"
        border_width = 2 if is_active else 1

        card = ctk.CTkFrame(self.scroll_frame, fg_color=bg_color, corner_radius=12, 
                            border_width=border_width, border_color=border_color)
        card.pack(pady=8, padx=10, fill="x")

        info_cont = ctk.CTkFrame(card, fg_color="transparent")
        info_cont.pack(side="left", padx=20, pady=15, fill="x", expand=True)

        nome_label = ctk.CTkLabel(info_cont, text=t['nome'], font=("Segoe UI", 16, "bold"), anchor="w")
        nome_label.pack(fill="x")
        
        cat_text = f"🏷️ {t.get('categoria', 'Geral')}"
        if t.get('historico_acumulado', 0) > 0:
            tempo_hist = self.formatar_tempo(t['historico_acumulado'])
            cat_text += f" • 📚 Histórico: {tempo_hist}"
            
        ctk.CTkLabel(info_cont, text=cat_text, font=("Segoe UI", 11), text_color=self.cor_texto_secundario, anchor="w").pack(fill="x")

        ctrl_cont = ctk.CTkFrame(card, fg_color="transparent")
        ctrl_cont.pack(side="right", padx=20)

        cor_tempo = self.cor_borda_ativa if is_active else "white"
        lbl_tempo = ctk.CTkLabel(ctrl_cont, text=self.formatar_tempo(t['tempo_atual']), 
                                 font=("Consolas", 24, "bold"), text_color=cor_tempo)
        lbl_tempo.pack(side="left", padx=(0, 20))

        btn_icon = "⏸" if is_active else "▶"
        btn_hover = "#c0392b" if is_active else "#2980b9"
        btn_fg = "#2c3e50" 
        
        btn_toggle = ctk.CTkButton(ctrl_cont, text=btn_icon, width=50, height=40, corner_radius=10,
                                   fg_color=btn_fg, hover_color=btn_hover, font=("Arial", 18),
                                   command=lambda i=index: self.toggle_timer(i))
        btn_toggle.pack(side="left", padx=5)

        btn_finish = ctk.CTkButton(ctrl_cont, text="✅", width=50, height=40, corner_radius=10,
                                   fg_color="#2c3e50", hover_color="#27ae60", font=("Arial", 16),
                                   command=lambda i=index: self.finalizar_ciclo(i))
        btn_finish.pack(side="left", padx=5)

        btn_del = ctk.CTkButton(ctrl_cont, text="🗑️", width=50, height=40, corner_radius=10,
                                fg_color="transparent", hover_color="#c0392b", text_color="#7f8c8d",
                                command=lambda i=index: self.excluir_tarefa(i))
        btn_del.pack(side="left", padx=5)

        self.tarefas[index]['ui_widgets'] = {'lbl_tempo': lbl_tempo}

    # --- Lógica de Widget Mini (COMPACTO) ---
    def setup_ui_mini(self):
        # ALTERAÇÃO: Font menor e padding reduzido para caber no widget pequeno
        self.lbl_mini_nome = ctk.CTkLabel(self.mini_container, text="Aguardando...", 
                                          font=("Segoe UI", 11, "bold"), text_color=self.cor_borda_ativa)
        self.lbl_mini_nome.pack(pady=(5, 0), padx=10) # Padding top reduzido para 5

        # ALTERAÇÃO: Font do relógio reduzida de 32 para 24
        self.lbl_mini_tempo = ctk.CTkLabel(self.mini_container, text="00:00:00", 
                                           font=("Consolas", 24, "bold"))
        self.lbl_mini_tempo.pack(pady=0)

        self.lbl_instrucao = ctk.CTkLabel(self.mini_container, text=":: Arraste ::", 
                                          font=("Arial", 8), text_color="gray")
        self.lbl_instrucao.pack(pady=(0, 2)) # Padding bottom reduzido

        # Bindings
        for widget in [self.mini_container, self.lbl_mini_nome, self.lbl_mini_tempo, self.lbl_instrucao]:
            widget.bind("<Button-1>", self.iniciar_arrasto)
            widget.bind("<B1-Motion>", self.executar_arrasto)
            widget.bind("<Double-Button-1>", lambda e: self.alternar_modo_mini())

    # --- Nova Funcionalidade: Finalizar Ciclo ---
    def finalizar_ciclo(self, index):
        t = self.tarefas[index]
        
        if self.tarefa_em_andamento_index == index:
            self.parar(index)
        
        tempo_sessao = t['tempo_atual']
        
        if tempo_sessao < 1:
            messagebox.showinfo("Aviso", "Não há tempo corrido para finalizar nesta tarefa.")
            return

        if messagebox.askyesno("Finalizar Ciclo", f"Deseja finalizar o ciclo atual de:\n'{t['nome']}'?\n\nO tempo será salvo no histórico e o cronômetro zerado."):
            t['historico_acumulado'] = t.get('historico_acumulado', 0) + tempo_sessao
            t['tempo_atual'] = 0
            t['data_fim'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            self.salvar_dados()
            self.recarregar_lista_completa()
            self.atualizar_cronometro_visual()

    # --- Lógica Core ---
    def carregar_dados(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f: 
                    dados = json.load(f)
                    for d in dados:
                        if 'tempo_atual' not in d: d['tempo_atual'] = d.pop('tempo_total', 0)
                        if 'historico_acumulado' not in d: d['historico_acumulado'] = 0
                    return dados
            except: return []
        return []

    def salvar_dados(self):
        with open(self.db_file, 'w') as f: json.dump(self.tarefas, f, indent=4)

    def adicionar_tarefa(self):
        nome = self.input_tarefa.get().strip()
        if not nome: return
        
        nova_tarefa = {
            'nome': nome, 
            'categoria': self.menu_categoria.get(), 
            'tempo_atual': 0,
            'historico_acumulado': 0,
            'data_inicio': datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
            'data_fim': None
        }
        
        self.tarefas.append(nova_tarefa)
        self.input_tarefa.delete(0, 'end')
        self.recarregar_lista_completa()
        self.salvar_dados()

    def recarregar_lista_completa(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        for i in range(len(self.tarefas)): self.renderizar_uma_tarefa(i)

    def formatar_tempo(self, segundos):
        return str(timedelta(seconds=int(segundos)))

    def toggle_timer(self, index):
        if self.tarefa_em_andamento_index == index: self.parar(index)
        else:
            if self.tarefa_em_andamento_index is not None: self.parar(self.tarefa_em_andamento_index)
            self.iniciar(index)
        self.recarregar_lista_completa()

    def iniciar(self, index):
        self.tarefa_em_andamento_index = index
        self.inicio_sessao_timer = time.time()
        self.loop_ativo = True
        self.lbl_mini_nome.configure(text=self.tarefas[index]['nome'])

    def parar(self, index):
        if self.inicio_sessao_timer:
            self.tarefas[index]['tempo_atual'] += time.time() - self.inicio_sessao_timer
        
        self.tarefas[index]['data_fim'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.tarefa_em_andamento_index = None
        self.loop_ativo = False
        self.lbl_mini_nome.configure(text="Aguardando...")
        self.salvar_dados()

    def excluir_tarefa(self, index):
        if messagebox.askyesno("Excluir", f"Remover tarefa '{self.tarefas[index]['nome']}'?"):
            if self.tarefa_em_andamento_index == index: self.parar(index)
            self.tarefas.pop(index)
            self.salvar_dados()
            self.recarregar_lista_completa()

    def atualizar_cronometro_visual(self):
        if self.loop_ativo and self.tarefa_em_andamento_index is not None:
            idx = self.tarefa_em_andamento_index
            atual = self.tarefas[idx]['tempo_atual'] + (time.time() - self.inicio_sessao_timer)
            tempo_str = self.formatar_tempo(atual)
            
            if 'ui_widgets' in self.tarefas[idx]:
                try:
                    self.tarefas[idx]['ui_widgets']['lbl_tempo'].configure(text=tempo_str)
                except: pass
            
            self.lbl_mini_tempo.configure(text=tempo_str)
            
        self.after(1000, self.atualizar_cronometro_visual)

    def exportar_excel(self):
        if self.tarefa_em_andamento_index is not None: self.parar(self.tarefa_em_andamento_index)
        
        lista_para_excel = []
        for t in self.tarefas:
            total_geral = t['tempo_atual'] + t.get('historico_acumulado', 0)
            
            lista_para_excel.append({
                "Demanda": t['nome'],
                "Categoria": t['categoria'],
                "Última Atividade": t.get('data_fim', '-'),
                "Tempo Sessão Atual": self.formatar_tempo(t['tempo_atual']),
                "Tempo Histórico (Finalizados)": self.formatar_tempo(t.get('historico_acumulado', 0)),
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
            
            # Atualiza para usar as dimensões reduzidas
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
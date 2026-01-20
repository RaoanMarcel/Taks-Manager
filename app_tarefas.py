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

        # --- Configurações de Janela ---
        self.title("ProTask Pericial")
        self.largura_normal = 950
        self.altura_normal = 700
        self.largura_mini = 280
        self.altura_mini = 90
        
        # Centralizar na abertura
        self.geometry(f"{self.largura_normal}x{self.altura_normal}")
        
        # Estado
        self.modo_mini = False
        self.categorias = ["Organização", "testes automação", "Suporte interno", "RMA e comunicação", "suporte clientes"]
        self.db_file = "database_tasks.json"
        self.tarefas = self.carregar_dados()
        
        self.tarefa_em_andamento_index = None
        self.inicio_sessao_timer = None
        self.loop_ativo = False

        # Variáveis para arrastar a janela no modo mini
        self.x_mouse = 0
        self.y_mouse = 0

        # --- Containers Principais ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.mini_container = ctk.CTkFrame(self, fg_color=("#ebebeb", "#2b2b2b"), border_width=2, border_color="#3B8ED0")

        self.setup_ui_completa()
        self.setup_ui_mini()
        
        # Inicia no modo normal
        self.main_container.pack(fill="both", expand=True)

        self.renderizar_tarefas_salvas()
        self.atualizar_cronometro_visual()

    def setup_ui_completa(self):
        # Header Superior (Barra de ferramentas)
        self.top_bar = ctk.CTkFrame(self.main_container, height=40, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=10, pady=(5, 0))

        self.btn_mini = ctk.CTkButton(self.top_bar, text="🔳 MODO WIDGET (Always on Top)", width=120, height=30, 
                                      fg_color="#3B8ED0", hover_color="#1f538d", command=self.alternar_modo_mini)
        self.btn_mini.pack(side="right", padx=5)

        # Entrada de tarefas
        self.header = ctk.CTkFrame(self.main_container)
        self.header.pack(pady=10, padx=20, fill="x")

        self.input_tarefa = ctk.CTkEntry(self.header, placeholder_text="Nome da Demanda...", width=350)
        self.input_tarefa.pack(side="left", padx=(20, 10), pady=20, expand=True, fill="x")
        self.input_tarefa.bind("<Return>", lambda e: self.adicionar_tarefa())

        self.menu_categoria = ctk.CTkOptionMenu(self.header, values=self.categorias, width=180)
        self.menu_categoria.pack(side="left", padx=10, pady=20)
        self.menu_categoria.set("Organização")

        self.btn_add = ctk.CTkButton(self.header, text="Nova Task", command=self.adicionar_tarefa, font=("Arial", 13, "bold"), width=100)
        self.btn_add.pack(side="right", padx=20)

        # Lista de tarefas
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.scroll_frame.pack(pady=0, padx=20, fill="both", expand=True)

        # Footer
        self.footer = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.footer.pack(pady=20, padx=20, fill="x")

        self.btn_export = ctk.CTkButton(self.footer, text="Gerar Relatório Excel", fg_color="#1E7E34", 
                                        hover_color="#155D27", command=self.exportar_excel, height=45)
        self.btn_export.pack(fill="x")

    def setup_ui_mini(self):
        """Configura a interface da caixinha flutuante."""
        self.lbl_mini_nome = ctk.CTkLabel(self.mini_container, text="Nenhuma task ativa", font=("Arial", 12, "bold"), text_color="#3B8ED0")
        self.lbl_mini_nome.pack(pady=(10, 0), padx=10)

        self.lbl_mini_tempo = ctk.CTkLabel(self.mini_container, text="00:00:00", font=("Consolas", 22, "bold"))
        self.lbl_mini_tempo.pack(pady=0)

        self.lbl_instrucao = ctk.CTkLabel(self.mini_container, text="Clique para expandir | Arraste para mover", font=("Arial", 8), text_color="gray")
        self.lbl_instrucao.pack(pady=(0, 5))

        # Eventos para clicar e expandir ou arrastar
        self.mini_container.bind("<Button-1>", self.iniciar_arrasto)
        self.mini_container.bind("<B1-Motion>", self.executar_arrasto)
        self.mini_container.bind("<Double-Button-1>", lambda e: self.alternar_modo_mini())
        
        # Aplicar binds aos filhos também (nome e tempo)
        for widget in [self.lbl_mini_nome, self.lbl_mini_tempo, self.lbl_instrucao]:
            widget.bind("<Button-1>", self.iniciar_arrasto)
            widget.bind("<B1-Motion>", self.executar_arrasto)
            widget.bind("<Double-Button-1>", lambda e: self.alternar_modo_mini())

    # --- Lógica de Arrastar Janela Sem Bordas ---
    def iniciar_arrasto(self, event):
        self.x_mouse = event.x
        self.y_mouse = event.y

    def executar_arrasto(self, event):
        deltax = event.x - self.x_mouse
        deltay = event.y - self.y_mouse
        new_x = self.winfo_x() + deltax
        new_y = self.winfo_y() + deltay
        self.geometry(f"+{new_x}+{new_y}")

    def alternar_modo_mini(self):
        if not self.modo_mini:
            # ENTRAR NO MODO MINI (Always on Top)
            self.main_container.pack_forget()
            
            # Cálculo para canto superior direito
            screen_width = self.winfo_screenwidth()
            pos_x = screen_width - self.largura_mini - 20
            pos_y = 50
            
            self.overrideredirect(True) # Remove bordas
            self.geometry(f"{self.largura_mini}x{self.altura_mini}+{pos_x}+{pos_y}")
            self.attributes("-topmost", True)
            
            self.mini_container.pack(fill="both", expand=True)
            self.modo_mini = True
        else:
            # VOLTAR AO MODO NORMAL
            self.mini_container.pack_forget()
            self.overrideredirect(False)
            self.attributes("-topmost", False)
            self.geometry(f"{self.largura_normal}x{self.altura_normal}")
            self.main_container.pack(fill="both", expand=True)
            self.modo_mini = False

    # --- Lógica de Dados e Backend ---

    def formatar_tempo(self, segundos):
        return str(timedelta(seconds=int(segundos)))

    def carregar_dados(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f: return json.load(f)
            except: return []
        return []

    def salvar_dados(self):
        dados_purificados = [{'nome': t['nome'], 'categoria': t.get('categoria', 'Geral'), 
                             'tempo_total': t['tempo_total'], 'data_inicio': t['data_inicio'], 
                             'data_fim': t['data_fim']} for t in self.tarefas]
        with open(self.db_file, 'w') as f: json.dump(dados_purificados, f, indent=4)

    def adicionar_tarefa(self):
        nome = self.input_tarefa.get().strip()
        if not nome: return
        self.tarefas.append({'nome': nome, 'categoria': self.menu_categoria.get(), 'tempo_total': 0, 
                             'data_inicio': None, 'data_fim': None, 'ui_widgets': {}})
        self.input_tarefa.delete(0, 'end')
        self.renderizar_uma_tarefa(len(self.tarefas) - 1)
        self.salvar_dados()

    def renderizar_uma_tarefa(self, index):
        t = self.tarefas[index]
        frame = ctk.CTkFrame(self.scroll_frame, border_width=1, border_color="gray30")
        frame.pack(pady=5, padx=5, fill="x")

        info_cont = ctk.CTkFrame(frame, fg_color="transparent")
        info_cont.pack(side="left", padx=15, pady=10, fill="x", expand=True)

        ctk.CTkLabel(info_cont, text=t['nome'], font=("Arial", 14, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(info_cont, text=f"🏷️ {t.get('categoria', 'Geral')}", font=("Arial", 11), text_color="#3B8ED0", anchor="w").pack(fill="x")

        time_cont = ctk.CTkFrame(frame, fg_color="transparent")
        time_cont.pack(side="right", padx=15)

        lbl_tempo = ctk.CTkLabel(time_cont, text=self.formatar_tempo(t['tempo_total']), font=("Consolas", 18, "bold"))
        lbl_tempo.pack(side="left", padx=20)

        btn = ctk.CTkButton(time_cont, text="START", width=80, command=lambda i=index: self.toggle_timer(i))
        btn.pack(side="right")
        self.tarefas[index]['ui_widgets'] = {'btn': btn, 'lbl_tempo': lbl_tempo}

    def renderizar_tarefas_salvas(self):
        for i in range(len(self.tarefas)): self.renderizar_uma_tarefa(i)

    def toggle_timer(self, index):
        if self.tarefa_em_andamento_index == index: self.parar(index)
        else:
            if self.tarefa_em_andamento_index is not None: self.parar(self.tarefa_em_andamento_index)
            self.iniciar(index)

    def iniciar(self, index):
        self.tarefa_em_andamento_index = index
        self.inicio_sessao_timer = time.time()
        self.loop_ativo = True
        if not self.tarefas[index]['data_inicio']:
            self.tarefas[index]['data_inicio'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        self.tarefas[index]['ui_widgets']['btn'].configure(text="STOP", fg_color="#A83232")
        self.lbl_mini_nome.configure(text=self.tarefas[index]['nome']) # Atualiza nome no modo mini
        self.salvar_dados()

    def parar(self, index):
        self.tarefas[index]['tempo_total'] += time.time() - self.inicio_sessao_timer
        self.tarefas[index]['data_fim'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.tarefas[index]['ui_widgets']['btn'].configure(text="START", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        self.tarefas[index]['ui_widgets']['lbl_tempo'].configure(text=self.formatar_tempo(self.tarefas[index]['tempo_total']))
        
        self.tarefa_em_andamento_index = None
        self.loop_ativo = False
        self.lbl_mini_nome.configure(text="Nenhuma task ativa")
        self.lbl_mini_tempo.configure(text="00:00:00")
        self.salvar_dados()

    def atualizar_cronometro_visual(self):
        if self.loop_ativo and self.tarefa_em_andamento_index is not None:
            idx = self.tarefa_em_andamento_index
            atual = self.tarefas[idx]['tempo_total'] + (time.time() - self.inicio_sessao_timer)
            tempo_str = self.formatar_tempo(atual)
            
            # Atualiza na lista principal
            self.tarefas[idx]['ui_widgets']['lbl_tempo'].configure(text=tempo_str, text_color="#3B8ED0")
            
            # Atualiza no WIDGET MINI
            self.lbl_mini_tempo.configure(text=tempo_str)
            
        self.after(1000, self.atualizar_cronometro_visual)

    def exportar_excel(self):
        if self.tarefa_em_andamento_index is not None: self.parar(self.tarefa_em_andamento_index)
        df = pd.DataFrame([{"Demanda": t['nome'], "Categoria": t['categoria'], "Início": t['data_inicio'], 
                           "Fim": t['data_fim'], "Tempo Total": self.formatar_tempo(t['tempo_total'])} for t in self.tarefas])
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if path:
            df.to_excel(path, index=False)
            messagebox.showinfo("Sucesso", "Planilha gerada!")

if __name__ == "__main__":
    app = ProTaskApp()
    app.mainloop()
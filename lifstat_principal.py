import customtkinter as ctk
import tkinter as tk
import frame_esquerdo
import Medir_cv
import Medir_ca
import sobre
import version
import motores
import calibracao
from filtroDeSinal_CV import run_filtro_app
from cyclic_voltammetry_filterCondenser import Get_CV_Data
import lifstat_sendEmail
# Configuração inicial da interface CustomTkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
class Janela(ctk.CTk):
    def __init__(self):
        super().__init__()
        global connected
        self.geometry("1380x790")
        self.title("Interface Potenciostato")
        # Configuração do layout
        self.grid_columnconfigure(0, weight=0)  # Frame esquerdo
        self.grid_columnconfigure(1, weight=3)  # Frame direito
        self.grid_rowconfigure(0, weight=1)
        # Criando o menu
        self.criar_menu()
        # Frame esquerdo
        self.frameesquerdo = frame_esquerdo.FrameEsquerdo(self, self.mostrar_frame_direito)
        self.frameesquerdo.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Inicializa o frame direito como None
        self.frame_direito = None

        # Exibe o frame direito inicialb
        self.mostrar_frame_direito(1)
    def criar_menu(self):
        # Menu principal da interface
        menu_bar = tk.Menu(self)
        # Menu Arquivo
        menu_arquivo = tk.Menu(menu_bar, tearoff=0)
        menu_arquivo.add_command(label="Abrir CV para filtragem", command=run_filtro_app)
        menu_arquivo.add_command(label="Abrir CV para envio ", command = Get_CV_Data)
        menu_arquivo.add_separator()
        menu_arquivo.add_command(label="Sair", command=self.quit)
        menu_bar.add_cascade(label="Processamento", menu=menu_arquivo)

       # Menu Configuração
       # menu_config = tk.Menu(menu_bar, tearoff=0)
       # menu_config.add_command(label="Preferências")
       # menu_bar.add_cascade(label="Configuração", menu=menu_config)

        # Menu Sobre
        menu_sobre = tk.Menu(menu_bar, tearoff=0)
        menu_sobre.add_command(label="Versão", command = version.mostrar_version)
        menu_sobre.add_command(label="Nota do programa", command=sobre.mostrar_sobre)
        menu_bar.add_cascade(label="Sobre", menu=menu_sobre)

        self.config(menu=menu_bar)
    def mostrar_frame_direito(self, frame_id, connected=True):
        # Remove o frame direito anterior, se houver
        if self.frame_direito:
            self.frame_direito.destroy()
        # Exibe o frame direito com base no botão clicado
        if frame_id == 3:
            self.frame_direito = Medir_cv.Medir_CV_GUI(self, self.frameesquerdo, is_connected_callback=self.verificar_conexao)
        elif frame_id == 1:
            self.frame_direito = motores.MotorFrame(self, self.frameesquerdo, is_connected_callback=self.verificar_conexao)
        elif frame_id == 2:
            self.frame_direito = calibracao.CalibracaoFrame(self, self.frameesquerdo, is_connected_callback=self.verificar_conexao)
        elif frame_id == 4:
            self.frame_direito = Medir_ca.Medir_CA_GUI(self, self.frameesquerdo, is_connected_callback=self.verificar_conexao)
        elif frame_id == 5:
            self.frame_direito = lifstat_sendEmail.EmailManager(self, self.frameesquerdo, is_connected_callback=self.verificar_conexao)
        # Exibe o frame direito
        if self.frame_direito:
            self.frame_direito.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

    # Função para fechar a janela e a comunicação serial
    def quit(self):
        self.destroy()

    # Função que verifica a conexão serial
    def verificar_conexao(self):
        # Verifica se a conexão serial foi estabelecida corretamente
        return self.frameesquerdo.conexao_serial is not None and self.frameesquerdo.conexao_serial.is_open

if __name__ == "__main__":
    # Inicializa a aplicação
    app = Janela()
    app.mainloop()



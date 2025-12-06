# -*- coding: utf-8 -*-
import numpy as np
import struct
import time
import serial
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
from datetime import datetime
import matplotlib.pyplot as plt
import customtkinter as ctk  # Supondo que esteja usando CustomTkinter
import threading
from tkinter import  *
from PIL import ImageTk, Image, ImageEnhance
import csv

class CalibracaoFrame(ctk.CTkFrame):
    def __init__(self, master, frame_esquerdo, is_connected_callback=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.frame_esquerdo = frame_esquerdo
        self.is_connected_callback = is_connected_callback
        self.running = False
        self.initiate_plot = True
        self.refresh_count = 0
        self.plot_type = 1
        self.data_collected = False
        self.create_widgets()
    def create_widgets(self):
        # Carregar e ajustar a imagem de fundo
        background_image = Image.open("images/lifstat_05.png")
        enhancer = ImageEnhance.Brightness(background_image)
        background_image = enhancer.enhance(1)  # Ajustar opacidade da imagem
        self.bg_image = ImageTk.PhotoImage(background_image)

        # Criar um Canvas para desenhar a imagem de fundo
        self.canvas = tk.Canvas(self, width=self.bg_image.width(), height=self.bg_image.height())
        self.canvas.grid(row=0, column=0, rowspan=6, columnspan=6, sticky="nsew")
        self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        # Label "Calibração do sensor"
        self.title_label = ctk.CTkLabel(self, text="Calibração do LIFstat", font=("Arial", 30, "bold"))
        self.title_label.grid(row=1, column=2, columnspan=3, padx=10, pady=5)

        # Label com a mensagem de calibração
        # Criar um frame para aplicar o espaçamento interno e o fundo colorido
        self.message_frame = ctk.CTkFrame(self, fg_color="#4a90e2", corner_radius=10)
        self.message_frame.grid(row=2, column=2, columnspan=3, padx=200, pady=10, sticky="nsew")

        # Colocar o label dentro do frame com espaçamento interno via padding no pack
        self.message_label = ctk.CTkLabel(
            self.message_frame,
            text=(
                "Você iniciou a calibração do sistema!\n\n"
                "Seja paciente, isso pode levar aproximadamente 20 segundos para a checagem dos dados "
                "e 10 segundos para começar a medição para a calibração.\n\n"
                "O LED irá acender indicando que o sistema está em operação de calibração. "
                "Se tudo correu bem, o LED irá piscar três vezes indicando que o processo está terminando.\n\n"
                "Clique em 'Calibração' para começar."
            ),
            wraplength=500,
            justify="center",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        )
        self.message_label.pack(padx=20, pady=20)

        # Scrolled Text para exibir as mensagens de saída da calibração
        self.output_text = ScrolledText(self, wrap=tk.WORD, height=10, width=50)
        self.output_text.grid(row=3, column=2, columnspan=3, padx=200, pady=10)

        # Botão para iniciar a calibração
        self.start_button = ctk.CTkButton(self, text="Iniciar Calibração", text_color= "black",font=("Times News Roman", 15, "bold"), command=self.start_calib_thread)
        self.start_button.grid(row=4, column=2, columnspan=3, padx=200, pady=10)

        # Configurações de plot
        plt.rcParams['mathtext.fontset'] = 'dejavuserif'
        plt.rcParams['font.sans-serif'] = ['Times new Roman']

    def write_output_calib(self, text):
        self.output_text.insert(tk.END, f"{text}\n")
        self.output_text.see(tk.END)

    def create_cal_file(self):
        txt_filename = datetime.today().strftime('CALIBRATION/%Y_%m_%d_Cal.txt')
        self.outfile_calib_data = open(txt_filename, 'w')

    def start_serial(self):
        if not self.frame_esquerdo.conexao_serial:
            messagebox.showerror("Erro de Comunicação", "Conexão Serial não estabelecida!")
            return

        try:
            randfloat = 11.01
            send_bytes = b'\x44\x66' + struct.pack('f', randfloat)
            self.frame_esquerdo.conexao_serial.write(send_bytes)
            time.sleep(2)
            ser_out_1 = self.frame_esquerdo.conexao_serial.readline().strip()
            ser_out_2 = self.frame_esquerdo.conexao_serial.readline().strip()
            if (ser_out_1 == send_bytes) and (float(ser_out_2) == np.round(randfloat, decimals=2)):
                self.write_output_calib("Comunicação serial estabelecida com sucesso!")
            else:
                messagebox.showwarning("Erro de Comunicação", "Dados recebidos estão corrompidos.")
        except Exception as e:
            messagebox.showerror("Erro de Comunicação", f"Erro: {str(e)}")

    def set_calib_params(self):
        try:
            # Parâmetros de calibração
            e_1, e_2, e_3, e_4, e_5 = -0.5, 0.5, 0.0, 0.0, 0.0
            t_1, t_2, t_3, t_4, t_5 = 5000.0, 5000.0, 0.0, 0.0, 0.0
            repetitions = 1.0
            self.read_resist = 120

            send_commands = [
                (b'\x12\x17', e_1), (b'\x12\x18', e_2), (b'\x12\x19', e_3),
                (b'\x12\x20', e_4), (b'\x12\x21', e_5), (b'\x12\x22', t_1),
                (b'\x12\x23', t_2), (b'\x12\x24', t_3), (b'\x12\x25', t_4),
                (b'\x12\x26', t_5), (b'\x12\x27', repetitions)
            ]
            for command, value in send_commands:
                self.frame_esquerdo.conexao_serial.write(command + struct.pack('f', value))
                time.sleep(2)

            self.write_output_calib("Parâmetros de calibração enviados com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro nos Parâmetros", f"Erro: {str(e)}")

    def start_calib(self):
        if not self.frame_esquerdo.conexao_serial:
            messagebox.showerror("Erro", "Conexão Serial não estabelecida!")
            return

        self.storage_array = np.zeros((1, 5))

        self.create_cal_file()
        messagebox.showinfo("Calibração Iniciada", "Processo de calibração iniciado. Aguarde.")
        self.set_calib_params()
        self.storage_array = np.zeros((1, 5))

        send_bytes = b'\x14\x00\x00\x00\x00\x00'
        self.frame_esquerdo.conexao_serial.write(send_bytes)

        starter = self.frame_esquerdo.conexao_serial.readline().strip()
        while starter != b'10101010':
            time.sleep(0.001)
            starter = self.frame_esquerdo.conexao_serial.readline().strip()
        self.running = True
        self.Serial_Looper()
        self.data_collected = True
        self.write_output_calib("Calibração em andamento...")

    def start_calib_thread(self):
        # Criar um thread separado para a calibração
        calib_thread = threading.Thread(target=self.start_calib)
        calib_thread.start()

    def StopReadSuccess_Calib(self):
        self.running = False
        if hasattr(self, 'outfile_calib_data') and self.outfile_calib_data:
            for i in range(len(self.storage_array[1:, 0])):
                self.outfile_calib_data.write(
                    f"{self.storage_array[i + 1, 0]}\t{self.storage_array[i + 1, 1]}\t{0.001 * self.storage_array[i + 1, 2]}\t"
                    f"{self.storage_array[i + 1, 3]}\t{self.storage_array[i + 1, 4]}\n"
                )
            self.outfile_calib_data.close()

        self.write_output_calib("Calibração concluída com sucesso.")
        try:
            #self.frame_esquerdo.conexao_serial.close()
            self.write_output_calib("Pode seguir com o processo de medição .")
        except Exception:
            pass

    def Serial_Looper(self):
        if self.running:
            try:
                data = self.frame_esquerdo.conexao_serial.readline().strip()
                print("Dados recebidos:", data)  # Confirmação dos dados recebidos
                if data:
                    if data != b'999999':
                        # Decodifica os dados e remove caracteres indesejados
                        decoded = [item.strip() for item in data.decode("utf-8").split('\t')]

                        # Tenta converter para float apenas os valores válidos
                        try:
                            decoded = np.array([float(item) for item in decoded]).astype(float)
                            if decoded.shape[0] == 5:  # Garante que há 5 elementos
                                self.storage_array = np.vstack([self.storage_array, decoded])
                                print("Storage array atualizado:", self.storage_array)  # Confirmar atualização
                        except ValueError:
                            print("Dados inválidos recebidos:", decoded)  # Exibe a linha problemática
                    else:
                        self.StopReadSuccess_Calib()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro na comunicação serial. Verifique a conexão. {str(e)}")
                self.running = False

        # Remover o comentário para continuar o loop:
        self.master.after(1, self.Serial_Looper)

    def quit(self):
        self.master.quit()
        self.master.destroy()

# Exemplo de como chamar o frame em um arquivo externo
if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry("1000x900")
    def mock_verificar_conexao():
        # Função de exemplo para simular a verificação de conexão
        return True

    calibracao = CalibracaoFrame(root, None, is_connected_callback=mock_verificar_conexao)
    calibracao.pack(expand=True, fill="both")

    root.mainloop()

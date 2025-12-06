import struct
import tkinter as tk
from tkinter import scrolledtext, messagebox
import customtkinter as ctk
from PIL import Image
import time
import numpy as np

class MotorFrame(ctk.CTkFrame):
    def __init__(self, master, frame_esquerdo, is_connected_callback=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.is_connected_callback = is_connected_callback
        self.frame_esquerdo = frame_esquerdo
        self.root = master

        # Interface dos motores
        self.motores_labelframe = tk.LabelFrame(self, text="Motores")
        self.motores_labelframe.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.motor_LD = []
        self.motor_buttons = []
        self.toggle_states = [False, False, False, False]

        for i in range(4):
            self.create_motor_block(i)

        # Configuração
        self.config_labelframe = tk.LabelFrame(self, text="Configuração")
        self.config_labelframe.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Variáveis para os entries
        self.entry_vars = [ctk.DoubleVar(value=1.0) for _ in range(4)]

        # Entradas com os labels
        labels = ["Motor geral vazio", "Motor geral cheio", "Motor NaCl", "Motor KCl"]
        for i, label in enumerate(labels):
            ctk.CTkLabel(self.config_labelframe, text=f"{label} (segundos):").grid(
                row=i, column=0, padx=10, pady=5, sticky="e")
            entry = ctk.CTkEntry(
                self.config_labelframe,
                textvariable=self.entry_vars[i],
                validate="key",
                validatecommand=(self.register(self.validate_float), '%P')
            )
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")

        # Botões
        self.write_button = ctk.CTkButton(self.config_labelframe, text="Gravar na EEPROM", command=self.write_config)
        self.write_button.grid(row=4, column=0, padx=5, pady=10)

        self.read_button = ctk.CTkButton(self.config_labelframe, text="Ler da EEPROM", command=self.read_config)
        self.read_button.grid(row=4, column=1, padx=5, pady=10)

        # Temperatura
        self.label_temperatura = ctk.CTkLabel(self, text="Temperatura da água do tanque:", font=("Arial", 15, "bold"))
        self.label_temperatura.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.temperatura_textbox = scrolledtext.ScrolledText(self, width=40, height=5)
        self.temperatura_textbox.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

    def validate_float(self, new_value):
        """Valida se o novo valor é float ou vazio"""
        if new_value == "":
            return True
        try:
            float(new_value)
            return True
        except ValueError:
            return False

    def create_motor_block(self, index):
        motor_image_path = f"images/motor{index + 1}.png"
        motor_image = Image.open(motor_image_path)
        motor_ctk_image = ctk.CTkImage(light_image=motor_image, dark_image=motor_image, size=(100, 100))
        motor_label = ctk.CTkLabel(self.motores_labelframe, image=motor_ctk_image, text="")
        motor_label.grid(row=0, column=index, padx=70, pady=5)
        motor_name = ["Motor Geral", "Motor KCl", "Motor NaCl", "SISTEMA"]
        motor_title = ctk.CTkLabel(self.motores_labelframe, text=motor_name[index], font=("Arial", 14, "bold"))
        motor_title.grid(row=1, column=index, padx=10, pady=(0, 10))

        if index == 0:
            self.encher_esvaziar_state = {"encher": False, "esvaziar": False}

            def toggle_encher():
                self.encher_esvaziar_state["encher"] = not self.encher_esvaziar_state["encher"]
                encher_button.configure(
                    text="Parar enchimento" if self.encher_esvaziar_state["encher"] else "Encher",
                    fg_color="red" if self.encher_esvaziar_state["encher"] else "blue"
                )
                msg = b'\x73'
                self._enviar_serial(msg)

            def toggle_esvaziar():
                self.encher_esvaziar_state["esvaziar"] = not self.encher_esvaziar_state["esvaziar"]
                esvaziar_button.configure(
                    text="Parar esvaziamento" if self.encher_esvaziar_state["esvaziar"] else "Esvaziar",
                    fg_color="red" if self.encher_esvaziar_state["esvaziar"] else "blue"
                )
                msg = b'\x74'
                self._enviar_serial(msg)

            encher_button = ctk.CTkButton(self.motores_labelframe, text="Encher", fg_color="blue",
                                          command=toggle_encher)
            encher_button.grid(row=2, column=index, padx=5, pady=5)
            esvaziar_button = ctk.CTkButton(self.motores_labelframe, text="Esvaziar", fg_color="blue",
                                            command=toggle_esvaziar)
            esvaziar_button.grid(row=3, column=index, padx=5, pady=5)

        elif index == 3:
            iniciar_button = ctk.CTkButton(self.motores_labelframe, text="Iniciar Modo Automático", fg_color="blue",
                                           command=self.iniciar_modo_automatico)
            iniciar_button.grid(row=2, column=index, padx=5, pady=5)
            parar_button = ctk.CTkButton(self.motores_labelframe, text="Parar Sistema", fg_color="red",
                                         command=self.parar_sistema)
            parar_button.grid(row=3, column=index, padx=5, pady=5)
        else:
            motor_button = ctk.CTkButton(self.motores_labelframe, text="Ligar",
                                         command=lambda idx=index: self.toggle_motor(idx))
            motor_button.grid(row=2, column=index, padx=10, pady=5)
            self.motor_buttons.append(motor_button)

    def _enviar_serial(self, mensagem):
        if self.is_connected_callback and self.is_connected_callback():
            self.frame_esquerdo.conexao_serial.write(mensagem)
        else:
            messagebox.showwarning("Erro de Conexão", "Nenhuma conexão serial estabelecida.")

    def iniciar_modo_automatico(self):
        self._enviar_serial(b'\x77\x00\x00\x00\x00\x00') # inicia modo automático

    def finalizar_automatico(self):
        if self.is_connected_callback and self.is_connected_callback():
            self.frame_esquerdo.conexao_serial.write(b'\x78\x00\x00\x00\x00\x00')  # Envia comando
        else:
            messagebox.showwarning("Erro de Conexão", "Nenhuma conexão serial estabelecida.")
    def parar_sistema(self):
        self._enviar_serial(b'\x79\x00\x00\x00\x00\x00') # para modo automático

    def toggle_motor(self, motor_index):
        if motor_index == 0:
            return
        estado_atual = self.toggle_states[motor_index]
        mensagem = f"M{motor_index + 2}"
        if (mensagem == "M3"):
            self._enviar_serial(b'\x75')
            self.motor_buttons[motor_index - 1].configure(
                text="Desligar" if not estado_atual else "Ligar",
                fg_color="red" if not estado_atual else "blue"
            )
            self.toggle_states[motor_index] = not estado_atual

        elif (mensagem == "M4"):
            self._enviar_serial(b'\x76')
            self.motor_buttons[motor_index - 1].configure(
                text="Desligar" if not estado_atual else "Ligar",
                fg_color="red" if not estado_atual else "blue"
            )
            self.toggle_states[motor_index] = not estado_atual

    def write_config(self):
        if not self.is_connected_callback or not self.is_connected_callback():
            self.status_var.set("Erro: Porta serial não conectada!")
            print("ERRO: Não há conexão serial estabelecida")
            return

        try:
            print("Enviando comando de escrita na EEPROM (0x71)...")
            #self.frame_esquerdo.conexao_serial.reset_input_buffer()
            #self.frame_esquerdo.conexao_serial.write(b'\x71')

            # Converte os valores para float
            Motor_vazio  = float(self.entry_vars[0].get())
            Motor_cheio  = float(self.entry_vars[1].get())
            Motor_NaCl   = float(self.entry_vars[2].get())
            Motor_KCl    = float(self.entry_vars[3].get())

            # Preparação para enviar os dados para o Arduino
            vazio = b'\x71' + b'\x01' + struct.pack('f', Motor_vazio)
            cheio = b'\x71' + b'\x02' + struct.pack('f', Motor_cheio)
            nacl  = b'\x71' + b'\x03' + struct.pack('f', Motor_NaCl)
            kcl   = b'\x71' + b'\x04' + struct.pack('f', Motor_KCl)

            # Verifica a conexão e envia os dados
            if self.is_connected_callback and self.is_connected_callback():
                self.frame_esquerdo.conexao_serial.write(vazio)
                time.sleep(2)
                self.frame_esquerdo.conexao_serial.write(cheio)
                time.sleep(2)
                self.frame_esquerdo.conexao_serial.write(nacl)
                time.sleep(2)
                self.frame_esquerdo.conexao_serial.write(kcl)
                time.sleep(2)

            else:
                messagebox.showwarning("Erro de Conexão", "Nenhuma conexão serial estabelecida.")
        except Exception as e:
            messagebox.showerror(title="Erro", message=f"Ocorreu um erro: {e}")
    """
    def read_config(self):
        if self.is_connected_callback and self.is_connected_callback():
            try:
                print("Enviando comando de leitura da EEPROM (0x72)...")
                Motor_tempo = np.zeros(4)
                get_bytes = b'\x72\x00\x00\x00\x00\x00'
                self.frame_esquerdo.conexao_serial.write(get_bytes)
                time.sleep(4)  # Aguarda resposta do Arduino

                # Lê os valores da serial
                Motor_tempo[0] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])  # vazio
                Motor_tempo[1] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])  # cheio
                Motor_tempo[2] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])  # nacl
                Motor_tempo[3] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])  # kcl

                # Apaga os entries antes de atualizar
                self.entry_vars[0].set("")  # Apaga entry para vazio
                self.entry_vars[1].set("")  # Apaga entry para cheio
                self.entry_vars[2].set("")  # Apaga entry para nacl
                self.entry_vars[3].set("")  # Apaga entry para kcl

                # Atualiza os entries na interface gráfica
                self.entry_vars[0].set(f"{Motor_tempo[0]:.2f}")  # Atualiza entry para vazio
                self.entry_vars[1].set(f"{Motor_tempo[1]:.2f}")  # Atualiza entry para cheio
                self.entry_vars[2].set(f"{Motor_tempo[2]:.2f}")  # Atualiza entry para nacl
                self.entry_vars[3].set(f"{Motor_tempo[3]:.2f}")  # Atualiza entry para kcl

                # Imprime os valores lidos
                print(f"Escrevendo valor {Motor_tempo[0]:.2f} (vazio)")
                print(f"Escrevendo valor {Motor_tempo[1]:.2f} (cheio)")
                print(f"Escrevendo valor {Motor_tempo[2]:.2f} (nacl)")
                print(f"Escrevendo valor {Motor_tempo[3]:.2f} (kcl)")

            except Exception as e:
                messagebox.showerror(title="Erro", message=f"Ocorreu um erro ao ler da EEPROM: {e}")
        else:
            # Se a conexão não estiver estabelecida, exibe um erro
            messagebox.showerror("Erro de Conexão", "Nenhuma conexão serial estabelecida.")
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    """

    def read_config(self):
        if self.is_connected_callback and self.is_connected_callback():
            try:
                print("Enviando comando de leitura da EEPROM (0x72)...")
                Motor_tempo = np.zeros(4)
                get_bytes = b'\x72\x00\x00\x00\x00\x00'
                self.frame_esquerdo.conexao_serial.write(get_bytes)
                time.sleep(1)  # Reduzido para 1 segundo para evitar travamento
                self.frame_esquerdo.conexao_serial.reset_input_buffer()  # Limpa o buffer antes de ler
                time.sleep(0.1)  # Pequeno delay para garantir que os dados estejam prontos

                # Verifica se há dados disponíveis antes de ler
                if self.frame_esquerdo.conexao_serial.in_waiting > 0:
                    Motor_tempo[0] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])  # vazio
                    Motor_tempo[1] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])  # cheio
                    Motor_tempo[2] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])  # nacl
                    Motor_tempo[3] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])  # kcl
                else:
                    raise Exception("Nenhum dado recebido do Arduino.")

                # Apaga os entries antes de atualizar
                self.entry_vars[0].set("")  # Apaga entry para vazio
                self.entry_vars[1].set("")  # Apaga entry para cheio
                self.entry_vars[2].set("")  # Apaga entry para nacl
                self.entry_vars[3].set("")  # Apaga entry para kcl

                # Atualiza os entries na interface gráfica
                self.entry_vars[0].set(f"{Motor_tempo[0]:.2f}")  # Atualiza entry para vazio
                self.entry_vars[1].set(f"{Motor_tempo[1]:.2f}")  # Atualiza entry para cheio
                self.entry_vars[2].set(f"{Motor_tempo[2]:.2f}")  # Atualiza entry para nacl
                self.entry_vars[3].set(f"{Motor_tempo[3]:.2f}")  # Atualiza entry para kcl

                # Imprime os valores lidos
                print(f"Escrevendo valor {Motor_tempo[0]:.2f} (vazio)")
                print(f"Escrevendo valor {Motor_tempo[1]:.2f} (cheio)")
                print(f"Escrevendo valor {Motor_tempo[2]:.2f} (nacl)")
                print(f"Escrevendo valor {Motor_tempo[3]:.2f} (kcl)")

            except Exception as e:
                messagebox.showerror(title="Erro", message=f"Ocorreu um erro ao ler da EEPROM: {e}")
        else:
            # Se a conexão não estiver estabelecida, exibe um erro
            messagebox.showerror("Erro de Conexão", "Nenhuma conexão serial estabelecida.")


    def update_temperature(self, serial_data):
        if serial_data.startswith("T"):
            try:
                temperature_value = float(serial_data[1:])
                self.temperatura_textbox.insert(tk.END, f"Temperatura: {temperature_value:.1f} ºC\n")
            except ValueError:
                print("Erro: Formato inválido de temperatura.")

if __name__ == "__main__":
    root = ctk.CTk()
    root.geometry("1000x900")

    class MockFrameEsquerdo:
        class MockSerial:
            def write(self, data):
                print(f"Mock Serial Write: {data}")

            def read(self, size):
                # Simulate reading 4 floats (4 bytes each)
                return struct.pack('f', 10.0)  # Mock value for testing

            @property
            def in_waiting(self):
                return 1

        conexao_serial = MockSerial()

    frame_esquerdo = MockFrameEsquerdo()

    def mock_verificar_conexao():
        return True

    motor_frame = MotorFrame(root, frame_esquerdo, is_connected_callback=mock_verificar_conexao)
    motor_frame.pack(expand=True, fill="both")
    root.mainloop()



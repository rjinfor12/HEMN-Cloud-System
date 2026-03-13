import tkinter as tk
from tkinter import messagebox
import sys

def show_popup():
    root = tk.Tk()
    root.withdraw() # Oculta a janela principal
    root.attributes('-topmost', True) # Força o popup a aparecer em cima de tudo
    
    msg = (
        "HEMN SYSTEM AVISO IMPORTANTE:\n\n"
        "Hoje às 19:30 ocorrerá a recomposição massiva da Base de Dados da Receita Federal (CNPJ).\n\n"
        "Por favor, NÃO DESLIGUE este computador ao final do expediente hoje!\n"
        "O sistema operará a construção pesada do banco (35GB) em segundo plano."
    )
    
    messagebox.showwarning("HEMN SYSTEM - Rotina Agendada", msg)
    root.destroy()

if __name__ == "__main__":
    show_popup()

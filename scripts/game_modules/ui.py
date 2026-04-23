"""Interface inicial em Tkinter."""

import tkinter as tk


def escolher_dificuldade_tkinter():
    """Abre uma pequena janela Tkinter para selecionar dificuldade e movimento."""
    dificuldade = {"valores": None, "tipo_movimento": None, "tipo_verificador": "tecla"}

    def selecionar(valores, tipo_movimento, tipo_verificador):
        dificuldade["valores"] = valores
        dificuldade["tipo_movimento"] = tipo_movimento
        dificuldade["tipo_verificador"] = tipo_verificador
        root.destroy()

    root = tk.Tk()
    root.title("Configuracoes do Jogo")

    tk.Label(root, text="Escolha a Dificuldade:", font=("Arial", 16)).pack(pady=10)

    dificuldades = [
        ("Muito Facil", "green", (5, 5, 120, "muito_facil")),
        ("Facil", "lightgreen", (5, 5, 120, "facil")),
        ("Medio", "khaki", (5, 5, 120)),
        ("Dificil", "salmon", (7, 7, 80)),
        ("Muito Dificil", "red", (10, 10, 60)),
    ]

    dificuldade_var = tk.StringVar()
    for texto, cor, valores in dificuldades:
        tk.Radiobutton(
            root,
            text=texto,
            bg=cor,
            variable=dificuldade_var,
            value=str(valores),
            width=20,
            indicatoron=0,
        ).pack(pady=2)

    tk.Label(root, text="Tipo de Movimento:", font=("Arial", 16)).pack(pady=10)

    tipo_movimento_var = tk.StringVar(value="comando")
    tk.Radiobutton(
        root,
        text="Movimento por Comando (ENTER)",
        variable=tipo_movimento_var,
        value="comando",
    ).pack()
    tk.Radiobutton(
        root,
        text="Movimento Imediato",
        variable=tipo_movimento_var,
        value="direto",
    ).pack()

    tk.Label(root, text="Gatilho do Verificador:", font=("Arial", 16)).pack(pady=10)

    tipo_verificador_var = tk.StringVar(value="tecla")
    tk.Radiobutton(
        root,
        text="Tecla pre-definida",
        variable=tipo_verificador_var,
        value="tecla",
    ).pack()
    tk.Radiobutton(
        root,
        text="QR code com palavra-chave",
        variable=tipo_verificador_var,
        value="qr",
    ).pack()

    def confirmar():
        if dificuldade_var.get():
            valores = eval(dificuldade_var.get())
            tipo = tipo_movimento_var.get()
            tipo_verificador = tipo_verificador_var.get()
            selecionar(valores, tipo, tipo_verificador)

    tk.Button(root, text="Confirmar", command=confirmar, bg="gray").pack(pady=20)

    root.mainloop()
    return (
        dificuldade["valores"],
        dificuldade["tipo_movimento"],
        dificuldade["tipo_verificador"],
    )

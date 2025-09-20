import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ------------------------
# Listes de tamis
# ------------------------
TAMIS_FINS = [5, 4, 2.5, 1.25, 1, 0.8, 0.63, 0.5, 0.4, 0.315, 0.25, 0.2, 0.16, 0.125, 0.08, 0.06, 0]
TAMIS_GROSSIERS = [20, 16, 12.5, 10, 8, 6.3, 5, 4, 2.5, 1.25, 0]

refus_entries = []  # global pour stocker les champs
canvas_graph = None  # pour stocker le canvas matplotlib

# ------------------------
# Mise à jour des champs selon le type de sol
# ------------------------
def update_refus_inputs():
    global refus_entries
    # Effacer anciens champs
    for widget in frame_refus.winfo_children():
        widget.destroy()
    refus_entries = []

    # Récupérer le type de sol
    type_sol = combo_type.get()
    d_tamis = TAMIS_FINS if type_sol == "Sols fins" else TAMIS_GROSSIERS

    # Créer les champs adaptés
    tk.Label(frame_refus, text="Entrer les refus partiels pour chaque tamis :").grid(row=0, column=0, columnspan=2, pady=5)

    for i, d in enumerate(d_tamis, start=1):
        tk.Label(frame_refus, text=f"Tamis {d} mm :").grid(row=i, column=0, padx=5, pady=2, sticky="e")
        e = tk.Entry(frame_refus, width=10)
        e.grid(row=i, column=1, padx=5, pady=2)
        refus_entries.append(e)

# ------------------------
# Fonction principale
# ------------------------
def analyser():
    global canvas_graph
    try:
        masse_initiale = float(entry_masse.get())
    except ValueError:
        messagebox.showerror("Erreur", "Veuillez entrer une masse initiale valide.")
        return
    
    # Choisir la série de tamis
    type_sol = combo_type.get()
    d_tamis = TAMIS_FINS if type_sol == "Sols fins" else TAMIS_GROSSIERS

    refus_partiel = []
    for entry in refus_entries:
        try:
            refus_partiel.append(float(entry.get()))
        except ValueError:
            refus_partiel.append(0.0)

    # Construire le tableau
    df = pd.DataFrame({"D_tamis_mm": d_tamis, "Refus_partiel": refus_partiel})
    df["Refus_cumul"] = df["Refus_partiel"].cumsum()
    df["%Refus_cumul"] = df["Refus_cumul"] / masse_initiale * 100
    df["%Passant"] = 100 - df["%Refus_cumul"]

    # Vérifier la perte
    perte = abs(masse_initiale - df["Refus_partiel"].sum()) / masse_initiale * 100

    # Courbe lissée
    mask = df["D_tamis_mm"] > 0
    x = np.array(df.loc[mask, "D_tamis_mm"])
    y = np.array(df.loc[mask, "%Passant"])
    order = np.argsort(x)
    x_sorted, y_sorted = x[order], y[order]

    x_new = np.logspace(np.log10(min(x_sorted)), np.log10(max(x_sorted)), 300)
    spline = make_interp_spline(np.log10(x_sorted), y_sorted, k=3)
    y_smooth = spline(np.log10(x_new))

    # Supprimer le canvas précédent s'il existe
    if canvas_graph:
        canvas_graph.get_tk_widget().destroy()

    # Supprimer tous les widgets d'entrée et bouton
    for widget in root.winfo_children():
        if widget not in [frame_graph]:
            widget.destroy()

    # Tracé dans Tkinter
    fig, ax = plt.subplots(figsize=(8,6))
    ax.plot(x_new, y_smooth, color="blue", label="Courbe lissée")
    ax.scatter(x_sorted, y_sorted, color="red", marker="o", label="Mesures")
    ax.set_xscale("log")
    ax.grid(True, which="both", linestyle="--", linewidth=0.7)
    ax.set_xlabel("Diamètre du tamis (mm) [log]")
    ax.set_ylabel("% Passant cumulé")
    ax.set_title(f"Courbe granulométrique ({type_sol})\n%Perte = {perte:.3f}%")
    ax.legend()

    canvas_graph = FigureCanvasTkAgg(fig, master=frame_graph)
    canvas_graph.draw()
    canvas_graph.get_tk_widget().pack(fill="both", expand=True)

# ------------------------
# Interface Tkinter
# ------------------------
root = tk.Tk()
root.title("Analyse granulométrique")
root.geometry("900x700")

# Type de sol
tk.Label(root, text="Type de sol :").grid(row=0, column=0, padx=5, pady=5, sticky="w")
combo_type = ttk.Combobox(root, values=["Sols fins", "Sols grossiers"])
combo_type.current(0)
combo_type.grid(row=0, column=1, padx=5, pady=5)
combo_type.bind("<<ComboboxSelected>>", lambda e: update_refus_inputs())

# Masse initiale
tk.Label(root, text="Masse initiale (g) :").grid(row=1, column=0, padx=5, pady=5, sticky="w")
entry_masse = tk.Entry(root)
entry_masse.grid(row=1, column=1, padx=5, pady=5)

# Zone pour les refus
frame_refus = tk.Frame(root)
frame_refus.grid(row=2, column=0, columnspan=2, pady=10)
update_refus_inputs()  # initialiser avec le choix par défaut

# Bouton analyser
btn = tk.Button(root, text="Analyser et tracer la courbe", command=analyser)
btn.grid(row=3, column=0, columnspan=2, pady=10)

# Zone pour le graphique
frame_graph = tk.Frame(root)
frame_graph.grid(row=4, column=0, columnspan=2, pady=10, sticky="nsew")
root.grid_rowconfigure(4, weight=1)
root.grid_columnconfigure(1, weight=1)

root.mainloop()

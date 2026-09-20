import plotly.graph_objects as go

def creer_droite_reels(points, val_ref, min_sub=-10, max_sub=10, step_sub=1, ref_pos=2):
    fig = go.Figure()

    # 1. Axe principal avec flèche à droite
    fig.add_annotation(
        x=max_sub + 0.5, y=0,
        ax=min_sub - 0.5, ay=0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=2.5,
        arrowcolor="gray"
    )

    # 2. Sous-graduations
    for x in range(min_sub, max_sub + 1, step_sub):
        fig.add_shape(
            type="line",
            x0=x, y0=-0.15, x1=x, y1=0.15,
            line=dict(color="gray", width=1.5)
        )

    # 3. Étiquettes sous la droite
    fig.add_annotation(
        x=0, y=-0.35, text="<b>0</b>",
        showarrow=False, font=dict(size=15, color="gray")
    )
    fig.add_annotation(
        x=ref_pos, y=-0.35, text=f"<b>{val_ref}</b>",
        showarrow=False, font=dict(size=15, color="gray")
    )

    # 4. Points à placer
    for lettre, pos in points.items():
        fig.add_shape(
            type="line",
            x0=pos, y0=-0.25, x1=pos, y1=0.25,
            line=dict(color="#E63946", width=3)
        )
        fig.add_annotation(
            x=pos, y=0.45, text=f"<i><b>{lettre}</b></i>",
            showarrow=False, font=dict(size=16, color="#E63946")
        )

    # Configuration du zoom tactile fonctionnel
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode="pan",
        xaxis=dict(
            visible=True,        # ✅ Doit être True pour que Plotly autorise le pinch-zoom mobile
            showticklabels=False,# Masque les chiffres automatiques
            showgrid=False,      # Masque la grille
            zeroline=False,      # Masque la ligne 0 automatique
            range=[min_sub - 1, max_sub + 1.5],
            fixedrange=False     # Autorise le zoom
        ),
        yaxis=dict(
            visible=False,
            range=[-0.8, 0.8],
            fixedrange=True      # Bloque la hauteur
        )
    )

    return fig
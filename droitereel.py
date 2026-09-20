import plotly.graph_objects as go

def creer_droite_reels(points, val_ref, min_sub=-10, max_sub=10, step_sub=1, ref_pos=2):
    """
    Génère une droite des réels épurée avec graduations majeures/mineures.
    """
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

    # 2. Graduations principales vs secondaires
    for x in range(min_sub, max_sub + 1, step_sub):
        # Vérifie si la graduation est un multiple du pas de référence (ex: tous les 2 ou 4 pas)
        est_majeure = (ref_pos != 0) and (x % ref_pos == 0)

        if est_majeure:
            # Trait plus grand, plus épais et plus sombre
            y_min, y_max = -0.22, 0.22
            epaisseur = 2.5
            couleur = "#444444"
        else:
            # Trait secondaire plus petit
            y_min, y_max = -0.12, 0.12
            epaisseur = 1.2
            couleur = "#A0A0A0"

        fig.add_shape(
            type="line",
            x0=x, y0=y_min, x1=x, y1=y_max,
            line=dict(color=couleur, width=epaisseur)
        )

    # 3. Étiquettes sous la droite (0 et Valeur de référence)
    fig.add_annotation(
        x=0, y=-0.38, text="<b>0</b>",
        showarrow=False, font=dict(size=15, color="gray")
    )
    fig.add_annotation(
        x=ref_pos, y=-0.38, text=f"<b>{val_ref}</b>",
        showarrow=False, font=dict(size=15, color="gray")
    )

    # 4. Points à placer (Traits rouges + Lettres)
    for lettre, pos in points.items():
        fig.add_shape(
            type="line",
            x0=pos, y0=-0.28, x1=pos, y1=0.28,
            line=dict(color="#E63946", width=3)
        )
        fig.add_annotation(
            x=pos, y=0.48, text=f"<i><b>{lettre}</b></i>",
            showarrow=False, font=dict(size=16, color="#E63946")
        )

    # Configuration statique et épurée (pas de zoom complexe)
    fig.update_layout(
        height=190,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            visible=False,
            range=[min_sub - 1, max_sub + 1.5],
            fixedrange=True
        ),
        yaxis=dict(
            visible=False,
            range=[-0.8, 0.8],
            fixedrange=True
        )
    )

    return fig
import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from droitereel import creer_droite_reels

# Configuration de la page
st.set_page_config(page_title="Évaluation - Droite des Réels", layout="wide")

# ---------------------------------------------------------
# CHARGEMENT DU FICHIER JSON
# ---------------------------------------------------------
@st.cache_data
def load_questions():
    with open("questions.json", "r", encoding="utf-8") as f:
        return json.load(f)

EXERCICES = load_questions()

# Fonction pour générer une droite des réels interactive (zoomable)
def tracer_droite_reels(exercice):
    min_x = exercice["min_x"]
    max_x = exercice["max_x"]
    
    fig = go.Figure()
    
    # Axe principal
    fig.add_shape(
        type="line",
        x0=min_x, y0=0, x1=max_x, y1=0,
        line=dict(color="black", width=3)
    )
    
    # Placement des points à trouver
    couleurs = ["#FF4B4B", "#1F77B4"]
    for idx, p in enumerate(exercice["points"]):
        c = couleurs[idx % len(couleurs)]
        fig.add_trace(go.Scatter(
            x=[p["valeur_vraie"]],
            y=[0],
            mode="markers+text",
            name=f"Point {p['nom']}",
            text=[f"<b>{p['nom']}</b>"],
            textposition="top center",
            marker=dict(size=14, color=c, symbol="diamond"),
            hoverinfo="text",
            hovertext=f"Point {p['nom']}"
        ))
        
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(
            range=[min_x - (max_x - min_x)*0.05, max_x + (max_x - min_x)*0.05],
            dtick=exercice["step_grad"],
            zeroline=True,
            zerolinecolor="black",
            zerolinewidth=2,
            showgrid=True,
            gridcolor="lightgrey"
        ),
        yaxis=dict(showticklabels=False, showgrid=False, range=[-1, 1], fixedrange=True),
        showlegend=False,
        dragmode="pan"  # Permet le déplacement latéral au doigt/souris
    )
    
    # Configuration du zoom pour mobiles
    config = {'scrollZoom': True, 'displayModeBar': False}
    return fig, config

# ---------------------------------------------------------
# STOCKAGE CENTRALISÉ
# ---------------------------------------------------------
@st.cache_resource
def get_global_database():
    return {
        "scores": {},        # {pseudo: score_total}
        "responses": {},     # {pseudo: {ex_idx: [val1, val2]}}
        "show_correction": False
    }

db = get_global_database()

@st.fragment(run_every=2)
def waiting_screen_fragment():
    if db["show_correction"]:
        st.rerun()
    else:
        st.info("🕒 En attente du lancement de la correction par l'enseignant...")

# Barre latérale : Commutateur Vue Élève / Vue Enseignant
mode = st.sidebar.radio("Mode d'affichage", ["Smartphone Élève", "Écran Projeté (Classement)"])

# ---------------------------------------------------------
# MODE 1 : INTERFACE SMARTPHONE ÉLÈVE
# ---------------------------------------------------------
if mode == "Smartphone Élève":
    st.title("📏 Lecture sur la droite des réels")
    
    already_submitted = st.session_state.get("submitted_pseudo", None)
    
    if already_submitted and already_submitted not in db["scores"]:
        st.session_state.submitted_pseudo = None
        already_submitted = None

    # CAS 1 : CORRECTION ACTIVÉE
    if db["show_correction"]:
        st.header("📝 Correction détaillée")
        
        if already_submitted and already_submitted in db["responses"]:
            score_eleve = db["scores"][already_submitted]
            st.success(f"Score total pour **{already_submitted}** : **{score_eleve} pts / 1000**")
            st.divider()
            
            user_res = db["responses"][already_submitted]
            
            for i, ex in enumerate(EXERCICES):
                st.markdown(f"### {ex['titre']}")
                fig = creer_droite_reels(
                    points=ex["points_pos"], 
                    val_ref=ex["val_ref"], 
                    ref_pos=ex.get("ref_pos", 2)
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                
                resp_eleve = user_res.get(i, [])
                for idx_p, p in enumerate(ex["points"]):
                    val_eleve = resp_eleve[idx_p] if idx_p < len(resp_eleve) else 0.0
                    vrai = p["valeur_vraie"]
                    ecart = abs(val_eleve - vrai)
                    
                    # Tolérance relative selon la taille de l'intervalle
                    amplitude = ex["max_x"] - ex["min_x"]
                    pts = max(0, int(round(100 * max(0, 1 - (ecart / (amplitude * 0.1))))))
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric(f"Votre valeur pour {p['nom']}", f"{val_eleve:.2f}")
                    col2.metric(f"Vraie valeur {p['nom']}", f"{vrai:.2f}")
                    col3.metric("Points", f"+{pts} pts")
                st.divider()
        else:
            st.info("La correction est affichée au tableau.")

    # CAS 2 : ÉLÈVE EN ATTENTE DE CORRECTION
    elif already_submitted and already_submitted in db["scores"]:
        st.success(f"✅ Réponses enregistrées pour **{already_submitted}** !")
        st.info(f"Votre score actuel : **{db['scores'][already_submitted]} pts / 1000**.")
        waiting_screen_fragment()

    # CAS 3 : FORMULAIRE DE SAISIE
    else:
        pseudo = st.text_input("Entrez votre Prénom :", key="user_pseudo")
        
        if pseudo:
            pseudo_clean = pseudo.strip()
            
            if pseudo_clean in db["scores"]:
                st.warning(f"⚠️ Le prénom **{pseudo_clean}** a déjà envoyé ses réponses.")
            else:
                st.subheader(f"Bonjour {pseudo_clean} !")
                st.caption("💡 Astuce : Vous pouvez zoomer et faire glisser la droite des réels avec vos doigts.")
                
                user_answers = {}
                
                for i, ex in enumerate(EXERCICES):
                    st.markdown(f"### {ex['titre']}")
                    
                    fig, config = tracer_droite_reels(ex)
                    st.plotly_chart(fig, config=config, use_container_width=True)
                    
                    answers_ex = []
                    cols = st.columns(len(ex["points"]))
                    for idx_p, p in enumerate(ex["points"]):
                        with cols[idx_p]:
                            val = st.number_input(
                                f"Valeur du point {p['nom']} :",
                                value=0.0,
                                step=ex["step_grad"] / 10,
                                format="%.2f",
                                key=f"ex_{i}_p_{idx_p}"
                            )
                            answers_ex.append(val)
                    
                    user_answers[i] = answers_ex
                    st.divider()
                
                if st.button("Envoyer mes réponses 🚀", type="primary"):
                    score_total = 0
                    
                    for i, ex in enumerate(EXERCICES):
                        amplitude = ex["max_x"] - ex["min_x"]
                        for idx_p, p in enumerate(ex["points"]):
                            est = user_answers[i][idx_p]
                            vrai = p["valeur_vraie"]
                            ecart = abs(est - vrai)
                            # Calcul de points proportionnel à la précision requise
                            pts = max(0, int(round(100 * max(0, 1 - (ecart / (amplitude * 0.1))))))
                            score_total += pts
                    
                    db["scores"][pseudo_clean] = score_total
                    db["responses"][pseudo_clean] = user_answers
                    st.session_state.submitted_pseudo = pseudo_clean
                    st.rerun()

# ---------------------------------------------------------
# MODE 2 : ÉCRAN PROJETÉ (VIDÉOPROJECTEUR)
# ---------------------------------------------------------
else:
    st.title("🏆 Classement en direct")
    
    if db["scores"]:
        df = pd.DataFrame(
            list(db["scores"].items()), 
            columns=["Élève", "Score Total (/1000)"]
        )
        df = df.sort_values(by="Score Total (/1000)", ascending=False).reset_index(drop=True)
        df.index += 1
        st.dataframe(df, use_container_width=True, height=300)
    else:
        st.info("En attente des réponses...")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Rafraîchir"):
            st.rerun()
    with col2:
        btn_label = "🙈 Masquer la correction" if db["show_correction"] else "👁️ Afficher la correction"
        if st.button(btn_label):
            db["show_correction"] = not db["show_correction"]
            st.rerun()
    with col3:
        if st.button("🗑️ Réinitialiser tout"):
            db["scores"].clear()
            db["responses"].clear()
            db["show_correction"] = False
            st.rerun()

    if db["show_correction"]:
        st.divider()
        st.subheader("📊 Correction générale")
        for i, ex in enumerate(EXERCICES):
            st.markdown(f"#### {ex['titre']}")
            fig, config = tracer_droite_reels(ex)
            st.plotly_chart(fig, config=config, use_container_width=True)
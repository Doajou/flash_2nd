import streamlit as st
import pandas as pd
import json
from droitereel import creer_droite_reels

# Configuration de la page
st.set_page_config(page_title="Évaluation - Droite des Réels", layout="wide")

# ---------------------------------------------------------
# CHARGEMENT DU JSON
# ---------------------------------------------------------
@st.cache_data
def load_questions():
    try:
        with open("questions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return [ex for ex in data if "points_pos" in ex and "val_ref" in ex and "reponses_exactes" in ex]
    except Exception as e:
        st.error(f"Erreur de lecture du fichier questions.json : {e}")
        return []

EXERCICES = load_questions()

# ---------------------------------------------------------
# STOCKAGE CENTRALISÉ
# ---------------------------------------------------------
@st.cache_resource
def get_global_database():
    return {
        "scores": {},        # {pseudo: score_total}
        "responses": {},     # {pseudo: {ex_idx: {lettre: valeur}}}
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
            st.success(f"Note finale pour **{already_submitted}** : **{score_eleve} / 5**")
            st.divider()
            
            user_res = db["responses"][already_submitted]
            
            for i, ex in enumerate(EXERCICES):
                st.markdown(f"### Exercice {ex.get('id', i+1)}")
                
                fig = creer_droite_reels(
                    points=ex.get("points_pos", {}), 
                    val_ref=ex.get("val_ref", "1"), 
                    ref_pos=ex.get("ref_pos", 2)
                )
                st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False, 'doubleClick': "reset"})
                
                resp_eleve = user_res.get(i, {})
                exactes = ex.get("reponses_exactes", {})
                
                cols = st.columns(len(exactes))
                for idx, (lettre, vrai) in enumerate(exactes.items()):
                    val_eleve = resp_eleve.get(lettre, 0.0)
                    ecart = abs(val_eleve - vrai)
                    pts = 0.5 if ecart < 1e-4 else 0.0
                    
                    with cols[idx]:
                        st.metric(f"Point {lettre}", f"{val_eleve}", delta=f"Vrai: {vrai}")
                        if pts > 0:
                            st.caption("✅ Correct (+0.5 pt)")
                        else:
                            st.caption("❌ Incorrect (0 pt)")
                st.divider()
        else:
            st.info("La correction est affichée au tableau.")

    # CAS 2 : ÉLÈVE EN ATTENTE DE CORRECTION (NOTE MASQUÉE)
    elif already_submitted and already_submitted in db["scores"]:
        st.success(f"✅ Réponses enregistrées pour **{already_submitted}** !")
        st.info("Vos réponses ont bien été transmises. La note s'affichera dès que la correction sera lancée.")
        waiting_screen_fragment()

    # CAS 3 : FORMULAIRE DE SAISIE
    else:
        if not EXERCICES:
            st.warning("⚠️ Aucune question chargée.")
        else:
            pseudo = st.text_input("Entrez votre Prénom :", key="user_pseudo")
            
            if pseudo:
                pseudo_clean = pseudo.strip()
                
                if pseudo_clean in db["scores"]:
                    st.warning(f"⚠️ Le prénom **{pseudo_clean}** a déjà envoyé ses réponses.")
                else:
                    st.subheader(f"Bonjour {pseudo_clean} !")
                    user_answers = {}
                    
                    for i, ex in enumerate(EXERCICES):
                        st.markdown(f"### Exercice {ex.get('id', i+1)}")
                        
                        fig = creer_droite_reels(
                            points=ex.get("points_pos", {}), 
                            val_ref=ex.get("val_ref", "1"), 
                            ref_pos=ex.get("ref_pos", 2)
                        )
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                        answers_ex = {}
                        points_pos = ex.get("points_pos", {})
                        
                        if points_pos:
                            cols = st.columns(len(points_pos))
                            for idx_p, (lettre, pos) in enumerate(points_pos.items()):
                                with cols[idx_p]:
                                    val = st.number_input(
                                        f"Point {lettre} :",
                                        value=0.0,
                                        step=0.001,
                                        format="%g",
                                        key=f"ex_{i}_p_{lettre}"
                                    )
                                    answers_ex[lettre] = val
                        
                        user_answers[i] = answers_ex
                        st.divider()
                    
                    if st.button("Envoyer mes réponses 🚀", type="primary"):
                        score_total = 0.0
                        
                        for i, ex in enumerate(EXERCICES):
                            exactes = ex.get("reponses_exactes", {})
                            for lettre, vrai in exactes.items():
                                est = user_answers[i].get(lettre, 0.0)
                                if abs(est - vrai) < 1e-4:
                                    score_total += 0.5
                        
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
            columns=["Élève", "Note (/5)"]
        )
        df = df.sort_values(by="Note (/5)", ascending=False).reset_index(drop=True)
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
            st.markdown(f"#### Exercice {ex.get('id', i+1)}")
            fig = creer_droite_reels(
                points=ex.get("points_pos", {}), 
                val_ref=ex.get("val_ref", "1"), 
                ref_pos=ex.get("ref_pos", 2)
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
import streamlit as st
import json
from datetime import datetime, date
from firebase_client import charger_data, sauvegarder_data

# Charger les données Firebase
data = charger_data()

# ---------- Utils ----------

def convertir_minutes(minutes):
    heures = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{heures}h{mins:02d}"

def temps_par_page(format_livre, profil):
    if format_livre == "poche":
        return profil["poche_sec"] / 60.0
    else:
        return profil["grand_sec"] / 60.0

def calcul_lecture(livre, profil):
    aujourd_hui = date.today()
    deadline = datetime.strptime(livre["echeance"], "%Y-%m-%d").date()

    if deadline <= aujourd_hui:
        return {"error": "La date limite doit être dans le futur."}

    pages_restantes = livre["pages_total"] - livre["pages_lues"]
    if pages_restantes <= 0:
        return {
            "done": True,
            "pages_restantes": 0,
            "jours_restants": 0,
            "pages_par_jour": 0,
            "temps_par_jour": 0
        }

    jours_restants = (deadline - aujourd_hui).days
    pages_par_jour = pages_restantes / jours_restants
    minutes_par_page = temps_par_page(livre["format"], profil)
    temps_par_jour = pages_par_jour * minutes_par_page

    return {
        "done": False,
        "pages_restantes": pages_restantes,
        "jours_restants": jours_restants,
        "pages_par_jour": pages_par_jour,
        "temps_par_jour": temps_par_jour,
        "temps_humain": convertir_minutes(temps_par_jour)
    }

# ---------- UI ----------

st.set_page_config(
    page_title="Lectures en cours",
    page_icon="📚",
    layout="wide"
)

st.sidebar.title("📚 Lectures en cours")
page = st.sidebar.radio(
    "Navigation",
    ["Lectures en cours", "Profils utilisateurs"]
)

# ---------- Page : Profils ----------

def page_profils():
    st.title("👤 Profils utilisateurs")

    col_list, col_form = st.columns([1, 1.2])

    with col_list:
        st.subheader("Profils existants")
        if not data["profils"]:
            st.info("Aucun profil pour l'instant.")
        else:
            for i, p in enumerate(data["profils"]):
                with st.expander(f"{p['nom']}"):
                    st.write(f"• Temps/page poche : {p['poche_sec']} sec")
                    st.write(f"• Temps/page grand format : {p['grand_sec']} sec")
                    cols_btn = st.columns(2)
                    with cols_btn[0]:
                        if st.button("Modifier", key=f"mod_{i}"):
                            st.session_state["profil_edit_index"] = i
                    with cols_btn[1]:
                        if st.button("Supprimer", key=f"del_{i}"):
                            del data["profils"][i]
                            sauvegarder_data(data)
                            st.rerun()

    with col_form:
        st.subheader("Ajouter / modifier un profil")

        edit_index = st.session_state.get("profil_edit_index", None)
        if edit_index is not None:
            profil = data["profils"][edit_index]
            mode = "Modification"
            default_nom = profil["nom"]
            default_poche = profil["poche_sec"]
            default_grand = profil["grand_sec"]
        else:
            mode = "Création"
            default_nom = ""
            default_poche = 45
            default_grand = 60

        st.markdown(f"**Mode : {mode}**")

        nom = st.text_input("Nom du profil", value=default_nom)
        poche_sec = st.number_input("Temps/page poche (sec)", min_value=1, max_value=600, value=default_poche)
        grand_sec = st.number_input("Temps/page grand format (sec)", min_value=1, max_value=600, value=default_grand)

        cols = st.columns(2)
        with cols[0]:
            if st.button("Enregistrer le profil"):
                if nom.strip() == "":
                    st.error("Le nom ne peut pas être vide.")
                else:
                    nouveau = {
                        "nom": nom.strip(),
                        "poche_sec": int(poche_sec),
                        "grand_sec": int(grand_sec)
                    }
                    if edit_index is not None:
                        data["profils"][edit_index] = nouveau
                        st.session_state["profil_edit_index"] = None
                    else:
                        data["profils"].append(nouveau)
                    sauvegarder_data(data)
                    st.success("Profil enregistré.")
                    st.rerun()

        with cols[1]:
            if edit_index is not None:
                if st.button("Annuler la modification"):
                    st.session_state["profil_edit_index"] = None
                    st.rerun()

# ---------- Page : Lectures ----------

def page_lectures():
    st.title("📘 Lectures en cours")

    col_left, col_right = st.columns([1.2, 1])

    # --- Liste des livres ---
    with col_left:
        st.subheader("Mes livres")

        if not data["livres"]:
            st.info("Aucun livre pour l'instant. Ajoute-en un à droite.")
        else:
            for i, livre in enumerate(data["livres"]):
                profil_nom = livre.get("profil") or "Aucun profil"
                with st.expander(f"{livre['titre']}"):
                    st.write(f"• Pages totales : {livre['pages_total']}")
                    st.write(f"• Format : {livre['format']}")
                    st.write(f"• Pages lues : {livre['pages_lues']}")
                    st.write(f"• Échéance : {livre['echeance']}")
                    st.write(f"• Profil utilisé : {profil_nom}")

                    cols = st.columns(3)
                    with cols[0]:
                        if st.button("Ouvrir", key=f"open_{i}"):
                            st.session_state["livre_open_index"] = i
                            st.rerun()
                    with cols[1]:
                        if st.button("Supprimer", key=f"del_book_{i}"):
                            del data["livres"][i]
                            sauvegarder_data(data)
                            st.rerun()

    # --- Ajout de livre ---
    with col_right:
        st.subheader("Ajouter un livre")

        titre = st.text_input("Titre du livre")
        pages_total = st.number_input("Pages totales", min_value=1, max_value=10000, value=300)
        format_livre = st.radio("Format", ["Poche", "Grand format"], horizontal=True)
        echeance = st.date_input("Échéance", value=date.today())

        if st.button("Ajouter ce livre"):
            if titre.strip() == "":
                st.error("Le titre ne peut pas être vide.")
            else:
                nouveau = {
                    "titre": titre.strip(),
                    "pages_total": int(pages_total),
                    "format": format_livre,
                    "pages_lues": 0,
                    "echeance": echeance.strftime("%Y-%m-%d"),
                    "profil": None
                }
                data["livres"].append(nouveau)
                sauvegarder_data(data)
                st.success("Livre ajouté.")
                st.rerun()

    # --- Fiche du livre sélectionné ---
    if "livre_open_index" in st.session_state:
        idx = st.session_state["livre_open_index"]
        if 0 <= idx < len(data["livres"]):
            livre = data["livres"][idx]

            st.markdown("---")
            st.header(f"📖 Fiche du livre : {livre['titre']}")

            cols_top = st.columns(3)
            with cols_top[0]:
                st.write(f"**Pages totales :** {livre['pages_total']}")
            with cols_top[1]:
                st.write(f"**Format :** {livre['format']}")
            with cols_top[2]:
                st.write(f"**Échéance :** {livre['echeance']}")

            profils_noms = [p["nom"] for p in data["profils"]]
            if not profils_noms:
                st.warning("Aucun profil disponible. Va en créer un dans l’onglet Profils.")
                return

            profil_nom = st.selectbox(
                "Profil utilisé",
                options=profils_noms,
                index=profils_noms.index(livre["profil"]) if livre.get("profil") in profils_noms else 0
            )

            pages_lues = st.number_input(
                "Pages déjà lues",
                min_value=0,
                max_value=livre["pages_total"],
                value=livre["pages_lues"]
            )

            nouvelle_echeance = st.date_input(
                "Nouvelle échéance",
                value=datetime.strptime(livre["echeance"], "%Y-%m-%d").date()
            )

            if st.button("Calculer le planning pour ce livre"):
                livre["pages_lues"] = int(pages_lues)
                livre["echeance"] = nouvelle_echeance.strftime("%Y-%m-%d")
                livre["profil"] = profil_nom
                sauvegarder_data(data)

                profil = next(p for p in data["profils"] if p["nom"] == profil_nom)
                result = calcul_lecture(livre, profil)

                if "error" in result:
                    st.error(result["error"])
                elif result["done"]:
                    st.success("Tu as déjà fini ce livre 🎉")
                else:
                    st.success("Planning calculé :")
                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        st.write(f"• Pages restantes : **{result['pages_restantes']}**")
                        st.write(f"• Jours restants : **{result['jours_restants']}**")
                    with col_res2:
                        st.write(f"• Pages/jour : **{result['pages_par_jour']:.2f}**")
                        st.write(f"• Temps/jour : **{result['temps_humain']}**")

# ---------- Router ----------

if page == "Profils utilisateurs":
    page_profils()
else:
    page_lectures()

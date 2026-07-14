import streamlit as st

from frontend import services as api
from frontend.pages.workspace._shared import SECTION_HEIGHT
from frontend.utils.session import select_chat


def _chats_panel(token: str, project_id: str):
    st.markdown(
        "<p style='color:#9B97C9; font-size:.8rem; text-transform:uppercase; "
        "letter-spacing:.08em; margin-bottom:.5rem;'>💬 Chats</p>",
        unsafe_allow_html=True,
    )

    if st.button("▶ Start a Chat", use_container_width=True, key="new_chat_btn"):
        try:
            chat = api.create_chat(token, project_id)
            select_chat(chat["id"], chat["name"])
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    with st.container(height=SECTION_HEIGHT):
        try:
            chats = api.list_chats(token, project_id)
        except RuntimeError as e:
            st.error(str(e))
            return

        if not chats:
            st.caption("No chats yet.")
            return

        active_id = st.session_state.get("active_chat_id")

        for chat in chats:
            cid   = chat["id"]
            cname = chat["name"]
            is_active = cid == active_id

            btn_label = f"{'▶ ' if is_active else ''}{cname}"
            if st.button(btn_label, key=f"chat_btn_{cid}", use_container_width=True):
                select_chat(cid, cname)
                st.rerun()

            if is_active:
                rc1, rc2 = st.columns(2)
                with rc1:
                    if st.button("Rename", key=f"rename_chat_{cid}", use_container_width=True,
                                 help="Rename chat"):
                        st.session_state[f"renaming_chat_{cid}"] = True
                        st.rerun()
                with rc2:
                    if st.button("Delete", key=f"del_chat_{cid}", use_container_width=True,
                                 help="Delete chat"):
                        st.session_state[f"confirm_del_chat_{cid}"] = True
                        st.rerun()

                if st.session_state.get(f"renaming_chat_{cid}"):
                    with st.form(f"rename_chat_form_{cid}", clear_on_submit=True):
                        new_name = st.text_input("New name", value=cname)
                        cs, cc = st.columns(2)
                        with cs:
                            save = st.form_submit_button("Save", type="primary",
                                                         use_container_width=True)
                        with cc:
                            cancel = st.form_submit_button("Cancel", use_container_width=True)
                    if save and new_name.strip(): # type: ignore
                        try:
                            api.rename_chat(token, cid, new_name.strip()) # type: ignore
                            select_chat(cid, new_name.strip()) # type: ignore
                            del st.session_state[f"renaming_chat_{cid}"]
                            st.rerun()
                        except RuntimeError as e:
                            st.error(str(e))
                    if cancel:
                        del st.session_state[f"renaming_chat_{cid}"]
                        st.rerun()

                if st.session_state.get(f"confirm_del_chat_{cid}"):
                    st.warning(f"Delete **{cname}**?")
                    cy, cn = st.columns(2)
                    with cy:
                        if st.button("Yes", key=f"yes_del_chat_{cid}",
                                     type="primary", use_container_width=True):
                            try:
                                api.delete_chat(token, cid)
                                st.session_state.active_chat_id = None
                                st.session_state.chat_histories.pop(cid, None)
                                del st.session_state[f"confirm_del_chat_{cid}"]
                                st.rerun()
                            except RuntimeError as e:
                                st.error(str(e))
                    with cn:
                        if st.button("No", key=f"no_del_chat_{cid}", use_container_width=True):
                            del st.session_state[f"confirm_del_chat_{cid}"]
                            st.rerun()

            st.markdown(
                "<hr style='border-color:#2A2D3E; margin:.3rem 0;'>",
                unsafe_allow_html=True,
            )
from datetime import datetime
import os
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, storage

# ==========================================
# CONFIGURAÇÃO INTELIGENTE DO FIREBASE
# ==========================================
@st.cache_resource
def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            arquivo_json = "serviceAccountKey.json"
            if os.path.exists(arquivo_json):
                cred = credentials.Certificate(arquivo_json)
            else:
                cred_dict = dict(st.secrets["firebase"])
                if "private_key" in cred_dict:
                    pk = cred_dict["private_key"].strip()
                    if "\\n" in pk:
                        pk = pk.replace("\\n", "\n")
                    cred_dict["private_key"] = pk
                cred = credentials.Certificate(cred_dict)

            # ATENÇÃO: Substitua pelo seu Storage Bucket real, ex: 'projeto.firebasestorage.app' ou '.appspot.com'
            app = firebase_admin.initialize_app(cred, {
                'storageBucket': 'seu-projeto.appspot.com' 
            })
            return app
        except Exception as e:
            st.error(f"Erro crítico ao inicializar o Firebase: {e}")
            return None
    else:
        return firebase_admin.get_app()

app_firebase = inicializar_firebase()

if app_firebase:
    db = firestore.client()
else:
    st.stop()

# ==========================================
# FUNÇÕES DE BANCO DE DADOS (FIRESTORE)
# ==========================================
def carregar_dados():
    estrutura_padrao = {
        "Atestados": [],
        "Guias_Planos": [],
        "Solicitacoes": [],
        "Comunicados": [],
        "usuarios": []
    }
    try:
        doc_ref = db.collection("sistema_escolar").document("dados_gerais")
        doc = doc_ref.get()
        if doc.exists:
            dados = doc.to_dict()
            for chave in estrutura_padrao:
                if chave not in dados:
                    dados[chave] = []
            return dados
        else:
            doc_ref.set(estrutura_padrao)
            return estrutura_padrao
    except Exception as e:
        st.error(f"Erro ao carregar dados do Firebase: {e}")
        return estrutura_padrao

def salvar_dados(dados):
    try:
        doc_ref = db.collection("sistema_escolar").document("dados_gerais")
        doc_ref.set(dados)
    except Exception as e:
        st.error(f"Erro ao salvar dados no Firebase: {e}")

def verificar_credenciais(login_informado, senha_informada, dados_sistema):
    try:
        lista_usuarios = dados_sistema.get("usuarios", [])
        if not lista_usuarios:
            st.warning("⚠️ Nenhum utilizador encontrado na lista de dados gerais.")
            return False
            
        login_limpo = str(login_informado).strip()
        senha_limpa = str(senha_informada).strip()
        
        for user in lista_usuarios:
            db_login = str(user.get("login", "")).strip()
            db_senha = str(user.get("senha", "")).strip()
            
            if db_login == login_limpo and db_senha == senha_limpa:
                return True
                
        return False
    except Exception as e:
        st.error(f"Erro ao validar credenciais: {e}")
        return False

# ==========================================
# CONFIGURAÇÃO DA INTERFACE (STREAMLIT)
# ==========================================
st.set_page_config(
    page_title="Comunicação Escolar",
    page_icon="🏫",
    layout="centered"
)

# Carrega os dados gerais do sistema logo no início (incluindo utilizadores)
dados = carregar_dados()

# Inicializa o estado de autenticação
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# ==========================================
# TELA DE LOGIN
# ==========================================
if not st.session_state.autenticado:
    st.title("🏫 Comunicação Escolar")
    #st.markdown("Por favor, faça login para aceder ao sistema.")
    
    with st.form("form_login"):
        login_input = st.text_input("Login")
        senha_input = st.text_input("Senha", type="password")
        submit_login = st.form_submit_button("Entrar")
        
        if submit_login:
            if verificar_credenciais(login_input, senha_input, dados):
                st.session_state.autenticado = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Login ou senha incorretos.")
    
    st.stop()

# ==========================================
# APLICATIVO PRINCIPAL (APÓS LOGIN)
# ==========================================
#st.title("🏫 Comunicação Escolar")

opcoes_menu = {
    "📢 Comunicados": "Comunicados",
    "📋 Licenças e Atestados": "Atestados",
    "📁 Pedagógico (Impressões, Provas, Guias)": "Guias_Planos",
    "📩 Solicitações": "Solicitacoes"
}

opcao_selecionada = st.sidebar.radio(
    "Selecione uma Categoria:",
    list(opcoes_menu.keys()),
    index=0
)

st.sidebar.markdown("---")
if st.sidebar.button("🔒 Sair do Sistema", use_container_width=True):
    st.session_state.autenticado = False
    st.rerun()

tipo_chave = opcoes_menu[opcao_selecionada]
itens = dados[tipo_chave]

# ==========================================
# CABEÇALHO E BOTÃO DE CADASTRO LADO A LADO
# ==========================================
col_titulo, col_botao = st.columns([3, 1])

with col_titulo:
    st.header(f"{opcao_selecionada}")

with col_botao:
    st.write("") 
    mostrar_form = st.button("Cadastrar (+)", use_container_width=True)

if "form_visivel" not in st.session_state:
    st.session_state.form_visivel = False

if mostrar_form:
    st.session_state.form_visivel = not st.session_state.form_visivel

# ==========================================
# SEÇÃO 1: FORMULÁRIO DE NOVO CADASTRO
# ==========================================
if st.session_state.form_visivel:
    with st.container(border=True):
        with st.form(key=f"form_{tipo_chave}", clear_on_submit=True):

            if tipo_chave == "Atestados":
                col1, col2 = st.columns(2)
                with col1:
                    data_inicio = st.text_input("Data Início (DD/MM/AAAA)", value=datetime.today().strftime("%d/%m/%Y"))
                with col2:
                    data_fim = st.text_input("Data Fim (DD/MM/AAAA)", value=datetime.today().strftime("%d/%m/%Y"))
                solicitante = st.text_input("Solicitante")
                observacao = st.text_area("Observação")
                componente = docente = bimestre_ano = None
                uploaded_file = st.file_uploader("Envio de Arquivo (Opcional)", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"])

            elif tipo_chave == "Guias_Planos":
                componente = st.text_input("Componente Curricular")
                docente = st.text_input("Docente")
                bimestre_ano = st.text_input("Bimestre / Ano (Ex: 1º Bimestre / 2026 ou 2026)")
                observacao = st.text_area("Observação (Opcional)")
                uploaded_file = st.file_uploader("Envio de Arquivo", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"])
                solicitante = docente
                data_inicio = data_fim = None

            else:
                solicitante = st.text_input("Solicitante / Comunicante")
                observacao = st.text_area("Observação")
                uploaded_file = st.file_uploader("Envio de Arquivo (Opcional)", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"])
                data_inicio = data_fim = componente = docente = bimestre_ano = None

            submit_button = st.form_submit_button(label="Salvar Registro")

            if submit_button:
                if solicitante:
                    url_arquivo_firebase = None

                    if uploaded_file is not None:
                        try:
                            bucket = storage.bucket()
                            nome_blob = f"uploads/{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
                            blob = bucket.blob(nome_blob)
                            blob.upload_from_file(uploaded_file, content_type=uploaded_file.type)
                            blob.make_public()
                            url_arquivo_firebase = blob.public_url
                        except Exception as e:
                            st.error(f"Erro ao enviar arquivo para o Firebase Storage: {e}")

                    registro = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "solicitante": solicitante,
                        "observacao": observacao,
                        "data_inicio": data_inicio,
                        "data_fim": data_fim,
                        "componente": componente,
                        "docente": docente,
                        "bimestre_ano": bimestre_ano,
                        "arquivo_url": url_arquivo_firebase
                    }

                    dados[tipo_chave].append(registro)
                    salvar_dados(dados)
                    st.session_state.form_visivel = False
                    st.success("Registro salvo com sucesso!")
                    st.rerun()
                else:
                    st.error("Por favor, preencha o campo do responsável/solicitante.")

st.markdown("---")

# ==========================================
# SEÇÃO 2: CONSULTA DE REGISTROS
# ==========================================
if not itens:
    st.info(f"Nenhum registro encontrado em '{opcao_selecionada}'.")
else:
    for item in reversed(itens):
        with st.container():
            # Exibe apenas o nome e a data (ID ocultado)
            st.markdown(f"**👤 {item['solicitante']}** — *Cadastrado em: {item['data_registro']}*")

            if tipo_chave == "Atestados":
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"📅 **Início:** {item.get('data_inicio')}")
                with col_b:
                    st.write(f"📅 **Fim:** {item.get('data_fim')}")
                if item.get('observacao'):
                    st.write(f"💬 **Observação:** {item.get('observacao')}")

            elif tipo_chave == "Guias_Planos":
                st.write(f"📚 **Componente:** {item.get('componente')}")
                st.write(f"👨‍🏫 **Docente:** {item.get('docente')}")
                st.write(f"📆 **Bimestre/Ano:** {item.get('bimestre_ano')}")
                if item.get('observacao'):
                    st.write(f"💬 **Observação:** {item.get('observacao')}")

            else:
                if item.get('observacao'):
                    st.write(f"💬 **Observação:** {item.get('observacao')}")

            # Exibe o link do arquivo apenas se houver arquivo anexado (caso contrário, não mostra nada)
            if item.get("arquivo_url"):
                st.markdown(f"📥 **Arquivo Anexado:** [Baixar Arquivo]({item.get('arquivo_url')})")

            st.markdown("---")
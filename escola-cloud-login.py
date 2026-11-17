from datetime import datetime
import os
import streamlit as st
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÃO DA INTERFACE & APK WEBVIEW
# ==========================================
st.set_page_config(
    page_title="Comunicação Escolar",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="auto"
)

# CSS otimizado para Android WebView + Espaço reservado para Banner AdMob no rodapé
st.markdown("""
    <style>
    /* Reserva espaço na parte inferior para que o Banner nativo do AdMob no APK não cubra o conteúdo */
    .main .block-container {
        padding-bottom: 95px !important;
    }

    /* Ajustes de usabilidade para telas de smartphones (Android) */
    @media (max-width: 768px) {
        .stButton button {
            width: 100%;
            min-height: 44px; /* Tamanho mínimo ideal para toque */
        }
        .stColumns {
            flex-direction: column;
        }
    }

    /* Estilização limpa do bloco de anúncio interno */
    .ad-container {
        margin-top: 20px;
        margin-bottom: 15px;
        padding: 10px;
        border: 1px dashed #d0d7de;
        border-radius: 8px;
        background-color: #f6f8fa;
        text-align: center;
    }
    .ad-label {
        font-size: 10px;
        text-transform: uppercase;
        color: #57606a;
        letter-spacing: 1px;
        margin-bottom: 6px;
        display: block;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONFIGURAÇÃO DO SUPABASE
# ==========================================
@st.cache_resource
def inicializar_supabase() -> Client | None:
    try:
        url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
        if not url or not key:
            st.error("⚠️ Credenciais do Supabase não encontradas nos segredos do sistema.")
            return None
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro crítico ao inicializar o cliente Supabase: {e}")
        return None

supabase = inicializar_supabase()

if not supabase:
    st.stop()

BUCKET_NAME = "uploads"
TABELA_SISTEMA = "sistema_escolar"
DOC_ID = "dados_gerais"

# ==========================================
# FUNÇÕES DE BANCO DE DADOS (SUPABASE)
# ==========================================
def carregar_dados() -> dict:
    estrutura_padrao = {
        "Atestados": [],
        "Guias_Planos": [],
        "Solicitacoes": [],
        "Comunicados": [],
        "Reunioes_Conselhos": [],
        "usuarios": []
    }
    try:
        resposta = supabase.table(TABELA_SISTEMA).select("dados").eq("id", DOC_ID).execute()
        if resposta.data and len(resposta.data) > 0:
            dados = resposta.data[0].get("dados", {})
            # Garante integridade de chaves caso o schema seja atualizado
            for chave in estrutura_padrao:
                if chave not in dados:
                    dados[chave] = []
            return dados
        else:
            supabase.table(TABELA_SISTEMA).insert({"id": DOC_ID, "dados": estrutura_padrao}).execute()
            return estrutura_padrao
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")
        return estrutura_padrao

def salvar_dados(dados: dict):
    try:
        supabase.table(TABELA_SISTEMA).upsert({"id": DOC_ID, "dados": dados}).execute()
    except Exception as e:
        st.error(f"Erro ao salvar dados no Supabase: {e}")

def verificar_credenciais(login_informado, senha_informada, dados_sistema) -> bool:
    try:
        lista_usuarios = dados_sistema.get("usuarios", [])
        if not lista_usuarios:
            st.warning("⚠️ Nenhum utilizador cadastrado no sistema.")
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

def renderizar_bloco_anuncio():
    """Renderiza um bloco de publicidade seguro para WebView e aderente às políticas."""
    st.markdown("""
        <div class="ad-container">
            <span class="ad-label">Publicidade</span>
            <a href="https://seu-link-patrocinador.com" target="_blank" style="text-decoration: none; color: #24292f;">
                <div style="font-size: 13px; font-weight: bold;">📚 Soluções Educacionais & Parcerias</div>
                <div style="font-size: 11px; color: #57606a;">Toque para conhecer materiais e conteúdos pedagógicos.</div>
            </a>
        </div>
    """, unsafe_allow_html=True)

# Carregamento inicial dos dados globais
dados = carregar_dados()

# Inicialização de sessão
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# ==========================================
# TELA DE LOGIN
# ==========================================
if not st.session_state.autenticado:
    st.title("🏫 Comunicação Escolar")
    
    with st.form("form_login"):
        login_input = st.text_input("Login")
        senha_input = st.text_input("Senha", type="password")
        submit_login = st.form_submit_button("Entrar", use_container_width=True)
        
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
opcoes_menu = {
    "📢 Comunicados": "Comunicados",
    "📋 Licenças e Atestados": "Atestados",
    "📁 Pedagógico (Impressões, Provas, Guias)": "Guias_Planos",
    "📅 Reuniões e Conselhos": "Reunioes_Conselhos",
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

# Bloco de anúncio lateral discreto
with st.sidebar:
    renderizar_bloco_anuncio()

tipo_chave = opcoes_menu[opcao_selecionada]
itens = dados.get(tipo_chave, [])

# ==========================================
# CABEÇALHO E BOTÃO DE CADASTRO
# ==========================================
col_titulo, col_botao = st.columns([2.5, 1.5])

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

            data_inicio = data_fim = componente = docente = bimestre_ano = solicitante = observacao = None
            uploaded_file = None

            if tipo_chave == "Atestados":
                col1, col2 = st.columns(2)
                with col1:
                    data_inicio = st.text_input("Data Início (DD/MM/AAAA)", value=datetime.today().strftime("%d/%m/%Y"))
                with col2:
                    data_fim = st.text_input("Data Fim (DD/MM/AAAA)", value=datetime.today().strftime("%d/%m/%Y"))
                solicitante = st.text_input("Solicitante")
                observacao = st.text_area("Observação")
                uploaded_file = st.file_uploader("Envio de Arquivo (Opcional)", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"])

            elif tipo_chave == "Guias_Planos":
                componente = st.text_input("Componente Curricular")
                docente = st.text_input("Docente")
                bimestre_ano = st.text_input("Bimestre / Ano (Ex: 1º Bimestre / 2026 ou 2026)")
                observacao = st.text_area("Observação (Opcional)")
                uploaded_file = st.file_uploader("Envio de Arquivo", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"])
                solicitante = docente

            elif tipo_chave == "Reunioes_Conselhos":
                solicitante = st.text_input("Responsável / Organizador")
                data_inicio = st.text_input("Data da Reunião (DD/MM/AAAA)", value=datetime.today().strftime("%d/%m/%Y"))
                observacao = st.text_area("Pauta / Ata / Observações")
                uploaded_file = st.file_uploader("Documento Anexo (Ata/Pauta - Opcional)", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"])

            else: # Comunicados e Solicitações
                solicitante = st.text_input("Solicitante / Comunicante")
                observacao = st.text_area("Observação")
                uploaded_file = st.file_uploader("Envio de Arquivo (Opcional)", type=["pdf", "doc", "docx", "png", "jpg", "jpeg"])

            submit_button = st.form_submit_button(label="Salvar Registro", use_container_width=True)

            if submit_button:
                if solicitante and str(solicitante).strip() != "":
                    url_arquivo_supabase = None

                    if uploaded_file is not None:
                        try:
                            caminho_arquivo = f"registros/{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"
                            bytes_arquivo = uploaded_file.getvalue()
                            
                            supabase.storage.from_(BUCKET_NAME).upload(
                                path=caminho_arquivo,
                                file=bytes_arquivo,
                                file_options={"content-type": uploaded_file.type}
                            )
                            url_resp = supabase.storage.from_(BUCKET_NAME).get_public_url(caminho_arquivo)
                            url_arquivo_supabase = url_resp
                        except Exception as e:
                            st.error(f"Erro ao enviar arquivo para o Supabase Storage: {e}")

                    registro = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "solicitante": str(solicitante).strip(),
                        "observacao": str(observacao).strip() if observacao else "",
                        "data_inicio": data_inicio,
                        "data_fim": data_fim,
                        "componente": componente,
                        "docente": docente,
                        "bimestre_ano": bimestre_ano,
                        "arquivo_url": url_arquivo_supabase
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
    for idx, item in enumerate(reversed(itens)):
        with st.container():
            solicitante_nome = item.get('solicitante', 'Desconhecido')
            data_reg = item.get('data_registro', 'Data não informada')
            st.markdown(f"**👤 {solicitante_nome}** — *Cadastrado em: {data_reg}*")

            if tipo_chave == "Atestados":
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"📅 **Início:** {item.get('data_inicio', '-')}")
                with col_b:
                    st.write(f"📅 **Fim:** {item.get('data_fim', '-')}")
                if item.get('observacao'):
                    st.write(f"💬 **Observação:** {item.get('observacao')}")

            elif tipo_chave == "Guias_Planos":
                st.write(f"📚 **Componente:** {item.get('componente', '-')}")
                st.write(f"👨‍🏫 **Docente:** {item.get('docente', '-')}")
                st.write(f"📆 **Bimestre/Ano:** {item.get('bimestre_ano', '-')}")
                if item.get('observacao'):
                    st.write(f"💬 **Observação:** {item.get('observacao')}")

            elif tipo_chave == "Reunioes_Conselhos":
                if item.get('data_inicio'):
                    st.write(f"📅 **Data da Reunião:** {item.get('data_inicio')}")
                if item.get('observacao'):
                    st.write(f"💬 **Pauta/Ata:** {item.get('observacao')}")

            else:
                if item.get('observacao'):
                    st.write(f"💬 **Observação:** {item.get('observacao')}")

            if item.get("arquivo_url"):
                st.markdown(f"📥 **Arquivo Anexado:** [Baixar Arquivo]({item.get('arquivo_url')})")

            st.markdown("---")

        # Insere um bloco de anúncio intercalado a cada 5 registros na listagem
        if (idx + 1) % 5 == 0:
            renderizar_bloco_anuncio()

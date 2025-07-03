import streamlit as st

def add_global_styles():
    """
    Aggiunge stili globali all'intera applicazione.
    Questo aggiunge stili per lo sfondo, elementi di input, pulsanti e altro.
    """
    st.markdown("""
    <style>
        /* Stile generale dell'app */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Stile dello sfondo per il contenuto principale */
        .main {
            background-color: #FAFBFF;
        }
        
        /* Stile dello sfondo per la barra laterale */
        .sidebar .sidebar-content {
            background-color: #F0F4FF;
        }
        
        /* Stile degli elementi di input */
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            border-radius: 8px !important;
            border: 1px solid #E0E5FF !important;
            padding: 0.5rem !important;
            background-color: white !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
            border-color: #4F6AF0 !important;
            box-shadow: 0 0 0 3px rgba(79, 106, 240, 0.2) !important;
        }
        
        /* Stile della casella di selezione */
        .stSelectbox, .stMultiselect {
            border-radius: 8px !important;
        }
        
        /* Stile dei pulsanti */
        .stButton > button {
            border-radius: 8px !important;
            border: 1px solid #4F6AF0 !important;
            background-color: #4F6AF0 !important;
            color: white !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            padding: 0.5rem 1rem !important;
            box-shadow: 0 2px 5px rgba(79, 106, 240, 0.2) !important;
        }
        
        .stButton > button:hover {
            background-color: #3A56E0 !important;
            box-shadow: 0 3px 10px rgba(79, 106, 240, 0.4) !important;
            transform: translateY(-1px) !important;
        }
        
        /* Stile delle caselle di controllo e dei pulsanti di opzione */
        .stCheckbox label, .stRadio label {
            font-weight: 400 !important;
            color: #333333 !important;
        }
        
        .stCheckbox > div[role="radiogroup"] > label > div:first-child, .stRadio > div[role="radiogroup"] > label > div:first-child {
            background-color: white !important;
            border-color: #C0C9F1 !important;
        }
        
        /* Stile delle schede */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0 !important;
            background-color: #EAEEFF !important;
            color: #333333 !important;
            padding: 0.5rem 1rem !important;
            border: 1px solid #E0E5FF !important;
            border-bottom: none !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: white !important;
            color: #4F6AF0 !important;
            font-weight: 600 !important;
            border-top: 2px solid #4F6AF0 !important;
        }
        
        /* Scheda con effetto ombra */
        .shadow-card {
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

def add_page_header(title, icon="💡", description=None):
    """
    Aggiunge un'intestazione di pagina stilizzata con un'icona, un titolo e una descrizione opzionale.
    
    Parametri:
    - title: Il titolo della pagina
    - icon: Icona emoji da mostrare prima del titolo
    - description: Testo descrittivo opzionale da mostrare sotto il titolo
    """
    # Applica prima gli stili globali
    add_global_styles()
    
    # Stili aggiuntivi specifici per l'intestazione
    st.markdown("""
    <style>
        .page-header {
            margin-bottom: 1.5rem;
            background-color: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(79, 106, 240, 0.1);
            border-left: 5px solid #4F6AF0;
        }
        .page-title {
            font-size: 2rem;
            font-weight: bold;
            color: #4F6AF0;
            margin-bottom: 0.5rem;
        }
        .page-description {
            font-size: 1.1rem;
            color: #666;
            margin-bottom: 0.5rem;
        }
        hr.header-divider {
            margin-top: 1rem;
            margin-bottom: 2rem;
            border: none;
            height: 1px;
            background: linear-gradient(to right, #4F6AF0, rgba(79, 106, 240, 0.1));
        }
        .section-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            color: #4F6AF0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(79, 106, 240, 0.2);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Crea l'intestazione
    st.markdown(f"""
    <div class="page-header">
        <div class="page-title">{icon} {title}</div>
        {f'<div class="page-description">{description}</div>' if description else ''}
    </div>
    <hr class="header-divider">
    """, unsafe_allow_html=True)

def add_section_title(title, icon=None):
    """
    Aggiunge un titolo di sezione stilizzato con un'icona opzionale.
    
    Parametri:
    - title: Il titolo della sezione
    - icon: Icona emoji opzionale da mostrare prima del titolo
    """
    icon_text = f"{icon} " if icon else ""
    st.markdown(f"""
    <div class="section-title">{icon_text}{title}</div>
    """, unsafe_allow_html=True)

def create_card(title, content, icon=None, is_success=False, is_warning=False, is_error=False):
    """
    Crea una scheda stilizzata con un titolo, un contenuto e uno stile opzionale.
    
    Parametri:
    - title: Il titolo della scheda
    - content: Il contenuto della scheda
    - icon: Icona emoji opzionale da mostrare prima del titolo
    - is_success: Stile come scheda di successo (verde)
    - is_warning: Stile come scheda di avviso (giallo)
    - is_error: Stile come scheda di errore (rosso)
    """
    # Determina il colore della scheda e il colore di sfondo in base al tipo
    color = "#4F6AF0"  # Blu predefinito
    bg_color = "white"
    border_style = "solid"
    shadow_color = "rgba(79, 106, 240, 0.15)"
    
    if is_success:
        color = "#28a745"  # Verde
        bg_color = "#f8fff9"
        shadow_color = "rgba(40, 167, 69, 0.15)"
    elif is_warning:
        color = "#ffc107"  # Giallo/Arancione
        bg_color = "#fffef8"
        shadow_color = "rgba(255, 193, 7, 0.15)"
    elif is_error:
        color = "#dc3545"  # Rosso
        bg_color = "#fff8f8"
        shadow_color = "rgba(220, 53, 69, 0.15)"
    
    icon_text = f"{icon} " if icon else ""
    
    st.markdown(f"""
    <style>
        .custom-card {{
            border-radius: 12px;
            border: 1px solid rgba({color.replace('#', '')}, 0.3);
            border-left: 5px solid {color};
            padding: 1.25rem;
            background-color: {bg_color};
            margin-bottom: 1.25rem;
            box-shadow: 0 4px 15px {shadow_color};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .custom-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 18px {shadow_color};
        }}
        .card-title {{
            font-weight: 600;
            font-size: 1.1rem;
            margin-bottom: 0.75rem;
            color: {color};
            display: flex;
            align-items: center;
        }}
        .card-content {{
            color: #333;
            line-height: 1.6;
        }}
        .card-icon {{
            font-size: 1.3rem;
            margin-right: 0.5rem;
        }}
    </style>
    
    <div class="custom-card">
        <div class="card-title"><span class="card-icon">{icon}</span>{title}</div>
        <div class="card-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)

def create_metrics_container(metrics_data):
    """
    Crea un contenitore con metriche ben stilizzate.
    
    Parametri:
    - metrics_data: Elenco di dizionari, ognuno contenente le chiavi 'label', 'value' e, facoltativamente, 'icon', 'unit', 'help'
    """
    # Inietta CSS personalizzato per il contenitore delle metriche con animazione e stile migliorato
    st.markdown("""
    <style>
        .metrics-container {
            display: flex;
            flex-wrap: wrap;
            gap: 1.25rem;
            margin-bottom: 2rem;
        }
        .metric-card {
            flex: 1;
            min-width: 160px;
            background: white;
            border-radius: 12px;
            padding: 1.5rem 1rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
            border: 1px solid rgba(230, 235, 255, 0.9);
            position: relative;
            overflow: hidden;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(79, 106, 240, 0.15);
        }
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, #4F6AF0, #7D8EF7);
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: bold;
            color: #4F6AF0;
            margin: 0.5rem 0;
            text-shadow: 0 2px 10px rgba(79, 106, 240, 0.15);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .metric-unit {
            font-size: 1.2rem;
            margin-left: 0.25rem;
            opacity: 0.8;
        }
        .metric-label {
            font-size: 1rem;
            color: #555;
            margin-top: 0.5rem;
            font-weight: 500;
        }
        .metric-icon {
            font-size: 2rem;
            margin-bottom: 0.75rem;
            background: linear-gradient(135deg, #F0F4FF, #E6EBFF);
            width: 60px;
            height: 60px;
            line-height: 60px;
            border-radius: 50%;
            margin: 0 auto 1rem auto;
            box-shadow: 0 4px 15px rgba(79, 106, 240, 0.1);
        }
        
        /* Animazione per le metriche quando appaiono */
        @keyframes metric-appear {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        
        .metric-card {
            animation: metric-appear 0.6s ease forwards;
        }
        
        .metric-card:nth-child(1) { animation-delay: 0.1s; }
        .metric-card:nth-child(2) { animation-delay: 0.2s; }
        .metric-card:nth-child(3) { animation-delay: 0.3s; }
        .metric-card:nth-child(4) { animation-delay: 0.4s; }
    </style>
    """, unsafe_allow_html=True)
    
    # Avvia il contenitore delle metriche
    metrics_html = '<div class="metrics-container">'
    
    # Aggiungi ogni scheda metrica
    for metric in metrics_data:
        icon_html = f'<div class="metric-icon">{metric.get("icon", "")}</div>' if metric.get("icon") else ""
        unit = metric.get("unit", "")
        unit_html = f'<span class="metric-unit">{unit}</span>' if unit else ""
        help_text = f'title="{metric.get("help")}"' if metric.get("help") else ""
        
        metrics_html += f"""
        <div class="metric-card" {help_text}>
            {icon_html}
            <div class="metric-value">{metric["value"]}{unit_html}</div>
            <div class="metric-label">{metric["label"]}</div>
        </div>
        """
    
    # Chiudi il contenitore delle metriche
    metrics_html += '</div>'
    
    # Renderizza l'HTML
    st.markdown(metrics_html, unsafe_allow_html=True)

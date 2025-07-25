import requests
import schedule
import time
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações obrigatórias
URL_ALVO = os.getenv("URL_ALVO")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE") 
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO")
SENHA_EMAIL = os.getenv("SENHA_EMAIL")
INTERVALO_MINUTOS = int(os.getenv("INTERVALO_MINUTOS", "5"))

# Validar configurações
if not all([URL_ALVO, EMAIL_REMETENTE, EMAIL_DESTINATARIO, SENHA_EMAIL]):
    logging.error("Variáveis de ambiente obrigatórias não configuradas!")
    exit(1)

# Garantir que URL tenha protocolo
if not URL_ALVO.startswith(('http://', 'https://')):
    URL_ALVO = 'https://' + URL_ALVO

def verificar_site():
    """Verifica se o site está online."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(URL_ALVO, timeout=30, headers=headers)
        response.raise_for_status()
        
        logging.info(f"Site {URL_ALVO} está online (Status: {response.status_code})")
        return True
        
    except Exception as e:
        mensagem = f"Site {URL_ALVO} está offline! Erro: {str(e)}"
        logging.error(mensagem)
        enviar_alerta(mensagem)
        return False

def enviar_alerta(mensagem):
    """Envia alerta por e-mail."""
    try:
        msg = MIMEText(mensagem, 'plain', 'utf-8')
        msg["Subject"] = f"[ALERTA] Site {URL_ALVO} Offline!"
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = EMAIL_DESTINATARIO
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_REMETENTE, SENHA_EMAIL)
            server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        
        logging.info("E-mail de alerta enviado com sucesso!")
        
    except Exception as e:
        logging.error(f"Erro ao enviar e-mail: {e}")

def main():
    """Função principal - SEM input interativo."""
    logging.info("=== MONITOR DE SITE INICIADO ===")
    logging.info(f"URL monitorada: {URL_ALVO}")
    logging.info(f"E-mail destino: {EMAIL_DESTINATARIO}")
    logging.info(f"Intervalo: {INTERVALO_MINUTOS} minutos")
    
    # Teste inicial automático
    logging.info("Executando verificação inicial...")
    verificar_site()
    
    # Agendar verificações
    schedule.every(INTERVALO_MINUTOS).minutes.do(verificar_site)
    
    logging.info("Monitor ativo! Verificações agendadas.")
    
    # Loop principal
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        time.sleep(10)  # Evitar restart loop muito rápido
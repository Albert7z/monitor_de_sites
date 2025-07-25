import requests
import schedule
import time
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
import logging

# Configurar logging para debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações - com validação
URL_ALVO = os.getenv("URL_ALVO")
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO")
SENHA_EMAIL = os.getenv("SENHA_EMAIL")

# Validar se todas as variáveis necessárias estão definidas
required_vars = {
    "URL_ALVO": URL_ALVO,
    "EMAIL_REMETENTE": EMAIL_REMETENTE,
    "EMAIL_DESTINATARIO": EMAIL_DESTINATARIO,
    "SENHA_EMAIL": SENHA_EMAIL
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    logging.error(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")
    exit(1)

# Validar formato da URL
if not URL_ALVO.startswith(('http://', 'https://')):
    URL_ALVO = 'https://' + URL_ALVO
    logging.info(f"URL corrigida para: {URL_ALVO}")

def verificar_site():
    """Verifica se o site está online e envia um alerta se estiver offline."""
    try:
        logging.info(f"Verificando site: {URL_ALVO}")
        
        # Headers para evitar bloqueios
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(URL_ALVO, timeout=30, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        logging.info(f"Site {URL_ALVO} está online (Status Code: {response.status_code})")
        return True
        
    except requests.exceptions.Timeout:
        mensagem = f"Site {URL_ALVO} está offline! Erro: Timeout após 30 segundos"
        logging.error(mensagem)
        enviar_alerta(mensagem)
        return False
        
    except requests.exceptions.ConnectionError:
        mensagem = f"Site {URL_ALVO} está offline! Erro: Não foi possível conectar"
        logging.error(mensagem)
        enviar_alerta(mensagem)
        return False
        
    except requests.exceptions.HTTPError as e:
        if response.status_code >= 500:
            mensagem = f"Site {URL_ALVO} com erro do servidor! Status Code: {response.status_code}"
            logging.error(mensagem)
            enviar_alerta(mensagem)
            return False
        else:
            logging.warning(f"Site {URL_ALVO} retornou status {response.status_code}, mas considerando como online")
            return True
            
    except requests.exceptions.RequestException as e:
        mensagem = f"Site {URL_ALVO} está offline! Erro: {e}"
        logging.error(mensagem)
        enviar_alerta(mensagem)
        return False

def enviar_alerta(mensagem):
    """Envia um alerta por e-mail."""
    logging.info("Enviando alerta...")
    enviar_email(mensagem)

def enviar_email_teste():
    """Envia um e-mail de teste."""
    mensagem = f"✅ TESTE: Sistema de monitoramento funcionando!\n\nSite monitorado: {URL_ALVO}\nStatus: Online\nHorário do teste: {time.strftime('%d/%m/%Y %H:%M:%S')}"
    enviar_email_personalizado("TESTE: Sistema de Monitoramento", mensagem)

def enviar_email_personalizado(assunto, mensagem):
    """Envia um e-mail personalizado."""
    try:
        msg = MIMEText(mensagem, 'plain', 'utf-8')
        msg["Subject"] = assunto
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = EMAIL_DESTINATARIO
        
        # Tentar diferentes servidores SMTP do Gmail
        smtp_configs = [
            ("smtp.gmail.com", 587, False),  # STARTTLS
            ("smtp.gmail.com", 465, True),   # SSL
        ]
        
        for smtp_server, port, use_ssl in smtp_configs:
            try:
                if use_ssl:
                    server = smtplib.SMTP_SSL(smtp_server, port)
                else:
                    server = smtplib.SMTP(smtp_server, port)
                    server.starttls()
                
                server.login(EMAIL_REMETENTE, SENHA_EMAIL)
                server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
                server.quit()
                
                logging.info("E-mail enviado com sucesso!")
                return True
                
            except Exception as e:
                logging.warning(f"Falha com {smtp_server}:{port} ({'SSL' if use_ssl else 'STARTTLS'}): {e}")
                continue
        
        raise Exception("Todos os servidores SMTP falharam")
        
    except Exception as e:
        logging.error(f"Erro ao enviar e-mail: {e}")
        return False

def enviar_email(mensagem):
    """Envia um e-mail com o alerta de site offline."""
    return enviar_email_personalizado(f"[ALERTA] Site {URL_ALVO} Offline!", mensagem)

def teste_inicial():
    """Executa um teste inicial para verificar se tudo está funcionando."""
    logging.info("=== TESTE INICIAL ===")
    logging.info(f"URL a ser monitorada: {URL_ALVO}")
    logging.info(f"E-mail remetente: {EMAIL_REMETENTE}")
    logging.info(f"E-mail destinatário: {EMAIL_DESTINATARIO}")
    
    # Teste de conexão com o site
    resultado = verificar_site()
    if resultado:
        logging.info("[OK] Teste de conexão com o site: SUCESSO")
    else:
        logging.error("[ERRO] Teste de conexão com o site: FALHOU")
    
    # Teste de envio de e-mail (opcional)
    resposta = input("Deseja testar o envio de e-mail? (s/n): ").lower().strip()
    if resposta == 's':
        logging.info("Testando envio de e-mail...")
        enviar_email_teste()
    
    logging.info("=== FIM DO TESTE ===\n")

if __name__ == "__main__":
    try:
        # Executar teste inicial
        teste_inicial()
        
        # Agendar a verificação do site a cada 5 minutos
        schedule.every(5).minutes.do(verificar_site)
        
        logging.info("Monitor iniciado. Verificando a cada 5 minutos...")
        logging.info("Pressione Ctrl+C para parar")
        
        # Loop principal para executar o agendamento
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto se há tarefas pendentes
            
    except KeyboardInterrupt:
        logging.info("Monitor interrompido pelo usuário")
    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
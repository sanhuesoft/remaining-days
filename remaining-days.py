import json
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

def enviar_correo(reporte_texto, reporte_html):
    # --- CONFIGURACIÓN DEL CORREO ---
    remitente = "sanhuesoft@gmail.com"
    destinatario = "contacto@fabiansanhueza.cl"
    password = os.getenv("GMAIL_PASSWORD")
    
    msg = EmailMessage()
    msg['Subject'] = f"Resumen de Días Hábiles - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = remitente
    msg['To'] = destinatario

    # Definimos la versión en texto plano (por si el gestor de correo no soporta HTML)
    msg.set_content(reporte_texto)

    # Añadimos la versión HTML como alternativa enriquecida
    msg.add_alternative(reporte_html, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return "\n[Correo enviado con éxito en formato HTML]"
    except Exception as e:
        return f"\n[Error al enviar correo: {e}]"

def calcular_dias_detallado():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        fecha_final = datetime.strptime(datos['fecha_termino'], '%Y-%m-%d').date()
        feriados = [datetime.strptime(f, '%Y-%m-%d').date() for f in datos['feriados']]
        vaca_inicio = datetime.strptime(datos['vacaciones_invierno']['inicio'], '%Y-%m-%d').date()
        vaca_fin = datetime.strptime(datos['vacaciones_invierno']['fin'], '%Y-%m-%d').date()
        
        hoy = datetime.now().date()
        if hoy > fecha_final:
            return None, "La fecha de término ya ha pasado."

        sabados, domingos, feriados_habiles, dias_vaca_habiles, dias_habiles_reales = 0, 0, 0, 0, 0

        dia_actual = hoy
        while dia_actual <= fecha_final:
            es_fin_de_semana = False
            if dia_actual.weekday() == 5:
                sabados += 1
                es_fin_de_semana = True
            elif dia_actual.weekday() == 6:
                domingos += 1
                es_fin_de_semana = True
            
            if not es_fin_de_semana:
                es_feriado = dia_actual in feriados
                es_vacacion = vaca_inicio <= dia_actual <= vaca_fin
                
                if es_feriado:
                    feriados_habiles += 1
                elif es_vacacion:
                    dias_vaca_habiles += 1
                else:
                    dias_habiles_reales += 1
            dia_actual += timedelta(days=1)

        resumen = {
            "habiles": dias_habiles_reales,
            "sabados": sabados,
            "domingos": domingos,
            "feriados": feriados_habiles,
            "vacaciones": dias_vaca_habiles
        }
        return resumen, None

    except FileNotFoundError:
        return None, "Error: No se encontró el archivo data.json"
    except Exception as e:
        return None, f"Error: {e}"

if __name__ == "__main__":
    resultado, error = calcular_dias_detallado()
    
    if error:
        print(error)
    else:
        # 1. Reporte para la Consola (Texto plano)
        reporte_consola = (
            "------------- Desglose del Calendario -------------\n"
            f"Sábados descontados: {resultado['sabados']}\n"
            f"Domingos descontados: {resultado['domingos']}\n"
            f"Feriados (en días hábiles): {resultado['feriados']}\n"
            f"Días de vacaciones invierno (Lun-Vie): {resultado['vacaciones']}\n"
            f"{'-' * 51}\n"
            f"TOTAL DÍAS HÁBILES RESTANTES: {resultado['habiles']}\n"
            f"{'-' * 51}"
        )

        # 2. Reporte para el Correo (HTML)
        reporte_html = f"""
        <html>
            <body>
                <p>Buenos días,</p>
                <p></p>
                <p>Me complace informar que quedan <b>{resultado['habiles']}</b> días hábiles.</p>
                <p></p>
                <p>Desglose de días:</p>
                <ul>
                    <li>Sábados descontados: {resultado['sabados']}</li>
                    <li>Domingos descontados: {resultado['domingos']}</li>
                    <li>Feriados (en días hábiles): {resultado['feriados']}</li>
                    <li>Días de vacaciones invierno (Lun-Vie): {resultado['vacaciones']}</li>
                </ul>
                <p></p>
                <p>Atte.<br/>FSV-Bot</p>
            </body>
        </html>
        """

        # 3. Limpiar pantalla e imprimir en consola
        os.system("cls" if os.name == "nt" else "clear")
        print(reporte_consola)

        # 4. Enviar por correo pasándole ambas versiones
        confirmacion = enviar_correo(reporte_consola, reporte_html)
        print(confirmacion)

from datetime import datetime
import re
import json
from parse import Currency, ExpenseCategory, get_expense

def test_email_parsing():
    text = b"""{\n    "subject": "Cargo en Cuenta",\n     "time": "2025-09-12T20:24:24.000Z",
\n     "content": " fraudes\n\n[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca
te llamaremos solicitando tus claves o informaci\xc3\xb3n
personal.\n\n[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca
hagas click en links ni descargues archivos adjuntos de correos
sospechosos.\n\n[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png]
Ingresa a la p\xc3\xa1gina del Banco digitando la direcci\xc3\xb3n en la barra
de tu navegador.\n\nRealiza todo de forma \xc3\xa1gil y simple usando nuestras
aplicaciones*\n\n[http://contentz.mkt8988.com/lp/14944/107981/mi_banco.png]\n\nMi
Banco\n\n[http://contentz.mkt8988.com/lp/14944/107881/MIPASSnuevo.png]\n\n\xe2\x80\x8dMi
Pass\n\n[http://contentz.mkt8988.com/lp/14944/107981/mi_inversion.png]\n\nMi
Inversi\xc3\xb3n\n\n\n\nEncu\xc3\xa9ntranos\n\n[http://contentz.mkt8988.com/lp/14944/107981/facebook.png]
bancochile\xe2\x80\x8e.\xe2\x80\x8dcl\n\n[http://contentz.mkt8988.com/lp/14944/107881/twe-X-BCH.png]
@\xe2\x80\x8dAyudaBancoChile\n\n[http://contentz.mkt8988.com/lp/14944/107981/instagram.png]
@\xe2\x80\x8dBancodechile\n\n[http://contentz.mkt8988.com/lp/14944/107981/telefono_2.png]
Banca Telef\xc3\xb3nica\n\n60\xe2\x80\x8d0 63\xe2\x80\x8d7
37\xe2\x80\x8d37\n\n* Por seguridad, descarga las aplicaciones solo en las
tiendas Google Play y App Store. Las Apps no est\xc3\xa1n disponibles para
tel\xc3\xa9fonos desbloqueados (Jailbreak o Rooteado).\n\nEste mensaje ha sido
enviado a \'richard.penab@gmail.com\' con informaci\xc3\xb3n exclusiva para
clientes del banco. Banco de Chile. Casa Matriz: Ahumada 251, Santiago de
Chile.\nInf\xc3\xb3rmese sobre la garant\xc3\xada estatal de los
dep\xc3\xb3sitos en su banco o en
www\xe2\x80\x8e.\xe2\x80\x8dcmfchile\xe2\x80\x8e.\xe2\x80\x8dcl
\xc2\xa9.\nTodos los derechos reservados.\nHoja
[http://contentz.mkt8988.com/lp/14944/107981/hoja.png] Comprometidos por un
medio ambiente mejor, prefiera los medios digitales al papel impreso.
[http://bancochile.cl/img/PS76JRn/pIolTcsauGpvWr527XL/belEcd0GnH+ooDQ=ttp://bancochile.cl/img/${id}]"\n}"""

    data = json.loads(text.replace(b'\n', b''))

    assert isinstance(data, dict)


def test_amount_data_cc():
    parsed_usd = {
        "subject": "Compra con Terjeta de Crédito",
        "time": "2025-09-12T20:24:24.000Z",
        "content": """ 
        [http://contentz.mkt8988.com/lp/14944/107881/BCH_nuevo.png] Richard Hector Alexander Pe a Bonifaz:Te
        informamos que se ha realizado una compra por US$15,20 con Tarjeta de Crédito ****2662 en Upwork
        -845399262ConnectsDublin IE el 12/09/2025 17:24.Revisa Saldos y Movimientos en App Mi Banco o Banco en
        Línea.Más información 60\u200d0 63\u200d7
        37\u200d37.[http://contentz.mkt8988.com/lp/14944/107981/aleta_BCH.png]Sigue estos consejos para evitar
        fraudes[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca te llamaremos solicitando tus
        claves o información personal.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca hagas click
        en links ni descargues archivos adjuntos de correos
        sospechosos.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Ingresa a la página del Banco
        digitando la dirección en la barra de tu navegador.Realiza todo de forma ágil y simple usando nuestras
        aplicaciones*[http://contentz.mkt8988.com/lp/14944/107981/mi_banco.png]Mi
        Banco[http://contentz.mkt8988.com/lp/14944/107881/MIPASSnuevo.png]\u200dMi
        Pass[http://contentz.mkt8988.com/lp/14944/107981/mi_inversion.png]Mi
        InversiónEncuéntranos[http://contentz.mkt8988.com/lp/14944/107981/facebook.png]
        bancochile\u200e.\u200dcl[http://contentz.mkt8988.com/lp/14944/107881/twe-X-BCH.png]
        @\u200dAyudaBancoChile[http://contentz.mkt8988.com/lp/14944/107981/instagram.png]
        @\u200dBancodechile[http://contentz.mkt8988.com/lp/14944/107981/telefono_2.png] Banca Telefónica60\u200d0
        63\u200d7 37\u200d37* Por seguridad, descarga las aplicaciones solo en las tiendas Google Play y App Store.
        Las Apps no están disponibles para teléfonos desbloqueados (Jailbreak o Rooteado).Este mensaje ha sido
        enviado a 'richard.penab@gmail.com' con información exclusiva para clientes del banco. Banco de Chile. Casa
        Matriz: Ahumada 251, Santiago de Chile.Infórmese sobre la garantía estatal de los depósitos en su banco o
        en www\u200e.\u200dcmfchile\u200e.\u200dcl ©.Todos los derechos reservados.Hoja
        [http://contentz.mkt8988.com/lp/14944/107981/hoja.png] Comprometidos por un medio ambiente mejor, prefiera
        los medios digitales al papel impreso. 
        [http://bancochile.cl/img/PS76JRn/pIolTcsauGpvWl9Atyie7MwN8CHjl3MRFXk=ttp://bancochile.cl/img/${id}]
        """.replace("\n", "")
    }

    parsed_clp = {
        "subject": "Compra con Terjeta de Crédito",
        "time": "2025-09-12T20:24:24.000Z",
        "content": """ 
        [http://contentz.mkt8988.com/lp/14944/107881/BCH_nuevo.png] Richard Hector Alexander Pe a Bonifaz:Te
        informamos que se ha realizado una compra por $7.050 con Tarjeta de Crédito ****2662 en Upwork
        -845399262ConnectsDublin IE el 09/09/2025 17:24.Revisa Saldos y Movimientos en App Mi Banco o Banco en
        Línea.Más información 60\u200d0 63\u200d7
        37\u200d37.[http://contentz.mkt8988.com/lp/14944/107981/aleta_BCH.png]Sigue estos consejos para evitar
        fraudes[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca te llamaremos solicitando tus
        claves o información personal.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Nunca hagas click
        en links ni descargues archivos adjuntos de correos
        sospechosos.[http://contentz.mkt8988.com/lp/14944/107981/ticket_BCH.png] Ingresa a la página del Banco
        digitando la dirección en la barra de tu navegador.Realiza todo de forma ágil y simple usando nuestras
        aplicaciones*[http://contentz.mkt8988.com/lp/14944/107981/mi_banco.png]Mi
        Banco[http://contentz.mkt8988.com/lp/14944/107881/MIPASSnuevo.png]\u200dMi
        Pass[http://contentz.mkt8988.com/lp/14944/107981/mi_inversion.png]Mi
        InversiónEncuéntranos[http://contentz.mkt8988.com/lp/14944/107981/facebook.png]
        bancochile\u200e.\u200dcl[http://contentz.mkt8988.com/lp/14944/107881/twe-X-BCH.png]
        @\u200dAyudaBancoChile[http://contentz.mkt8988.com/lp/14944/107981/instagram.png]
        @\u200dBancodechile[http://contentz.mkt8988.com/lp/14944/107981/telefono_2.png] Banca Telefónica60\u200d0
        63\u200d7 37\u200d37* Por seguridad, descarga las aplicaciones solo en las tiendas Google Play y App Store.
        Las Apps no están disponibles para teléfonos desbloqueados (Jailbreak o Rooteado).Este mensaje ha sido
        enviado a 'richard.penab@gmail.com' con información exclusiva para clientes del banco. Banco de Chile. Casa
        Matriz: Ahumada 251, Santiago de Chile.Infórmese sobre la garantía estatal de los depósitos en su banco o
        en www\u200e.\u200dcmfchile\u200e.\u200dcl ©.Todos los derechos reservados.Hoja
        [http://contentz.mkt8988.com/lp/14944/107981/hoja.png] Comprometidos por un medio ambiente mejor, prefiera
        los medios digitales al papel impreso. 
        [http://bancochile.cl/img/PS76JRn/pIolTcsauGpvWl9Atyie7MwN8CHjl3MRFXk=ttp://bancochile.cl/img/${id}]
        """.replace("\n", "")
    }


    expense = get_expense(parsed_usd["content"])
    assert expense.value == 15.2
    assert expense.currency == Currency.USD
    assert expense.category == ExpenseCategory.ONLINE_PLATFORM, f"Invalid category for {expense.commerce}"
    assert expense.date == datetime(2025, 9, 12, 17, 24)

    expense = get_expense(parsed_clp["content"])
    assert expense.value == 7050.0
    assert expense.currency == Currency.CLP
    assert expense.category == ExpenseCategory.ONLINE_PLATFORM
    assert expense.date == datetime(2025, 9, 9, 17, 24)



